from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.websockets import WebSocket, WebSocketDisconnect
from manager import WebSocketManager
from db.main import init_db, close_db
from contextlib import asynccontextmanager
from auth.routes import auth_router
from users.routes import user_router
from mailserver.routes import mail_router
from middleware import custome_simple_middle
from errors import register_error_handlers



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()




app = FastAPI(lifespan=lifespan)

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Register middleware, error handlers, and routers
custome_simple_middle(app)
register_error_handlers(app)

manager = WebSocketManager()
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(mail_router, prefix="/mail", tags=["mail"])

@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse(
        'index.html',
        {"request": request}
    )

@app.get("/ws")
async def ws_get():
    return {"message": "This endpoint is for WebSockets. Please connect using a WebSocket client or visit the root URL '/' to use the chat UI."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            message = await websocket.receive_json()
            for client in manager.connected_clients:
                await manager.send_message(client, message)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        print(f"Error in websocket loop: {e}")
        await manager.disconnect(websocket)
