import streamlit as st
import numpy as np
import pandas as pd
import requests
from difflib import get_close_matches

# Load the main dataset and similarity score matrix with caching
@st.cache_data(ttl=86400)
def load_data():
    pt = pd.read_csv('anime_dataset.csv', index_col=0, dtype={'name': 'string'})
    similarity_score = np.load('similarity_score.npy').astype(np.float32)
    return pt, similarity_score

# Load popular anime DataFrame
@st.cache_data(ttl=86400)
def load_popular_anime():
    popular_df = pd.read_csv('popular_anime.csv', usecols=['name'], dtype={'name': 'string'})
    return popular_df

# Load data
pt, similarity_score = load_data()
popular_df = load_popular_anime()

# Fetch anime details using AniList API
def fetch_anime_details(anime_title):
    query = '''
    query ($search: String) {
        Media (search: $search, type: ANIME) {
            title {
                romaji
            }
            coverImage {
                large
            }
            siteUrl
        }
    }
    '''
    variables = {"search": anime_title}
    url = "https://graphql.anilist.co"
    response = requests.post(url, json={'query': query, 'variables': variables})
    
    if response.status_code == 200:
        data = response.json()
        anime_data = data.get("data", {}).get("Media", None)
        if anime_data:
            return {
                "title": anime_data["title"]["romaji"],
                "image": anime_data["coverImage"]["large"],
                "link": anime_data["siteUrl"]
            }
    return None

# Recommendation function
def recommend(anime_name, pt, similarity_score):
    closest_matches = get_close_matches(anime_name, pt.index, n=1, cutoff=0.6)
    
    if closest_matches:
        matched_name = closest_matches[0]
        st.write(f"Did you mean: **{matched_name}**?")
        
        index = pt.index.get_loc(matched_name)
        similar_items = sorted(list(enumerate(similarity_score[index])), key=lambda x: x[1], reverse=True)[1:6]
        
        suggestions = [pt.index[i[0]] for i in similar_items]
        
        details = []
        for anime in suggestions:
            anime_details = fetch_anime_details(anime)
            if anime_details:
                details.append(anime_details)
        return details
    else:
        st.write("No similar anime found. Please try a different title.")
        return []

# Main layout
st.title("Anime Recommendation System")

# Layout with main content and sidebar on the right
main_col, sidebar_col = st.columns([3, 1], gap="small")

with main_col:
    st.write("## Search for an Anime")

    # Search box for user input
    anime_input = st.text_input("Enter Anime Title:")

    # Display recommendations based on user input
    if st.button("Get Recommendations"):
        if anime_input:
            recommendations = recommend(anime_input, pt, similarity_score)
            if recommendations:
                st.write("### Recommended Anime")
                
                # Display recommendations in a horizontal layout
                columns = st.columns(len(recommendations))
                for idx, anime in enumerate(recommendations):
                    with columns[idx]:
                        st.image(anime["image"], caption=anime["title"], use_column_width=True)
                        st.write(f"[Watch on AniList]({anime['link']})")
            else:
                st.write("No recommendations found.")
        else:
            st.write("Please enter an anime title.")

# Sidebar column for popular anime
with sidebar_col:
    # Add a title with tabs (Note: Streamlit doesn't natively support tabs in the sidebar)
    st.write("## Top Anime")
    st.write("Today | Week | Month")  # Static text for simplicity

    # Custom CSS to style the sidebar section
    st.markdown("""
        <style>
        .anime-entry {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .anime-rank {
            font-size: 22px;
            font-weight: bold;
            color: white;
            margin-right: 10px;
        }
        .anime-title {
            font-size: 16px;
            font-weight: bold;
            color: white;
        }
        .anime-views {
            font-size: 14px;
            color: gray;
        }
        .anime-image {
            border-radius: 5px;
            width: 40px;
            height: 60px;
            margin-right: 10px;
        }
        .anime-details {
            display: flex;
            flex-direc000000000000000000000000tion: column;
        }
        </style>
    """, unsafe_allow_html=True)

    # Display the list of top anime in a structured format
    for idx, title in enumerate(popular_df['name'].head(10), start=1):
        anime_details = fetch_anime_details(title)
        if anime_details:
            st.markdown(f"""
                <div class="anime-entry">
                    <span class="anime-rank">{idx}</span>
                    <img src="{anime_details['image']}" class="anime-image"/>
                    <div class="anime-details">
                        <span class="anime-title">{anime_details['title']}</span>
                        <span class="anime-views">👁️ {np.random.randint(10000, 100000)} views</span>
                        <a href="{anime_details['link']}" target="_blank">Watch on AniList</a>
                    </div>
                </div>
            """, unsafe_allow_html=True)