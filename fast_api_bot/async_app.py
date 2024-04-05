import uvicorn
from tools import *
from fastapi.responses import JSONResponse
import httpx
from fastapi import FastAPI, Request, BackgroundTasks
from contextlib import asynccontextmanager


async def code_misha(input, chat_id, message_id, requests_client):
    global que
    await send_message(chat_id, f" Loading ... Position in queue {que}", requests_client)
    response = Ollama.invoke(input)
    await message_update(chat_id, response, message_id + 1, requests_client)
    que = que - 1
    return response


async def say_misha(input, context, user_message, chat_id, audio, requests_client):
    response = say(input, context)
    print(response)
    print(Black_List)
    if "say" in user_message or audio:
        audio_file_path = text_to_audio(response)
        await send_audio_message(chat_id, audio_file_path)
    else:
        await send_message(chat_id, response, requests_client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.requests_client = httpx.AsyncClient()
    yield
    await app.requests_client.aclose()


app = FastAPI(lifespan=lifespan)

que = 0

## TELEGRAM BOT WITH FLASK
print("Bot started")


@app.post('/')
async def index(request: Request, background_tasks: BackgroundTasks):
    requests_client = request.app.requests_client
    audio = False
    body = await request.json()
    print(body)
    try:
        if "voice" in body["message"]:
            audio = True
            chat_id, user_id, file_id, user_name, first_name = handle_voice_message(body["message"])
            user_message = await load_audio_to_text(file_id, requests_client)
        else:
            chat_id, user_message, user_id, message_id, user_name, first_name = message_parser(body["message"])
        if not str(user_id) in Black_List:
            Black_List[str(user_id)] = 0


    except BaseException:

        return JSONResponse(content={"message": "Bad request"}, status_code=200)

    else:
        if misha_mentioned(user_message):
            small_dick_mentioned, context = await asyncio.gather(is_small_dick(user_message),
                                                                 retrieve_query(user_message))
            input = prepare_input(user_message, chat_id, user_id, first_name, small_dick_mentioned, )
            background_tasks.add_task(say_misha, input, context, user_message, chat_id, audio, requests_client)

        elif "/code" in user_message:
            global que
            que = que + 1
            background_tasks.add_task(code_misha, user_message, chat_id, message_id, requests_client)
            """response = send_message(chat_id, " ...")
                msg_id = response.json()["result"]["message_id"]
                send_stream_data(chat_id, user_message, msg_id)"""

    return JSONResponse(content={"message": "Done"}, status_code=200)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
