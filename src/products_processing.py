# ############################
# Description: This script is used to generate product descriptions for a list of products
# products_processing.py

#%%
import os
try:
    from src import app
    from src.firebase_utils import get_investigation_and_product_details, update_investigation_status, update_firestore_individual_products, initialize_firestore, save_product_details_to_firestore
    from src.products_data_processing_utils import extract_brand_name, remove_brand, clean_description_data, calculate_median_price
    from src.openai_utils    import chat_completion_request
except ImportError:
    from firebase_utils import get_investigation_and_product_details, update_investigation_status, update_firestore_individual_products, initialize_firestore, save_product_details_to_firestore
    from products_data_processing_utils import extract_brand_name, remove_brand, clean_description_data, calculate_median_price
    from openai_utils    import chat_completion_request
    
GPT_MODEL = "gpt-3.5-turbo"

################################## PROCESS INDIVIDUAL PRODUCTS #########################################
# %%

def process_products(investigationId, GPT_MODEL, db):
    """
    Processes products based on the given investigationId.
    
    Parameters:
    - investigationId (str): The ID of the investigation.
    - GPT_MODEL (str): The model name to be used for OpenAI.
    
    Returns:
    - list: A list of processed products.
    """
    
    # Fetch products
    try:
        products = get_investigation_and_product_details(investigationId, db)
    except Exception as e:
        print(f"Error fetching product details for investigation {investigationId}: {e}")
        return []

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


    for product in products:
        title = product.get('title')
        asin = product['asin']
        bullets = product['features']

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

        try:
            response = response.json()
            print(response)
            product['product_description_data'] = response
        except Exception as e:
            print(f"Error generating product description for product {asin}: {e}")
            continue


    # Process Responses
    for product in products:
        product['cleanProductDescriptionData'] = clean_description_data(product['product_description_data'])  # Changed to CamelCase
        data = eval(product['cleanProductDescriptionData']['choices'][0]['message']['function_call']['arguments'])  # Updated to use CamelCase key
        product['cleanProductDescriptionData'] = data  # Updated to use CamelCase key


    newProductsList = [] 
    for product in products:
        asinLevelData = {}
        asinLevelData = product
        newProductsList.append(asinLevelData)
        
    return newProductsList


# %%

################################ PROCESS PRODUCT DESCRIPTIONS #########################################



