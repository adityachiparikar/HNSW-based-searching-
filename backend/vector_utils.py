import math
from typing import Any, Iterable, List


Vector = List[float]


def to_vector(values: Any) -> Vector:
    """Convert common vector-like objects into a plain Python list of floats."""
    if hasattr(values, "tolist"):
        values = values.tolist()
    return [float(value) for value in values]


def to_vector_batch(values: Any) -> List[Vector]:
    """Convert model output into a list of plain Python float vectors."""
    if hasattr(values, "tolist"):
        values = values.tolist()
    if not values:
        return []
    if isinstance(values[0], (int, float)):
        return [to_vector(values)]
    return [to_vector(row) for row in values]


def zero_vector(dimensions: int) -> Vector:
    return [0.0 for _ in range(dimensions)]


def dot(v1: Iterable[float], v2: Iterable[float]) -> float:
    total = 0.0
    for a, b in zip(v1, v2):
        total += float(a) * float(b)
    return total


def norm(vector: Iterable[float]) -> float:
    return math.sqrt(dot(vector, vector))


def normalize(vector: Any) -> Vector:
    values = to_vector(vector)
    length = norm(values)
    if length == 0.0:
        return values
    return [value / length for value in values]


def l2_distance(v1: Iterable[float], v2: Iterable[float]) -> float:
    total = 0.0
    for a, b in zip(v1, v2):
        diff = float(a) - float(b)
        total += diff * diff
    return math.sqrt(total)


def weighted_concat(v1: Iterable[float], weight1: float, v2: Iterable[float], weight2: float) -> Vector:
    combined = [float(value) * weight1 for value in v1]
    combined.extend(float(value) * weight2 for value in v2)
    return normalize(combined)
