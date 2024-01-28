# openai_utils.py

import aiohttp
import json
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
import traceback
from aiohttp import ContentTypeError, ClientResponseError

embedding_model = "text-embedding-ada-002"
embedding_encoding = "cl100k_base"
max_tokens = 8000
encoding = tiktoken.get_encoding(embedding_encoding)

response_queue = asyncio.Queue() 

GPT_MODEL = "gpt-3.5-turbo"

try:
    from src.firebase_utils import FirestoreClient, PubSubClient, GAEClient

except ImportError:
    from firebase_utils import FirestoreClient, PubSubClient, GAEClient

try:
    db = FirestoreClient.get_instance()
except Exception as e:
    logging.error(f"Error initializing Firestore: {e}")

try:
    publisher, subscriber, project_id, topic_id, subscription_id, topic_path, subscription_path = PubSubClient.get_instance()
except Exception as e:
    logging.error(f"Error initializing Pub/Sub: {e}")

try:
    GAEClient.get_instance()
except Exception as e:
    logging.error(f"Error initializing GAE: {e}")

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

async def process_message(message):
    data = message.data.decode('utf-8')
    content = json.loads(data)
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300))
    semaphore = asyncio.Semaphore(6)
    progress_log = ProgressLog(1)  # Assuming one task per message
    await get_completion(content, session, semaphore, progress_log)
    message.ack()

async def callback(message):
    await process_message(message)

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


@retry(wait=wait_random_exponential(min=1, max=180), stop=stop_after_attempt(10),
       before_sleep=lambda retry_state: print(f"Sleeping for {retry_state.next_action} seconds"),
       retry_error_callback=lambda retry_state: print(f"Attempt {retry_state.attempt_number} failed. Error: {retry_state.outcome.result()}"))
async def get_completion(content, session, semaphore, progress_log, functions=None, function_call=None, GPT_MODEL=GPT_MODEL, TEMPERATURE=0):
    async with semaphore:
        await asyncio.sleep(3)  # Introduce a 5.45-second delay between requests to avoid hitting the RPM & TPM limits.

        # 1. Prepare request payload
        json_data = {
            "model": GPT_MODEL,
            "messages": content,
            "temperature": TEMPERATURE
        }

        # 2. Optionally update payload with additional fields
        if functions is not None:
            json_data.update({"functions": functions})
        if function_call is not None:
            json_data.update({"function_call": function_call})

        try:
            # 3. Make API request
            async with session.post("https://api.openai.com/v1/chat/completions", headers=HEADERS, json=json_data) as resp:
                resp.raise_for_status()
                
                try:
                    response_json = await resp.json()
                except ContentTypeError:
                    logging.error("Failed to decode API response as JSON.")
                    raise  # This exception will trigger a retry if within the retry count

                # 4. Check for API-specific errors in the response
                if "error" in response_json:
                    error_message = response_json["error"]["message"]
                    logging.error(f"OpenAI API Error: {error_message}")
                    raise ValueError(error_message)

                # 5. Print usage data if available
                try:
                    print(response_json['usage'])
                except KeyError:
                    logging.warning("Usage data not found in the response.")

                # 6. Increment progress and print log
                progress_log.increment()
                print(progress_log)

                # 7. Return the message from the API response
                return response_json["choices"][0]['message']

        except ClientResponseError as e:
            logging.error(f"HTTP Error {e.status}: {e.message}")
            if e.status in [400, 401, 403, 404]:
                raise  # These are not retriable errors, so re-raise them immediately
            elif e.status in [429, 502, 503, 504]:
                logging.warning("Temporary API issue or rate limit hit. Retrying...")
                raise  # This exception will trigger a retry if within the retry count
            else:
                raise  # For other errors, re-raise them immediately

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            traceback.print_exc()
            raise  # This exception will trigger a retry if within the retry count



async def get_completion_list(content_list, functions=None, function_call=None, GPT_MODEL=GPT_MODEL, TEMPERATURE=0):
    #global publisher, topic_path


    for content in content_list:
        data = json.dumps(content).encode('utf-8')
        publisher.publish(topic_path, data)
    
    # Wait for responses
    responses = []
    for _ in range(len(functions_list) * len(content_list)):
        try:
            # Wait for a response with a timeout of 4 minutes
            response = await asyncio.wait_for(response_queue.get(), timeout=240)
            responses.append(response)
        except asyncio.TimeoutError:
            print("Timeout waiting for a response")
            break

    return responses


async def get_completion_list_multifunction(content_list, functions_list, function_calls_list, GPT_MODEL=GPT_MODEL, TEMPERATURE=0):
    if functions_list is None or content_list is None:
        raise ValueError("functions_list or content_list is None")

    if not isinstance(functions_list, list) or not isinstance(content_list, list):
        raise TypeError("functions_list and content_list must be lists")

    # Send all the messages
    for i in range(len(functions_list)):
        for content in content_list:
            data = json.dumps({"content": content, "functions": functions_list[i], "function_call": function_calls_list[i]}).encode('utf-8')
            publisher.publish(topic_path, data)

    # Wait for responses
    responses = []
    for _ in range(len(functions_list) * len(content_list)):
        try:
            # Wait for a response with a timeout of 4 minutes
            response = await asyncio.wait_for(response_queue.get(), timeout=240)
            responses.append(response)
        except asyncio.TimeoutError:
            print("Timeout waiting for a response")
            break

    return responses



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
