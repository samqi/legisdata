import os
import pickle

from unstructured.documents.elements import Element, Title


def check_is_oral_inquiry_answer(element: Element) -> bool:
    return isinstance(element, Title) and element.text.upper().startswith("JAWAPAN")


def check_is_oral_inquiry_heading(element: Element) -> bool:
    return isinstance(element, Title) and element.text.upper().startswith(
        "PERTANYAAN-PERTANYAAN MULUT DARIPADA"
    )


def unpickler(file_item: os.DirEntry[str]) -> tuple[os.DirEntry, list[Element]]:
    with open(file_item, "rb") as file_content:
        return (file_item, pickle.load(file_content))