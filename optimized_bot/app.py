from sqlalchemy.future import select
from tools import *
from fastapi.responses import JSONResponse
from fastapi import FastAPI, BackgroundTasks, Depends
from typing import List
from models import Message_History
from typing import Annotated
from sqlalchemy.orm import Session


class Message(BaseModel):
    message: dict

    class Config:
        extra = Extra.allow


async def code_misha(input, chat_id, message_id, task):
    global que
    response = Ollama.invoke(input)
    await send_stream_data(chat_id, response, message_id + 1, task)
    # message_update(chat_id, "Here, what i've got: \n"+ response + " ", message_id + 1)
    que = que - 1
    return response


def say_misha(input, item_to_inject: InjectItem, audio, db, background_tasks):
    context = retrieve_query(item_to_inject.user_message)
    response = say(input, context)
    item_to_inject.bot_message = response
    item_to_inject.is_bot = True
    background_tasks.add_task(inject, item_to_inject, db)
    if "say" in item_to_inject.user_message or audio:
        audio_file = text_to_audio(response)
        send_audio_message(item_to_inject.chat_id, audio_file)
    else:
        send_message(item_to_inject.chat_id, response)


app = FastAPI()
models.Base.metadata.create_all(bind=sync_engine)

que = 0

## TELEGRAM BOT WITH FLASK
print("Bot started")

db_dependency = Annotated[Session, Depends(get_db)]


@app.post('/')
def index(item: Message, background_tasks: BackgroundTasks, db: db_dependency):
    audio = False
    try:
        if "voice" in item.message:
            audio = True
            chat_id, user_id, file_id, user_name, first_name, message_id = handle_voice_message(item.message)
            user_message = load_audio_to_text(file_id)
        else:
            chat_id, user_message, user_id, user_name, first_name, message_id = message_parser(item.message)
            print(chat_id, user_message, user_id, message_id, user_name, first_name, message_id)

        if not str(user_id) in Black_List:
            Black_List[str(user_id)] = 0

        item_to_inject = InjectItem(
            message_id=message_id,
            user_id=user_id,
            user_message=user_message,
            is_bot=False,
            chat_id=chat_id,
            username=user_name,
            user_first_name=first_name,
            bot_message=" "
        )
    except BaseException:

        return JSONResponse(content={"message": "Bad request"}, status_code=200)

    else:
        if misha_mentioned(user_message):
            small_dick_mentioned = is_small_dick(user_message),
            input = prepare_input(user_message, chat_id, user_id, first_name, small_dick_mentioned[0])
            say_misha(input, item_to_inject, audio, db, background_tasks)


        elif "/code" in user_message:
            global que
            send_message(chat_id, f" Loading ... Position in queue {que}")
            que = que + 1
            background_tasks.add_task(code_misha, user_message, chat_id, message_id, background_tasks)
            """response = send_message(chat_id, " ...")
                msg_id = response.json()["result"]["message_id"]
                send_stream_data(chat_id, user_message, msg_id)"""
        else:
            background_tasks.add_task(inject, item_to_inject, db)

    return JSONResponse(content={"message": "Done"}, status_code=200)


@app.post("/inject/")
def inject(item: InjectItem, db: db_dependency):
    db_item = models.Message_History(**item.dict())
    db.add(db_item)
    db.commit()


@app.get("/chat_history/", response_model=List[MessageHistoryResponse])
async def chat_history(db: AsyncSession = Depends(get_async_session)):
    query = select(Message_History).order_by(Message_History.message_id.desc()).limit(6)
    result = await db.execute(query)
    messages = result.scalars().all()
    return messages


class BotMessage(BaseModel):
    message: str
    chat_id: int


@app.post("/bot_message/")
def bot_message(item: BotMessage, db: db_dependency, background_tasks: BackgroundTasks):
    response = send_message(item.chat_id, item.message)
    message_id = response.json()["result"]["message_id"]

    item_to_inject = InjectItem(
        message_id=message_id,
        user_id=0000,
        user_message="secret_bot@",
        is_bot=True,
        chat_id=item.chat_id,
        username="BOT",
        user_first_name="Babayn",
        bot_message=item.message
    )
    background_tasks.add_task(inject, item_to_inject, db)
    return JSONResponse(content={"message": "Done"}, status_code=200)