from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from kapruka_client import (
    check_delivery,
    list_delivery_cities,
    list_kapruka_tools,
    search_products,
)
from shopping_agent import handle_chat

app = FastAPI(title="Kapruka Companion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ProductSearchRequest(BaseModel):
    query: str
    category: str | None = None
    limit: int = 8
    min_price: float | None = None
    max_price: float | None = None


class DeliveryCitiesRequest(BaseModel):
    query: str
    limit: int = 10


class DeliveryCheckRequest(BaseModel):
    city: str
    delivery_date: str | None = None
    product_id: str | None = None


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "kapruka-companion-api",
        "time": datetime.utcnow().isoformat(),
    }


@app.get("/api/kapruka/tools")
async def get_kapruka_tools():
    try:
        return {"tools": await list_kapruka_tools()}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/products/search")
async def api_search_products(request: ProductSearchRequest):
    try:
        return await search_products(
            query=request.query,
            category=request.category,
            limit=request.limit,
            min_price=request.min_price,
            max_price=request.max_price,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/delivery/cities")
async def api_delivery_cities(request: DeliveryCitiesRequest):
    try:
        return await list_delivery_cities(query=request.query, limit=request.limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/delivery/check")
async def api_delivery_check(request: DeliveryCheckRequest):
    try:
        return await check_delivery(
            city=request.city,
            delivery_date=request.delivery_date,
            product_id=request.product_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        response = await handle_chat(request.message)
        return {
            **response,
            "received": request.message,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
