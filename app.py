import streamlit as st
import pandas as pd
import re
import io
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# ---------------------------
# NLTK Setup
# ---------------------------
nltk.download("stopwords")
nltk.download("wordnet")

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

# ---------------------------
# Text Cleaning Functions
# ---------------------------
def clean_text(text):
    if pd.isnull(text):
        return ""
    text = text.lower()
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = " ".join([lemmatizer.lemmatize(w) for w in text.split() if w not in stop_words])
    return text

VAGUE_PHRASES = [
    "human error", "not known", "unaware", "unable to identify",
    "informed concerned ", "na", "n/a", "not available", "lack of communication"
]

def is_vague(text, min_words=5):
    if len(text.split()) < min_words:
        return True
    for phrase in VAGUE_PHRASES:
        if phrase in text:
            return True
    return False

def score_quality(text):
    if pd.isnull(text) or len(text.strip()) == 0:
        return 0
    word_count = len(text.split())
    if word_count < 5:
        return 1
    elif any(p in text for p in VAGUE_PHRASES):
        return 2
    elif word_count >= 10:
        return 4
    else:
        return 3

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("🩺 QA Incident RCA/CA/PA Analyzer")

uploaded_file = st.file_uploader("Upload Incident Excel File", type=["xlsx"])

if uploaded_file is not None:
    # Load all sheets
    all_sheets = pd.read_excel(uploaded_file, sheet_name=None)

    # Regex to match "Month Year" like "January 2025"
    month_year_pattern = re.compile(
        r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$"
    )

    sheet_data = []
    for sheet_name, df in all_sheets.items():
        if month_year_pattern.match(sheet_name):
            df["Month"] = sheet_name
            sheet_data.append(df)

    if sheet_data:
        combined_df = pd.concat(sheet_data, ignore_index=True)

        # Clean text
        combined_df["RCA_clean"] = combined_df["RCA"].apply(clean_text)
        combined_df["CA_clean"] = combined_df["CA"].apply(clean_text)
        combined_df["PA_clean"] = combined_df["PA"].apply(clean_text)

        # Vague flags
        combined_df["RCA_vague"] = combined_df["RCA"].fillna("").apply(lambda x: is_vague(x.lower()))
        combined_df["CA_vague"] = combined_df["CA"].fillna("").apply(lambda x: is_vague(x.lower()))
        combined_df["PA_vague"] = combined_df["PA"].fillna("").apply(lambda x: is_vague(x.lower()))

        # Quality scores
        combined_df["RCA_score"] = combined_df["RCA_clean"].apply(score_quality)
        combined_df["CA_score"] = combined_df["CA_clean"].apply(score_quality)
        combined_df["PA_score"] = combined_df["PA_clean"].apply(score_quality)

        st.success("✅ Analysis complete!")

        # Show preview
        st.dataframe(combined_df.head(20))

        # Download button
        output = io.BytesIO()
        combined_df.to_excel(output, index=False)
        st.download_button(
            "📥 Download Processed Data",
            data=output.getvalue(),
            file_name="RCA_Analysis_Output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("No valid 'Month Year' sheets found in this file.")

