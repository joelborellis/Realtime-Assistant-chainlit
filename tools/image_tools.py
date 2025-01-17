from utils.llm import generate_image_prompt, describe_image_prompt, process_image
from utils.utils import timeit_decorator, model_name_to_id, ModelName
import chainlit as cl
from .base_tool import BaseTool
from jinja2 import Environment, FileSystemLoader
from dotenv import dotenv_values
import os
import csv
import pandas as pd
import glob


config = dotenv_values(".env")

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
        try:
            # Attempt to retrieve the model ID
            model_id = model_name_to_id[model]
        except KeyError:
            return {"status": "Error: Invalid model name specified"}

        try:
            # Generate the image URL
            image_url = await generate_image_prompt(prompt, model_id)
        except Exception as e:
            # Handle any unforeseen errors during image generation
            return {"status": f"Error generating image: {str(e)}"}

        # Check if an image was actually generated
        if not image_url:
            return {"status": "No image generated"}

        try:
            # Create and send the image in a Chainlit message
            image = cl.Image(url=image_url, name="Generated Image", display="inline")
            await cl.Message(content="Here is your image:", elements=[image]).send()
        except Exception as e:
            # Handle any errors related to Chainlit message sending
            return {"status": f"Error displaying image: {str(e)}"}

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
    async def handle(
        self, prompt: str, image_url: str, model: ModelName = ModelName.base_model
    ) -> dict:
        try:
            # Log incoming parameters
            print(f"In the describe function: {prompt} : {image_url}")

            # Attempt to fetch and render the template
            describe_image_template = env.get_template("describe_image_prompt.xml")
            describe_prompt = describe_image_template.render(
                image_url=image_url, 
                prompt=prompt
            )
        except Exception as e:
            return {"status": f"Error rendering template: {str(e)}"}

        try:
            # Attempt to generate image description
            description = await describe_image_prompt(
                describe_prompt, image_url, model_name_to_id[model]
            )
        except KeyError:
            return {"status": "Error: Invalid model name specified."}
        except Exception as e:
            return {"status": f"Error describing image: {str(e)}"}

        # If everything succeeds, return the successful response
        return {"status": "Description created", "description": description}
    
class ProcessScreenshotsTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="process_screenshots",
            description="Processes screenshot images when the user prompts you to process them.",
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
    async def handle(
        self, model: ModelName = ModelName.base_model
    ) -> dict:
        try:
            SCREENSHOTS_DIR = config.get("SCREENSHOTS_DIR", "./screenshots")
            #os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
            
            file_path = os.path.join(SCREENSHOTS_DIR, "screenshot_annotations.csv")
            
            if os.path.isfile(file_path):
                df = pd.read_csv(file_path)
            else:
                df = pd.DataFrame(columns=["image_file", "description"])
            
            print(file_path)
            
            image_files = glob.glob(f"{SCREENSHOTS_DIR}/*.png")
            image_files.sort()
            
            for image_file in image_files:
                if image_file not in df["image_file"].values:
                    print(image_file)

                    print(f"\nProcessing {image_file}\n")

                    result = await process_image(image_file, model_name_to_id[model])

                    # Add a new row to the DataFrame
                    df.loc[len(df)] = [image_file, result.text_content]
                    
            # Save the DataFrame to a CSV file
            df.to_csv(
                "screenshot_annotations.csv",
                index=False,
                quoting=csv.QUOTE_ALL,  # Put quotes around fields
                escapechar="\\",  # Escape backslashes
                lineterminator="\n",  # Ensure newline characters are recognized
                encoding="utf-8-sig",
)

        except Exception as e:
            return {"status": f"Error in describe_screenshots: {str(e)}"}

        # If everything succeeds, return the successful response
        return {"status": "Screenshot annotation file updated", "description": "description"}

