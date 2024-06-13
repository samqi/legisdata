import json
import mimetypes
import os
import pickle
import time
from enum import Enum, auto
from functools import reduce
from itertools import chain
from math import inf
from posixpath import basename
from random import randrange
from typing import Iterable, List

import requests
import structlog
import typer
from huggingface_hub import HfApi
from parsel import Selector
from unstructured.documents.elements import Element, ListItem, Title
from unstructured.partition.pdf import partition_pdf

from legisdata.schema import (
    Answer,
    ContentElement,
    Hansard,
    HansardCache,
    Inquiry,
    Meta,
    Person,
    Question,
    Questions,
    Speech,
)

app = typer.Typer()
api = HfApi()
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




@app.command()
def download(year: int, session: int) -> None:
    logger.info("Requesting download", year=year, session=session)

    archive_download(
        year,
        session,
        "hansard",
        "hansard",
        "https://dewan.selangor.gov.my/penyata-rasmi/",
        "mb-2",
    )
    archive_download(
        year,
        session,
        "inquiry",
        "soalan",
        "https://dewan.selangor.gov.my/arkib-soalan-mulut-dan-soalan-bertulis/",
        "mb-1",
    )

    logger.info("Uploading downloaded archive to huggingface")
    api.upload_folder(
        folder_path="data", repo_id="sinarproject/legisdata", repo_type="dataset"
    )


@app.command()
def extract(year: int, session: int) -> None:
    logger.info("Extracting PDF", year=year, session=session)

    path_base = path_generate(year, session)
    hansard_path = listing_get_path(path_base, "hansard")
    inquiry_path = listing_get_path(path_base, "inquiry")
    assert archive_exists(
        hansard_path, inquiry_path
    ), "Archive is not properly downloaded"

    for archive_path in (hansard_path, inquiry_path):
        os.makedirs(archive_path.replace("raw", "extract"), exist_ok=True)

    target_files = tuple(
        target
        for target in chain(os.scandir(inquiry_path), os.scandir(hansard_path))
        if target.is_file()
        and mimetypes.guess_type(target.path)[0] == "application/pdf"
    )

    for idx, target_file in enumerate(target_files):
        with open(
            target_file.path.replace("raw", "extract") + ".pickle", "wb"
        ) as file_extract:
            logger.info(
                f"Extracting file {idx + 1}/{len(target_files)}",
                source=target_file.name,
                target=file_extract.name,
            )
            pickle.dump(
                partition_pdf(
                    target_file.path,
                    languages=["msa", "eng"],
                    strategy="hi_res",
                    extract_image_block_types=["Image", "Table"],
                    extract_image_block_to_payload=True,
                ),
                file_extract,
            )

    logger.info("Uploading extracted archive to huggingface")
    api.upload_folder(
        folder_path="data", repo_id="sinarproject/legisdata", repo_type="dataset"
    )


@app.command()
def parse(year: int, session: int) -> None:
    logger.info("Parsing extracted PDFs", year=year, session=session)

    path_base = path_generate(year, session)
    hansard_path = listing_get_path(path_base, "hansard").replace("raw", "extract")
    inquiry_path = listing_get_path(path_base, "inquiry").replace("raw", "extract")
    assert archive_exists(
        hansard_path, inquiry_path
    ), "Archive is not properly downloaded"

    for archive_path in (hansard_path, inquiry_path):
        os.makedirs(archive_path.replace("extract", "parse"), exist_ok=True)

    hansard_parse(
        year,
        session,
        tuple(target for target in os.scandir(hansard_path) if target.is_file()),
        hansard_path.replace("extract", "parse"),
    )
    inquiry_parse(
        year,
        session,
        tuple(target for target in os.scandir(inquiry_path) if target.is_file()),
        inquiry_path.replace("extract", "parse"),
    )

    # logger.info("Uploading parsed archive to huggingface")
    # api.upload_folder(
    #    folder_path="data", repo_id="sinarproject/legisdata", repo_type="dataset"
    # )


