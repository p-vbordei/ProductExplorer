# etl.py

import pandas as pd
from google.cloud import firestore
import nest_asyncio
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_asins(asin_filepath):
    """
    Load ASIN list from a CSV file

    Parameters:
        asin_filepath (Path): Path to CSV file containing 'asin' column

    Returns:
        asins (List[str]): List of ASIN strings

    Raises:
        ValueError: If asin_filepath does not exist
        FileNotFoundError: If asin_filepath does not point to a file
    """
    
    if not asin_filepath.exists():
        raise ValueError(f"File {asin_filepath} does not exist.")

    if not asin_filepath.is_file():
        raise FileNotFoundError(f"{asin_filepath} is not a file.")

    df = pd.read_csv(asin_filepath)
    asins = df["asin"].tolist()

    if not asins:
        logger.warning("No ASINs found in CSV file.")
    
    return asins


async def fetch_reviews_async(asin, db):
    """
    Asynchronously fetch reviews for a single ASIN using Firestore.

    Parameters:
        asin (str): ASIN string
        db (google.cloud.firestore.Client): Initialized Firestore client

    Returns:
        reviews (List[dict]): List of review dicts
    
    Raises:
        ValueError: If invalid ASIN provided
    """
    
    if not isinstance(asin, str):
        raise ValueError("ASIN must be a string.")

    if len(asin) != 10:
        raise ValueError(f"Invalid ASIN: {asin}. Must be 10 characters.")

    doc_ref = db.collection("products").document(asin)

    if not doc_ref.get().exists:
        logger.warning(f"No product document found for ASIN {asin}.")
        return []

    product_reviews = []
    
    async for doc in doc_ref.collection("reviews").stream_async():
        product_reviews.append(doc.to_dict())
        
    return product_reviews


async def extract_reviews_async(asins, db):
    """
    Asynchronous version of extract_reviews using asyncio.

    Parameters:
        asins (List[str]): List of ASIN strings
        db (google.cloud.firestore.Client): Initialized Firestore client

    Returns:
        reviews (List[List[dict]]): Nested list of review dicts per ASIN
    """

    if not isinstance(asins, list):
        raise TypeError("asins must be a list.")

    if not all(isinstance(asin, str) for asin in asins):
        raise ValueError("All ASINs must be strings.")

    tasks = []

    for asin in asins:
        task = asyncio.create_task(fetch_reviews_async(asin, db))
        tasks.append(task)

    reviews = await asyncio.gather(*tasks)
    
    return reviews


def prepare_reviews(extracted_reviews):
    """
    Clean, process and transform raw review data.

    Parameters:
        extracted_reviews (List[List[dict]]): Extracted review data

    Returns:
        df (pandas.DataFrame): Cleaned and transformed review data
    
    Raises:
        ValueError: If invalid input format provided
    """

    if not isinstance(extracted_reviews, list):
        raise ValueError("extracted_reviews must be a list.")

    if not extracted_reviews:
        logger.warning("No reviews provided.")
        return pd.DataFrame()

    # Flatten nested list
    flattened = [review for batch in extracted_reviews for review in batch]
    
    # Transform into dataframe 
    df = pd.DataFrame(flattened)

    # Validate dataframe
    if len(df) == 0:
        logger.warning("No reviews loaded into dataframe.")
        return df

    if "review" not in df.columns:
        raise ValueError("Dataframe missing required 'review' column.")

    # Cleaning and transformation logic

    # Remove special characters
    df['clean_review'] = df['review'].str.replace(r'[^a-zA-Z0-9\s]+', '')

    # Remove duplicates
    df.drop_duplicates(subset=['clean_review'], inplace=True)

    # Remove reviews with less than 5 words
    df['word_count'] = df['clean_review'].str.split().apply(len)
    df = df[df['word_count'] > 5]

    # Lemmatize text
    from textblob import Word
    df['clean_review'] = df['clean_review'].apply(lambda x: " ".join([Word(word).lemmatize() for word in x.split()]))

    # Convert to lowercase
    df['clean_review'] = df['clean_review'].str.lower()

    # Remove stopwords
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words('english'))
    df['clean_review'] = df['clean_review'].apply(lambda x: ' '.join([word for word in x.split() if word not in (stop_words)]))

    # Save cleaned text 
    df['clean_review_text'] = df['clean_review']

    # Optionally drop original review text
    df.drop(columns=['review', 'clean_review'], inplace=True)

    return df