import os
import openai
import requests
from google.cloud import firestore
from tenacity import retry, wait_random_exponential, stop_after_attempt

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
HUGGINGFACEHUB_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN')
GPT_MODEL = "gpt-3.5-turbo"

db = firestore.Client()  # Make sure you have set GOOGLE_APPLICATION_CREDENTIALS environment variable for this to work

if OPENAI_API_KEY is not None:
    print("OPENAI_API_KEY is ready")
else:
    print("OPENAI_API_KEY environment variable not found")


def extract_brand_name(string):
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


def read_data(folder_path):
    product = pd.DataFrame()

    for file_name in os.listdir(folder_path):
        if file_name.startswith("asin"):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)
            product = pd.concat([product, df])

    return product


products = read_data("/Users/vladbordei/Documents/Development/ProductExplorer/data/raw/RaisedGardenBed")
products['product_information.brand'] = products['product_information.brand'].apply(extract_brand_name)


product = products.copy()
product.reset_index(drop=True, inplace=True)
asin_list = pd.read_csv('/Users/vladbordei/Documents/Development/ProductExplorer/data/external/asin_list.csv')['asin'].tolist()


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, functions=None, function_call=None, temperature=0, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + OPENAI_API_KEY,
    }
    json_data = {"model": model, "messages": messages, "temperature": temperature}
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": function_call})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


def remove_brand(strings, brand_column):
    cleaned_strings = []
    for string, brand in zip(strings, brand_column):
        cleaned_string = string.replace(brand, '').strip()
        cleaned_strings.append(cleaned_string)
    return cleaned_strings


product['product_information_title'] = remove_brand(product.title, product.product_information_brand)
product_tile = product['product_information_title'].iloc[0]
product_tile


functions = [
    {
        "name": "describe_product",
        "description": "Provide a detailed description of a product",
        "parameters": {
            "type": "object",
            "properties": {
                "Product Summary": {
                    "type": "string",
                    "description": "A brief summary of the product in 200 words"
                },
                "What is in the box": {
                    "type": "string",
                    "description": "Contents of the product package. Example: one micro USB charging cable, one 3.5mm auxiliary cable, and a user manual"
                },
                "Technical Facts": {
                    "type": "string",
                    "description": "Technical details about the product. Example: water-resistant body made from high-quality ABS plastic, stainless steel, BPA-free, lead-free, synthetic leather"
                },
                "Features": {
                    "type": "string",
                    "description": "Features of the product. Example: water-resistant design, excellent bounce consistency, suitable for both indoor and outdoor use "
                },
                "How the product is used": {
                    "type": "string",
                    "description": "Information about what the product is used for or about how the product is used. Example: doodling, practicing letters/shapes, playing games"
                },
                "Where the product is used": {
                    "type": "string",
                    "description": "Suggested locations or situations where the product can be used. Example: car, restaurant, garden, public parks"
                },
                "User Description": {
                    "type": "string",
                    "description": "Description of the user for the product. Example: children, preschoolers,  basketball players, mothers, office workers"
                },
                "Packaging": {
                    "type": "string",
                    "description": "Description of the product's packaging. Example: sturdy recyclable box, wrapped in plastic, great for gifting"
                },
                "Season": {
                    "type": "string",
                    "description": "Season or time of year when the product is typically used. Example: fall and winter"
                },
                "When the product is used": {
                    "type": "string",
                    "description": "Time of day or week when the product is typically used. Example: early in the morning, in the weekend"
                }
            },
            "required": ["Product Summary", "Features"]
        },
    }
]

chatbot_responses = dict()

for i in product.index:
    print(i)
    title = product['title'][i]
    asin = product['asin'][i]
    bullets = product['feature_bullets'][i]

    print(asin)
    print(bullets)
    print(title)

    messages = [
        {"role": "user", "content": f"PRODUCT TITLE:``` {title} ``` PRODUCT BULLETS:```{bullets}```"},
    ]

    response = chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "describe_product"},
        temperature=0,
        model=GPT_MODEL
    )

    chatbot_responses[asin] = response.json()["choices"]
    product.loc[i, 'product_description_data'] = chatbot_responses[asin]


for i in product.index:
    if isinstance(product.product_description_data[i], list):
        first_element = product.product_description_data[i][0]
        product.product_description_data[i] = first_element
    else:
        pass

for i in product.index:
    try:
        data = eval(product.product_description_data[i]['message']['function_call']['arguments'])
    except:
        data = product.product_description_data[i]['message']['function_call']['arguments']
    product['product_description_data'][i] = data


# Update the Firestore database
for _, row in product.iterrows():
    doc_ref = db.collection('products').document(row['asin'])
    doc_ref.set(row.to_dict())
