import asyncio
import base64
import hashlib
import re
import threading
from queue import Queue


def async_to_sync_generator(async_gen):
    """
    Converts an async generator to a sync generator using a Queue.
    """
    # Create a Queue to communicate between async and sync
    queue = Queue()

    # Define the async task that fetches items and puts them in the queue
    async def fetch_items():
        async for item in async_gen:
            queue.put(item)
        queue.put(None)  # Signal the end of the stream

    # Start the async fetching in a background thread
    def start_background_fetching(loop):
        asyncio.set_event_loop(loop)
        loop.run_until_complete(fetch_items())

    loop = asyncio.new_event_loop()
    threading.Thread(
        target=start_background_fetching, args=(loop,), daemon=True
    ).start()

    # Synchronously yield items from the queue
    while True:
        item = queue.get()
        if item is None:  # End of stream signal
            break
        yield item


# # Usage example assuming an async generator `async_gen_function`
# async_gen = async_gen_function()  # Replace with your actual async generator
# for item in async_to_sync_generator(async_gen):
#     print(item)


def id_hash(input_string, length=10):
    # Hash the input string using SHA-256
    hash_obj = hashlib.sha256(input_string.encode("utf-8"))
    hash_digest = hash_obj.digest()

    # Encode the hash using base64
    base64_encoded = base64.urlsafe_b64encode(hash_digest).decode("utf-8")

    # Truncate or adjust the encoded string to the desired length
    short_hash = base64_encoded[:length]

    return short_hash


def convert_keys_to_lowercase(obj):
    if isinstance(obj, dict):
        return {k.lower(): convert_keys_to_lowercase(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_keys_to_lowercase(element) for element in obj]
    else:
        return obj


def extract_code(text: str):
    """
    Extracts code and its type from the provided text enclosed in triple backticks.

    Args:
    text (str): The input text containing code blocks enclosed in triple backticks.

    Returns:
    tuple: A tuple containing the cleaned text (without the code blocks), and a list of tuples,
           each with the type of the code (e.g., python, json) and the code itself.
           If no code blocks are found, returns the original text and None.
    """
    # Pattern to match code blocks including the type specifier
    pattern = r"```(\w+)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    if not matches:
        return text, None

    # Extract and return the code blocks along with their types
    code_blocks = [(match[0], match[1].strip()) for match in matches]
    cleaned_text = re.sub(pattern, "", text, flags=re.DOTALL).strip()

    return cleaned_text, code_blocks
