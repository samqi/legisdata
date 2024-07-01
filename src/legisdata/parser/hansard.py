import json
import os
from enum import Enum, auto
from functools import reduce
from itertools import chain
from math import inf
from pathlib import Path

import structlog
import typedload
from lxml import builder, etree
from unstructured.documents.elements import Element, Title

from legisdata.parser.common import (
    check_is_answer_to_inquiry,
    check_is_oral_inquiry_heading,
    check_is_written_inquiry_heading,
    last_item_replace,
    unpickler,
)
from legisdata.schema import (
    Answer,
    ContentElement,
    Hansard,
    HansardCache,
    Meta,
    Person,
    Question,
    Questions,
    Speech,
)

logger = structlog.get_logger()

HANSARD_ROLES = (
    "TUAN SPEAKER",
    "Y.B TUAN SPEAKER",
    "Y.B. TUAN SPEAKER",
    "TUAN TIMBALAN SPEAKER",
    "Y.B TUAN TIMBALAN SPEAKER",
    "Y.B. TUAN TIMBALAN SPEAKER",
    "SETIAUSAHA DEWAN",
    "Y.A.B. DATO' MENTERI BESAR",
)
HANSARD_SPEAKERS = (
    "TUAN SPEAKER",
    "Y.B TUAN SPEAKER",
    "Y.B. TUAN SPEAKER",
    "TUAN TIMBALAN SPEAKER",
    "Y.B TUAN TIMBALAN SPEAKER",
    "Y.B. TUAN TIMBALAN SPEAKER",
)


class HansardSection(Enum):
    DOCUMENT_START = auto()
    PRESENT = auto()
    ABSENT = auto()
    GUEST = auto()
    OFFICER = auto()
    START = auto()
    SPEECH = auto()
    QUESTION = auto()
    ANSWER = auto()
    END = auto()

def akn_get_container(E: builder.ElementMaker, component: Speech | Questions):
    return (
        E.speech(
            E(
                "from",
                component.by.name,
            ),
            E.div(*[E.p(item.value) for item in component.content]),
        )
        if isinstance(component, Speech)
        else E.questions(
            *[
                E(
                    "question" if isinstance(item, Question) else "answer",
                    E(
                        "from",
                        item.inquirer.name
                        if isinstance(item, Question)
                        else item.respondent.name,
                    ),
                    E.div(*[E.p(content.value) for content in item.content]),
                )
                for item in component.content
            ]
        )
    )


def akn_populate(hansard: Hansard) -> Hansard:
    E = builder.ElementMaker()

    return hansard._replace(
        akn=etree.tostring(
            E.akomaNtoso(
                E.debate(
                    E.debateBody(
                        E.debateSection(
                            *[
                                akn_get_container(E, content)
                                for content in hansard.debate
                            ]
                        ),
                    ),
                    name="hansard",
                )
            ),
            pretty_print=True,  # type: ignore
            xml_declaration=True,  # type: ignore
            encoding="utf-8",  # type: ignore
        ).decode("utf-8")
    )


def assembly_person_parse(
    current: Hansard, element: Element, section: HansardSection
) -> Hansard:
    area = element.text[element.text.find("(") : element.text.find(")") + 1]
    name = element.text.partition(area)[0].split(",")
    role = element.text.partition(area)[-1]
    person = Person(
        name=name[0],
        raw=element.text.partition(area)[0].strip(),
        # FIXME some title cannot be extracted due to missing leading comma
        title=[title.strip() for title in name[1:]],
        area=area.strip("()"),
        role=role.strip("()"),
    )

    return current._replace(
        **(
            {"present": [*current.present, person]}
            if section == HansardSection.PRESENT
            else {"absent": [*current.absent, person]}
        )
    )


def assembly_role_parse(
    current: Hansard, element: Element, section: HansardSection
) -> Hansard:
    result = current

    role = element.text.strip("( )")

    if section == HansardSection.PRESENT and role:
        result = current._replace(
            present=last_item_replace(
                current.present, lambda last: last._replace(role=role)
            )
        )

    return result


def check_is_answer(current: Hansard) -> bool:
    return (
        len(current.debate) > 0
        and isinstance(current.debate[-1], Questions)
        and (
            (
                isinstance(current.debate[-1].content[-1], Answer)
                and current.debate[-1].content[-1].respondent.name in HANSARD_SPEAKERS
            )
            or not isinstance(current.debate[-1].content[-1], Answer)
        )
    )


def check_is_assembly_person(element: Element, section: HansardSection) -> bool:
    text = element.text.upper().strip()

    return section in (HansardSection.PRESENT, HansardSection.ABSENT) and (
        text.startswith("Y.B") or text.startswith("Y.A.B")
    )


def check_is_assembly_role(element: Element, section: HansardSection) -> bool:
    text = element.text.strip()

    return (
        section == HansardSection.PRESENT
        and text.startswith("(")
        and text.endswith(")")
    )


