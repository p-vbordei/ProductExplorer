# products_data_processing_utils.py

from typing import List

def extract_brand_name(string: str) -> str:
    if isinstance(string, str) and ("Brand: " in string or "Visit the " in string):
        try:
            if "Brand: " in string:
                brand_name = string.split("Brand: ")[1]
            else:
                brand_name = string.split("Visit the ")[1]
            brand_name = brand_name.replace("Store", "").strip()
            return brand_name
        except IndexError:
            pass
    return string

def remove_brand(strings: List[str], brand_column: List[str]) -> List[str]:
    cleaned_strings = []
    for string, brand in zip(strings, brand_column):
        cleaned_string = string.replace(brand, '').strip()
        cleaned_strings.append(cleaned_string)
    return cleaned_strings

def clean_description_data(data):
  if isinstance(data, list):
    return data[0]
  return data




from tqdm import tqdm
import numpy as np

def calculate_median_price(products):
    """
    Ensures all product prices are floats and calculates the median price.
    
    Parameters:
    - products (list): A list of product dictionaries with price details.
    
    Returns:
    - float: The median product price.
    """
    
    # Ensure all the prices are floats
    for product in tqdm(products, desc="Processing product prices"):
        price = product['price']['current_price']
        if price is not None:
            product['price']['current_price'] = float(price)

    # Extract the prices and remove None values
    prices = [product['price']['current_price'] for product in products if product['price']['current_price'] is not None]

    # Calculate the median and round it
    return round(np.median(prices), 0)

# Usage:
# median_price = calculate_median_price(products)
