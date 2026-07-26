"""
Finds "the right audience" inside a customer's loaded contacts.

A segment is stored as a small rule-set, e.g.:

{
  "match": "all",                # "all" = AND, "any" = OR
  "conditions": [
    {"field": "consent_status", "op": "eq", "value": "opted_in"},
    {"field": "engagement_score", "op": "gte", "value": 40},
    {"field": "industry", "op": "in", "value": ["SaaS", "Fintech"]},
    {"field": "country", "op": "eq", "value": "US"},
    {"field": "tags", "op": "contains", "value": "newsletter"}
  ]
}

Because it's stored as data (not hard-coded SQL), a segment stays live —
re-running it after a new upload automatically picks up new/updated contacts
that now match, without anyone having to rebuild the list by hand.
"""
from sqlalchemy import and_, or_, cast
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session

from .models import Contact

FILTERABLE_FIELDS = {
    "email", "company", "industry", "job_title", "country",
    "engagement_score", "last_purchase_date", "consent_status", "tags",
}

OPS = {"eq", "neq", "gte", "lte", "gt", "lt", "in", "contains"}


def _condition_to_filter(cond: dict):
    field = cond.get("field")
    op = cond.get("op")
    value = cond.get("value")

    if field not in FILTERABLE_FIELDS:
        raise ValueError(f"Unknown field: {field}")
    if op not in OPS:
        raise ValueError(f"Unknown operator: {op}")

    column = getattr(Contact, field)

    if op == "eq":
        return column == value
    if op == "neq":
        return column != value
    if op == "gte":
        return column >= value
    if op == "lte":
        return column <= value
    if op == "gt":
        return column > value
    if op == "lt":
        return column < value
    if op == "in":
        return column.in_(value)
    if op == "contains":  # for the `tags` array column
        return column.contains(cast([value], ARRAY(Contact.__table__.c.tags.type.item_type)))

    raise ValueError(f"Unhandled operator: {op}")


def build_query(db: Session, customer_id, rules: dict):
    query = db.query(Contact).filter(Contact.customer_id == customer_id)

    conditions = [_condition_to_filter(c) for c in rules.get("conditions", [])]
    if not conditions:
        return query

    combined = and_(*conditions) if rules.get("match", "all") == "all" else or_(*conditions)
    return query.filter(combined)


# A few starter templates customers can reach for immediately after their
# first upload, before they've learned the rule syntax.
STARTER_SEGMENTS = {
    "recently_engaged": {
        "name": "Engaged in the last 90 days, opted in",
        "rules": {
            "match": "all",
            "conditions": [
                {"field": "consent_status", "op": "eq", "value": "opted_in"},
                {"field": "engagement_score", "op": "gte", "value": 40},
            ],
        },
    },
    "high_value_prospects": {
        "name": "High engagement, no purchase yet",
        "rules": {
            "match": "all",
            "conditions": [
                {"field": "consent_status", "op": "eq", "value": "opted_in"},
                {"field": "engagement_score", "op": "gte", "value": 60},
            ],
        },
    },
    "win_back": {
        "name": "Opted in but gone quiet",
        "rules": {
            "match": "all",
            "conditions": [
                {"field": "consent_status", "op": "eq", "value": "opted_in"},
                {"field": "engagement_score", "op": "lte", "value": 15},
            ],
        },
    },
}
