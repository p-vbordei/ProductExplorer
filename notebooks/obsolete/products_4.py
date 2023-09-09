# %% [markdown]
# ## STRUCTURE
# - Eliminate a part of the general product information in order to minimize token cost
#     - Read general product data
#     - Define minimum required product information and save as new dictionary
#     - Save to json

# %%
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import json

load_dotenv()

# from sqlalchemy import create_engine, text
# engine = create_engine('postgresql://postgres:mysecretpassword@localhost:5432/postgres')



# %%
def num_tokens_from_string(string: str, encoding_name = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

# %%
# query = text("SELECT * FROM products WHERE asin IN :asin_list")
# product = pd.read_sql_query(query, engine, params={"asin_list": tuple(asin_list)})
# product['product_description_data'] = product['product_description_data'].apply(lambda x: eval(x))

# %%
# Read data about the product

with open('/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/summarised_product_information.json') as file:
    json_string = file.read()
    general_product_data = json.loads(json_string)

# %%
general_product_data.keys()

# %%
general_product_keys_to_keep = ['Product Summary', 'product_summary','In_the_Box', 'in_the_box', 'technical_facts', 'features', 'how_the_product_is_used',  'where_the_product_is_used', 'user_description']

# %%
short_product_data = {}

for key in general_product_keys_to_keep:
    if key in general_product_data.keys():
        short_product_data[key] = general_product_data[key]

# %%
print(f"The General Product Data has {num_tokens_from_string(str(general_product_data))} tokens")

for key in general_product_data.keys():
    print(f"{key} has {num_tokens_from_string(general_product_data[key])} tokens")

print('  ')

print(f"The Short Product Data has {num_tokens_from_string(str(short_product_data))} tokens")

for key in general_product_keys_to_keep:
    if key in general_product_data.keys():
        print(f"{key} has {num_tokens_from_string(general_product_data[key])} tokens")

# %%
with open('/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/short_product_information.json', 'w') as f:
    json.dump(short_product_data, f)

# %%
# Check if the JSON file is valid
import json
with open('/Users/vladbordei/Documents/Development/ProductExplorer/data/interim/short_product_information.json') as file:
    try:
        data = json.load(file)
    except json.JSONDecodeError as e:
        print("JSONDecodeError:", e)
        file.seek(0)
        lines = file.readlines()
        for i, line in enumerate(lines):
            if e.lineno <= i + 1:
                col = e.colno - 1
                print(f"{i + 1}: {line}")
                print(" " * col + "^")
                break


