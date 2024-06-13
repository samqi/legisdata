import json
from datetime import datetime
from typing import Any, NamedTuple, Union


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
    inquirer: Person | None = None
    respondent: Person | None = None
    number: int | None = None
    title: str | None = None
    inquiries: list[list[ContentElement]] = []
    responds: list[list[ContentElement]] = []
    akn: str | None = None

    def json(self) -> str:
        def dump_value(
            value: Union[int, str, list[list[ContentElement]], NamedTuple, None],
        ) -> Any:
            result = None

            if value is None:
                result = None
            elif isinstance(value, str) or isinstance(value, int):  # eg. title
                result = value
            elif isinstance(value, list):
                result = [
                    [
                        dict(item._asdict(), _type=item.__class__.__name__)
                        for item in sub_list
                    ]
                    for sub_list in value
                ]
            else:
                result = dict(value._asdict(), _type=value.__class__.__name__)

            return result

        return json.dumps(
            {
                key: dump_value(value)
                for key, value in dict(
                    self._asdict(), _type=self.__class__.__name__
                ).items()
            },
            indent=2,
        )


class Speech(NamedTuple):
    by: Person
    role: str | None
    content: list[ContentElement]

    def dump(self) -> dict[Any, Any]:
        return {
            "by": dict(self.by._asdict(), _type=self.by.__class__.__name__),
            "role": self.role,
            "content": [
                dict(item._asdict(), _type=item.__class__.__name__)
                for item in self.content
            ],
            "_type": self.__class__.__name__,
        }


class Question(NamedTuple):
    by: Person
    role: str | None
    content: list[ContentElement]


class Answer(NamedTuple):
    by: Person
    role: str | None
    content: list[ContentElement]


class Questions(NamedTuple):
    content: list[Question | Answer]

    def dump(self) -> dict[Any, Any]:
        return {
            "content": [
                dict(
                    dict(
                        item._asdict(),
                        by=dict(item.by._asdict(), _type=item.by.__class__.__name__),
                    ),
                    _type=item.__class__.__name__,
                )
                for item in self.content
            ],
            "_type": self.__class__.__name__,
        }


class Hansard(NamedTuple):
    meta: Meta
    present: list[Person] = []
    absent: list[Person] = []
    guest: list[Person] = []
    officer: list[Person] = []
    debate: list[Speech | Questions] = []
    akn: str | None = None

    def json(self) -> str:
        def dump_value(
            value: Union[
                list[Person], list[Union[Speech, Questions], None], NamedTuple
            ],
        ) -> Any:
            result = None

            if isinstance(value, list):
                result = [
                    item._asdict() if isinstance(item, Person) else item.dump()
                    for item in value
                ]

            elif value is not None:
                result = value._asdict()

            return result

        return json.dumps(
            dict(
                {key: dump_value(value) for key, value in dict(self._asdict()).items()},
                _type=self.__class__.__name__,
            ),
            indent=2,
        )


class HansardCache(NamedTuple):
    speaker: Person
    content: list[ContentElement]
    is_question: bool = False