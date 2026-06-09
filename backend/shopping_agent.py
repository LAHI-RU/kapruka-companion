import re
from datetime import datetime, timedelta, timezone
from typing import Any

from kapruka_client import check_delivery, list_delivery_cities, search_products


ASSISTANT_NAME = "Kavi"
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
        r"(?:rs\.?|lkr)\s*([0-9][0-9,\.]*)",
        r"(?:under|below|less than|max|maximum)\s*([0-9][0-9,\.]*)",
        r"([0-9][0-9,\.]*)\s*(?:rs\.?|lkr)",
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

    relationship_phrases = [
        "break up",
        "broke up",
        "leave my girl",
        "leave my girlfriend",
        "end relationship",
        "dump her",
    ]
    if any(phrase in lower_message for phrase in relationship_phrases):
        return "red roses flowers", "relationship_care"

    if any(word in lower_message for word in ["sorry", "apology", "forgive"]):
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


def _intent_label(intent: str) -> str:
    labels = {
        "relationship_care": "Close friend mode",
        "apology": "Apology gift plan",
        "everyday": "Everyday shopping",
        "gift": "Gift concierge",
        "general": "Smart shopping",
    }
    return labels.get(intent, "Smart shopping")


def _friend_note(intent: str) -> str:
    if intent == "relationship_care":
        return (
            "Kavi is not just trying to sell flowers. The better move is to cool down, "
            "talk properly, and use the gift only as a gentle opener."
        )

    if intent == "everyday":
        return "Kavi is optimizing for useful items, stock, and delivery instead of only gift-style recommendations."

    if intent in ["gift", "apology"]:
        return "Kavi is balancing emotional tone, price, and delivery practicality."

    return "Kavi is reading the situation first, then shopping."


def _next_actions(intent: str, city: str | None, delivery_date: str | None) -> list[str]:
    if intent == "relationship_care":
        return [
            "Do not rush the breakup decision",
            "Talk calmly before sending anything",
            "Pick simple flowers with a sincere note",
        ]

    if intent == "apology":
        return [
            "Choose one meaningful item",
            "Keep the message short and honest",
            "Check delivery timing before checkout",
        ]

    if intent == "everyday":
        return [
            "Build a multi-item cart",
            "Confirm delivery city",
            "Compare essentials by price and stock",
        ]

    actions = ["Compare the top picks", "Confirm budget", "Add delivery details"]
    if city:
        actions.append(f"Use {city} as delivery city")
    if delivery_date:
        actions.append(f"Target delivery date {delivery_date}")

    return actions[:3]


def _delivery_sentence(
    delivery: dict[str, Any] | None,
    city_text: str,
) -> str:
    if not delivery:
        return ""

    if delivery.get("available"):
        return (
            f" Delivery to {delivery.get('city', city_text)} is available on "
            f"{delivery.get('checked_date')} with a flat fee of Rs. {delivery.get('rate')}."
        )

    if delivery.get("next_available_date"):
        return (
            f" That date may not work for {delivery.get('city', city_text)}; "
            f"next available date is {delivery.get('next_available_date')}."
        )

    return ""


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
            "Give me a clearer item, city, or budget and I will refine it."
        )

    top = products[0]
    delivery_text = _delivery_sentence(delivery, city_text)

    if intent == "relationship_care":
        return (
            "Machan, do not do it right now. Do not decide to break up while emotions are high. "
            "Talk to her first, listen properly, and try to solve the real problem before doing anything final. "
            "If you still want to make a gentle move, keep it respectful: simple flowers, "
            "a short note, no drama. "
            f"I found {top['name']} at {top['price']} as a calm first option.{delivery_text}"
        )

    if intent == "apology":
        return (
            "Aiyo, that situation needs a careful touch. Keep it simple: fresh flowers, "
            "a short honest note, and no overdoing it. "
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

    safe_delivery = delivery if isinstance(delivery, dict) else None
    reply = _reply_for_intent(
        intent=intent,
        products=products,
        city=canonical_city,
        delivery=safe_delivery,
        budget=budget,
    )

    return {
        "assistant_name": ASSISTANT_NAME,
        "reply": reply,
        "products": products,
        "intent": intent,
        "intent_label": _intent_label(intent),
        "tone": "close friend",
        "friend_note": _friend_note(intent),
        "next_actions": _next_actions(intent, canonical_city, delivery_date),
        "search_query": query,
        "city": canonical_city,
        "delivery_date": delivery_date,
        "delivery": safe_delivery,
    }