def archive_download(
    year: int,
    session: int,
    listing_name: str,
    listing_class: str,
    listing_idx_url: str,
    file_p_class: str,
) -> None:
    logger.info(f"Retrieving the index for {listing_name}", url=listing_idx_url)
    listing_idx_req = requests.get(listing_idx_url)
    listing_idx_html = Selector(text=listing_idx_req.text)

    listing_session_url = listing_get_session_url(
        listing_idx_html,
        listing_class,
        listing_get_year_index(listing_idx_html, listing_name, listing_class, year),
        session,
    )

    logger.info(
        f"Fetching {listing_name} list",
        url=listing_session_url,
    )

    logger.info(f"Creating directory to store {listing_name}")
    os.makedirs(
        listing_get_path(path_generate(year, session), listing_name), exist_ok=True
    )

    listing_url_list = listing_get_session_files(listing_session_url, file_p_class)
    with open(
        f"{listing_get_path(path_generate(year, session), listing_name)}/url_list.json",
        "w",
    ) as list_file:
        for listing_idx, listing_url in enumerate(listing_url_list):
            with open(
                f"{listing_get_path(path_generate(year, session), listing_name)}/{basename(listing_url)}",
                "wb",
            ) as listing_file:
                list_file.write(
                    "{}\n".format(
                        json.dumps(
                            {
                                "url": listing_url,
                                "path": list_file.name,
                                "year": year,
                                "session": "session",
                                "dun": "selangor",
                            }
                        )
                    )
                )

                logger.info(
                    f"Fetching {listing_name} document {listing_idx + 1}/{len(listing_url_list)}",
                    url=listing_url,
                )
                listing_req = requests.get(listing_url)

                logger.info(
                    f"Writing {listing_name} to destination", file=listing_file.name
                )
                listing_file.write(listing_req.content)

            time.sleep(randrange(5, 10))


def archive_exists(*archive_list: Iterable[str]) -> bool:
    return all(os.path.exists(archive_path) for archive_path in archive_list)  # type: ignore


def check_is_inquiry_answer(element: Element) -> bool:
    return isinstance(element, Title) and element.text.upper().startswith("JAWAPAN")


def check_is_inquiry_heading(element: Element) -> bool:
    return isinstance(element, Title) and element.text.upper().startswith(
        "PERTANYAAN-PERTANYAAN MULUT DARIPADA"
    )


def check_is_inquiry_new_content(
    inquiry: Inquiry, is_question: bool, element: Element
) -> bool:
    return (
        isinstance(element, ListItem)
        or (is_question and not inquiry.inquiries)
        or (not is_question and not inquiry.responds)
    )


def check_is_inquiry_respondent_mention(element) -> bool:
    return element.text.lower().find("bertanya kepada") in range(6)


def check_is_inquiry_title(element: Element) -> bool:
    return isinstance(element, Title) and element.text.upper().startswith("TAJUK")


def check_is_hansard_answer(current: Hansard) -> bool:
    return (
        len(current.debate) > 0
        and isinstance(current.debate[-1], Questions)
        and (
            (
                isinstance(current.debate[-1].content[-1], Answer)
                and current.debate[-1].content[-1].by.name in HANSARD_SPEAKERS
            )
            or not isinstance(current.debate[-1].content[-1], Answer)
        )
    )


def check_is_hansard_assembly_person(element: Element, section: HansardSection) -> bool:
    text = element.text.upper().strip()

    return section in (HansardSection.PRESENT, HansardSection.ABSENT) and (
        text.startswith("Y.B") or text.startswith("Y.A.B")
    )


def check_is_hansard_assembly_role(element: Element, section: HansardSection) -> bool:
    text = element.text.strip()

    return (
        section == HansardSection.PRESENT
        and text.startswith("(")
        and text.endswith(")")
    )


def check_is_hansard_event(element: Element, section: HansardSection) -> bool:
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


def check_is_hansard_guest(element: Element, section: HansardSection) -> bool:
    text = element.text.upper().strip()

    return section == HansardSection.GUEST and (text.startswith("Y.B"))


