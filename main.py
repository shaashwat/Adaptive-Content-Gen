import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("PERPLEXITY_API_KEY")

def perplexity_search(query, strategies):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {API_KEY}"
    }
    
    strategy_prompt = ", ".join([f"{s}: {v}%" for s, v in strategies.items() if v > 0])
    
    data = {
        "model": "llama-3.1-70b-instruct",
        "messages": [
            {"role": "system", "content": "You are an assistant helping teachers find publicly available content tailored to their students' learning strategies. Provide a concise summary and relevant links."},
            {"role": "user", "content": f"Find educational content on '{query}' tailored to the following learning strategies: {strategy_prompt}. Provide a brief summary and relevant links for each strategy with a non-zero percentage."}
        ]
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

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
            st.subheader("Search Results:")
            st.markdown(results)
        else:
            st.warning("Please enter a topic to search.")

if __name__ == "__main__":
    main()