import aiohttp
import asyncio
import os
import numpy as np
import random
import pandas as pd
from tenacity import retry, wait_random_exponential, stop_after_attempt


import tiktoken

embedding_model = "text-embedding-ada-002"
embedding_encoding = "cl100k_base"
max_tokens = 8000
encoding = tiktoken.get_encoding(embedding_encoding)

GPT_MODEL = "gpt-3.5-turbo"

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

max_parallel_calls = 100
timeout = 60

class ProgressLog:
    def __init__(self, total):
        self.total = total
        self.done = 0

    def increment(self):
        self.done = self.done + 1

    def __repr__(self):
        return f"Done runs {self.done}/{self.total}."


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(20), before_sleep=print, retry_error_callback=lambda _: None)
async def get_completion(content, session, semaphore, progress_log, functions=None, function_call=None, GPT_MODEL=GPT_MODEL):
    async with semaphore:
        json_data = {
            "model": GPT_MODEL,
            "messages": content,
            "temperature": 0
        }
        
        if functions is not None:
            json_data.update({"functions": functions})
        if function_call is not None:
            json_data.update({"function_call": function_call})

        async with session.post("https://api.openai.com/v1/chat/completions", headers=HEADERS, json=json_data) as resp:
            response_json = await resp.json()
            progress_log.increment()
            print(progress_log)
            return response_json["choices"][0]['message']

async def get_completion_list(content_list, functions=None, function_call=None, GPT_MODEL=GPT_MODEL):
    semaphore = asyncio.Semaphore(value=max_parallel_calls)
    progress_log = ProgressLog(len(content_list))

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(timeout)) as session:
        return await asyncio.gather(*[get_completion(content, session, semaphore, progress_log, functions, function_call, GPT_MODEL) for content in content_list])



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


max_tokens = 8048  # Define max tokens or get it from somewhere

async def process_dataframe_async_embedding(df: pd.DataFrame, embedding_model="text-embedding-ada-002") -> pd.DataFrame:
    loop = asyncio.get_event_loop()
    tasks = []

    # Filter rows by token count
    df["n_tokens"] = df['Value'].apply(lambda x: len(encoding.encode(x)))
    df = df[df.n_tokens <= max_tokens]

    for index, row in df.iterrows():
        task = loop.create_task(get_embedding(row['Value'], model=embedding_model))
        tasks.append(task)

    df['embedding'] = await asyncio.gather(*tasks)
    return df