def check_is_hansard_header(element: Element, header: Element) -> bool:
    return element.text.upper().strip() == header.text.upper().strip()


def check_is_hansard_officer(element: Element, section: HansardSection) -> bool:
    text = element.text.lower().strip()

    return (
        section == HansardSection.OFFICER
        and text.startswith("encik")
        or text.startswith("puan")
    )


def check_is_hansard_page(element: Element) -> bool:
    return element.text.strip().isdigit()


def check_is_hansard_section_absent(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.PRESENT
        and isinstance(element, Title)
        and element.text.upper().strip().startswith("TIDAK HADIR")
    )


def check_is_hansard_section_end(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.START
        and isinstance(element, Title)
        and element.text.upper().strip("( )").startswith("DEWAN DITANGGUHKAN")
    )


def check_is_hansard_section_guest(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.ABSENT
        and isinstance(element, Title)
        and element.text.upper().strip() == "TURUT HADIR"
    )


def check_is_hansard_section_officer(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.GUEST
        and isinstance(element, Title)
        and element.text.upper().strip() == "PEGAWAI BERTUGAS"
    )


def check_is_hansard_section_present(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.DOCUMENT_START
        and isinstance(element, Title)
        and element.text.upper().strip() == "YANG HADIR"
    )


def check_is_hansard_section_start(element: Element, section: HansardSection) -> bool:
    return (
        section == HansardSection.OFFICER
        and isinstance(element, Title)
        and "mempengerusikan mesyuarat" in element.text.lower()
    )


def check_is_hansard_speakline(
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


def check_is_hansard_speakline_alternative(
    element: Element, section: HansardSection
) -> bool:
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


def hansard_cache_insert_element(cache: HansardCache, element: Element) -> HansardCache:
    return cache._replace(
        is_question=cache.is_question or check_is_inquiry_heading(element),
        content=cache.content
        + [
            ContentElement(
                type=type(element).__name__.lower(),
                value=element.metadata.text_as_html or element.text,
                image=element.metadata.image_base64,
            )
        ],
    )


def hansard_insert_cache(cache: HansardCache, current: Hansard) -> Hansard:
    if not cache:
        return current

    result = current

    if cache.is_question:
        result = current._replace(
            debate=current.debate
            + [
                Questions(
                    content=[
                        Question(by=cache.speaker, role=None, content=cache.content)
                    ]
                )
            ]
        )

    elif check_is_hansard_answer(current):
        questions = current.debate[-1]

        result = current._replace(
            debate=current.debate[:-1]
            + [
                questions._replace(
                    content=questions.content
                    + [Answer(by=cache.speaker, role=None, content=cache.content)]
                )
            ]
        )

    else:
        result = current._replace(
            debate=current.debate
            + [Speech(by=cache.speaker, role=None, content=cache.content)]
        )

    return result


def hansard_parse(
    year: int,
    session: int,
    hansard_files: tuple[os.DirEntry[str], ...],
    parse_path: str,
) -> None:
    for file_idx, (file_entry, elements) in enumerate(map(unpickler, hansard_files)):
        logger.info(
            f"Parsing file {file_idx + 1}/{len(hansard_files)}", path=file_entry.path
        )

        elements_stripped = [
            element
            for element in elements
            if not check_is_hansard_header(element, elements[0])
            and not check_is_hansard_page(element)
        ]

        section = HansardSection.DOCUMENT_START
        parsed = Hansard(
            meta=Meta(
                source=file_entry.path, year=year, session=session, dun="selangor"
            )
        )
        cache = None

        for idx, element in enumerate(elements_stripped):
            if check_is_hansard_section_present(element, section):
                section = HansardSection.PRESENT

            elif check_is_hansard_section_absent(element, section):
                section = HansardSection.ABSENT

            elif check_is_hansard_section_guest(element, section):
                section = HansardSection.GUEST

            elif check_is_hansard_section_officer(element, section):
                section = HansardSection.OFFICER

            elif check_is_hansard_section_start(element, section):
                section = HansardSection.START

            elif check_is_hansard_section_end(element, section):
                section = HansardSection.END

            elif check_is_hansard_event(element, section):
                parsed = hansard_insert_cache(cache, parsed) if cache else parsed

            elif check_is_hansard_assembly_person(element, section):
                parsed = hansard_parse_assembly_person(parsed, element, section)

            elif check_is_hansard_assembly_role(element, section):
                parsed = hansard_parse_assembly_role(parsed, element, section)

            elif check_is_hansard_guest(element, section):
                parsed = hansard_parse_guest(parsed, element)

            elif check_is_hansard_officer(element, section):
                parsed = hansard_parse_officer(parsed, element)

            elif check_is_hansard_speakline(element, section, parsed):
                cache, parsed = hansard_parse_speakline(cache, parsed, element)

            elif check_is_hansard_speakline_alternative(element, section):
                cache, parsed = hansard_parse_speakline_alternative(
                    cache, parsed, element
                )

            elif (
                section == HansardSection.START
                and cache
                and not check_is_inquiry_answer(element)
            ):
                cache = hansard_cache_insert_element(cache, element)

            elif int(os.environ.get("DEBUG", "0")) == 1:
                logger.debug(
                    "Skipping element",
                    idx=idx,
                    section=section,
                    element=element,
                    text=element.text,
                )

        parsed = hansard_insert_cache(cache, parsed) if cache else parsed

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
            handle.write(parsed.json())


def hansard_parse_assembly_person(
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
            {"present": current.present + [person]}
            if section == HansardSection.PRESENT
            else {"absent": current.absent + [person]}
        )
    )


