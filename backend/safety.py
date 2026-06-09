import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyResult:
    level: str
    intent: str
    reply: str
    friend_note: str
    next_actions: list[str]
    resources: list[dict[str, str]]
    suppress_products: bool


SELF_HARM_PATTERNS = [
    r"\bsuicide\b",
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\btake my life\b",
    r"\bi want to die\b",
    r"\bi do not want to live\b",
    r"\bdon't want to live\b",
    r"\bharm myself\b",
    r"\bself[- ]?harm\b",
]


def _contains_any(patterns: list[str], message: str) -> bool:
    return any(re.search(pattern, message, re.IGNORECASE) for pattern in patterns)


def assess_safety(message: str) -> SafetyResult | None:
    if _contains_any(SELF_HARM_PATTERNS, message):
        return SafetyResult(
            level="crisis",
            intent="self_harm",
            reply=(
                "I am really sorry you are feeling this way. I cannot help with anything that "
                "would hurt you, and I am not going to search products for this. Please pause "
                "for the next few minutes and move away from anything you could use to harm "
                "yourself. Call 1926 now, or call 1990 if there is immediate danger. If you can, "
                "message or call one trusted person nearby and say: 'I am not safe alone right now. "
                "Please stay with me.'"
            ),
            friend_note=(
                "Kavi has switched to care mode. Shopping is paused because this message may involve immediate self-harm risk."
            ),
            next_actions=[
                "Call 1926 National Mental Health Helpline now",
                "Call 1990 ambulance if there is immediate danger",
                "Move away from harmful objects and stay near another person",
            ],
            resources=[
                {
                    "name": "1926 National Mental Health Helpline",
                    "detail": "Free confidential support in Sri Lanka, available 24/7 by phone.",
                    "contact": "Call 1926",
                },
                {
                    "name": "1990 Suwa Seriya",
                    "detail": "Free emergency ambulance service in Sri Lanka.",
                    "contact": "Call 1990",
                },
                {
                    "name": "Trusted person nearby",
                    "detail": "A friend, family member, neighbor, security officer, or colleague who can stay with you.",
                    "contact": "Ask them to come to you now",
                },
            ],
            suppress_products=True,
        )

    return None
