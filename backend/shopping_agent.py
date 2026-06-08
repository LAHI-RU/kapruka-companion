import re
from datetime import datetime, timedelta, timezone
from typing import Any

from kapruka_client import check_delivery, list_delivery_cities, search_products


LK_TZ = timezone(timedelta(hours=5, minutes=30))

CITY_KEYWORDS = [
    "colombo",
    "kandy",
    "galle",
    "negombo",
    "kurunegala",
    "jaffna",
    "matara",
    "gampaha",
    "ratnapura",
]


def _extract_budget(message: str) -> float | None:
    patterns = [
        r"(?:rs\.?|lkr|රු)\s*([0-9][0-9,\.]*)",
        r"(?:under|below|less than|max|maximum)\s*([0-9][0-9,\.]*)",
        r"([0-9][0-9,\.]*)\s*(?:rs\.?|lkr|රු)",
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))

    return None


def _extract_city(message: str) -> str | None:
    lower_message = message.lower()

    for city in CITY_KEYWORDS:
        if city in lower_message:
            return city

    return None


def _extract_delivery_date(message: str) -> str | None:
    lower_message = message.lower()
    today = datetime.now(LK_TZ).date()

    if "today" in lower_message or "ada" in lower_message:
        return today.isoformat()
    if "tomorrow" in lower_message or "heta" in lower_message:
        return (today + timedelta(days=1)).isoformat()

    return None


def _infer_search_query(message: str) -> tuple[str, str]:
    lower_message = message.lower()

    if any(word in lower_message for word in ["break", "broke up", "sorry", "apology"]):
        return "red roses flowers", "apology"
    if any(word in lower_message for word in ["flower", "flowers", "rose", "roses"]):
        return "roses flowers", "gift"
    if any(word in lower_message for word in ["grocery", "groceries", "food", "daily essentials"]):
        return "grocery essentials", "everyday"
    if any(word in lower_message for word in ["cake", "birthday"]):
        return "birthday cake", "gift"
    if any(word in lower_message for word in ["phone", "headphone", "electronic", "charger"]):
        return "electronics", "everyday"
    if any(word in lower_message for word in ["amma", "mother", "wife", "girlfriend", "gift"]):
        return "gift hamper", "gift"

    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", message).strip()
    return cleaned[:80] if len(cleaned) >= 3 else "gift hamper", "general"


def _format_price(price: dict[str, Any] | None) -> str:
    if not price or price.get("amount") is None:
        return "Price unavailable"

    amount = float(price["amount"])
    currency = price.get("currency", "LKR")

    if currency == "LKR":
        return f"Rs. {amount:,.0f}"

    return f"{currency} {amount:,.2f}"


def _normalise_products(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []

    products = []

    for item in payload.get("results", []):
        category = item.get("category") or {}
        products.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "category": category.get("name") or "Kapruka",
                "price": _format_price(item.get("price")),
                "image": item.get("image_url"),
                "note": item.get("summary") or "Available on Kapruka.",
                "url": item.get("url"),
                "in_stock": item.get("in_stock"),
                "stock_level": item.get("stock_level"),
            }
        )

    return products


def _reply_for_intent(
    intent: str,
    products: list[dict[str, Any]],
    city: str | None,
    delivery: dict[str, Any] | None,
    budget: float | None,
) -> str:
    city_text = city.title() if city else "the delivery city"
    budget_text = f" under Rs. {budget:,.0f}" if budget else ""

    if not products:
        return (
            f"I searched Kapruka but did not find a strong match{budget_text}. "
            "Try a more specific item name, budget, or category and I will refine it."
        )

    top = products[0]
    delivery_text = ""
    if delivery:
        if delivery.get("available"):
            delivery_text = (
                f" Delivery to {delivery.get('city', city_text)} is available on "
                f"{delivery.get('checked_date')} with a flat fee of Rs. {delivery.get('rate')}."
            )
        elif delivery.get("next_available_date"):
            delivery_text = (
                f" That date may not work for {delivery.get('city', city_text)}; "
                f"next available date is {delivery.get('next_available_date')}."
            )

    if intent == "apology":
        return (
            "Aiyo, that situation needs a careful touch. I would keep it simple: "
            "fresh red roses, a short honest note, and no overdoing it. "
            f"My first pick is {top['name']} at {top['price']}.{delivery_text}"
        )

    if intent == "everyday":
        return (
            "I found practical Kapruka options for your everyday shopping. "
            f"Start with {top['name']} at {top['price']}, then we can build a proper multi-item cart "
            f"for {city_text}.{delivery_text}"
        )

    if intent == "gift":
        return (
            "I found gift-ready options with good visual impact. "
            f"My first pick is {top['name']} at {top['price']}. "
            "We can add a message card once you choose the item."
            f"{delivery_text}"
        )

    return (
        "I found matching Kapruka products. "
        f"The strongest first option is {top['name']} at {top['price']}.{delivery_text}"
    )


async def handle_chat(message: str) -> dict[str, Any]:
    query, intent = _infer_search_query(message)
    budget = _extract_budget(message)
    city_query = _extract_city(message)
    delivery_date = _extract_delivery_date(message)

    search_payload = await search_products(
        query=query,
        limit=6,
        max_price=budget,
    )
    products = _normalise_products(search_payload)

    canonical_city = None
    delivery = None

    if city_query:
        cities_payload = await list_delivery_cities(city_query, limit=1)
        cities = cities_payload.get("cities", []) if isinstance(cities_payload, dict) else []
        if cities:
            canonical_city = cities[0]["name"]

    if canonical_city and delivery_date:
        delivery = await check_delivery(
            city=canonical_city,
            delivery_date=delivery_date,
            product_id=products[0]["id"] if products else None,
        )

    reply = _reply_for_intent(
        intent=intent,
        products=products,
        city=canonical_city,
        delivery=delivery if isinstance(delivery, dict) else None,
        budget=budget,
    )

    return {
        "reply": reply,
        "products": products,
        "intent": intent,
        "search_query": query,
        "city": canonical_city,
        "delivery_date": delivery_date,
        "delivery": delivery,
    }
