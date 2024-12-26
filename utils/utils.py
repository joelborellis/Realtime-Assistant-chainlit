import asyncio
import functools
import json
import os
import time
from datetime import datetime
from enum import Enum

from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
from dotenv import dotenv_values
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Load environment variables
config = dotenv_values(".env")

# Constants and configurations
PROMPT_DIR = "prompts"  # Directory where your XML templates are stored
RUN_TIME_TABLE_LOG_JSON = "runtime_time_table.jsonl"
PERSONALIZATION_FILE = config.get("PERSONALIZATION_FILE", "./personalization.json")

# Attempt to load Jinja2 environment
try:
    env = Environment(loader=FileSystemLoader(PROMPT_DIR), autoescape=True)
except Exception as e:
    raise RuntimeError(f"Failed to initialize Jinja environment: {e}")

class ModelName(str, Enum):
    state_of_the_art_model = "state_of_the_art_model"
    reasoning_model = "reasoning_model"
    sonnet_model = "sonnet_model"
    base_model = "base_model"
    fast_model = "fast_model"
    image_model = "image_model"

# Mapping from enum options to model IDs
model_name_to_id = {
    ModelName.state_of_the_art_model: "o1-preview",
    ModelName.reasoning_model: "o1-mini",
    ModelName.sonnet_model: "claude-3-5-sonnet-20240620",
    ModelName.base_model: "gpt-4o",
    ModelName.fast_model: "gpt-4o-mini",
    ModelName.image_model: "dall-e-3",
}

# Load personalization settings with exception handling
try:
    with open(PERSONALIZATION_FILE, "r", encoding="utf-8") as f:
        personalization = json.load(f)
except FileNotFoundError:
    # If the file doesn't exist, fallback to defaults
    personalization = {}
except json.JSONDecodeError as e:
    raise ValueError(f"Error decoding JSON from {PERSONALIZATION_FILE}: {e}")

ai_assistant_name = personalization.get("ai_assistant_name", "Assistant")
human_name = personalization.get("human_name", "User")
suffix = personalization.get("system_message_suffix", "")
voice = personalization.get("voice", "alloy")

# Render the realtime prompt template
try:
    realtime_template = env.get_template("realtime_prompt.xml")
    realtime_prompt = realtime_template.render(
        ai_assistant_name=ai_assistant_name,
        human_name=human_name,
        suffix=suffix
    )
except TemplateNotFound:
    raise FileNotFoundError("The template 'realtime_prompt.xml' could not be found in the prompts directory.")
except Exception as e:
    raise RuntimeError(f"Error rendering realtime prompt: {e}")

def timeit_decorator(func):
    """
    A decorator that times the execution of both sync and async functions.
    It logs the function name, execution duration, and optionally the model used.
    Logs are appended to a JSONL file defined by RUN_TIME_TABLE_LOG_JSON.
    """

    def log_time_record(name, duration, model, prompt=None):
        # Prepare to log the model usage
        model_id = model_name_to_id.get(model, "unknown")
        time_record = {
            "timestamp": datetime.now().isoformat(),
            "function": name,
            "duration": f"{duration:.4f}",
            "model": f"{model} - {model_id}"
        }
        if prompt is not None:
            time_record["prompt"] = prompt

        try:
            with open(RUN_TIME_TABLE_LOG_JSON, "a", encoding="utf-8") as file:
                json.dump(time_record, file)
                file.write("\n")
        except IOError as e:
            # If logging fails, print a warning to console (non-blocking)
            print(f"Warning: Could not write to {RUN_TIME_TABLE_LOG_JSON}: {e}")

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        model = kwargs.get("model", None)
        prompt = kwargs.get("prompt", None)

        try:
            result = await func(*args, **kwargs)
        except Exception as e:
            print(f"Error in async function {func.__name__}: {e}")
            raise

        end_time = time.perf_counter()
        duration = round(end_time - start_time, 4)

        # Attempt to get instance name if first arg is self
        instance = args[0] if args else None
        name = getattr(instance, "name", func.__name__)
        print(f"⏰ {name}() took {duration:.4f} seconds")

        # Log the time record
        log_time_record(name, duration, model, prompt)
        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        model = kwargs.get("model", None)

        try:
            result = func(*args, **kwargs)
        except Exception as e:
            print(f"Error in sync function {func.__name__}: {e}")
            raise

        end_time = time.perf_counter()
        duration = round(end_time - start_time, 4)
        name = func.__name__
        print(f"⏰ {name}() took {duration:.4f} seconds")

        # Log the time record
        log_time_record(name, duration, model)
        return result

    # Decide which wrapper to return based on whether func is async
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

def upload_file_to_images_container(filename, file):
    """
    Upload a given file-like object to the 'images' container in Azure Blob Storage.
    
    Parameters:
        filename (str): The name of the file (blob) to store in Azure.
        file (file-like): The file-like object to upload. Must support .read().
    
    Returns:
        str: The URL of the uploaded blob.
    
    Raises:
        ValueError: If the Azure connection string is not provided.
        RuntimeError: For general Azure upload errors.
    """
    AZURE_STORAGE_CONNECTION_STRING = config.get("AZURE_STORAGE_CONNECTION_STRING", "")
    if not AZURE_STORAGE_CONNECTION_STRING:
        raise ValueError("Azure storage connection string not configured.")

    container_name = "images"

    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)
        
        # Upload the file and overwrite if it already exists
        blob_client.upload_blob(file, overwrite=True)

        # Construct and return the blob URL
        return blob_client.url

    except ResourceExistsError:
        # This should not occur due to overwrite=True, but included for completeness
        raise RuntimeError(f"The blob '{filename}' already exists and could not be overwritten.")
    except AzureError as e:
        raise RuntimeError(f"Failed to upload file to Azure Blob Storage: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred during the file upload: {e}")
