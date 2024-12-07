Title: POC Realtime API assistant (with function Agents)
Tags: [multimodal, audio]

# POC Realtime API assistant

This repo is inspired by two repos.  First the amazing work by IndyDevDan (https://github.com/disler). He inspired the idea of creating an assistant that is able to perform tasks on the users behalf using the Realtime API.  This project was also inspred by Jesus Copado (https://github.com/jesuscopado) who expanded on IndyDevDans work and added a visual component in order to be able to see output from certain tasks.

## Key Features

- **Realtime Python Client**: Based off https://github.com/openai/openai-realtime-api-beta
- **Multimodal experience**: Speak and write to the assistant at the same time (image uploads an interesting new feature)
- **Tool calling**: Ask the assistant to perform tasks and see their output in the UI uisng Chainlit
- **Visual Cues**: Visual cues indicating if the assistant is listening or speaking (part of Chainlit)

## Tools

The Assistant has a tools that are implemented as functions and they can perform the following tasks:

- **create_file**: This tool/agent creates a file. For example say "Hey Ada, create me a file named myfil.csv".  Files will be created in the scratchpad directory and they will be displayed in the UI and availavle for download from the UI.
- **update_file**:  This tool/agent updates the content of a file.  For example say 'Hey Ada, add twenty rows of random data to myfile.csv about animals".  You can also perform tasks like deleting certain information from the file.  Say "Hey Ada, remove the row about alligators from myfile.csv"
- **delete_file**: Delete a file.  This tool/agent not just delees a file but showcases how you can send back a clarification to the user confirming the operation.  So for example say "Hey Ada, delete the file myfile.csv".  Ada might ask you to confirm the delete by using the phrase "force delete".  
- **generate_image**:  Generate and image.  This tool/agent creates images using a very simple system prompt using an image model (currently Dall-e-3)
- **get_current_time**:  Simple tool/agent just to test that function calls are working.  Repeats the current date and time.
- **generate_random_number**:  Simple tool/agent to test that funtions calls are working.  Generates a random number.
- **bing_search**:  Simple tool/agent to search the internet.  Try asking current questions like "Who won the 2024 baseball World Series?

## Other concepts this project will hightlight

- **Predictive Prompts**:  This is a way to use a quick call to the LLM to return a predictive value.  In this project there is  concept of which model to use to perform a task.  For example use the "fast model" or the "state of the art model".  The idea is the user can tell Ada which model to use for a certain task and she will use the model corresponding to users request.

- **Basic Configurations**:  Thru a json file you can customize things like the name of the assistant and what you want it to call you.

- **Basic Logging**:  There is a decorator function that does basic logging to keep track of the time it took for the tool/agent to execute eack tool/agent.  This could be greatly improved to also maybe capture costs related to function calls etc.

## Setup

- **Install uv**:  Install uv (https://docs.astral.sh/uv/), the hyper modern Python package manager.  Or, pip install uv (allow uv to create an environment)
- **Setup your environment**:  Setup environment cp .env.sample .env add your OPENAI_API_KEY.
- **Update your personalization**:  Update personalization.json to fit your setup
- **Install dependencies**:  Install dependencies uv sync
- **Run the Assistant**:  Run the realtime assistant using chainlit by running chainlit run app.py