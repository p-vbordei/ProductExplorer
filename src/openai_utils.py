# openai_utils.py

import aiohttp
import asyncio
import os
import numpy as np
import random
import pandas as pd
from tenacity import retry, wait_random_exponential, stop_after_attempt
import requests
import tiktoken
import nest_asyncio
nest_asyncio.apply()
import logging
logging.basicConfig(level=logging.INFO)

from aiohttp import ContentTypeError, ClientResponseError

embedding_model = "text-embedding-ada-002"
embedding_encoding = "cl100k_base"
max_tokens = 8000
encoding = tiktoken.get_encoding(embedding_encoding)

GPT_MODEL = "gpt-3.5-turbo"

import os

def get_openai_key():
    """Retrieve OpenAI API key."""

    # Try to get the key from environment variable
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # If not found, try to get from secret management
    if not OPENAI_API_KEY:
        try:
            from src.firebase_utils import get_secret
            OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
        except:
            pass

    # If still not found, load from .env (mostly for local development)
    if not OPENAI_API_KEY:
        from dotenv import load_dotenv
        load_dotenv()
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment or secrets")

    return OPENAI_API_KEY

OPENAI_API_KEY = get_openai_key()


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


@retry(wait=wait_random_exponential(min=1, max=180), stop=stop_after_attempt(10))
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
        try:
            print(response.json()['usage'])
        except:
            pass

        try:
            print(response.json())
        except:
            pass
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e






@retry(wait=wait_random_exponential(min=1, max=180), stop=stop_after_attempt(10), before_sleep=print, retry_error_callback=lambda _: None)
async def get_completion(content, session, semaphore, progress_log, functions=None, function_call=None, GPT_MODEL=GPT_MODEL):
    async with semaphore:
        await asyncio.sleep(5.45)  # Introduce a 5.45-second delay between requests. This is to avoid hitting the RPM & TPM limits.
        
        json_data = {
            "model": GPT_MODEL,
            "messages": content,
            "temperature": 0
        }
        
        if functions is not None:
            json_data.update({"functions": functions})
        if function_call is not None:
            json_data.update({"function_call": function_call})

        try:
            async with session.post("https://api.openai.com/v1/chat/completions", headers=HEADERS, json=json_data) as resp:
                resp.raise_for_status()  # This will raise an error for 4xx and 5xx responses
                
                try:
                    response_json = await resp.json()
                except ContentTypeError:
                    logging.error("Failed to decode API response as JSON.")
                    raise

                if "error" in response_json:
                    error_message = response_json["error"]["message"]
                    logging.error(f"OpenAI API Error: {error_message}")
                    raise ValueError(error_message)

                try:
                    print(response_json['usage'])
                except KeyError:
                    logging.warning("Usage data not found in the response.")
                
                print(response_json)
                progress_log.increment()
                print(progress_log)
                return response_json["choices"][0]['message']

        except ClientResponseError as e:
            logging.error(f"HTTP Error {e.status}: {e.message}")
            if e.status == 400:
                raise ValueError("Bad Request: The API request was malformed.")
            elif e.status == 401:
                raise PermissionError("Unauthorized: Check your API key.")
            elif e.status == 403:
                raise PermissionError("Forbidden: You might have exceeded your rate limits or don't have permission.")
            elif e.status == 404:
                raise ValueError("Endpoint not found.")
            elif e.status in [429, 502, 503, 504]:
                logging.warning("Temporary API issue or rate limit hit. Retrying...")
            else:
                raise
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise


async def get_completion_list(content_list, functions=None, function_call=None, GPT_MODEL=GPT_MODEL):
    semaphore = asyncio.Semaphore(1)  # Allow only 1 request at a time to ensure you don't exceed the RPM
    progress_log = ProgressLog(len(content_list))

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
        return await asyncio.gather(*[get_completion(content, session, semaphore, progress_log, functions, function_call, GPT_MODEL) for content in content_list])




async def get_completion_list_multifunction(content_list, functions_list, function_calls_list, GPT_MODEL=GPT_MODEL):
    semaphore = asyncio.Semaphore(value=max_parallel_calls)
    progress_log = ProgressLog(len(content_list) * len(functions_list))  # Adjust for multiple functions

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(timeout)) as session:
        tasks = []
        for i in range(len(functions_list)):
            for content in content_list:
                tasks.append(get_completion(content, session, semaphore, progress_log, functions_list[i], function_calls_list[i], GPT_MODEL))
        return await asyncio.gather(*tasks)


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