def check_is_event(element: Element, section: HansardSection) -> bool:
    return (
        section
        in (
            HansardSection.START,
            HansardSection.SPEECH,
            HansardSection.QUESTION,
            HansardSection.ANSWER,
        )
        and ")" in element.text
        and element.text.replace(")", ")\n").splitlines()[0].startswith("(")
    )


def check_is_guest(element: Element, section: HansardSection) -> bool:
    text = element.text.upper().strip()

    return section == HansardSection.GUEST and (text.startswith("Y.B"))


def check_is_header(element: Element, header: Element) -> bool:
    return element.text.upper().strip() == header.text.upper().strip()


def check_is_officer(element: Element, section: HansardSection) -> bool:
    text = element.text.lower().strip()

    return (
        section == HansardSection.OFFICER
        and text.startswith("encik")
        or text.startswith("puan")
    )


def check_is_page_number(element: Element) -> bool:
    return element.text.strip().isdigit()


def check_is_section_absent(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.PRESENT
        and isinstance(element, Title)
        and element.text.upper().strip().startswith("TIDAK HADIR")
    )


def check_is_section_end(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.START
        and isinstance(element, Title)
        and element.text.upper().strip("( )").startswith("DEWAN DITANGGUHKAN")
    )


def check_is_section_guest(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.ABSENT
        and isinstance(element, Title)
        and element.text.upper().strip() == "TURUT HADIR"
    )


def check_is_section_officer(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.GUEST
        and isinstance(element, Title)
        and element.text.upper().strip() == "PEGAWAI BERTUGAS"
    )


def check_is_section_present(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.DOCUMENT_START
        and isinstance(element, Title)
        and element.text.upper().strip() == "YANG HADIR"
    )


def check_is_section_start(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.OFFICER
        and isinstance(element, Title)
        and "mempengerusikan mesyuarat" in element.text.lower()
    )


def check_is_speakline(
    element: Element, section: HansardSection, hansard: Hansard
) -> bool:
    text = element.text.strip().upper()

    return section in (
        HansardSection.START,
        HansardSection.SPEECH,
        HansardSection.QUESTION,
        HansardSection.ANSWER,
    ) and (
        any(
            text.startswith(person.raw.upper())
            for person in chain(hansard.present, hansard.guest)
            if person.raw
        )
        or any(text.startswith(role) for role in HANSARD_ROLES)
        or any(
            text.startswith(person.role.upper())
            for person in hansard.officer
            if person.role
        )
    )


def check_is_speakline_alternative(element: Element, section: HansardSection) -> bool:
    items = element.text.split(" ")
    return (
        section
        in (
            HansardSection.START,
            HansardSection.SPEECH,
            HansardSection.QUESTION,
            HansardSection.ANSWER,
        )
        and ":" in items
        and items.index(":") < 10
        and not element.text.strip().upper().startswith("TAJUK")
        and not element.text.strip().upper().startswith("JAWAPAN")
    )


def cache_append_element(cache: HansardCache, element: Element) -> HansardCache:
    return cache._replace(
        is_question=cache.is_question
        or check_is_oral_inquiry_heading(element)
        or check_is_written_inquiry_heading(element),
        content=[
            *cache.content,
            ContentElement(
                type=type(element).__name__.lower(),
                value=element.metadata.text_as_html or element.text,
                image=element.metadata.image_base64,
            ),
        ],
    )


def cache_insert(cache: HansardCache, current: Hansard) -> Hansard:
    if not cache:
        return current

    result = current

    if cache.is_question:
        result = current._replace(
            debate=[
                *current.debate,
                Questions(
                    content=[
                        Question(
                            inquirer=cache.speaker, role=None, content=cache.content
                        )
                    ]
                ),
            ]
        )

    elif check_is_answer(current):
        result = current._replace(
            debate=last_item_replace(
                current.debate,
                lambda questions: questions._replace(
                    content=[
                        *questions.content,
                        Answer(
                            respondent=cache.speaker, role=None, content=cache.content
                        ),
                    ]
                ),
            )
        )

    else:
        result = current._replace(
            debate=[
                *current.debate,
                Speech(by=cache.speaker, role=None, content=cache.content),
            ]
        )

    return result


def guest_parse(current: Hansard, element: Element) -> Hansard:
    role_idx = max(
        element.text.strip().find("Setiausaha"),
        element.text.strip().find("Penasihat"),
        element.text.strip().find("Pegawai"),
    )
    role = element.text.strip()[role_idx:]
    name = element.text.strip().removesuffix(role).split(",")

    return current._replace(
        guest=[
            *current.guest,
            Person(name=name[0], raw=name[0], title=name[1:], area=None, role=role),
        ]
    )


