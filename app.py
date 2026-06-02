import streamlit as st
import pandas as pd
import numpy as np
import joblib
from scipy.sparse import hstack
from google import genai
from google.genai import types

# genai
client = genai.Client(api_key="AIzaSyCpzr_vdsbyq6sBZ7SJ8zvbclFnfSy7VOE")

# load artifacts
rf = joblib.load("models/rf_model.pkl")

tfidf = joblib.load("models/tfidf.pkl")
mlb = joblib.load("models/genre_encoder.pkl")
ohe_lang = joblib.load("models/language_encoder.pkl")

author_counts = joblib.load("models/author_counts.pkl")
publisher_counts = joblib.load("models/publisher_counts.pkl")

target_encoder = joblib.load(
    "models/target_encoder.pkl"
)

train_columns = joblib.load(
    "models/train_columns.pkl"
)

# dropdown values
authors = sorted(
    author_counts.index.tolist()
)

publishers = sorted(
    publisher_counts.index.tolist()
)

languages = [
    "English",
    "Arabic",
    "Hindi",
    "Tamil",
    "Telugu",
    "unknown"
]

genres = sorted(
    mlb.classes_.tolist()
)

st.title(
    "Book Popularity Predictor"
)

# inputs
author = st.selectbox(
    "Author",
    authors
)

publisher = st.selectbox(
    "Publisher",
    publishers
)

genre = st.multiselect(
    "Genres",
    genres
)

language = st.selectbox(
    "Language",
    languages
)

pages = st.number_input(
    "Pages",
    1,
    5000,
    200
)

year = st.number_input(
    "Year",
    1000,
    2026,
    2020
)

price = st.number_input(
    "Price",
    0.0,
    2000.0,
    300.0
)

rating = st.slider(
    "Rating",
    0.0,
    5.0,
    4.0
)

description = st.text_area(
    "Description"
)

if st.button("Predict"):

    # frequency encoding
    author_freq = np.log1p(
        author_counts.get(author, 0)
    )

    publisher_freq = np.log1p(
        publisher_counts.get(publisher, 0)
    )

    # genre
    genre_vec = mlb.transform(
        [genre]
    )

    # language
    lang_input = pd.DataFrame(
        {
            "language_name": [language]
        }
    )

    lang_vec = ohe_lang.transform(
        lang_input
    )

    # tfidf
    if language == "English":
        desc_input = description
    else:
        desc_input = ""

    desc_vec = tfidf.transform(
        [desc_input]
    )

    # numeric features
    numeric = pd.DataFrame(
        [[
            pages,
            rating,
            year,
            price,
            author_freq,
            publisher_freq
        ]],
        columns=[
            "pages",
            "rating",
            "year",
            "price",
            "author_freq",
            "publisher_freq"
        ]
    )

    # combine
    combined = hstack([
        numeric.values,
        genre_vec,
        lang_vec,
        desc_vec
    ])

    final_df = pd.DataFrame(
        combined.toarray(),
        columns=train_columns
    )

    final_df = final_df.reindex(
        columns=train_columns,
        fill_value=0
    )

    pred = rf.predict(
        final_df
    )

    result = (
        target_encoder
        .inverse_transform(pred)[0]
    )

    proba = rf.predict_proba(
        final_df
    )[0]

    confidence = max(proba)

    # prediction
    st.success(
        f"Predicted Popularity: {result}"
    )

    # confidence
    st.info(
        f"Confidence Score: {confidence:.1%}"
    )

    prompt = f"""
You are explaining a machine learning prediction.

Prediction:
{result}

Prediction confidence:
{confidence}

Book Inputs:
Pages: {pages}
Rating: {rating}
Year: {year}
Price(in inr): {price}

Genres:
{genre}

Language:
{language}

Description:
{description[:300]}

Explain:
1. Why this popularity was predicted
2. Mention positive and negative signals
3. How to improve book reach

Keep under 150 words.
"""

    with st.spinner(
        "Generating Explanation"
    ):

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        st.subheader(
            "Explanation"
        )

        st.write(
            response.text
        )

