import streamlit as st
import requests
import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from fpdf import FPDF
import base64

# Load environment variables
load_dotenv()

# Get API keys from environment variables
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def perplexity_search(query, strategies):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {PERPLEXITY_API_KEY}"
    }
    
    # Filter strategies above 10% and sort by percentage
    filtered_strategies = sorted(
        [(s, v) for s, v in strategies.items() if v > 10],
        key=lambda x: x[1],
        reverse=True
    )
    
    strategy_prompt = ", ".join([f"{s}: {v}%" for s, v in filtered_strategies])
    
    data = {
        "model": "llama-3.1-70b-instruct",
        "messages": [
            {"role": "system", "content": "You are an assistant helping teachers find publicly available content tailored to their students' learning strategies. Provide a concise summary and relevant links."},
            {"role": "user", "content": f"Find educational content on '{query}' tailored to the following learning strategies (listed in order of importance): {strategy_prompt}. Prioritize strategies with higher percentages. For each strategy above 10%, provide a brief summary and relevant links, with more emphasis on higher-ranked strategies."}
        ]
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

def generate_learning_plan(results, days, strategies):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.1, api_key=OPENAI_API_KEY)
    
    template = """
    Based on the following search results:
    {results}

    Create a {days}-day learning plan that incorporates the resources mentioned above. 
    Prioritize the following learning strategies: {strategies}. 
    For each day, recommend specific resources and activities that align with the prioritized strategies.
    Include relevant links from the search results in your recommendations.

    The learning plan should be structured as follows:
    Day 1:
    - Activity 1: [Description] (Strategy: [Related Strategy]) [Link if applicable]
    - Activity 2: [Description] (Strategy: [Related Strategy]) [Link if applicable]

    Day 2:
    ...

    Please provide a comprehensive and well-structured learning plan.
    """

    prompt = ChatPromptTemplate.from_template(template)

    chain = LLMChain(llm=llm, prompt=prompt)

    strategy_prompt = ", ".join([f"{s}: {v}%" for s, v in strategies.items() if v > 10])
    
    plan = chain.run(results=results, days=days, strategies=strategy_prompt)
    return plan

def create_pdf(content, plan):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Search Results", ln=True, align='C')
    pdf.multi_cell(0, 10, txt=content)
    
    pdf.add_page()
    pdf.cell(200, 10, txt="Learning Plan", ln=True, align='C')
    pdf.multi_cell(0, 10, txt=plan)
    
    return pdf.output(dest='S').encode('latin-1')

def get_pdf_download_link(pdf_bytes, filename):
    b64 = base64.b64encode(pdf_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF</a>'

def main():
    st.set_page_config(page_title="Teacher's Content Finder", layout="wide")
    
    st.title("Teacher's Content Finder")
    st.write("Find publicly available content tailored to your students' learning strategies.")

    query = st.text_input("Enter the topic you want to teach:")

    st.write("Adjust the importance of each learning strategy:")
    
    strategies = {
        "Apprentice - Mentor-Student interaction": st.slider("Apprentice - Mentor-Student interaction", 0, 100, 20, help="Content presented in a systematic step-by-step procedural way"),
        "Incidental - Case Studies": st.slider("Incidental - Case Studies", 0, 100, 20, help="Content presented in real-life scenarios or case studies"),
        "Inductive - Examples": st.slider("Inductive - Examples", 0, 100, 20, help="Content presented with examples that illustrate the principle clearly"),
        "Deductive - Application": st.slider("Deductive - Application", 0, 100, 20, help="Content presented with interactive animations for learning by doing"),
        "Discovery - Experimentation": st.slider("Discovery - Experimentation", 0, 100, 20, help="Content presented in a simulated learning environment for self-discovery")
    }

    if st.button("Find Content"):
        if query:
            with st.spinner("Searching for content..."):
                results = perplexity_search(query, strategies)
            st.session_state.results = results
            st.session_state.show_plan_button = True
        else:
            st.warning("Please enter a topic to search.")

    if 'results' in st.session_state:
        st.subheader("Search Results:")
        st.markdown(st.session_state.results)

    if st.session_state.get('show_plan_button', False):
        days = st.number_input("Enter the number of days for the learning plan:", min_value=1, max_value=30, value=7)
        if st.button("Create Plan"):
            with st.spinner("Generating learning plan..."):
                plan = generate_learning_plan(st.session_state.results, days, strategies)
            st.session_state.plan = plan
            
    if 'plan' in st.session_state:
        st.subheader("Learning Plan:")
        st.markdown(st.session_state.plan)
        
        # Create PDF
        pdf_bytes = create_pdf(st.session_state.results, st.session_state.plan)
        st.markdown(get_pdf_download_link(pdf_bytes, "learning_plan.pdf"), unsafe_allow_html=True)

if __name__ == "__main__":
    main()