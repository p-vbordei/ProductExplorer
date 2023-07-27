# %% [markdown]
# ## STRUCTURE
# - Read Scraped Reviews & Products
#     - Create the asin list
#     - Create reviews lists, parse by ASIN
#     - Create products lists, parse by ASIN
# - Run sentiment analysis on reviews
# - Save results
# 
# 

# %%
import pandas as pd

from dotenv import load_dotenv
import os

load_dotenv()
HUGGINGFACEHUB_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN')

if os.getenv("HUGGINGFACEHUB_API_TOKEN") is not None:
    print ("HUGGINGFACEHUB_API_TOKEN is ready")
else:
    print ("HUGGINGFACEHUB_API_TOKEN environment variable not found")

# %%
# asin_list_path = './data/external/asin_list.csv'
asin_list_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/external/asin_list.csv'
asin_list = pd.read_csv(asin_list_path)['asin'].tolist()

# %%
def read_data(folder_path):
    reviews = pd.DataFrame()
    
    for file_name in os.listdir(folder_path):
        if file_name.startswith("reviews"):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)
            reviews = pd.concat([reviews, df])
    
    return reviews

# %%
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load the pre-trained BERT model for sentiment analysis
model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

def get_sentiment_probabilities(text):
    # Tokenize the text and truncate if it's too long
    inputs = tokenizer.encode_plus(text, return_tensors="pt", truncation=True, max_length=512)
    outputs = model(**inputs)
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=-1)

    # Combine probabilities for positive (4-5 stars) and negative (1-2 stars) sentiment
    positive = probabilities[0, 3] + probabilities[0, 4]
    negative = probabilities[0, 0] + probabilities[0, 1]

    return positive.item(), negative.item()


def process_review(row):
    review_text = row["review"]
    print(f"Review text: {review_text}")

    # Check if review_text is a valid string
    if not isinstance(review_text, str):
        return pd.Series([0.5, 0.5])

    positive, negative = get_sentiment_probabilities(review_text)
    print(f"Sentiment allocation - Positive: {positive}, Negative: {negative}")
    
    return pd.Series([positive, negative])


# %%
def read_data_from_filtered_h10_folder(folder_path):
    reviews = pd.DataFrame()
    
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        df = pd.read_csv(file_path)
        reviews = pd.concat([reviews, df])
    
    return reviews


# %%
reviews_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/raw/RaisedGardenBed/h10reviews'
# reviews = read_data(reviews_path)
reviews = read_data_from_filtered_h10_folder(reviews_path)

# %%
try:
    reviews.rename(columns={'Body': 'review'}, inplace=True)
except:
    pass

# %%
# Apply the sentiment analysis to the "review" column
reviews[["positive_sentiment", "negative_sentiment"]] = reviews.apply(process_review, axis=1)

# %%
# save_path = './data/interim/reviews_with_sentiment.csv'
save_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/reviews_with_sentiment.csv'
reviews.to_csv(save_path, index=False)

# %%



