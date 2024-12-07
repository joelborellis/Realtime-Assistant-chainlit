import openai
import os
from pydantic import BaseModel

def structured_output_prompt(
    prompt: str, response_format: BaseModel, model: str) -> BaseModel:
    """
    Parse the response from the OpenAI API using structured output.

    Args:
        prompt (str): The prompt to send to the OpenAI API.
        response_format (BaseModel): The Pydantic model representing the expected response format.

    Returns:
        BaseModel: The parsed response from the OpenAI API.
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        response_format=response_format,
    )

    model_used = completion.model
    print(f"structured output prompt used model: {model}")
    message = completion.choices[0].message
    #print(message.parsed)

    if not message.parsed:
        raise ValueError(message.refusal)

    return message.parsed, model_used


def chat_prompt(prompt: str, model: str) -> str:
    """
    Run a chat model based on the specified model name.

    Args:
        prompt (str): The prompt to send to the OpenAI API.
        model (str): The model ID to use for the API call.

    Returns:
        str: The assistant's response.
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )

    model_used = completion.model
    print(f"chat prompt used model: {model}")
    message = completion.choices[0].message

    return message.content, model_used

def model_predictive_prompt(prompt: str) -> str:
    
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print(prompt)
    
    model_choices = """
        /// <summary>
        /// Represents a mapping of a common name that a user might call model to the actual model name.  For example ModelName.base_model would return 'gpt-4o-2024-08-06'"
        /// </summary>
            /// <summary>
            /// Represents the state of the art model.
            /// </summary>
            ModelName.state_of_the_art_model: 'o1-preview',
            /// <summary>
            /// Represents the reasoning model.
            /// </summary>
            ModelName.reasoning_model: 'o1-mini',
            /// <summary>
            /// Represents the Claude sonnet model.
            /// </summary>
            ModelName.sonnet_model: 'claude-3-5-sonnet-20240620',
            /// <summary>
            /// Represents the base model.
            /// </summary>
            ModelName.base_model: 'gpt-4o-2024-08-06',
            /// <summary>
            /// Represents the fast model.
            /// </summary>
            ModelName.fast_model: 'gpt-4o-mini',
            /// <summary>
            /// Represents the image model.
            /// </summary>
            ModelName.image_model: 'dall-e-3',
        """

    #prompt = "create a file called myfile.csv and populate it with 20 rows of random information about animals and use the base model"

    completion = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "user",
                "content": f"Choose the right model name based on the the following directive from the user {prompt}.  Respond only with the model name, and with no markdown formatting."
            },
            {
                "role": "user",
                "content": model_choices
            }
        ],
        prediction={
            "type": "content",
            "content": model_choices
        }
    )

    model_selected = completion.choices[0].message.content
    print(model_selected)
    return model_selected

def create_image_prompt(prompt: str, model: str) -> str:
    """
    Call an image generation model to generate an image.

    Args:
        prompt (str): The prompt to send to the Image generation model like Dall-e or Groq API.
        model (str): The model ID to use for the API call.

    Returns:
        str: The assistant's response.
    """

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.images.generate(
        model=model,
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    
    return image_url



def describe_image_prompt(prompt: str, image_url: str, model: str) -> str:
    """
    Call a model to describe an image.

    Args:
        prompt (str): The prompt to send to the Image generation model like Dall-e or Groq API.
        iimage_url (str): The url link to the image to be described.
        model (str): The model ID to use for the API call.

    Returns:
        str: The assistant's response.
    """

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
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

    print(response.choices[0].message.content)

    return response.choices[0].message.content

def parse_markdown_backticks(str) -> str:
    if "```" not in str:
        return str.strip()
    # Remove opening backticks and language identifier
    str = str.split("```", 1)[-1].split("\n", 1)[-1]
    # Remove closing backticks
    str = str.rsplit("```", 1)[0]
    # Remove any leading or trailing whitespace
    return str.strip()