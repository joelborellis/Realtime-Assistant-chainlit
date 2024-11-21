import yfinance as yf
import chainlit as cl
import plotly
import os
from pydantic import BaseModel
from utils.llm import (
    parse_markdown_backticks,
    structured_output_prompt,
    chat_prompt,
    image_prompt,
    model_predictive_prompt
)
from utils.utils import ModelName, model_name_to_id, timeit_decorator
from chainlit.logger import logger


class CreateFileResponse(BaseModel):
    file_content: str
    file_name: str


class FileSelectionResponse(BaseModel):
    file: str
    model: ModelName = ModelName.base_model


class FileDeleteResponse(BaseModel):
    file: str
    force_delete: bool


create_file_def = {
    "type": "function",
    "name": "create_file",
    "description": "Generates content for a new file based on the user's prompt and file name.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": "The name of the file to create.",
            },
            "prompt": {
                "type": "string",
                "description": "The user's prompt to generate the file content.",
            },
            "model": {
                "type": "string",
                "enum": [
                    "state_of_the_art_model",
                    "reasoning_model",
                    "base_model",
                    "fast_model",
                    "image_model",
                ],
                "description": "The model to use for updating the file content. Defaults to 'base_model' if not explicitly specified.",
            },
        },
        "required": ["file_name", "prompt"],
    },
}


@timeit_decorator
async def create_file_handler(
    file_name: str, prompt: str, model: ModelName = ModelName.base_model
) -> dict:
    """
    Generate content for a new file based on the user's prompt and the file name.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

    # Ensure the scratch pad directory exists
    os.makedirs(scratch_pad_dir, exist_ok=True)

    # Construct the full file path
    file_path = os.path.join(scratch_pad_dir, file_name)

    # Check if the file already exists
    if os.path.exists(file_path):
        return {"status": "file already exists"}

    # Get all memory content
    # memory_content = memory_manager.get_xml_for_prompt(["*"])  # need to implement this
    memory_content = "No real content to consider in memory"

    # Build the structured prompt
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

    #model_selected = model_predictive_prompt(prompt)
    # Call the LLM to generate the file content
    response, model_used = structured_output_prompt(
        prompt_structure, CreateFileResponse, model_name_to_id[model]
    )
    
    logger.info(f"🍓 Create File Used the Model: {model_used}")

    # Write the generated content to the file
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
    return {"status": "file created", "file_name": response.file_name}


create_file = (create_file_def, create_file_handler)

update_file_def = {
    "type": "function",
    "name": "update_file",
    "description": "Updates a file based on the user's prompt.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The user's prompt describing the updates to the file.",
            },
            "model": {
                "type": "string",
                "enum": [
                    "state_of_the_art_model",
                    "reasoning_model",
                    "base_model",
                    "fast_model",
                    "image_model",
                ],
                "description": "The model to use for updating the file content. Defaults to 'base_model' if not explicitly specified.",
            },
        },
        "required": ["prompt"],  # 'model' is optional
    },
}


@timeit_decorator
async def update_file_handler(
    prompt: str, model: ModelName = ModelName.base_model
) -> dict:
    """
    Update a file based on the user's prompt.
    """

    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

    # Ensure the scratch pad directory exists
    os.makedirs(scratch_pad_dir, exist_ok=True)

    # List available files in SCRATCH_PAD_DIR
    available_files = os.listdir(scratch_pad_dir)
    available_files_str = ", ".join(available_files)

    # Build the structured prompt to select the file
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

    # Call the LLM to select the file
    file_selection_response, model_used_structured = structured_output_prompt(
        select_file_prompt,
        FileSelectionResponse,
        model=model_name_to_id[model],
    )
    
    logger.info(f"🍓 Update File Used the Model: {model_used_structured}")

    # Check if a file was selected
    if not file_selection_response.file:
        return {"status": "No matching file found"}

    selected_file = file_selection_response.file
    file_path = os.path.join(scratch_pad_dir, selected_file)

    # Load the content of the selected file
    with open(file_path, "r") as f:
        file_content = f.read()

    # Get all memory content
    # memory_content = memory_manager.get_xml_for_prompt(["*"])  # need to implement this
    memory_content = "No real content to consider in memory"

    # Build the structured prompt to generate the updates
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
    <instruction>If code generation was requested, be sure to output runnable code, don't include any markdown formatting.</instruction>
</instructions>

<file-name>
    {selected_file}
</file-name>

<file-content>
    {file_content}
</file-content>

{memory_content}

<user-prompt>
    {prompt}
</user-prompt>
"""

    # Call the LLM to generate the updates using the specified model
    #model_selected = model_predictive_prompt(prompt)
    file_update_response, model_used_chat = chat_prompt(update_file_prompt, model_name_to_id[model])
    
    logger.info(f"🍓 Update File Used the Model: {model_used_chat}")

    # Apply the updates by writing the new content to the file
    with open(file_path, "w") as f:
        f.write(parse_markdown_backticks(file_update_response))

    return {
        "status": "File updated",
        "file_name": selected_file,
        "model_used": model_used_chat,
    }