def hansard_parse_assembly_role(
    current: Hansard, element: Element, section: HansardSection
) -> Hansard:
    result = current

    role = element.text.strip("( )")

    if section == HansardSection.PRESENT and role:
        result = current._replace(
            present=current.present[:-1] + [current.present[-1]._replace(role=role)]
        )

    return result


def hansard_parse_guest(current: Hansard, element: Element) -> Hansard:
    role_idx = max(
        element.text.strip().find("Setiausaha"),
        element.text.strip().find("Penasihat"),
        element.text.strip().find("Pegawai"),
    )
    role = element.text.strip()[role_idx:]
    name = element.text.strip().removesuffix(role).split(",")

    return current._replace(
        guest=current.guest
        + [Person(name=name[0], title=name[1:], area=None, role=role)]
    )


def hansard_parse_officer(current: Hansard, element: Element) -> Hansard:
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
        officer=current.officer + [Person(name=name, role=role) for name in names]
    )


def hansard_parse_speaker(current: Hansard, element: Element) -> str:
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


def hansard_parse_speakline(
    cache: HansardCache | None, current: Hansard, element: Element
) -> tuple[HansardCache, Hansard]:
    speaker = hansard_parse_speaker(current, element)

    return (
        HansardCache(
            speaker=Person(name=speaker),
            content=[
                ContentElement(
                    type=type(element).__name__.lower(),
                    value=element.text[len(speaker) :].strip(": "),
                    image=None,
                )
            ],
        ),
        hansard_insert_cache(cache, current) if cache else current,
    )


def hansard_parse_speakline_alternative(
    cache: HansardCache | None, current: Hansard, element: Element
) -> tuple[HansardCache, Hansard]:
    speaker = element.text.partition(":")[0].strip()
    # name = speaker[speaker.find("(") : speaker.find(")") + 1] or speaker
    # role = speaker.partition(name)[0].strip() or None

    return (
        HansardCache(
            # person=Person(name=name.strip("( )"), role=role),
            speaker=Person(name=speaker),
            content=[
                ContentElement(
                    type=type(element).__name__.lower(),
                    value="".join(element.text.partition(":")[2:]).strip(),
                    image=None,
                )
            ],
        ),
        hansard_insert_cache(cache, current) if cache else current,
    )


