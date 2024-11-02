from enum import Enum
import os
import json

class ModelName(str, Enum):
    state_of_the_art_model = "state_of_the_art_model"
    reasoning_model = "reasoning_model"
    sonnet_model = "sonnet_model"
    base_model = "base_model"
    fast_model = "fast_model"


# Mapping from enum options to model IDs
model_name_to_id = {
    ModelName.state_of_the_art_model: "o1-preview",
    ModelName.reasoning_model: "o1-mini",
    ModelName.sonnet_model: "claude-3-5-sonnet-20240620",
    ModelName.base_model: "gpt-4o-2024-08-06",
    ModelName.fast_model: "gpt-4o-mini",
}

# Load personalization settings
personalization_file = os.getenv("PERSONALIZATION_FILE", "./personalization.json")
with open(personalization_file, "r") as f:
    personalization = json.load(f)

ai_assistant_name = personalization.get("ai_assistant_name", "Assistant")
human_name = personalization.get("human_name", "User")
voice = personalization.get("voice", "alloy")

SESSION_INSTRUCTIONS = (
    f"You are {ai_assistant_name}, a helpful assistant. Respond to {human_name}. "
    f"{personalization.get('system_message_suffix', '')}"
)