from datetime import datetime
from typing import NamedTuple


class Person(NamedTuple):
    name: str
    raw: str | None = None
    title: list[str] = []
    area: str | None = None
    role: str | None = None


class ContentElement(NamedTuple):
    type: str
    value: str
    image: None | str


class Meta(NamedTuple):
    source: str
    year: int
    session: int
    dun: str
    parse_time: str = str(datetime.now())


class Inquiry(NamedTuple):
    meta: Meta
    is_oral: bool = False
    inquirer: Person | None = None
    respondent: Person | None = None
    number: int | None = None
    title: str | None = None
    inquiries: list[list[ContentElement]] = []
    responds: list[list[ContentElement]] = []
    akn: str | None = None


class Speech(NamedTuple):
    by: Person
    role: str | None
    content: list[ContentElement]


class Question(NamedTuple):
    by: Person
    role: str | None
    content: list[ContentElement]
    is_oral: bool = False


class Answer(NamedTuple):
    by: Person
    role: str | None
    content: list[ContentElement]


class Questions(NamedTuple):
    content: list[Question | Answer]


class Hansard(NamedTuple):
    meta: Meta
    present: list[Person] = []
    absent: list[Person] = []
    guest: list[Person] = []
    officer: list[Person] = []
    debate: list[Speech | Questions] = []
    akn: str | None = None


class HansardCache(NamedTuple):
    speaker: Person
    content: list[ContentElement]
    is_question: bool = False