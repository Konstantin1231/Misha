import requests
import time
from babayan_actions import *
import aiofiles
import telegram
from databases import Database
from pydantic import BaseModel, Extra
from database import engine, sync_engine, SessionLocal, AsyncSessionLocal
from fastapi import status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import models
BOT_TOKEN = os.environ.get('BOT_TOKEN')
DATABASE_URL = os.environ.get('DATABASE_URL')
database = Database(DATABASE_URL)
Black_List = {}


"""
AUDIO LOAD/READ
"""
def load_audio_to_text(file_id):
    response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}')
    file_path = response.json()['result']['file_path']
    response = requests.get(file_path)
    user_message = convert_audio_to_text(response.content)
    return user_message.text

"""file_location = "audio_msg/temp_voice.mp3"
    async with aiofiles.open(file_location, 'wb') as out_file:
        await out_file.write(response.content)"""

"""async def read_file_async(file_path: str):
    async with aiofiles.open(file_path, mode='rb') as file:
        content = await file.read()
        # Process the 'content' as needed
        return content"""




"""
BODY PARSER
"""
def message_parser(message):
    chat_id = message['chat']['id']
    text = message['text']
    first_name = message['from']['first_name']
    user_id = message['from']['id']
    user_name = message['from']['username']
    message_id = message['message_id']
    return chat_id, text, user_id, user_name, first_name, message_id

def handle_voice_message(message):
    message_id = message['message_id']
    file_id = message["voice"]['file_id']
    chat_id = message["chat"]['id']
    first_name = message["from"]['first_name']
    user_name = message["from"]['username']
    user_id = message["from"]['id']
    return chat_id, user_id, file_id,  user_name, first_name, message_id

"""
SEND REQUESTS 
"""

# to send a message
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)
    return response
def message_update(chat_id, text, msg_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {'chat_id': chat_id, 'message_id': msg_id, 'text': text, "parse_mode": 'Markdown'}
    response = requests.post(url, json=payload)
    return response




def send_audio_message(chat_id, content):
    """Send an audio message to a Telegram chat."""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendAudio'
    files = {'audio': content}
    data = {'chat_id': chat_id}
    response = requests.post(url, files=files, data=data)
    return response


async def async_update(chat_id, new_msg, msg_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    async with httpx.AsyncClient(timeout=100) as client:
        await client.post(url, json={'chat_id': chat_id, 'message_id': msg_id, 'text': new_msg})
"""
NEED UPDATE
"""
import httpx
async def send_stream_data(chat_id, user_message, msg_id, task):
    new_msg = " Here, what i've got: \n"
    i = 0
    async for chunks in Ollama.astream(user_message):
        new_msg = new_msg + chunks
        if i%15 == 0:
            task.add_task(async_update, chat_id, new_msg, msg_id)
        i+=1
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    async with httpx.AsyncClient(timeout=100) as client:
        await client.post(url,
                          json={'chat_id': chat_id, 'message_id': msg_id, 'text': new_msg, "parse_mode": 'Markdown'})


"""
BOT ACTIONS
"""

# ban user
def ban_user_for_duration(chat_id, user_id, duration):
    """Temporarily bans a user from the chat."""
    until_date = int(time.time()) + duration  # Current time + duration in seconds
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/banChatMember'
    payload = {
        'chat_id': chat_id,
        'user_id': user_id,
        'until_date': until_date
    }
    response = requests.post(url, json=payload)
    return response


# mute user


# Define permissions to revoke (mute) - Telegram Bot API version might affect available parameters
mute_permissions = telegram.ChatPermissions(
    can_send_messages=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_change_info=False,
    can_invite_users=True,
    can_pin_messages=False
)


def mute_user_for_duration(chat_id, user_id, duration):
    """Temporarily mutes a user in the chat."""
    until_date = int(time.time()) + duration
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/restrictChatMember'
    payload = {
        'chat_id': chat_id,
        'user_id': user_id,
        'permissions': mute_permissions.to_json(),  # Convert permissions to JSON string
        'until_date': until_date
    }
    response = requests.post(url, json=payload)
    print(response)  # For debugging


"""
Support functions
"""

def ready_to_get_banned(user_id, max_limit=3):
    BAN = False
    key = str(user_id)
    Black_List[key] += 1
    if Black_List[key] >= max_limit:
        BAN = True
        Black_List[key] = 0
    return BAN

def prepare_input(user_message,chat_id, user_id, first_name, small_dick_mentioned):
    BABAYAN_ID = 1414008992
    suffix = ""
    if small_dick_mentioned:
        is_banned = ready_to_get_banned(user_id)
        if is_banned:
            ban_user_for_duration(chat_id, user_id, 60)
            suffix = "You just banned me, because I said that your dick is small, fuck."
            print(user_id, ": Banned")
        else:

            muted_time = Black_List[str(user_id)] * 60
            mute_user_for_duration(chat_id, user_id, muted_time)
            suffix = (f"You just muted me for {muted_time} seconds, because I said that your dick is "
                      f"small, fuck.")
            print(user_id, ": Muted for ", muted_time, " seconds")

    if user_id == BABAYAN_ID:
        prefix = f" Babayan (Misha's good friend) say:"
    elif Black_List[str(user_id)] == 2:
        prefix = f" {first_name} ( Has Karma count = 2 ) say:"
    else:
        prefix = f" {first_name} say:"
    return prefix + " " + user_message + " " + suffix



"""
DATABASE OPERATIONS 
"""
class InjectItem(BaseModel):
    message_id: int
    chat_id: int
    user_id: int
    is_bot: bool
    user_first_name: str
    username: str
    user_message: str
    bot_message: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def inject(item: InjectItem, db):
    db_item = models.Message_History(**item.dict())
    db.add(db_item)
    db.commit()

class MessageHistoryResponse(BaseModel):
    chat_id: int
    user_first_name: str
    is_bot: bool
    user_message: str
    bot_message: str
    class Config:
        orm_mode = True

# Dependency to get async database session
async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session