from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.controllers.chat_controller import handle_chat_message
from app.schemas.routes import ChatRequest, ChatResponse

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat(request: ChatRequest) -> JSONResponse:
    response = handle_chat_message(request)
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(response))
