from typing import Tuple

from openai import RateLimitError, AsyncOpenAI
from pydantic import BaseModel, ValidationError
from dotenv import dotenv_values
from openai import OpenAIError
from markitdown import MarkItDown

import backoff

# Load environment variables
config = dotenv_values(".env")

###  OpenAI chat completions call with backoff for rate limits and structured outputs
@backoff.on_exception(backoff.expo, RateLimitError, max_tries=5)
async def structured_output_prompt(
    prompt: str, response_format: BaseModel, model: str
) -> Tuple[BaseModel, str]:
    """
    Parse the response from the OpenAI API using structured output.

    Args:
        prompt (str): The prompt to send to the OpenAI API.
        response_format (BaseModel): The Pydantic model representing the expected response format.
        model (str): The model ID to use for the API call.

    Returns:
        Tuple[BaseModel, str]: A tuple containing the parsed response and the model used.

    Raises:
        ValueError: If the response cannot be parsed into the given response_format.
        OpenAIError: If there's an error from the OpenAI API.
    """
    api_key = config.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not found or empty.")
    
    # setup the OpenAI Client
    client = AsyncOpenAI(api_key=api_key)

    try:
        # Using a hypothetical beta parse method as provided in original code snippet.
        # Adjust this call to the actual method available in your environment.
        completion = await client.beta.chat.completions.parse(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format=response_format
        )
    except OpenAIError as e:
        raise OpenAIError(f"OpenAI API error: {e}") from e
    

    # Extract the message content
    if not completion.choices or not completion.choices[0].message:
        raise ValueError("No response message found in completion.")

    # Here we assume the response is supposed to be parsed into `response_format`.
    # If the `response_format` is a Pydantic model class, we try to parse the content.
    # Adjust parsing logic as per your actual response structure.
    content = completion.choices[0].message

    # If you have a structured response in JSON format, parse it:
    try:
        parsed = content.parsed
        parsed.model = completion.model  # kind of messing up the structured output concept but set the model
    except (ValidationError, ValueError) as e:
        raise ValueError(f"Failed to parse response into the given response_format: {e}") from e

    return parsed


def model_predictive_prompt(prompt: str) -> str:
    """
    Choose the right model name based on a directive from the user.

    Args:
        prompt (str): The user directive prompt.

    Returns:
        str: The selected model name.
    """
    api_key = config.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not found or empty.")

    client = AsyncOpenAI(api_key=api_key)

    model_choices = """
        ModelName.state_of_the_art_model: 'o1',
        ModelName.reasoning_model: 'o1-mini',
        ModelName.sonnet_model: 'claude-3-5-sonnet-20240620',
        ModelName.base_model: 'gpt-4o-2024-08-06',
        ModelName.fast_model: 'gpt-4o-mini',
        ModelName.image_model: 'dall-e-3',
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Choose the right model name based on the following directive from the user: {prompt}. "
                        "Respond only with the model name, and with no markdown formatting."
                    )
                },
                {"role": "user", "content": model_choices}
            ]
        )
    except OpenAIError as e:
        raise OpenAIError(f"OpenAI API error: {e}") from e

    if not completion.choices or not completion.choices[0].message:
        raise ValueError("No response message found in completion.")

    model_selected = completion.choices[0].message
    print(model_selected)
    return model_selected


async def generate_image_prompt(prompt: str, model: str) -> str:
    """
    Call an image generation model to generate an image.

    Args:
        prompt (str): The prompt for the image generation model.
        model (str): The model ID to use for the API call.

    Returns:
        str: The URL of the generated image.
    """
    api_key = config.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not found or empty.")

    client = AsyncOpenAI(api_key=api_key)

    try:
        # This assumes the openai Python library supports `openai.Image.create` or similar.
        # Adjust this method according to the actual image generation API.
        # If `client.images.generate` was a custom method, replace it with the actual supported method.
        response = await client.images.generate(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
    except OpenAIError as e:
        raise OpenAIError(f"OpenAI API error: {e}") from e

    if not response.data:
        raise ValueError("No data returned from image generation.")
    image_url = response.data[0].url
    return image_url


async def describe_image_prompt(prompt: str, image_url: str, model: str) -> str:
    """
    Call a model to describe an image by providing an image URL and a prompt.

    Args:
        prompt (str): The prompt for the model.
        image_url (str): The URL of the image to describe.
        model (str): The model ID to use for the API call.

    Returns:
        str: The assistant's description of the image.
    """
    api_key = config.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not found or empty.")

    client = AsyncOpenAI(api_key=api_key)

    # Assuming the API supports sending image URLs in the request.
    # Adjust according to actual API specifications.
    try:
        response = await client.chat.completions.create(
    model=model,
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": prompt,
            },
            {
            "type": "image_url",
            "image_url": {
                "url":  image_url,
            },
            },
        ],
        }
    ],
    )
    except OpenAIError as e:
        raise OpenAIError(f"OpenAI API error: {e}") from e

    if not response.choices or not response.choices[0].message:
        raise ValueError("No description returned from the model.")

    description = response.choices[0].message
    #print(description)
    return description.content

# processing the images
async def process_image(image_file: str, model: str):
    
    api_key = config.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not found or empty.")
    
    client = AsyncOpenAI(api_key=api_key)
    
    print(model)
    
    markitdown = MarkItDown(llm_client=client, llm_model=model)

    result = markitdown.convert("../screenshots/Screenshot 2023-04-03 111400.png")
    
    return result

def parse_markdown_backticks(str) -> str:
    if "```" not in str:
        return str.strip()
    # Remove opening backticks and language identifier
    str = str.split("```", 1)[-1].split("\n", 1)[-1]
    # Remove closing backticks
    str = str.rsplit("```", 1)[0]
    # Remove any leading or trailing whitespace
    return str.strip()