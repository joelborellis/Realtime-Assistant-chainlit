# POC Realtime API Assistant (with Function Agents)

**Tags**: [multimodal, audio, Realtime API]

## Table of Contents
1. [Introduction](#introduction)  
2. [Key Features](#key-features)  
3. [Tools](#tools)  
4. [Other Concepts](#other-concepts)  
5. [Setup](#setup)  
6. [References & Inspiration](#references--inspiration)

---

## Introduction

This project is a proof-of-concept (POC) Realtime API assistant, inspired by the work of:

- **[IndyDevDan](https://github.com/disler)**: Conceptualized the idea of an assistant that can perform user tasks via the Realtime API.
- **[Jesus Copado](https://github.com/jesuscopado)**: Enhanced IndyDevDan’s work by adding a visual component to display task output using **Chainlit**.

This POC demonstrates how an assistant can execute various tasks on the user's behalf, while providing multimodal experiences (e.g., text + speech) and integration with **Chainlit** for UI interactions.

---

## Key Features

- **Realtime Python Client**  
  Based on [openai-realtime-api-beta](https://github.com/openai/openai-realtime-api-beta).  

- **Multimodal Experience**  
  Speak and write to the assistant simultaneously. (Image uploads are an interesting new feature!)

- **Tool Calling**  
  Ask the assistant to perform tasks and see their output in the UI using Chainlit.

- **Visual Cues**  
  Visual indicators showing when the assistant is listening or speaking (part of the Chainlit integration).

---

## Tools

The assistant offers a collection of tools (implemented as function calls). Each tool performs a specific task and returns the result in the UI.

1. **create_file**  
   - **What it does**: Creates a file in the `scratchpad` directory.  
   - **Example usage**:  
     ```plaintext
     Hey Ada, create me a file named "myfile.csv".
     ```
   - Files appear in the UI, available for download.

2. **update_file**  
   - **What it does**: Updates the content of an existing file.  
   - **Example usage**:  
     ```plaintext
     Hey Ada, add twenty rows of random data about animals to "myfile.csv".
     ```
   - You can remove lines as well:
     ```plaintext
     Hey Ada, remove the row about alligators from "myfile.csv".
     ```

3. **delete_file**  
   - **What it does**: Deletes a file.  
   - **Example usage**:  
     ```plaintext
     Hey Ada, delete the file "myfile.csv".
     ```
   - The assistant might ask for confirmation before deleting. Use the phrase `"force delete"` to confirm.

4. **generate_image**  
   - **What it does**: Creates images using a simple system prompt with an image model (currently DALL·E 3).  
   - **Example usage**:  
     ```plaintext
     Hey Ada, generate an image of a futuristic city skyline at sunset.
     ```

5. **get_current_time**  
   - **What it does**: Returns the current date and time.  
   - **Example usage**:  
     ```plaintext
     Hey Ada, what time is it right now?
     ```

6. **generate_random_number**  
   - **What it does**: Returns a random number.  
   - **Example usage**:  
     ```plaintext
     Hey Ada, pick a number between 1 and 100.
     ```

7. **bing_search**  
   - **What it does**: Performs a simple internet search.  
   - **Example usage**:  
     ```plaintext
     Hey Ada, who won the 2024 baseball World Series?
     ```

---

## Other Concepts

### Predictive Prompts
Use a quick LLM call to decide on a predictive value. In this project, you can specify which model (fast vs. state-of-the-art) to use for a given task.

### Basic Configurations
A JSON file allows you to customize:
- The assistant’s name
- What you want the assistant to call you

### Basic Logging
A decorator function logs the execution time of each tool/agent to `runtime_time_table.json`. This can be expanded to track additional metrics, like function call costs.

### Memory
- You can instruct the assistant to **save** certain information to “memory” (stored in `active_memory.json`).
- You can **retrieve** memory at any time.
- You can **reset** memory to erase all stored data.
- Future improvements will include storing memory in databases (e.g., Cosmos DB).

---

## Setup

1. **Install `uv`**  
   - [uv Documentation](https://docs.astral.sh/uv/)  
   - A hyper-modern Python package manager.  
   - Alternatively, run:
     ```bash
     pip install uv
     ```
   - Allow `uv` to create and manage a virtual environment.

2. **Set Up Your Environment**  
   - Copy the sample file and rename it:
     ```bash
     cp .env.sample .env
     ```
   - All the settings in `.env.sample` are required for the Assistant to function properly.

3. **Update Your Personalization**  
   - Edit `personalization.json` to configure the Assistant according to your preferences.

4. **Install Dependencies**  
   - Sync and install all required packages:
     ```bash
     uv sync
     ```

5. **Run the Assistant**  
   - Launch the Realtime Assistant using Chainlit:
     ```bash
     chainlit run app.py
     ```

## References & Inspiration

- [IndyDevDan’s Realtime API Work](https://github.com/disler)  
- [Jesus Copado’s Enhancements](https://github.com/jesuscopado)  
- [OpenAI Realtime API Beta](https://github.com/openai/openai-realtime-api-beta)

---

Happy building! If you encounter any issues, please submit an issue or open a pull request.  
Enjoy exploring how an AI assistant can help you with real-time tasks!