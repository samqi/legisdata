import os

import structlog
from unstructured.documents.elements import Element, ListItem, Title

from legisdata.parser.common import (
    check_is_oral_inquiry_answer,
    check_is_oral_inquiry_heading,
    last_item_replace,
    unpickler,
)
from legisdata.schema import ContentElement, Inquiry, Meta, Person

logger = structlog.get_logger()


def check_is_new_content(inquiry: Inquiry, is_question: bool, element: Element) -> bool:
    return (
        isinstance(element, ListItem)
        or (is_question and not inquiry.inquiries)
        or (not is_question and not inquiry.responds)
    )


def check_is_respondent_mention(element) -> bool:
    return element.text.lower().find("bertanya kepada") in range(6)


def check_is_title(element: Element) -> bool:
    return isinstance(element, Title) and element.text.upper().startswith("TAJUK")


def content_append_element(
    current: Inquiry, item: ContentElement, is_question: bool
) -> Inquiry:
    return current._replace(
        **(
            {
                "inquiries": last_item_replace(
                    current.inquiries, lambda inquiry: [*inquiry, item]
                )
            }
            if is_question
            else {
                "responds": last_item_replace(
                    current.responds, lambda respond: [*respond, item]
                )
            }
        )
    )


def content_insert_new(
    current: Inquiry, item: ContentElement, is_question: bool
) -> Inquiry:
    return current._replace(
        **(
            {"inquiries": [*current.inquiries, [item]]}
            if is_question
            else {"responds": [*current.responds, [item]]}
        )
    )


def create_new(
    element: Element, file_entry: os.DirEntry, year: int, session: int, dun: str
) -> Inquiry:
    return Inquiry(
        inquirer=Person(
            name=element.text[
                element.text.upper().rfind("DARIPADA") + 8 : element.text.find("(")
            ].strip(),
            area=element.text[element.text.find("(") + 1 : element.text.find(")")],
        ),
        meta=Meta(
            source=file_entry.path,
            year=year,
            session=session,
            dun=dun,
        ),
    )


def parse(
    year: int,
    session: int,
    inquiry_files: tuple[os.DirEntry[str], ...],
    parse_path: str,
) -> None:
    for file_idx, (file_entry, elements) in enumerate(map(unpickler, inquiry_files)):
        if not check_is_oral_inquiry_heading(elements[0]):
            logger.info(
                f"Skipping non inquiry file {file_idx + 1}/{len(inquiry_files)}",
                path=file_entry.path,
            )
            continue

        logger.info(
            f"Parsing file {file_idx + 1}/{len(inquiry_files)}", path=file_entry.path
        )

        parsed: list[Inquiry] = []
        is_question = False
        for idx, element in enumerate(elements):
            if check_is_oral_inquiry_heading(element):
                parsed.append(
                    create_new(element, file_entry, year, session, "selangor")
                )

            elif check_is_title(element):
                parsed.append(title_insert(parsed.pop(), element))

            elif check_is_respondent_mention(element):
                is_question = True

                parsed.append(respondent_insert(parsed.pop(), element))

            elif check_is_oral_inquiry_answer(element):
                is_question = False

            else:
                item = ContentElement(
                    type=type(element).__name__.lower(),
                    value=element.metadata.text_as_html or element.text,
                    image=element.metadata.image_base64,
                )

                if check_is_new_content(parsed[-1], is_question, element):
                    parsed.append(content_insert_new(parsed.pop(), item, is_question))

                else:
                    parsed.append(
                        content_append_element(parsed.pop(), item, is_question)
                    )

        for idx, inquiry in enumerate(parsed):
            file_name = "{}/{}".format(
                parse_path,
                file_entry.name.replace(".pickle", f".{inquiry.number}.json"),
            )

            logger.info(
                f"Writing inquiry to file {idx + 1}/{len(parsed)}",
                source=file_entry.name,
                parsed_inquiry=file_name,
            )
            with open(file_name, "w") as handle:
                handle.write(inquiry.json())


def respondent_insert(current: Inquiry, element) -> Inquiry:
    return current._replace(
        number=int(element.text[: element.text.index(".")]),
        respondent=Person(
            name=element.text[element.text.lower().find("kepada") + 6 :].strip(" :-")
        ),
    )


def title_insert(current: Inquiry, element) -> Inquiry:
    return current._replace(
        title=element.text[element.text.find("TAJUK") + 5 :].strip(" :")
    )