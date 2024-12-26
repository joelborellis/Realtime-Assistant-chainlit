from utils.llm import create_image_prompt, describe_image_prompt
from utils.utils import timeit_decorator, model_name_to_id, ModelName
import chainlit as cl
from .base_tool import BaseTool
from jinja2 import Environment, FileSystemLoader

# Load Jinja2 environment
PROMPT_DIR = "prompts"  # Directory where your XML templates are stored
env = Environment(loader=FileSystemLoader(PROMPT_DIR), autoescape=True)


class GenerateImageTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="generate_image",
            description="Generates an image based on the user's prompt.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Prompt for the image.",
                    },
                    "model": {
                        "type": "string",
                        "enum": ["image_model"],
                        "description": "The model to use.",
                    },
                },
                "required": ["prompt"],
            },
        )

    @timeit_decorator
    async def handle(self, prompt: str, model: str = "image_model") -> dict:
        image_url = create_image_prompt(prompt, model_name_to_id[model])

        if not image_url:
            return {"status": "No image generated"}

        image = cl.Image(url=image_url, name="Generated Image", display="inline")
        await cl.Message(content="Here is your image:", elements=[image]).send()

        return {"status": "Image generated"}


class DescribeImageTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="describe_image",
            description="Returns a detailed description of the contents of an image file uploaded by the user.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The user's text prompt.",
                    },
                    "image_url": {
                        "type": "string",
                        "description": "The url of the image to describe.",
                    },
                    "model": {
                        "type": "string",
                        "enum": ["base_model", "fast_model"],
                        "description": "The model to use.",
                    },
                },
                "required": ["prompt", "image_url"],
            },
        )

    @timeit_decorator
    async def handle(self, prompt: str, image_url: str, model: ModelName = ModelName.base_model) -> dict:
        print(f"In the describe function:  {prompt}:  {image_url}")

        # Render update_file_prompt template
        describe_image_template = env.get_template("describe_image_prompt.xml")
        describe_prompt = describe_image_template.render(
            image_url=image_url,
            prompt=prompt
        )

        description = describe_image_prompt(describe_prompt, image_url, model_name_to_id[model])

        return {"status": "Description created", "description": description}
