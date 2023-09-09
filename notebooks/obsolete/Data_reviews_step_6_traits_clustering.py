import numpy as np
import pandas as pd
import tiktoken
from openai.embeddings_utils import get_embedding
from sklearn.cluster import AgglomerativeClustering

import os
import openai
from dotenv import load_dotenv
from sqlalchemy import create_engine


def run_clustering_script(database = 'postgresql://postgres:mysecretpassword@localhost/postgres'):
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    if os.getenv("OPENAI_API_KEY") is not None:
        print ("OPENAI_API_KEY is ready")
    else:
        print ("OPENAI_API_KEY environment variable not found")

    engine = create_engine(database)

    embedding_model = "text-embedding-ada-002"
    embedding_encoding = "cl100k_base"  # this the encoding for text-embedding-ada-002
    max_tokens = 8000  # the maximum for text-embedding-ada-002 is 8191
    encoding = tiktoken.get_encoding(embedding_encoding)
        

    def get_text_from_embedding(embedding):
        return openai.Embedding.retrieve(embedding, model="text-embedding-ada-002")["data"][0]["text"]

    def get_type_categories(engine=engine, data_table='weighted_trait_graph'):
        query = f"""
            SELECT DISTINCT type FROM {data_table};
            """
        type_list = pd.read_sql_query(query, engine)
        return type_list

    def get_type_data(type, engine=engine, data_table='weighted_trait_graph'):
        query = f"""
            SELECT DISTINCT data_label FROM {data_table} WHERE type = '{type}';
            """
        selected_data = pd.read_sql_query(query, engine)
        return selected_data

    def write_cluster_labels(df, type, engine=engine, data_table='weighted_trait_graph'):
        with engine.connect() as con:
            # Add cluster_label column if it doesn't exist
            con.execute(f"ALTER TABLE {data_table} ADD COLUMN IF NOT EXISTS cluster_label VARCHAR;")
            
            for index, row in df.iterrows():
                data_label_val = row['data_label']
                cluster_label_val = row['cluster_label']
        
                query = f"""
                    UPDATE {data_table}
                    SET cluster_label = '{cluster_label_val}'
                    WHERE type = '{type}'
                        AND data_label = '{data_label_val}';
                    """
        
                con.execute(query)

    def fit_clusters(df, n_clusters = 7, embedding_model = embedding_model, max_tokens = max_tokens):

        # omit reviews that are too long to embed
        df["n_tokens"] = df['data_label'].apply(lambda x: len(encoding.encode(x)))
        df = df[df.n_tokens <= max_tokens]

        # Get embeddings
        df["embedding"] = df['data_label'].apply(lambda x: get_embedding(x, engine=embedding_model))
        df["embedding"] = df["embedding"].apply(np.array)  # convert string to numpy array
        matrix = np.vstack(df.embedding.values)

        # Fit clusters
        n_clusters = n_clusters  # Adjust as needed
        clustering = AgglomerativeClustering(n_clusters=n_clusters)
        labels = clustering.fit_predict(matrix)

        # Add cluster labels to dataframe and create clusters dictionary
        df["cluster"] = labels
        clusters_dict = {}
        for i in range(n_clusters):
            clusters_dict[i] = df[df.cluster == i].data_label.values.tolist()

        return df, clusters_dict

    # %%
    def get_chatbot_trait_labels(clusters_dict, temperature=0.2, api_key=OPENAI_API_KEY):
        
        User_Prompt_1 = """
        I have a list of phrases, each related to a specific theme. Provide a single label for the theme represented in the list.
        List of phrases: {99: ['improved magnet pushability', ' improved magnet strength and functionality', 'improved magnet strength and quality']}
        """

        AI_Prompt_1 = """
        Magnet Strength and Functionality
        """

        chatbot_responses = {}

        for key, data_list in clusters_dict.items():
            User_Prompt_2 = f"List of phrases: {{ {key}: {data_list} }}"

            # Send the prompt to the chatbot and get the response
            response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "user", "content": User_Prompt_1},
                            {"role": "assistant", "content": AI_Prompt_1},
                            {"role": "user", "content": User_Prompt_2} ],
                        temperature=temperature,
                        api_key=api_key
            )
        
            # Process the response and store in the dictionary
            chatbot_responses[key] = response["choices"][0]["message"]["content"]
            print(chatbot_responses[key])
        
        return chatbot_responses

    #%%
    types = get_type_categories(engine=engine, data_table='weighted_trait_graph')
    types_list = types['type'].tolist()
    for type in types_list:
        df = get_type_data(type = type, data_table = 'weighted_trait_graph')
        df, clusters_dict = fit_clusters(n_clusters = 7, df = df)
        trait_labels = get_chatbot_trait_labels(clusters_dict,temperature=0.2)
        df['cluster_label'] = df['cluster'].map(trait_labels)
        write_cluster_labels(df, type = type, data_table = 'weighted_trait_graph' )
        write_cluster_labels(df, type = type, data_table = 'weighted_trait_heatmap' )