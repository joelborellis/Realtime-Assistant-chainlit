from utils.llm import image_prompt
from utils.utils import timeit_decorator, model_name_to_id
import chainlit as cl
from .base_tool import BaseTool


class GenerateImageTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="generate_image",
            description="Generates an image based on the user's prompt.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt for the image."},
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
        image_url = image_prompt(prompt, model_name_to_id[model])

        if not image_url:
            return {"status": "No image generated"}

        image = cl.Image(url=image_url, name="Generated Image", display="inline")
        await cl.Message(content="Here is your image:", elements=[image]).send()

        return {"status": "Image generated"}