def process_product_description(products, GPT_MODEL):


    productSummaryDict = {}
    whatIsInTheBoxDict = {}
    technicalFactsDict = {}
    featuresDict = {} 
    howProductUseDict = {}
    whereProductUseDict = {}
    userDescriptionDict = {}
    packagingDescriptionDict = {}
    seasonDescriptionDict = {}
    whenProductUseDict = {}

    for product_item in products:
        asin = product_item['asin']
        data = product_item['product_description_data']

        productSummaryDict[asin] = data.get('Product Summary')
        whatIsInTheBoxDict[asin] = data.get('What is in the box?')
        technicalFactsDict[asin] = data.get('Technical Facts?')
        featuresDict[asin] = data.get('Features')
        howProductUseDict[asin] = data.get('How the product is used?')
        whereProductUseDict[asin] = data.get('Where the product is used?')
        userDescriptionDict[asin] = data.get('User Description?')
        packagingDescriptionDict[asin] = data.get('Packaging?')
        seasonDescriptionDict[asin] = data.get('Season?')
        whenProductUseDict[asin] = data.get('When the product is used?')


    # ### Product Summary

    functions = [
        {
            "name": "product_summary_function",
            "description": "Provide a detailed description of a product based on observations on simmilar products",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_summary": {
                        "type": "string",
                        "description": "Write a single product fact sheet summary of a product based on these observations from an ecommerce site, in 200 words. Exclude brand names."
                    },
                    "product_summary_outliers": {
                        "type": "string",
                        "description": "Identify if any outliers exist and explain them. Example: B09VBZZ9C8 (<asin>) is an outlier as it includes 3 mini magnetic drawing boards \
                                        instead of a single board, and B085Q3TLF8 stands out for its glowing in the dark feature."\
                    }
                },
                "required": ["product_summary", "product_summary_outliers"]
            },
        }
    ]

    messages = [
        {"role": "user", "content": f"```PRODUCT SUMMARIES:``` {productSummaryDict}"}
    ]

    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "product_summary_function"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary

    mainProductSummaryResponse = response.json()["choices"]

    mainProductSummaryResponse

    # ### What is in the box

    functions = [
        {
            "name": "what_is_in_the_box",
            "description": "Provide a detailed description of what is in the box of a product based on knowledge of simmilar products",
            "parameters": {
                "type": "object",
                "properties": {
                    "in_the_box": {
                        "type": "string",
                        "description": "Write a single what is in the box of a product based on these OBSERVATIONS. Select the most common values from OBSERVATIONS."
                    },
                    "in_the_box_outliers": {
                        "type": "string",
                        "description": "Identify if any outliers exist on  what is in the box of a product and explain them. If any products have something extra in the box, say what the ASIN is and what is diffrent"\
                    }
                },
                "required": ["in_the_box", "in_the_box_outliers"]
            },
        }
    ]

    messages = [
        {"role": "user", "content": f"{whatIsInTheBoxDict}"}
    ]

    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "what_is_in_the_box"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary
    mainProductWhatIsInTheBoxResponse = response.json()["choices"]



    # ### Technical Facts

    functions = [
        {
            "name": "technical_facts_function",
            "description": "write the technical facts / details of a single product from the feat sheets of simmilar products",
            "parameters": {
                "type": "object",
                "properties": {
                    "technical_facts": {
                        "type": "string",
                        "description": "Write a single what is in the box of a product based on these OBSERVATIONS. \
                            Select the most common values from OBSERVATIONS."
                    },
                    "technical_facts_outliers": {
                        "type": "string",
                        "description": "Identify if any outliers exist on  technical facts / details of a single product from the feat sheets of a product and explain them. Say what the ASIN is and what is diffrent"\
                    }
                },
                "required": ["technical_facts", "technical_facts_outliers"]
            },
        }
    ]

    messages = [
        {"role": "user", "content": f"{technicalFactsDict}"}
    ]

    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "technical_facts_function"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary
    mainProductTechnicalFactsResponse = response.json()["choices"]

    # ### Features

    functions = [
        {
            "name": "features_function",
            "description": "write the features of a single product from the feat sheets of simmilar products",
            "parameters": {
                "type": "object",
                "properties": {
                    "features": {
                        "type": "string",
                        "description": """ Write the features of a single product from the fact sheets of a product \
                                        based on these OBSERVATIONS. Focus on the benefits that using the product brings. Example output: \
                                            "Learning disguised as play": "Makes learning fun and engaging",\
                                            "Portable and travel-friendly": "Easy to carry and use on the go",\
                                            "No eraser needed": "Effortless erasing and reusing",\
                                            "120 magnetic beads": "Provides ample space for creativity and learning",\
                                            "Easy to erase and reset": "Convenient and time-saving",\
                                            "Stylus stored at the bottom": "Ensures easy storage and transportation",\
                                            "Magnetized beads": "Allows for smooth drawing and tactile learning",\
                                            "Stylus pen": "Enables precise control and encourages proper grip" """
                    },
                    "features_outliers": {
                        "type": "string",
                        "description": "Identify if any features outliers exist and explain them. Say what the ASIN is and what is diffrent"\
                    }
                },
                "required": ["features", "features_outliers"]
            },
        }
    ]

    messages = [
        {"role": "user", "content": f"{featuresDict}"}
    ]

    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "features_function"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary
    mainProductFeaturesResponse = response.json()["choices"]

    # ### How to use the product

    functions = [
        {
            "name": "how_product_use_function",
            "description": "write how a single product is used based on the observations  on simmilar products", 
            "parameters": {
                "type": "object",
                "properties": {
                    "how_the_product_is_used": {
                        "type": "string",
                        "description": """ Write how a single product is used / can be used based on these \
                                        OBSERVATIONS  on simmilar products. Example output: \
                                        "The product is primarily used for drawing, \
                                        designing, creating, and playing with magnetic beads. \
                                        It can also be used for teaching children how to write and draw, \
                                        taking messages, completing classroom assignments, and practicing alphabets and numbers." """
                    },
                    "how_the_product_is_used_outliers": {
                        "type": "string",
                        "description": "Identify if any outliers exist on who the product is used and explain them. Say what the ASIN is and what is diffrent"\
                    }
                },
                "required": ["how_the_product_is_used", "how_the_product_is_used_outliers"]
            },
        }
    ]

    messages = [
        {"role": "user", "content": f"{howProductUseDict}"}
    ]

    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "how_product_use_function"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary
    mainProductHowToUseResponse = response.json()["choices"]

    # ### Where the product is used

    functions = [
        {
            "name": "where_product_use_function",
            "description": "write where a single product is used based on the observations  on simmilar products", 
            "parameters": {
                "type": "object",
                "properties": {
                    "where_the_product_is_used": {
                        "type": "string",
                        "description": """ Write where a single product is used based on these \
                                        OBSERVATIONS. Example output: \
                                        "Home, schools, classrooms, long drives, \
                                        doctor's offices, waiting for a flight, restaurants, on-the-go, and travel" """
                    },
                    "where_the_product_is_used_outliers": {
                        "type": "string",
                        "description": "Identify if any features outliers exist on where the product is used and explain them. Say what the ASIN is and what is diffrent"\
                    }
                },
                "required": ["where_the_product_is_used", "where_the_product_is_used_outliers"]
            },
        }
    ]

    messages = [
        {"role": "user", "content": f"{whereProductUseDict}"}
    ]

    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "where_product_use_function"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary
    mainProductWhereToUseResponse = response.json()["choices"]

    # ### User Description

    functions = [
        {
            "name": "user_description_function",
            "description": "write who the user of a single product is based on the observations on simmilar products", 
            "parameters": {
                "type": "object",
                "properties": {
                    "user_description": {
                        "type": "string",
                        "description": """ Write a user description of a single product based on these OBSERVATIONS. \
                                        Example output: \
                                        "This product is primarily designed for children, \
                                        including kids, toddlers, and preschoolers, with a broad age range from 3 years old \
                                        up to adults. """
                    },
                    "user_description_outliers": {
                        "type": "string",
                        "description": "Identify if any outliers exist on wheo the user of the product is and explain them. Say what the ASIN is and what is diffrent"\
                    }
                },
                "required": ["user_description", "user_description_outliers"]
            },
        }
    ]

    messages = [
        {"role": "user", "content": f"{userDescriptionDict}"}
    ]

    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "user_description_function"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary
    mainProductUserDescriptionResponse = response.json()["choices"]

    # ### Packaging Description

    functions = [
        {
            "name": "product_packaging_function",
            "description": "describe the packaging of a single product based on the observations on simmilar products", 
            "parameters": {
                "type": "object",
                "properties": {
                    "product_packaging": {
                        "type": "string",
                        "description": "summarize the packaging of a single product based on these OBSERVATIONS. Don't repeat information and eleminate any brand names" 
                    },
                    "product_packaging_outliers": {
                        "type": "string",
                        "description": "Identify if any outliers exist on the product packaging and explain them. Say what the ASIN is and what is diffrent"
                    }
                },
                "required": ["product_packaging", "product_packaging_outliers"]
            },
        }
    ]

    messages = [
        {"role": "user", "content": f"{packagingDescriptionDict}"}
    ]

    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "product_packaging_function"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary
    mainProductPackagingDescriptionResponse = response.json()["choices"]

    # ### Season Description

    functions = [
        {
            "name": "product_seasonal_use_function",
            "description": "write where a single product is used based on the observations on simmilar products", 
            "parameters": {
                "type": "object",
                "properties": {
                    "product_seasonal_use": {
                        "type": "string",
                        "description": "describe the seasonal use of a product based on these OBSERVATIONS." 
                    },
                    "product_seasonal_use_outliers": {
                        "type": "string",
                        "description": "Identify if any outliers exist on the season when the product is used and explain them. Say what the ASIN is and what is diffrent"\
                    }
                },
                "required": ["product_seasonal_use", "product_seasonal_use_outliers"]
            },
        }
    ]

    messages = [
        {"role": "user", "content": f"{seasonDescriptionDict}"}
    ]

    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "product_seasonal_use_function"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary
    mainProductSeasonToUseResponse = response.json()["choices"]

    # ### When the product is used Description

    functions = [
        {
            "name": "when_product_use_function",
            "description": "write where a single product is used based on the observations on simmilar products", 
            "parameters": {
                "type": "object",
                "properties": {
                    "when_the_product_is_used": {
                        "type": "string",
                        "description": "describe when a product is used based on these OBSERVATIONS." 
                    },
                    "when_the_product_is_used_outliers": {
                        "type": "string",
                        "description": "Identify if any outliers exist on when the product is used and explain them. Say what the ASIN is and what is diffrent"\
                    }
                },
                "required": ["when_the_product_is_used", "when_the_product_is_used_outliers"]
            },
        }
    ]

    messages = [
        {"role": "user", "content": f"{whenProductUseDict}"}
    ]

    # Send the request to the LLM and get the response
    response =  chat_completion_request(
        messages=messages,
        functions=functions,
        function_call={"name": "when_product_use_function"},
        temperature=0,
        model=GPT_MODEL
    )

    # Process the response and store in the dictionary
    mainProductWhenToUseResponse = response.json()["choices"]

    initialResponses = {}
    initialResponses['productSummary'] = mainProductSummaryResponse
    initialResponses['whatIsInTheBox'] = mainProductWhatIsInTheBoxResponse
    initialResponses['technicalFacts'] = mainProductTechnicalFactsResponse 
    initialResponses['features'] = mainProductFeaturesResponse 
    initialResponses['howProductUse'] = mainProductHowToUseResponse
    initialResponses['whereProductUse'] = mainProductWhereToUseResponse
    initialResponses['userDescription'] = mainProductUserDescriptionResponse
    initialResponses['packagingDescription'] = mainProductPackagingDescriptionResponse
    initialResponses['seasonDescription'] = mainProductSeasonToUseResponse
    initialResponses['whenProductUse'] = mainProductWhenToUseResponse




    productDataInterim ={}
    for key in initialResponses.keys():
        productDataInterim[key] = eval(initialResponses[key][0]['message']['function_call']['arguments'])

    productData = {}
    for main_key in productDataInterim.keys():
        for secondary_key in productDataInterim[main_key].keys():
            productData[secondary_key] = productDataInterim[main_key][secondary_key]

    productData['medianProductPrice'] = calculate_median_price(products)

    general_product_keys_to_keep = ['productSummary','whatIsInTheBox', 'technicalFacts', 'features', 'howProductUse',  'whereProductUse', 'userDescription','medianProductPrice']

    shortProductData = {} 
    for key in general_product_keys_to_keep:
        if key in productData.keys():
            shortProductData[key] = productData[key]

    otherProductDataKeys = set(productData.keys()) - set(shortProductData.keys())


    otherProductData = {}
    for key in otherProductDataKeys:
        if key in productData.keys():
            otherProductData[key] = productData[key]
            
    finalProductData = {}
    finalProductData['shortProductData'] = shortProductData
    finalProductData['otherProductData'] = otherProductData


    return finalProductData

################################## RUN #########################################


# %%
def run_products_investigation(investigationId):
    
    db = initialize_firestore()
    update_investigation_status(investigationId, "startedProducts", db)
    newProductsList = process_products(investigationId, GPT_MODEL, db)
    update_firestore_individual_products(newProductsList, db)
    update_investigation_status(investigationId, "finishedIndividualProducts", db)
    finalProductsData = process_product_description(newProductsList, GPT_MODEL)
    save_product_details_to_firestore(db, investigationId, finalProductsData)
    update_investigation_status(investigationId, 'finishedProducts', db)

# =============================================================================


# %%
