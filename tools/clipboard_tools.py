from typing import Optional
import re
import os
from .base_tool import BaseTool
from utils.utils import (
    ModelName,
    model_name_to_id,
    timeit_decorator,
)
from utils.memory_management import memory_manager
import pyperclip
from dotenv import dotenv_values
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from utils.llm import structured_output_prompt
from chainlit.logger import logger

config = dotenv_values(".env")

# Load Jinja2 environment
PROMPT_DIR = "prompts"  # Directory where your XML templates are stored
env = Environment(loader=FileSystemLoader(PROMPT_DIR), autoescape=True)


class FileNameResponse(BaseModel):
    file_name: str
    model: ModelName


class ClipboardToMemoryTool(BaseTool):
    """
    Copy the content from the clipboard to memory.
    If a key is provided, it will be used to store the content in memory.
    If no key is provided, a default key 'clipboard_content' will be used.
    """

    def __init__(self):
        super().__init__(
            name="clipboard_to_memory",
            description="Copies the contents of the clipboard into memory.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The key to use for storing the clipboard content in memory. If not provided, a default key 'clipboard_content' will be used.",
                    },
                },
                "required": [],
            },
        )

    @timeit_decorator
    async def handle(self, key: Optional[str] = None) -> dict:
        try:
            clipboard_content = pyperclip.paste()
            memory_key = key if key else "clipboard_content"
            memory_manager.upsert(memory_key, clipboard_content)
            return {
                "status": "success",
                "key": memory_key,
                "message": f"Clipboard content stored in memory under key '{memory_key}'",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to copy clipboard content to memory: {str(e)}",
            }


class ClipboardToFileTool(BaseTool):
    """
    Get content from clipboard, generate a file name based on the content,
    and save the content (trimmed to 1000 chars max) to a file in the scratch_pad_dir.
    """

    def __init__(self):
        super().__init__(
            name="clipboard_to_file",
            description="Gets content from clipboard, generates a file name based on the content, and saves the content (trimmed to 1000 chars max) to a file in the scratch_pad_dir.",
            parameters={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "enum": ["base_model", "fast_model"],
                        "description": "The model to use.",
                    },
                },
                "required": [],
            },
        )

    @timeit_decorator
    async def handle(self, model: ModelName = ModelName.base_model) -> dict:

        SCRATCHPAD_DIR = config.get("SCRATCH_PAD_DIR", "./scratchpad")

        try:
            # Get content from clipboard
            content = pyperclip.paste().strip()

            # Trim content to 1000 chars max
            trimmed_content = content[:1000]

            # Render select_file_prompt template
            clipboard_to_file_template = env.get_template(
                "clipboard_to_file_prompt.xml"
            )
            clipboard_to_file_prompt = clipboard_to_file_template.render(
                trimmed_content=trimmed_content
            )

            logger.info(f"🍓 Clipboard to file prompt: {clipboard_to_file_prompt}")

            file_name_response = await structured_output_prompt(
                clipboard_to_file_prompt, FileNameResponse, model_name_to_id[model]
            )
            file_name = file_name_response.file_name

            # Ensure the file name is valid
            file_name = re.sub(r"[^\w\-_\.]", "_", file_name)
            file_name = file_name[:50]  # Limit to 50 characters

            # Save to file
            file_path = os.path.join(SCRATCHPAD_DIR, file_name)
            with open(file_path, "w") as file:
                file.write(content)

            return {
                "status": "success",
                "message": f"Content saved to {file_path}",
                "file_name": file_name,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to save clipboard content to file: {str(e)}",
            }
