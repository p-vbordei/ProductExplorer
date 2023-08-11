import aiohttp
import asyncio
import os
import numpy as np
import random
import pandas as pd
from tenacity import retry, wait_random_exponential, stop_after_attempt

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(20))
async def get_completion(session, content, functions=None, function_call=None):
    json_data = {
        "model": "gpt-3.5-turbo",
        "messages": content,
        "temperature": 0
    }
    
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": function_call})

    async with session.post("https://api.openai.com/v1/chat/completions", headers=HEADERS, json=json_data) as resp:
        return await resp.json()

async def get_completion_list(content_list, functions=None, function_call=None):
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[get_completion(session, content, functions, function_call) for content in content_list])

async def get_embedding(text: str, model="text-embedding-ada-002") -> list[float]:
    async with aiohttp.ClientSession() as session:
        for attempt in range(6):  # Retry up to 6 times
            try:
                async with session.post(
                    'https://api.openai.com/v1/embeddings',
                    json={"input": [text], "model": model},
                    headers=HEADERS
                ) as response:
                    response = await response.json()
                    return np.array(response["data"][0]["embedding"])  # Convert embedding to numpy array directly
            except Exception as e:
                wait_time = random.uniform(1, min(20, 2 ** attempt))  # Exponential backoff
                print(f"Request failed with {e}, retrying in {wait_time} seconds.")
                await asyncio.sleep(wait_time)
        print("Failed to get embedding after 6 attempts, returning None.")
        return None

import nest_asyncio
nest_asyncio.apply()

# Assuming you have OpenAI's tokenizer
from openai import tokenizer

max_tokens = 8048  # Define max tokens or get it from somewhere

async def process_dataframe_async_embedding(df: pd.DataFrame, embedding_model="text-embedding-ada-002") -> pd.DataFrame:
    loop = asyncio.get_event_loop()
    tasks = []

    # Filter rows by token count
    df["n_tokens"] = df['Value'].apply(lambda x: len(tokenizer.encode(x)))
    df = df[df.n_tokens <= max_tokens]

    for index, row in df.iterrows():
        task = loop.create_task(get_embedding(row['Value'], model=embedding_model))
        tasks.append(task)

    df['embedding'] = await asyncio.gather(*tasks)
    return df
