import json
import mimetypes
import os
import pickle
import time
from itertools import chain
from posixpath import basename
from random import randrange

import requests
import structlog
import typer
from huggingface_hub import HfApi
from parsel import Selector
from unstructured.partition.pdf import partition_pdf

from legisdata.common import (
    ListingClass,
    ListingType,
    archive_exists,
    data_get_path,
    path_generate,
)
from legisdata.parser.hansard import parse as hansard_parse
from legisdata.parser.inquiry import parse as inquiry_parse

app = typer.Typer()
api = HfApi()
logger = structlog.get_logger()


@app.command()
def download(year: int, session: int) -> None:
    logger.info("Requesting download", year=year, session=session)

    archive_download(
        year,
        session,
        ListingType.Hansard,
        "hansard",
        "https://dewan.selangor.gov.my/penyata-rasmi/",
        "mb-2",
    )
    archive_download(
        year,
        session,
        ListingType.Inquiry,
        "soalan",
        "https://dewan.selangor.gov.my/arkib-soalan-mulut-dan-soalan-bertulis/",
        "mb-1",
    )

    logger.info("Uploading downloaded archive to huggingface")
    api.upload_folder(
        folder_path="data",
        repo_id=os.environ.get("LEGISDATA_HF_REPO", "sinarproject/legisdata"),
        repo_type="dataset",
    )


@app.command()
def extract(year: int, session: int) -> None:
    logger.info("Extracting PDF", year=year, session=session)

    path_base = path_generate(year, session)
    hansard_path = data_get_path(path_base, ListingType.Hansard, ListingClass.RAW)
    inquiry_path = data_get_path(path_base, ListingType.Inquiry, ListingClass.RAW)
    assert archive_exists(
        hansard_path, inquiry_path
    ), "Archive is not properly downloaded"

    for archive_type in (ListingType.Hansard, ListingType.Inquiry):
        os.makedirs(
            data_get_path(path_base, archive_type, ListingClass.EXTRACT), exist_ok=True
        )

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
        folder_path="data",
        repo_id=os.environ.get("LEGISDATA_HF_REPO", "sinarproject/legisdata"),
        repo_type="dataset",
    )


@app.command()
def parse(year: int, session: int) -> None:
    logger.info("Parsing extracted PDFs", year=year, session=session)

    path_base = path_generate(year, session)
    hansard_path = data_get_path(path_base, ListingType.Hansard, ListingClass.EXTRACT)
    inquiry_path = data_get_path(path_base, ListingType.Inquiry, ListingClass.EXTRACT)
    assert archive_exists(
        hansard_path, inquiry_path
    ), "Archive is not properly downloaded"

    for archive_type in (ListingType.Hansard, ListingType.Inquiry):
        os.makedirs(
            data_get_path(path_base, archive_type, ListingClass.PARSE), exist_ok=True
        )

    hansard_parse(
        year,
        session,
        tuple(target for target in os.scandir(hansard_path) if target.is_file()),
        data_get_path(path_base, ListingType.Hansard, ListingClass.PARSE),
    )
    inquiry_parse(
        year,
        session,
        tuple(target for target in os.scandir(inquiry_path) if target.is_file()),
        data_get_path(path_base, ListingType.Inquiry, ListingClass.PARSE),
    )

    logger.info("Uploading parsed archive to huggingface")
    api.upload_folder(
        folder_path="data",
        repo_id=os.environ.get("LEGISDATA_HF_REPO", "sinarproject/legisdata"),
        repo_type="dataset",
    )


def archive_download(
    year: int,
    session: int,
    listing_type: ListingType,
    listing_css_class: str,
    listing_idx_url: str,
    file_p_class: str,
) -> None:
    logger.info(f"Retrieving the index for {listing_type.value}", url=listing_idx_url)
    listing_idx_req = requests.get(listing_idx_url)
    listing_idx_html = Selector(text=listing_idx_req.text)

    listing_session_url = listing_get_session_url(
        listing_idx_html,
        listing_css_class,
        listing_get_year_index(
            listing_idx_html, listing_type.value, listing_css_class, year
        ),
        session,
    )

    logger.info(
        f"Fetching {listing_type.value} list",
        url=listing_session_url,
    )

    logger.info(f"Creating directory to store {listing_type.value}")
    os.makedirs(
        data_get_path(path_generate(year, session), listing_type, ListingClass.RAW),
        exist_ok=True,
    )

    listing_url_list = listing_get_session_files(listing_session_url, file_p_class)
    with open(
        data_get_path(path_generate(year, session), listing_type, ListingClass.RAW)
        / "url_list.json",
        "w",
    ) as list_file:
        for listing_idx, listing_url in enumerate(listing_url_list):
            with open(
                data_get_path(
                    path_generate(year, session), listing_type, ListingClass.RAW
                )
                / basename(listing_url),
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
                    f"Fetching {listing_type.value} document {listing_idx + 1}/{len(listing_url_list)}",
                    url=listing_url,
                )
                listing_req = requests.get(listing_url)

                logger.info(
                    f"Writing {listing_type.value} to destination",
                    file=listing_file.name,
                )
                listing_file.write(listing_req.content)

            time.sleep(randrange(5, 10))


def listing_get_session_files(listing_session_url: str, file_p_class: str) -> list[str]:
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


if __name__ == "__main__":
    app()