def inquiry_append_content(
    current: Inquiry, item: ContentElement, is_question: bool
) -> Inquiry:
    return current._replace(
        **(
            {"inquiries": current.inquiries[:-1] + [current.inquiries[-1] + [item]]}
            if is_question
            else {"responds": current.responds[:-1] + [current.responds[-1] + [item]]}
        )
    )


def inquiry_create_new(
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


def inquiry_insert_new_content(
    current: Inquiry, item: ContentElement, is_question: bool
) -> Inquiry:
    return current._replace(
        **(
            {"inquiries": current.inquiries + [[item]]}
            if is_question
            else {"responds": current.responds + [[item]]}
        )
    )


def inquiry_insert_respondent_mention(current: Inquiry, element) -> Inquiry:
    return current._replace(
        number=int(element.text[: element.text.index(".")]),
        respondent=Person(
            name=element.text[element.text.lower().find("kepada") + 6 :].strip(" :-")
        ),
    )


def inquiry_insert_title(current: Inquiry, element) -> Inquiry:
    return current._replace(
        title=element.text[element.text.find("TAJUK") + 5 :].strip(" :")
    )


def inquiry_parse(
    year: int,
    session: int,
    inquiry_files: tuple[os.DirEntry[str], ...],
    parse_path: str,
) -> None:
    for file_idx, (file_entry, elements) in enumerate(map(unpickler, inquiry_files)):
        if not check_is_inquiry_heading(elements[0]):
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
            if check_is_inquiry_heading(element):
                parsed.append(
                    inquiry_create_new(element, file_entry, year, session, "selangor")
                )

            elif check_is_inquiry_title(element):
                parsed.append(inquiry_insert_title(parsed.pop(), element))

            elif check_is_inquiry_respondent_mention(element):
                is_question = True

                parsed.append(inquiry_insert_respondent_mention(parsed.pop(), element))

            elif check_is_inquiry_answer(element):
                is_question = False

            else:
                item = ContentElement(
                    type=type(element).__name__.lower(),
                    value=element.metadata.text_as_html or element.text,
                    image=element.metadata.image_base64,
                )

                if check_is_inquiry_new_content(parsed[-1], is_question, element):
                    parsed.append(
                        inquiry_insert_new_content(parsed.pop(), item, is_question)
                    )

                else:
                    parsed.append(
                        inquiry_append_content(parsed.pop(), item, is_question)
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


def listing_get_path(path_base: str, listing_name: str) -> str:
    return f"{path_base}/{listing_name}-raw"


def listing_get_session_files(listing_session_url: str, file_p_class: str) -> List[str]:
    listing_session_req = requests.get(listing_session_url)
    listing_session_html = Selector(text=listing_session_req.text)

    return listing_session_html.css(
        f"div.entry-content p.{file_p_class} a::attr(href)"
    ).getall()


def listing_get_session_url(
    listing_idx_html: Selector, listing_class: str, year_idx: int, session: int
) -> str:
    listing_sessions = listing_idx_html.css(
        f"div.{listing_class}-items div.{listing_class}-item ul.list-attachment"
    )[year_idx].css("li")
    logger.info("Sessions available", sessions=listing_sessions.css("a::text").getall())

    if session > len(listing_sessions):
        raise ValueError("Invalid session is requested")

    return listing_sessions.css("a::attr(href)").getall()[session - 1]


def listing_get_year_index(
    listing_idx_html: Selector, listing_name: str, listing_class: str, year: int
) -> int:
    listing_years = [
        int(year)
        for year in listing_idx_html.css(
            f"div.{listing_class}-items div.{listing_class}-item h4::text"
        ).getall()
    ]

    logger.info(f"Years available for {listing_name}", years=listing_years)
    if year not in listing_years:
        raise ValueError("Invalid year is requested")

    return listing_years.index(year)


def path_generate(year: int, session: int) -> str:
    return f"data/{year}/session-{session}"


def unpickler(file_item: os.DirEntry[str]) -> tuple[os.DirEntry, List[Element]]:
    with open(file_item, "rb") as file_content:
        return (file_item, pickle.load(file_content))


if __name__ == "__main__":
    app()
