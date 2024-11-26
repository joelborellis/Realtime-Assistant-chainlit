import asyncio
from openai import AsyncOpenAI
import json

import chainlit as cl
from uuid import uuid4
from chainlit.logger import logger

from realtime import RealtimeClient
from utils.utils import SESSION_INSTRUCTIONS, voice
from tools.general_tools import GetCurrentTimeTool
from tools.general_tools import GetRandomNumberTool
from tools.general_tools import BingSearchTool
from tools.file_tools import CreateFileTool
from tools.file_tools import DeleteFileTool
from tools.file_tools import UpdateFileTool
from tools.image_tools import GenerateImageTool

client = AsyncOpenAI()  

tools = [
    CreateFileTool().get_tool(),  # returns the def and handle
    UpdateFileTool().get_tool(),  # returns the def and handle
    DeleteFileTool().get_tool(), # returns the def and handle
    GenerateImageTool().get_tool(), # returns the def and handle
    GetCurrentTimeTool().get_tool(), # returns the def and handle
    GetRandomNumberTool().get_tool(), # returns the def and handle
    BingSearchTool().get_tool(), # returns the def and handle
]  

async def setup_openai_realtime():
    """Instantiate and configure the OpenAI Realtime Client"""
    openai_realtime = RealtimeClient()
    await openai_realtime.update_session(instructions=SESSION_INSTRUCTIONS, voice=voice) # set the instructions
    cl.user_session.set("track_id", str(uuid4()))
    async def handle_conversation_updated(event):
        item = event.get("item")
        delta = event.get("delta")
        """Currently used to stream audio back to the client."""
        if delta:
            # Only one of the following will be populated for any given event
            if 'audio' in delta:
                audio = delta['audio']  # Int16Array, audio added
                await cl.context.emitter.send_audio_chunk(cl.OutputAudioChunk(mimeType="pcm16", data=audio, track=cl.user_session.get("track_id")))
            if 'transcript' in delta:
                transcript = ' '.join(delta['transcript'].split())
                cl.user_session.set(f"current_{item['role']}_transcript", transcript) # set the session with user AND assistant transcript
                print(f"User: {cl.user_session.get("current_user_transcript")}")
                print(f"Assistant: {cl.user_session.get("current_assistant_transcript")}")
                pass
            if 'arguments' in delta:
                arguments = delta['arguments']  # string, function arguments added
                pass
            
    async def handle_item_completed(event):
        """Used to populate the chat context with transcription once an item is completed."""        
        #print(event.get("type"))
        # Check if the role is "user"
        #if event.get("item", {}).get("role") == "user":
        #    # Extract the text
        #    content = event.get("item", {}).get("content", [])
        #    if content:  # Ensure the content list is not empty
        #        print(content)
        #        text = content[0].get("text")
        #        print(f"Extracted text: {text}")
        #    else:
        #        print("No content found.")
        #else:
        #   print("Role is not 'user'.")
        #pass
    
    async def handle_conversation_interrupt(event):
        """Used to cancel the client previous audio playback."""
        cl.user_session.set("track_id", str(uuid4()))
        await cl.context.emitter.send_audio_interrupt()
        
    async def handle_error(event):
        logger.error(event)
        
    openai_realtime.on('conversation.updated', handle_conversation_updated)
    openai_realtime.on('conversation.item.completed', handle_item_completed)
    openai_realtime.on('conversation.interrupted', handle_conversation_interrupt)
    openai_realtime.on('error', handle_error)

    coros = [openai_realtime.add_tool(tool_def, tool_handler) for tool_def, tool_handler in tools]
    await asyncio.gather(*coros)

    cl.user_session.set("openai_realtime", openai_realtime)

@cl.on_chat_start
async def start():
    await cl.Message(
        content="Welcome to a fun POC using Realtime API. Press `P` to talk!"
    ).send()
    await setup_openai_realtime()

@cl.on_message
async def on_message(message: cl.Message):
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        # TODO: Try image processing with message.elements
        await openai_realtime.send_user_message_content([{ "type": 'input_text', "text": message.content }])
    else:
        await cl.Message(content="Please activate voice mode before sending messages!").send()

@cl.on_audio_start
async def on_audio_start():
    try:
        openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
        #print(SESSION_INSTRUCTIONS)
        #await openai_realtime.update_session(instructions=SESSION_INSTRUCTIONS, voice=voice)  # this will update the session instructions and voice
        await openai_realtime.connect()
        logger.info(f"Connected to OpenAI realtime track_id: {cl.user_session.get("track_id")}")
        # TODO: might want to recreate items to restore context
        # openai_realtime.create_conversation_item(item)
        return True
    except Exception as e:
        await cl.ErrorMessage(content=f"Failed to connect to OpenAI realtime: {e}").send()
        return False

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")            
    if openai_realtime.is_connected():
        await openai_realtime.append_input_audio(chunk.data)
    else:
        logger.info("RealtimeClient is not connected")

@cl.on_audio_end
@cl.on_chat_end
@cl.on_stop
async def on_end():
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        await openai_realtime.disconnect()