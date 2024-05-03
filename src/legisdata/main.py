import os
import time
from posixpath import basename
from random import randrange
from typing import List

import requests
import structlog
import typer
from huggingface_hub import HfApi
from parsel import Selector

app = typer.Typer()
api = HfApi()
logger = structlog.get_logger()


@app.command()
def download(year: int, session: int) -> None:
    logger.info("Requesting download", year=year, session=session)

    download_archive(
        year,
        session,
        "hansard",
        "hansard",
        "https://dewan.selangor.gov.my/penyata-rasmi/",
        "mb-2",
    )
    download_archive(
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
def parse(year: int, session: int) -> None:
    pass


def download_archive(
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
    os.makedirs(f"data/{year}/session-{session}/{listing_name}-raw", exist_ok=True)

    listing_url_list = listing_get_session_files(listing_session_url, file_p_class)
    for listing_idx, listing_url in enumerate(listing_url_list):
        with open(
            f"data/{year}/session-{session}/{listing_name}-raw/{basename(listing_url)}",
            "wb",
        ) as listing_file:
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


if __name__ == "__main__":
    app()