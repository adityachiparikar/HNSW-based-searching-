import json
import csv
import io
from typing import Any, Dict, List, Tuple


PREFERRED_FIELD_ORDER = (
    "brand",
    "make",
    "manufacturer",
    "model",
    "engine",
    "engine_type",
    "engine type",
    "price",
    "msrp",
    "category",
    "body",
    "text",
)


def _decode_bytes(content: bytes) -> Tuple[str, str]:
    """
    Best-effort decode for user-uploaded files.

    Many CSVs exported from Excel/Windows are CP1252 (or Latin-1) rather than UTF-8.
    We try a small set of common encodings before giving up.
    """
    encodings_to_try = ("utf-8", "utf-8-sig", "cp1252", "latin-1")
    last_error: Exception | None = None
    for enc in encodings_to_try:
        try:
            return content.decode(enc), enc
        except UnicodeDecodeError as e:
            last_error = e

    # As a final fallback, replace invalid bytes so the user can still proceed.
    # This keeps the API resilient and avoids hard-failing on one bad character.
    return content.decode("utf-8", errors="replace"), "utf-8 (replacement)"

def _clean_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_row(row: Dict[str, Any]) -> Dict[str, str]:
    cleaned = {}
    for key, value in row.items():
        clean_key = _clean_value(key)
        clean_value = _clean_value(value)
        if clean_key and clean_value:
            cleaned[clean_key] = clean_value
    return cleaned


def _get_field(fields: Dict[str, str], names: Tuple[str, ...]) -> str:
    lookup = {key.casefold().strip(): value for key, value in fields.items()}
    for name in names:
        value = lookup.get(name)
        if value:
            return value
    return ""


def _display_text(fields: Dict[str, str]) -> str:
    brand = _get_field(fields, ("brand", "make", "manufacturer"))
    model = _get_field(fields, ("model", "car model", "vehicle model", "name"))
    engine = _get_field(fields, ("engine", "engine_type", "engine type", "motor"))
    text = _get_field(fields, ("text", "description", "summary"))

    if brand and model:
        return f"{brand} {model}"
    if model:
        return model
    if brand and engine:
        return f"{brand} {engine}"
    if brand:
        return brand
    if text:
        return text
    return " ".join(list(fields.values())[:2])


def _ordered_fields(fields: Dict[str, str]) -> List[Tuple[str, str]]:
    def sort_key(item: Tuple[str, str]) -> Tuple[int, str]:
        key = item[0].casefold().strip()
        try:
            return (PREFERRED_FIELD_ORDER.index(key), key)
        except ValueError:
            return (len(PREFERRED_FIELD_ORDER), key)

    return sorted(fields.items(), key=sort_key)


def build_search_document(item: Any) -> Dict[str, Any]:
    if isinstance(item, dict) and "searchable_text" in item and "fields" in item:
        fields = _clean_row(item.get("fields", {}))
        text = _clean_value(item.get("text")) or _display_text(fields)
        searchable_text = _clean_value(item.get("searchable_text"))
        if not searchable_text and fields:
            searchable_text = ". ".join(f"{key}: {value}" for key, value in _ordered_fields(fields))
        if not searchable_text:
            raise ValueError("Empty row")
        return {
            "text": text,
            "searchable_text": searchable_text,
            "fields": fields or {"text": text},
        }

    if isinstance(item, dict):
        fields = _clean_row(item)
    else:
        text = _clean_value(item)
        fields = {"text": text} if text else {}

    if not fields:
        raise ValueError("Empty row")

    brand = _get_field(fields, ("brand", "make", "manufacturer"))
    model = _get_field(fields, ("model", "car model", "vehicle model", "name"))
    engine = _get_field(fields, ("engine", "engine_type", "engine type", "motor"))
    price = _get_field(fields, ("price", "msrp", "cost"))

    natural_parts = []
    if brand or model or engine:
        subject = " ".join(part for part in (brand, model) if part)
        if subject and engine:
            natural_parts.append(f"{subject} uses a {engine} engine")
        elif subject:
            natural_parts.append(subject)
        elif engine:
            natural_parts.append(f"Vehicle with {engine} engine")
    if price:
        natural_parts.append(f"Price {price}")

    field_parts = [f"{key}: {value}" for key, value in _ordered_fields(fields)]
    searchable_text = ". ".join(natural_parts + field_parts)

    return {
        "text": _display_text(fields),
        "searchable_text": searchable_text,
        "fields": fields,
    }


def parse_upload_file(content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Parse uploaded content (JSON or CSV) into structured search documents."""
    try:
        decoded_content, _encoding_used = _decode_bytes(content)
        if filename.endswith(".json"):
            data = json.loads(decoded_content)
            if isinstance(data, list):
                docs = []
                for item in data:
                    try:
                        docs.append(build_search_document(item))
                    except ValueError:
                        continue
                return docs
            raise ValueError("Invalid JSON format. Expected a list.")
            
        elif filename.endswith(".csv"):
            docs = []
            reader = csv.DictReader(io.StringIO(decoded_content))
            for row in reader:
                try:
                    docs.append(build_search_document(row))
                except ValueError:
                    continue
            if not docs:
                raise ValueError("No valid rows found in CSV.")
            return docs
            
        else:
            raise ValueError(f"Unsupported file format: {filename}")
            
    except Exception as e:
        raise ValueError(f"Error parsing file: {str(e)}")

def get_sample_dataset() -> List[Dict[str, Any]]:
    """Returns a small structured sample dataset."""
    return [
        build_search_document({"brand": "Toyota", "model": "GR86", "engine": "BOXER-4", "category": "sports coupe"}),
        build_search_document({"brand": "Toyota", "model": "GR Supra", "engine": "I6", "category": "sports coupe"}),
        build_search_document({"brand": "Ferrari", "model": "Roma Spider", "engine": "V8", "category": "grand tourer"}),
        build_search_document({"brand": "Ford", "model": "Mustang GT", "engine": "V8", "category": "muscle car"}),
        build_search_document({"brand": "BMW", "model": "M3", "engine": "I6", "category": "sports sedan"}),
        build_search_document({"brand": "Porsche", "model": "911 Carrera", "engine": "BOXER-6", "category": "sports car"}),
    ]
