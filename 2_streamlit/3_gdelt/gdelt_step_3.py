import streamlit as st
import requests

EXTERNAL_SENTIMENT_API = # INSERT API ENDPOINT HERE (Check Moodle)


st.title("News Search with GDELT")

query = st.text_input("Enter your search query")

lang = st.selectbox("Select language", ["eng", "spa"])

API_NEWS = f'https://api.gdeltproject.org/api/v2/doc/doc?query=%22{query}%22%20sourcelang:{lang}&startdatetime=20190920133005&enddatetime=20190920143005&format=json'

if st.button("Search"):
    data = requests.get(API_NEWS, headers={'User-Agent': 'request'})

    results = data.json()
    if 'articles' in results:
        for result in results['articles']:

            st.subheader(result['title'])

            with st.spinner("Analyzing sentiment..."):
                sentiment_query = f"{EXTERNAL_SENTIMENT_API}?text={result['title']}&lang=en"
                sentiment_response = requests.get(sentiment_query)

            if sentiment_response.status_code == 200:
                sentiment_data = sentiment_response.json()
                sentiment = sentiment_data['Sentiment']
                if sentiment == "POSITIVE":
                    st.badge(f"{sentiment}", color="blue", icon="✔️")
                elif sentiment == "NEGATIVE":
                    st.badge(f"{sentiment}", color="red", icon="❌")
                else:
                    st.badge(f"{sentiment}", color="gray")
            else:
                sentiment = "UNKNOWN"

            st.link_button("Read more", url=result['url'])
            st.write("---")
