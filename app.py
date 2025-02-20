import asyncio
from openai import AsyncOpenAI
from uuid import uuid4
import warnings

import chainlit as cl
from chainlit.logger import logger


from realtime import RealtimeClient
from utils.utils import voice, upload_file_to_images_container, realtime_prompt
from tools.general_tools import GetCurrentTimeTool
from tools.general_tools import GetRandomNumberTool
from tools.general_tools import BingSearchTool
from tools.file_tools import CreateFileTool, DeleteFileTool, IngestFileTool, UpdateFileTool
from tools.image_tools import GenerateImageTool, DescribeImageTool, ProcessScreenshotsTool
from tools.memory_tools import AddToMemoryTool, IngestMemoryTool, ResetActiveMemoryTool
from tools.clipboard_tools import ClipboardToMemoryTool, ClipboardToFileTool

warnings.filterwarnings("ignore", category=DeprecationWarning)

client = AsyncOpenAI()  

tools = [
    CreateFileTool().get_tool(),  # returns the def and handle
    UpdateFileTool().get_tool(),  # returns the def and handle
    DeleteFileTool().get_tool(), # returns the def and handle
    GenerateImageTool().get_tool(), # returns the def and handle
    GetCurrentTimeTool().get_tool(), # returns the def and handle
    GetRandomNumberTool().get_tool(), # returns the def and handle
    BingSearchTool().get_tool(), # returns the def and handle
    DescribeImageTool().get_tool(), # returns the def and handle
    AddToMemoryTool().get_tool(), # returns the def and handle
    IngestMemoryTool().get_tool(), # returns the def and handle
    ResetActiveMemoryTool().get_tool(), # returns the def and handle
    ClipboardToMemoryTool().get_tool(), # returns the def and handle
    ClipboardToFileTool().get_tool(), # returns the def and handle
    ProcessScreenshotsTool().get_tool(), # returns the def and handle
    IngestFileTool().get_tool() # returns the def and handle
]  

async def setup_openai_realtime():
    """Instantiate and configure the OpenAI Realtime Client"""
    openai_realtime = RealtimeClient()
    await openai_realtime.update_session(instructions=realtime_prompt, voice=voice) # set the instructions
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
                transcript = delta['transcript']
                pass
            if 'arguments' in delta:
                arguments = delta['arguments']  # string, function arguments added
                pass
            
    async def handle_item_completed(event):
        """Used to populate the chat context with transcription once an item is completed."""    
        item = event.get("item")

        # Check if item exists and has the required keys
        if item and item.get("type") == "message" and item.get("status") and item.get("role") == "assistant":
            content = item.get("content")
            if content:
                # Assuming content is a list of dictionaries, extract the first transcript
                #print(f"{item.get('type')} : {item.get('role')} : {content[0].get('transcript', 'Transcript not found')}")
                await cl.Message(
                    content=content[0].get('transcript', 'Transcript not found')
                ).send()

        pass
    
    async def handle_conversation_input_completed(event):
        """Used to populate the chat context with transcription once an item is completed.""" 
        #print(event)
        if event and event.get("type") == "conversation.item.input_audio_transcription.completed":
            transcript = event.get("transcript")   
            if transcript:   
                print(transcript.replace("\r", "").replace("\n", ""))

        pass

    async def handle_function_call_arguments_done(event):
        """Used to populate the chat context with transcription once an item is completed.""" 
        #print(event)
        pass
    
    async def handle_conversation_interrupt(event):
        """Used to cancel the client previous audio playback."""
        cl.user_session.set("track_id", str(uuid4()))
        await cl.context.emitter.send_audio_interrupt()
        
    async def handle_error(event):
        logger.error(event)
        
    openai_realtime.on('conversation.updated', handle_conversation_updated)
    openai_realtime.on('conversation.item.completed', handle_item_completed)
    openai_realtime.on('conversation.interrupted', handle_conversation_interrupt)
    openai_realtime.on('conversation.item.input_audio_transcription.completed', handle_conversation_input_completed) # get the transcribed text that the user voiced
    openai_realtime.on('response.function_call_arguments.done', handle_function_call_arguments_done) # get the transcribed text that the user voiced
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
        if not message.elements:  # this means there was not an attachment
            await openai_realtime.send_user_message_content([{ "type": 'input_text', "text": message.content}])
        else:
            # create an image url from the uploaded image
            # Processing images exclusively
            #print(f"message.elememnts:  {message.elements}")  # will be the actual name of the file

            files = []
            for file in message.elements:
                if "image" in file.mime:
                    # Append the file object to a list if needed
                    files.append(file)
                elif "pdf" in file.mime:
                    print("pdf")

            if files:
                # Read the first image only so index [0]
                with open(files[0].path, "rb") as f:
                    url = upload_file_to_images_container(files[0].name, f)
                    # Do something with the file name
                    print("File url:", url)

            await openai_realtime.send_user_message_content([{ "type": 'input_text', "text": f"{message.content}: image: {url}" }])
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