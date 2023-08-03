# %% [markdown]
# ## STRUCTURE
# - Read Scraped Reviews & Products
#     - Create the asin list
#     - Create reviews lists, parse by ASIN
#     - Create products lists, parse by ASIN
# - Save results
# 
# 

# %%
import pandas as pd

from dotenv import load_dotenv
import os

load_dotenv()
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
# save_path = './data/interim/reviews.csv'
save_path = '/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/reviews.csv'
reviews.to_csv(save_path, index=False)
