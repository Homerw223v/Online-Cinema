import aio_pika
from models import ProcessingMessage, User, Pattern, WorkerType
from config import settings
from services.auth import AuthService, get_auth_service
import services.auth # noqa!
import services.broker # noqa!
import services.mongo_db # noqa!
from services.mongo_db import MongoMessageStorage, get_message_db
from services.broker import get_broker_chanel
from operator import attrgetter
from utils import WebsocketMessage


from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect
from contextlib import asynccontextmanager
from uuid import UUID


connected_clients = {}


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    auth_service = AuthService(
        username=settings.auth.username,
        password=settings.auth.password,
        login_url=settings.auth.login_url,
        refresh_url=settings.auth.refresh_url,
    )
    auth_service.connections()
    services.auth.auth_service = auth_service
    message_db = MongoMessageStorage(str(settings.mongo_db.dsn), settings.mongo_db.db_name)
    await message_db.init_model()
    services.mongo_db.message_db = message_db
    broker_connection = await aio_pika.connect_robust(str(settings.broker.dsn))
    channel: aio_pika.abc.AbstractRobustChannel = await broker_connection.channel()
    await channel.set_qos(prefetch_count=1000)
    services.broker.broker_chanel = channel
    yield
    await broker_connection.close()
    await auth_service.close()


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws/{user_id}")
async def websocket_endpoint( # noqa!
    websocket: WebSocket,
    user_id: UUID,
    auth_service: AuthService = Depends(get_auth_service),
    message_db: MongoMessageStorage = Depends(get_message_db),
    channel: aio_pika.abc.AbstractChannel = Depends(get_broker_chanel),
):
    await websocket.accept()
    await websocket.send_text("Test message")
    connected_clients.setdefault(user_id, set()).add(websocket)
    queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(
        settings.broker.websocket_worker_queue_name, auto_delete=True,
    )
    await queue.bind(exchange=settings.broker.worker_exchange_name, routing_key=f"{WorkerType.web_socket}.{user_id}")
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                for websocket_client in connected_clients[user_id]:
                    try: # noqa!
                        broker_msg = ProcessingMessage.model_validate_json(message.body.decode())
                        auth_service.request_id = broker_msg.request_id
                        user_info_url = f'{settings.url.user_info_url}{broker_msg.user_id}'
                        user = await auth_service.get_query(user_info_url, User)
                        if user.notice_websocket:
                            pattern_info_url = f"{settings.template.url}{broker_msg.pattern_id}"
                            pattern = await auth_service.get_query(pattern_info_url, Pattern)
                            if pattern.aggregate:
                                msg_list = await message_db.get_messages(broker_msg.user_id, broker_msg.pattern_id)
                                data = {"messages": [msg.data for msg in msg_list]}
                            else:
                                msg = await message_db.get_by_id(broker_msg.msg_id)
                                msg_list = [msg]
                                data = msg.data
                            websocket_msg = WebsocketMessage(user, pattern, data)
                            await websocket_client.send_text(websocket_msg.text)
                            await message_db.set_state_sent(list(map(attrgetter("id"), msg_list)))
                    except WebSocketDisconnect:
                        connected_clients[user_id].remove(websocket)
                        if not connected_clients[user_id]:
                            return


from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def chat_interface(request: Request):
    return templates.TemplateResponse("ws.html", {"request": request})
