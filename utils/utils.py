from enum import Enum
import os
import json
import functools
import asyncio
import time
from datetime import datetime

RUN_TIME_TABLE_LOG_JSON = "runtime_time_table.jsonl"

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
    ModelName.base_model: "gpt-4o-2024-08-06",
    ModelName.fast_model: "gpt-4o-mini-2024-07-18",
    ModelName.image_model: "dall-e-3",
}

# Load personalization settings
personalization_file = os.getenv("PERSONALIZATION_FILE", "./personalization.json")
with open(personalization_file, "r") as f:
    personalization = json.load(f)

ai_assistant_name = personalization.get("ai_assistant_name", "Assistant")
human_name = personalization.get("human_name", "User")
voice = personalization.get("voice", "alloy")

SESSION_INSTRUCTIONS = (
    f"System settings:\nTool use: enabled.\n\nInstructions:\n- You are {ai_assistant_name}, a helpful assistant. Respond to {human_name}.  You are responsible for helping test realtime voice capabilities\n- Please make sure to respond with a helpful voice via audio\n- Be kind, helpful, and curteous\n- It is okay to ask the user questions\n- Use tools and functions you have available liberally, it is part of the training apparatus\n- Be open to exploration and conversation\n- Remember: this is just for fun and testing!\n\nPersonality:\n- Be upbeat and genuine\n- Try speaking quickly as if excited\n\n"
    f"{personalization.get('system_message_suffix', '')}"
)

def timeit_decorator(func):
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        
        # Retrieve model from kwargs if present; default to None if not
        #print(args)
        print(kwargs)
        model = kwargs.get("model", None)
        prompt = kwargs.get("prompt", None)
        async_wrapper.model = model  # Assign model to wrapper attribute, defaulting to None if not provided
            
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = round(end_time - start_time, 4)

        # `args[0]` refers to the instance (`self`) of the tool class
        instance = args[0] if len(args) > 0 else None
        #description = getattr(instance, "description", func.__name__)
        name = getattr(instance, "name", func.__name__)
        
        print(f"⏰ {name}() took {duration:.4f} seconds")
        
        # Prepare to log the model usage
        model_name = model_name_to_id.get(async_wrapper.model, "unknown")

        jsonl_file = RUN_TIME_TABLE_LOG_JSON

        # Create new time record
        time_record = {
            "timestamp": datetime.now().isoformat(),
            "function": name,
            "prompt": prompt,
            "duration": f"{duration:.4f}",
            "model": f"{async_wrapper.model} - {model_name}",
        }

        # Append the new record to the JSONL file
        with open(jsonl_file, "a") as file:
            json.dump(time_record, file)
            file.write("\n")

        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        
        # Retrieve model from kwargs if present; default to None if not
        model = kwargs.get("model", None)
        async_wrapper.model = model  # Assign model to wrapper attribute, defaulting to None if not provided
            
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = round(end_time - start_time, 4)
        print(f"⏰ {func.__name__}() took {duration:.4f} seconds")
        
        # Prepare to log the model usage
        model_name = model_name_to_id.get(async_wrapper.model, "unknown")

        jsonl_file = RUN_TIME_TABLE_LOG_JSON

        # Create new time record
        time_record = {
            "timestamp": datetime.now().isoformat(),
            "function": func.__name__,
            "duration": f"{duration:.4f}",
            "model": f"{sync_wrapper.model} - {model_name}",
        }

        # Append the new record to the JSONL file
        with open(jsonl_file, "a") as file:
            json.dump(time_record, file)
            file.write("\n")

        return result

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper