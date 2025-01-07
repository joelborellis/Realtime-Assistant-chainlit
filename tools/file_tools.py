import os
from utils.llm import structured_output_prompt, parse_markdown_backticks, chat_prompt
from .base_tool import BaseTool
from utils.utils import ModelName, model_name_to_id, timeit_decorator
from pydantic import BaseModel
from chainlit.logger import logger
from jinja2 import Environment, FileSystemLoader
import chainlit as cl

# Load Jinja2 environment
PROMPT_DIR = "prompts"  # Directory where your XML templates are stored
env = Environment(loader=FileSystemLoader(PROMPT_DIR), autoescape=True)

class CreateFileResponse(BaseModel):
    file_content: str
    file_name: str


class CreateFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="create_file",
            description="Generates content for a new file based on the user's prompt and file name.",
            parameters={
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The name of the file to create.",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "The user's prompt to generate the file content.  If not specified then do not add any content to the file.",
                    },
                    "model": {
                        "type": "string",
                        "enum": [
                            "base_model",
                            "fast_model",
                        ],
                        "description": "The model to use for generating content.",
                    },
                },
                "required": ["file_name", "prompt"],
            },
        )

    @timeit_decorator
    async def handle(
        self, file_name: str, prompt: str, model: ModelName = ModelName.base_model
    ) -> dict:
        scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")
        os.makedirs(scratch_pad_dir, exist_ok=True)
        file_path = os.path.join(scratch_pad_dir, file_name)

        if os.path.exists(file_path):
            return {"status": "file already exists"}

        # Get all memory content
        # memory_content = memory_manager.get_xml_for_prompt(["*"])  # need to implement this
        memory_content = "No real content to consider in memory"
        
        # Render select_file_prompt template
        create_content_template = env.get_template("create_file_prompt.xml")
        create_content_prompt = create_content_template.render(
            file_name=file_name,
            prompt=prompt,
            memory_content=memory_content
        )
        
        response, model_used = structured_output_prompt(
            create_content_prompt, CreateFileResponse, model_name_to_id[model]
        )
        with open(file_path, "w") as f:
            f.write(parse_markdown_backticks(response.file_content))
            
        elements = [
            cl.File(
                name=response.file_name,
                path=scratch_pad_dir + "/" + response.file_name,
                display="inline",
            )
        ]

        await cl.Message(content=response.file_content, elements=elements).send()
        return {"status": "file created", "file_name": file_name}


class FileDeleteResponse(BaseModel):
    file: str
    force_delete: bool


class DeleteFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="delete_file",
            description="Deletes a file based on the user's prompt.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Prompt describing the file to delete.",
                    },
                    "force_delete": {
                        "type": "boolean",
                        "description": "Whether to force delete without confirmation.",
                    },
                    "model": {
                        "type": "string",
                        "enum": ["base_model", "fast_model"],
                        "description": "The model to use.",
                    },
                },
                "required": ["prompt", "force_delete"],
            },
        )

    @timeit_decorator
    async def handle(
        self, prompt: str, force_delete: bool, model: str = "base_model"
    ) -> dict:
        scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")
        os.makedirs(scratch_pad_dir, exist_ok=True)

        available_files = os.listdir(scratch_pad_dir)
        select_prompt = f"""
        Select a file to delete based on the following prompt:
        {prompt}
        Available files: {', '.join(available_files)}
        """

        response, model_used = structured_output_prompt(
            select_prompt, FileDeleteResponse, model_name_to_id[model]
        )

        if not response.file:
            return {"status": "No matching file found"}

        file_path = os.path.join(scratch_pad_dir, response.file)
        if not os.path.exists(file_path):
            return {"status": "File does not exist"}

        if not force_delete:
            return {"status": "Confirmation required", "file_name": response.file}

        os.remove(file_path)
        return {"status": f"File {response.file} deleted"}


class FileSelectionResponse(BaseModel):
    file: str
    model: ModelName = ModelName.base_model


class UpdateFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="update_file",
            description="Updates a file based on the user's prompt.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The user's prompt describing the updates to the file.",
                    },
                    "model": {
                        "type": "string",
                        "enum": [
                            "base_model",
                            "fast_model",
                        ],
                        "description": "The model to use for updating the file content. Defaults to 'base_model' if not explicitly specified.",
                    },
                },
                "required": ["prompt"],
            },
        )

    @timeit_decorator
    async def handle(
        self, prompt: str, model: ModelName = ModelName.base_model
    ) -> dict:
        """
        Update a file based on the user's prompt.
        """
        scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")
        os.makedirs(scratch_pad_dir, exist_ok=True)

        # List available files
        available_files = os.listdir(scratch_pad_dir)
        available_files_str = ", ".join(available_files)

        logger.info(
            f"🍓 Available files in update file (list from /scratchpad): {available_files_str}"
        )
    
        
        # Render select_file_prompt template
        select_file_template = env.get_template("select_file_prompt.xml")
        select_file_prompt = select_file_template.render(
            available_files_str=available_files_str,
            prompt=prompt
        )

        logger.info(
            f"🍓 Select file prompt: {select_file_prompt}"
        )
        
        # Call LLM to select a file
        file_selection_response, model_used_file_select = structured_output_prompt(
            select_file_prompt, FileSelectionResponse, model_name_to_id[model]
        )

        logger.info(
            f"🍓 Select File to Update found the file: {file_selection_response.file}"
        )

        # If no file is selected
        if not file_selection_response.file:
            return {"status": "No matching file found"}

        selected_file = file_selection_response.file
        file_path = os.path.join(scratch_pad_dir, selected_file)

        # Read the content of the selected file
        with open(file_path, "r") as f:
            file_content = f.read()
            
        # Render update_file_prompt template
        update_file_template = env.get_template("update_file_prompt.xml")
        update_file_prompt = update_file_template.render(
            selected_file=selected_file,
            file_content=file_content,
            prompt=prompt
        )

        logger.info(f"🍓 Update file prompt: {update_file_prompt}")
        
        # Call LLM to generate file updates
        file_update_response, model_used_chat = chat_prompt(
            update_file_prompt, model_name_to_id[model]
        )

        logger.info(f"🍓 File Update Response: {file_update_response}")

        # Write the updated content to the file
        with open(file_path, "w") as f:
            f.write(parse_markdown_backticks(file_update_response))
        
        elements = [
            cl.File(
                name=selected_file,
                path=scratch_pad_dir + "/" + selected_file,
                display="inline",
            )
        ]

        await cl.Message(content=file_update_response, elements=elements).send()

        return {
            "status": "File updated",
            "file_name": selected_file,
        }