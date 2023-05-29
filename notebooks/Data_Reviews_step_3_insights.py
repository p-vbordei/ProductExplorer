# %%
import pandas as pd
import numpy as np
from typing import Dict
import os
from dotenv import load_dotenv
import openai
import ast
from typing import List

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# %%
import ast

def explode_data(dataframe, column_name):
    # Convert strings to lists

    for i in range(len(dataframe[column_name])):
        try:
            if isinstance(dataframe[column_name][i], str):
                dataframe[column_name][i] = ast.literal_eval(dataframe[column_name][i])   
        except:
            pass
    
    # Extract single values from lists
    dataframe[column_name] = dataframe[column_name].apply(lambda x: x[0] if isinstance(x, list) and len(x) == 1 else [x][0] if not isinstance(x, list) else x)

    # Explode the specified column
    dataframe = dataframe.explode(column_name)

    # Rename the column
    dataframe.rename(columns={column_name: 'key_data'}, inplace=True)

    # Replace missing values with NaN
    dataframe['key_data'].replace(['', 'NA', 'N/A', 'missing', 'NaN', 'unknown', 'Unknown', ['Unknown']], np.nan, inplace=True)

    # Drop NaN values
    dataframe.dropna(subset=['key_data'], inplace=True)

    # Replace missing values with 'Unknown'
    dataframe['key_data'].fillna(value='unknown', inplace=True)

    # Drop 'Unknown' values
    dataframe = dataframe[dataframe['key_data'] != 'unknown']

    # Get value counts and sort values
    value_counts = dataframe['key_data'].value_counts()
    key_data_list = sorted(list(set(dataframe['key_data'])))

    dataframe.reset_index(inplace=True, drop=True)
    
    return dataframe, key_data_list


# %%
def get_chatbot_responses(key_data_list, batch_size=80, temperature=0.2,api_key=OPENAI_API_KEY):
    
    User_Prompt_1 = """
    ```Input List:``` ['cleaning','cleaning ease','adjustability' ,'adjustability of forks','adjustable length']
    """

    AI_Prompt_1 = """{
    'cleaning' : 'easy to clean',
    'cleaning ease': 'easy to clean',
    'adjustability' : 'length is adjustable',
    'adjustability of forks': 'length is adjustable',
    'adjustable length': 'length is adjustable',
    }"""

    chatbot_responses = {}
    for i in range(0, len(key_data_list), batch_size):
        # Get the current batch of up to batch_size items
        batch = key_data_list[i:i+batch_size]
        User_Prompt_2 = f"```Input List:``` {batch}"

        # Send the prompt to the chatbot and get the response
        response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": User_Prompt_1},
                        {"role": "assistant", "content": AI_Prompt_1},
                        {"role": "user", "content": User_Prompt_2} ],
                    temperature=0.2,
                    api_key=api_key
        )
    
        # Process the response and store in the dictionary
        chatbot_responses[i] = response["choices"][0]["message"]["content"]
        print(chatbot_responses[i])
    
    return chatbot_responses

# %%
def stick_together_dictionaries(placeholder_dict):
    merged_dict = {}
    for key in placeholder_dict.keys():
        dict_obj = eval(placeholder_dict[key])
        merged_dict.update(dict_obj)

    return merged_dict

# Remove 'Unknown' values and eliminate duplicates
def process_list(column_data):
    return list(set(x for x in column_data if x != 'Unknown'))


# %%


def get_weighted_results_heatmap(dataframe, data_column_name, aisin_column):
    
    dataframe['positive_sentiment'] = dataframe['positive_sentiment'].astype(float)
    dataframe['negative_sentiment'] = dataframe['negative_sentiment'].astype(float)

    # Apply ast.literal_eval() to relevant columns before aggregation
    for column_name in ['how_product_is_used', 'media', 'where_product_is_used', 'user_description']:
        dataframe[column_name] = dataframe[column_name].fillna('').apply(lambda elem: ast.literal_eval(elem) if isinstance(elem, str) and elem.startswith('[') else [elem] if isinstance(elem, str) else elem)
    
    # Allocate sentiment to main_improvement_iter_2 by ASIN and aggregate
    agg_result = dataframe.groupby([aisin_column, data_column_name]).agg({
        'positive_sentiment': 'mean',
        'negative_sentiment': 'mean',
        'rating': lambda x: list(x),
        'id': lambda x: list(x),
        'how_product_is_used': lambda x: sum((lst for lst in x), []),
        'media': lambda x: sum((lst for lst in x), []),
        'where_product_is_used': lambda x: sum((lst for lst in x), []),
        'user_description': lambda x: sum((lst for lst in x), [])
    }).reset_index()


    # Aggregate the count separately
    count_result = dataframe.groupby([aisin_column, data_column_name]).size().reset_index(name='observation_count')

    # Merge the aggregated count with the main result
    result = pd.merge(agg_result, count_result, on=[aisin_column, data_column_name])

    columns_to_process = ['id']
    for column in columns_to_process:
        result[column] = result[column].apply(process_list)

    # Calculate the sum of observation_count for each ASIN
    asin_observation_sum = result.groupby(aisin_column)['observation_count'].sum().to_dict()

    # Create a percentage column using the asin_observation_sum dictionary
    result['percentage'] = result.apply(lambda row: row['observation_count'] / asin_observation_sum[row[aisin_column]] * 100, axis=1)
    result.rename(columns={data_column_name: 'data_label'}, inplace=True)
    return result


