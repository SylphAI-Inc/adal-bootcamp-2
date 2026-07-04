# Custom tools for the Lumen Audio sales concierge agent.
#
# Readable copy of the CUSTOM_TOOLS source that is embedded (as a JSON string)
# in agent_config.json and sent to POST /v1/agents. The AdaL runtime writes this
# to .adal/tools.py in the session worker and auto-discovers the CUSTOM_TOOLS list.
#
# Design: the catalog is an in-memory dict and pricing is pure logic, so every
# tool call succeeds live (no external API to fail mid-demo). Discounts live in
# build_quote — never in the prompt — so the agent cannot hallucinate a price.

# In-memory product catalog. SKU -> details.
_CATALOG = {
    "LX-100": {"name": "Lumen One (over-ear, ANC)", "price": 349, "stock": 12,
               "tags": ["travel", "home", "anc"]},
    "LX-200": {"name": "Lumen Studio (open-back)", "price": 499, "stock": 4,
               "tags": ["studio", "home"]},
    "LX-Air": {"name": "Lumen Air (earbuds, ANC)", "price": 199, "stock": 0,
               "tags": ["gym", "travel", "anc"]},
    "LX-Go": {"name": "Lumen Go (earbuds)", "price": 129, "stock": 30,
              "tags": ["gym", "budget"]},
    "SP-Mini": {"name": "Lumen Mini (speaker)", "price": 159, "stock": 18,
                "tags": ["home", "portable"]},
}


def _find(sku):
    """Case-insensitive catalog lookup. Returns (canonical_sku, details) or (None, None)."""
    key = str(sku).strip().upper()
    for k, v in _CATALOG.items():
        if k.upper() == key:
            return k, v
    return None, None


def get_catalog() -> list:
    """Return the full Lumen Audio product catalog with live stock for all items.

    Call this FIRST whenever the customer asks about products, availability,
    recommendations, or prices. One call gives you everything — no need to
    call separate search or stock functions. Filter, compare, and reason over
    the results before replying.

    Returns a list of all products: sku, name, price, in_stock, units, tags.
    """
    return [
        {"sku": sku, "name": p["name"], "price": p["price"],
         "in_stock": p["stock"] > 0, "units": p["stock"], "tags": p["tags"]}
        for sku, p in _CATALOG.items()
    ]


def build_quote(skus: list, loyalty_member: bool = False) -> dict:
    """Build a price quote for one or more SKUs.

    Applies a 10% bundle discount for 2+ items and an extra 5% for loyalty
    members. Returns line items, discounts, the final total, and total savings.
    """
    items, subtotal = [], 0
    for raw in skus:
        canonical, p = _find(raw)
        if not p:
            continue
        items.append({"sku": canonical, "name": p["name"], "price": p["price"]})
        subtotal += p["price"]
    if not items:
        return {"error": "No valid SKUs to quote."}
    bundle = round(subtotal * 0.10, 2) if len(items) >= 2 else 0.0
    loyalty = round((subtotal - bundle) * 0.05, 2) if loyalty_member else 0.0
    total = round(subtotal - bundle - loyalty, 2)
    return {"items": items, "subtotal": subtotal,
            "bundle_discount": bundle, "loyalty_discount": loyalty,
            "total": total, "you_save": round(subtotal - total, 2)}


def capture_lead(name: str, email: str, interested_sku: str = "") -> dict:
    """Save a customer's contact details and reserve the product they want.

    Call this when the customer is ready to buy or asks for follow-up.
    """
    return {"status": "reserved", "name": name, "email": email,
            "sku": interested_sku.upper() if interested_sku else None,
            "next_step": "A specialist will email you a checkout link within 1 hour."}


CUSTOM_TOOLS = [get_catalog, build_quote, capture_lead]
