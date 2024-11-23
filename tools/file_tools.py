import os
from utils.llm import structured_output_prompt, parse_markdown_backticks, chat_prompt
from .base_tool import BaseTool
from utils.utils import ModelName, model_name_to_id, timeit_decorator
from pydantic import BaseModel
from chainlit.logger import logger


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
    ):
        scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")
        os.makedirs(scratch_pad_dir, exist_ok=True)
        file_path = os.path.join(scratch_pad_dir, file_name)

        if os.path.exists(file_path):
            return {"status": "file already exists"}

        # Get all memory content
        # memory_content = memory_manager.get_xml_for_prompt(["*"])  # need to implement this
        memory_content = "No real content to consider in memory"

        # Generate content using structured_output_prompt
        prompt_structure = f"""
            <purpose>
                Generate content for a new file based on the user's prompt, the file name, and the current memory content.
            </purpose>

            <instructions>
                <instruction>Based on the user's prompt, the file name, and the current memory content, generate content for a new file.</instruction>
                <instruction>The file name is the name of the file that the user wants to create.</instruction>
                <instruction>The user's prompt is the prompt that the user wants to use to generate the content for the new file.</instruction>
                <instruction>Consider the current memory content when generating the file content, if relevant.</instruction>
                <instruction>If code generation was requested, be sure to output runnable code, don't include any markdown formatting.</instruction>
            </instructions>

            <user-prompt>
                {prompt}
            </user-prompt>

            <file-name>
                {file_name}
            </file-name>

            {memory_content}
                """

        response, model_used = structured_output_prompt(
            prompt_structure, CreateFileResponse, model_name_to_id[model]
        )
        with open(file_path, "w") as f:
            f.write(parse_markdown_backticks(response.file_content))
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

        # Prompt to select the file
        select_file_prompt = f"""
        <purpose>
            Select a file from the available files based on the user's prompt.
        </purpose>
        <instructions>
            <instruction>Based on the user's prompt and the list of available files, infer which file the user wants to update.</instruction>
            <instruction>If no file matches, return an empty string for 'file'.</instruction>
        </instructions>
        <available-files>
            {available_files_str}
        </available-files>
        <user-prompt>
            {prompt}
        </user-prompt>
        """

        # Call LLM to select a file
        file_selection_response, model_used_file_select = structured_output_prompt(
            select_file_prompt, FileSelectionResponse, model_name_to_id[model]
        )

        logger.info(f"🍓 Select File to Update Used the Model: {model_used_file_select}")

        # If no file is selected
        if not file_selection_response.file:
            return {"status": "No matching file found"}

        selected_file = file_selection_response.file
        file_path = os.path.join(scratch_pad_dir, selected_file)

        # Read the content of the selected file
        with open(file_path, "r") as f:
            file_content = f.read()

        # Build update prompt
        update_file_prompt = f"""
        <purpose>
            Update the content of the file based on the user's prompt, the current file content, and the current memory content.
        </purpose>
        <instructions>
            <instruction>Based on the user's prompt, the current file content, and the current memory content, generate the updated content for the file.</instruction>
            <instruction>The file-name is the name of the file to update.</instruction>
            <instruction>The user's prompt describes the updates to make.</instruction>
            <instruction>Consider the current memory content when generating the file updates, if relevant.</instruction>
            <instruction>Respond exclusively with the updates to the file and nothing else; they will be used to overwrite the file entirely using f.write().</instruction>
            <instruction>Do not include any preamble or commentary or markdown formatting, just the raw updates.</instruction>
            <instruction>Be precise and accurate.</instruction>
        </instructions>
        <file-name>
            {selected_file}
        </file-name>
        <file-content>
            {file_content}
        </file-content>
        <user-prompt>
            {prompt}
        </user-prompt>
        """

        # Call LLM to generate file updates
        file_update_response, model_used_chat = chat_prompt(
            update_file_prompt, model_name_to_id[model]
        )

        logger.info(f"🍓 Update File Used the Model: {model_used_chat}")

        # Write the updated content to the file
        with open(file_path, "w") as f:
            f.write(parse_markdown_backticks(file_update_response))

        return {
            "status": "File updated",
            "file_name": selected_file,
        }