update_file = (update_file_def, update_file_handler)

delete_file_def = {
    "type": "function",
    "name": "delete_file",
    "description": "Deletes a file based on the user's prompt.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The user's prompt describing the file to delete.",
            },
            "force_delete": {
                "type": "boolean",
                "description": "Whether to force delete the file without confirmation. Infer whether to force delete based on the users prompt.  Defaults to 'false' if 'force delete' is not explicitly specified.",
            },
            "model": {
                "type": "string",
                "enum": [
                    "state_of_the_art_model",
                    "reasoning_model",
                    "base_model",
                    "fast_model",
                    "image_model",
                ],
                "description": "The model to use for deleting the file content. Defaults to 'base_model' if not explicitly specified.",
            },
        },
        "required": ["prompt", "force_delete"],
    },
}


@timeit_decorator
async def delete_file_handler(
    prompt: str, force_delete: bool = False, model: ModelName = ModelName.base_model
) -> dict:
    """
    Delete a file based on the user's prompt.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

    # Ensure the scratch pad directory exists
    os.makedirs(scratch_pad_dir, exist_ok=True)

    # List available files in SCRATCH_PAD_DIR
    available_files = os.listdir(scratch_pad_dir)
    available_files_str = ", ".join(available_files)

    # Build the structured prompt to select the file and determine 'force_delete' status
    select_file_prompt = f"""
    <purpose>
        Select a file from the available files to delete.
    </purpose>

    <instructions>
        <instruction>Based on the user's prompt and the list of available files, infer which file the user wants to delete.</instruction>
        <instruction>If no file matches, return an empty string for 'file'.</instruction>
        <instruction>If user prompt does not contain 'force delete' return False.</instruction>
    </instructions>

    <available-files>
        {available_files_str}
    </available-files>

    <user-prompt>
        {prompt}
    </user-prompt>
    """

    # Call the LLM to select the file and determine 'force_delete'
    file_delete_response, model_used = structured_output_prompt(
        select_file_prompt, FileDeleteResponse, model_name_to_id[model]
    )
    
    logger.info(f"🍓 Delete File Used the Model: {model_used}")
    print(file_delete_response.force_delete)
    print(f"{force_delete}: {prompt}")
    
    # Check if a file was selected
    if not file_delete_response.file:
        result = {"status": "No matching file found"}
    else:
        selected_file = file_delete_response.file
        file_path = os.path.join(scratch_pad_dir, selected_file)
        # Check if the file exists
        if not os.path.exists(file_path):
            result = {"status": "File does not exist", "file_name": selected_file}
            
        # If 'force_delete' is False, prompt for confirmation
        elif not file_delete_response.force_delete:
            result = {
                "status": "Confirmation required",
                "file_name": selected_file,
                "message": f"Are you sure you want to delete '{selected_file}'? Say force delete if you want to delete.",
            }
        else:
            # Proceed to delete the file
            os.remove(file_path)
            result = {"status": f"The file {selected_file} has been deleted", "file_name": selected_file}

    return result


delete_file = (delete_file_def, delete_file_handler)

generate_image_def = {
    "type": "function",
    "name": "generate_image",
    "description": "Generates an image or picture based on the users prompt.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The user's prompt describing the image or picture they want generated",
            },
            "model": {
                "type": "string",
                "enum": [
                    "state_of_the_art_model",
                    "reasoning_model",
                    "base_model",
                    "fast_model",
                    "image_model",
                ],
                "description": "The model to use for creating an image. Defaults to 'image_model' if not explicitly specified by the user.",
            },
        },
        "required": ["prompt", "model"],
    },
}


@timeit_decorator
async def generate_image_handler(
    prompt: str, model: ModelName = ModelName.image_model
) -> dict:

    generate_image_prompt = f"""
    <purpose>
        Generate an image based on the users prompt.
    </purpose>

    <instructions>
        <instruction>Based on the user's prompt generate an image.</instruction>
    </instructions>

    <user-prompt>
        {prompt}
    </user-prompt>
    """
    
    
    # Call the LLM to generate the updates using the specified model
    image_url = image_prompt(generate_image_prompt, model_name_to_id[model])
    
    logger.info(f"🍓 Create Image Used the Model: {model_name_to_id[model]}")

    # Check if a file was selected
    if not image_url:
        result = {"status": "No image was generated"}
    else:
        # Download and open the image using PIL
        # image_response = requests.get(image_url)
        image = cl.Image(url=image_url, name="image1", display="inline")
        # Attach the image to the message
        await cl.Message(
            content="This message has an image!",
            elements=[image],
        ).send()
        result = {"status": "Image created"}
    
    return result


generate_image = (generate_image_def, generate_image_handler)

tools = [
    create_file,
    update_file,
    delete_file,
    generate_image,
]
