import os
import pickle
from typing import Any, Callable

from unstructured.documents.elements import Element, Title


def check_is_answer_to_inquiry(element: Element) -> bool:
    return isinstance(element, Title) and element.text.upper().startswith("JAWAPAN")


def check_is_oral_inquiry_heading(element: Element) -> bool:
    return isinstance(element, Title) and element.text.upper().startswith(
        "PERTANYAAN-PERTANYAAN MULUT DARIPADA"
    )


def check_is_written_inquiry_heading(element: Element) -> bool:
    return isinstance(element, Title) and element.text.upper().startswith(
        "PERTANYAAN-PERTANYAAN BERTULIS DARIPADA"
    )


def last_item_replace(current: list[Any], func: Callable[[Any], Any]) -> list[Any]:
    return [*current[:-1], func(current[-1])]


def unpickler(file_item: os.DirEntry[str]) -> tuple[os.DirEntry, list[Element]]:
    with open(file_item, "rb") as file_content:
        return (file_item, pickle.load(file_content))