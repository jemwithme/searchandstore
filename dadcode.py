import streamlit as st
import requests
import re
from urllib.parse import urlparse

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def verify_url(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code < 400
    except requests.RequestException:
        return False

def extract_and_verify_urls(text):
    urls = re.findall(r'https?://\S+', text)
    verified_urls = []
    for url in urls:
        if is_valid_url(url):
            clean_url = url.rstrip('.)') # Remove trailing punctuation
            if verify_url(clean_url):
                verified_urls.append(clean_url)
    return verified_urls

def search_perplexity(query, search_type, region=None):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {st.secrets['PERPLEXITY_API_KEY']}"
    }
    
    system_content = """You are an AI assistant for a chemical sourcing business. Your task is to find direct chemical producers 
                 based on the given product query. Focus solely on manufacturers and exclude any aggregators, middlemen, or trading companies.

                Provide a list of potential chemical producers in the following format:
                1. Company Name - Location (City, Country) - Main Products - Website - Contact Information
                2. ...

                Requirements:
                - Include ONLY companies that you are highly confident are direct producers of the specified chemical.
                - For each company, briefly explain why it's a direct producer (e.g., mention of production facilities, capacity, etc.).
                - If available, mention any certifications, specializations, or notable customers.
                - If possible, mention the company's year of establishment or years of experience in the industry.
                - Ensure all website URLs are complete and begin with http:// or https://.
                - If you're unsure about any information, especially URLs or contact details, state "Not verified" instead of guessing.

                Quality is more important than quantity and quality is best defined with price - only include companies you're confident about."""

    user_content = f"Find direct {'global' if search_type == 'Global' else region} chemical producers for the product: {query}. Focus on accuracy over quantity."
    
    if search_type == 'Regional':
        system_content += f"\n\nFocus your search on producers located in the {region} region."
    
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        return f"Error occurred: {str(e)}"

def process_results(results):
    processed_results = results
    urls = extract_and_verify_urls(results)
    for url in urls:
        if verify_url(url):
            processed_results = processed_results.replace(url, f"[Verified] {url}")
        else:
            processed_results = processed_results.replace(url, f"[Unverified] {url}")
    return processed_results

st.title("Global Chemical Producer Search")
st.write("This tool finds direct manufacturers worldwide or in specific regions with an emphasis on accuracy.")

search_type = st.radio("Select search type:", ('Global', 'Regional'))

if search_type == 'Regional':
    regions = ['North America', 'South America', 'Europe', 'Asia', 'Africa', 'Oceania']
    region = st.selectbox("Select a region:", regions)

query = st.text_input("Enter the name of the chemical product you're looking for:")

if st.button("Search"):
    if query:
        with st.spinner("Searching for producers and verifying information..."):
            if search_type == 'Global':
                results = search_perplexity(query, search_type)
            else:
                results = search_perplexity(query, search_type, region)
            processed_results = process_results(results)
            st.markdown(processed_results)
    else:
        st.warning("Please enter a chemical product name.")

st.info("Note: This search provides results for direct manufacturers. URLs are verified where possible.")
