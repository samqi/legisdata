from enum import Enum
from pathlib import Path


class ListingType(Enum):
    Hansard = "hansard"
    Inquiry = "inquiry"


class ListingClass(Enum):
    RAW = "raw"
    EXTRACT = "extract"
    PARSE = "parse"


def archive_exists(*archive_list: Path) -> bool:
    return all(archive_path.exists() for archive_path in archive_list)


def data_get_path(
    base_path: Path, listing_type: ListingType, listing_class: ListingClass
) -> Path:
    return base_path / f"{listing_type.value}-{listing_class.value}"


def path_generate(year: int, session: int) -> Path:
    return Path(".") / "data" / str(year) / f"session-{session}"