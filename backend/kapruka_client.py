import json
import os
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


KAPRUKA_MCP_URL = os.getenv("KAPRUKA_MCP_URL", "https://mcp.kapruka.com/mcp")


def _extract_tool_payload(result: Any) -> Any:
    text_parts: list[str] = []

    for item in result.content:
        text = getattr(item, "text", None)
        if text:
            text_parts.append(text)

    raw_text = "\n".join(text_parts).strip()

    if not raw_text:
        return None

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {"raw": raw_text}


async def call_kapruka_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
    async with streamablehttp_client(KAPRUKA_MCP_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, {"params": arguments or {}})
            return _extract_tool_payload(result)


async def list_kapruka_tools() -> list[dict[str, Any]]:
    async with streamablehttp_client(KAPRUKA_MCP_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()

            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in result.tools
            ]


async def search_products(
    query: str,
    category: str | None = None,
    limit: int = 8,
    min_price: float | None = None,
    max_price: float | None = None,
) -> Any:
    arguments: dict[str, Any] = {
        "q": query,
        "limit": limit,
        "currency": "LKR",
        "in_stock_only": True,
        "response_format": "json",
    }

    if category:
        arguments["category"] = category
    if min_price is not None:
        arguments["min_price"] = min_price
    if max_price is not None:
        arguments["max_price"] = max_price

    return await call_kapruka_tool("kapruka_search_products", arguments)


async def list_delivery_cities(query: str, limit: int = 10) -> Any:
    return await call_kapruka_tool(
        "kapruka_list_delivery_cities",
        {
            "query": query,
            "limit": limit,
            "response_format": "json",
        },
    )


async def check_delivery(
    city: str,
    delivery_date: str | None = None,
    product_id: str | None = None,
) -> Any:
    arguments: dict[str, Any] = {
        "city": city,
        "response_format": "json",
    }

    if delivery_date:
        arguments["delivery_date"] = delivery_date
    if product_id:
        arguments["product_id"] = product_id

    return await call_kapruka_tool("kapruka_check_delivery", arguments)