def get_weighted_results_graph(dataframe, data_column_name, aisin_column):

    # Apply ast.literal_eval() to relevant columns before aggregation
    for column_name in ['how_product_is_used', 'media', 'where_product_is_used', 'user_description',aisin_column]:
        dataframe[column_name] = dataframe[column_name].fillna('').apply(lambda elem: ast.literal_eval(elem) if isinstance(elem, str) and elem.startswith('[') else [elem] if isinstance(elem, str) else elem)
    
    dataframe['positive_sentiment'] = dataframe['positive_sentiment'].astype(float)
    dataframe['negative_sentiment'] = dataframe['negative_sentiment'].astype(float)

    # Allocate sentiment to main_improvement_iter_2 by ASIN and aggregate
    agg_result = dataframe.groupby([data_column_name]).agg({
        'positive_sentiment': 'mean',
        'negative_sentiment': 'mean',
        'rating': lambda x: list(x),
        'id': lambda x: list(x),
        'how_product_is_used': lambda x: sum((lst for lst in x), []),
        'media': lambda x: sum((lst for lst in x), []),
        'where_product_is_used': lambda x: sum((lst for lst in x), []),
        'user_description': lambda x: sum((lst for lst in x), []),
        aisin_column: lambda x: sum((lst for lst in x), [])
    }).reset_index()

    # Aggregate the count separately
    count_result = dataframe.groupby([data_column_name]).size().reset_index(name='observation_count')

    # Merge the aggregated count with the main result
    result = pd.merge(agg_result, count_result, on=[data_column_name])

    m = []
    for e in result['rating']:
        f =[]
        for r in e:
            f.append(int(r))
        m.append(np.mean(f))
    k = []
    for e in m:
        f = round(e,0)
        f = int(f)
        k.append(f)

    result['rating_avg'] = k

    columns_to_process = ['id', 'how_product_is_used', 'media', 'where_product_is_used', 'user_description', aisin_column]
    for column in columns_to_process:
        result[column] = result[column].apply(process_list)

    result.rename(columns={data_column_name: 'data_label'}, inplace=True)
    return result


def process_data_short(file_path: str, key: str) -> pd.DataFrame:
    
    # Read in the data frame
    df = pd.read_csv(file_path)
    
    # Select columns to keep
    cols = list(df.columns)
    keep_cols = ['positive_sentiment', 'negative_sentiment', 'rating', 'asin.original', 'id', 'user_known', 'user_description',  'how_product_is_used', 'media', 'where_product_is_used']
    keep_cols.append(key)
    drop_cols = list(set(cols) - set(keep_cols))

    # Drop unnecessary columns
    df.drop(columns=drop_cols, inplace=True)
    df.rename(columns={key: 'key_data'}, inplace=True)

    # Explode the data
    key_data_df, key_data_list_iter_1 = explode_data(df, 'key_data')

    # Get data from AI ITER 1
    bot_replies_iter_1 = get_chatbot_responses(batch_size=80, key_data_list=key_data_list_iter_1, temperature=0.3)

    # Stick the dictionaries together ITER 1
    key_data_dict_1 = stick_together_dictionaries(bot_replies_iter_1)
    key_data_df['key_data_iter_1'] = key_data_df['key_data'].map(key_data_dict_1)
    key_data_df['key_data_iter_1']= key_data_df['key_data_iter_1'].fillna(' ')
    key_data_list_iter_2 = sorted(list(set(key_data_df['key_data_iter_1'])))

    # ITER 2
    if len(key_data_list_iter_2) < 30:
        dict_column = 'key_data_iter_1'
    else:
        # Get data from AI ITER 2
        bot_replies_iter_2 = get_chatbot_responses(batch_size=80, key_data_list=key_data_list_iter_2, temperature=0.5)

        # Stick the dictionaries together ITER 2
        key_data_dict_2 = stick_together_dictionaries(bot_replies_iter_2)
        key_data_df['key_data_iter_2'] = key_data_df['key_data_iter_1'].apply(lambda x: key_data_dict_2.get(x))
        dict_column = 'key_data_iter_2'

    return key_data_df, dict_column