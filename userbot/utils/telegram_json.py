__all__ = [
    "json_value_to_python",
]

from typing import overload

from pyrogram.raw.base import JSONValue
from pyrogram.raw.types import JsonArray, JsonBool, JsonNull, JsonNumber, JsonObject, JsonString

PrimitiveT = bool | float | str | None
PythonValueT = PrimitiveT | list[PrimitiveT] | dict[str, PrimitiveT]


@overload
def json_value_to_python(value: JsonNull) -> None:
    pass


@overload
def json_value_to_python(value: JsonBool) -> bool:
    pass


@overload
def json_value_to_python(value: JsonNumber) -> float:
    pass


@overload
def json_value_to_python(value: JsonString) -> str:
    pass


@overload
def json_value_to_python(value: JsonArray) -> list[PrimitiveT]:
    pass


@overload
def json_value_to_python(value: JsonObject) -> dict[str, PrimitiveT]:
    pass


def json_value_to_python(json_value: JSONValue) -> PythonValueT:
    if isinstance(json_value, JsonNull):
        return None
    if isinstance(json_value, JsonBool):
        return bool(json_value.value)
    if isinstance(json_value, JsonNumber):
        return float(json_value.value)
    if isinstance(json_value, JsonString):
        return str(json_value.value)
    if isinstance(json_value, JsonArray):
        return [json_value_to_python(x) for x in json_value.value]
    if isinstance(json_value, JsonObject):
        return {x.key: json_value_to_python(x.value) for x in json_value.value}
    raise AssertionError(f"Unknown JSON type: {type(json_value)}")  # shouldn't happen