def officer_parse(current: Hansard, element: Element) -> Hansard:
    role_idx = reduce(
        lambda current, incoming: incoming if (0 < incoming < current) else current,
        [
            element.text.strip().find("Setiausaha"),
            element.text.strip().find("Penolong"),
            element.text.strip().find("Bentara"),
            element.text.strip().find("Pelapor"),
        ],
        inf,
    )
    role = element.text.strip()[role_idx:]
    names = [
        name.strip()
        for name in element.text.strip()
        .removesuffix(role)
        .replace("Encik", "|Encik")
        .replace("Puan", "|Puan")
        .lstrip("|")
        .split("|")
    ]

    return current._replace(
        officer=current.officer
        + [Person(name=name, raw=name, role=role) for name in names]
    )


def speaker_parse(current: Hansard, element: Element) -> str:
    text = element.text.strip().upper()

    for person in chain(current.present, current.guest):
        if person.raw and text.startswith(person.raw.upper()):
            return person.raw.upper()

    for role in HANSARD_ROLES:
        if text.startswith(role):
            return role

    for person in current.officer:
        if person.role and text.startswith(person.role.upper()):
            return person.role.upper()

    return "_UNKNOWN"


def speakline_alternative_parse(
    cache: HansardCache | None, current: Hansard, element: Element
) -> tuple[HansardCache, Hansard]:
    speaker = element.text.partition(":")[0].strip()
    # name = speaker[speaker.find("(") : speaker.find(")") + 1] or speaker
    # role = speaker.partition(name)[0].strip() or None

    return (
        HansardCache(
            # person=Person(name=name.strip("( )"), role=role),
            speaker=Person(name=speaker, raw=speaker),
            content=[
                ContentElement(
                    type=type(element).__name__.lower(),
                    value="".join(element.text.partition(":")[2:]).strip(),
                    image=element.metadata.image_base64,
                )
            ],
        ),
        cache_insert(cache, current) if cache else current,
    )


def speakline_parse(
    cache: HansardCache | None, current: Hansard, element: Element
) -> tuple[HansardCache, Hansard]:
    speaker = speaker_parse(current, element)

    return (
        HansardCache(
            speaker=Person(name=speaker, raw=speaker),
            content=[
                ContentElement(
                    type=type(element).__name__.lower(),
                    value=element.text[len(speaker) :].strip(": "),
                    image=element.metadata.image_base64,
                )
            ],
        ),
        cache_insert(cache, current) if cache else current,
    )


def parse(
    year: int,
    session: int,
    hansard_files: tuple[os.DirEntry[str], ...],
    parse_path: Path,
) -> None:
    for file_idx, (file_entry, elements) in enumerate(map(unpickler, hansard_files)):
        logger.info(
            f"Parsing file {file_idx + 1}/{len(hansard_files)}", path=file_entry.path
        )

        elements_stripped = [
            element
            for element in elements
            if not check_is_header(element, elements[0])
            and not check_is_page_number(element)
        ]

        section = HansardSection.DOCUMENT_START
        parsed = Hansard(
            meta=Meta(
                source=file_entry.path, year=year, session=session, dun="selangor"
            )
        )
        cache = None

        for idx, element in enumerate(elements_stripped):
            if check_is_section_present(element, section):
                section = HansardSection.PRESENT

            elif check_is_section_absent(element, section):
                section = HansardSection.ABSENT

            elif check_is_section_guest(element, section):
                section = HansardSection.GUEST

            elif check_is_section_officer(element, section):
                section = HansardSection.OFFICER

            elif check_is_section_start(element, section):
                section = HansardSection.START

            elif check_is_section_end(element, section):
                section = HansardSection.END

                parsed = cache_insert(cache, parsed) if cache else parsed

            elif check_is_event(element, section):
                parsed = cache_insert(cache, parsed) if cache else parsed

            elif check_is_assembly_person(element, section):
                parsed = assembly_person_parse(parsed, element, section)

            elif check_is_assembly_role(element, section):
                parsed = assembly_role_parse(parsed, element, section)

            elif check_is_guest(element, section):
                parsed = guest_parse(parsed, element)

            elif check_is_officer(element, section):
                parsed = officer_parse(parsed, element)

            elif check_is_speakline(element, section, parsed):
                cache, parsed = speakline_parse(cache, parsed, element)

            elif check_is_speakline_alternative(element, section):
                cache, parsed = speakline_alternative_parse(cache, parsed, element)

            elif (
                section == HansardSection.START
                and cache
                and not check_is_answer_to_inquiry(element)
            ):
                cache = cache_append_element(cache, element)

            elif int(os.environ.get("DEBUG", "0")) == 1:
                logger.debug(
                    "Skipping element",
                    idx=idx,
                    section=section,
                    element=element,
                    text=element.text,
                )

        parsed = akn_populate(parsed)

        file_name = "{}/{}".format(
            parse_path,
            file_entry.name.replace(".pickle", ".json"),
        )

        logger.info(
            f"Writing hansard to file {file_idx + 1}/{len(hansard_files)}",
            source=file_entry.name,
            parsed_inquiry=file_name,
        )
        with open(file_name, "w") as handle:
            json.dump(typedload.dump(parsed), handle, indent=2)