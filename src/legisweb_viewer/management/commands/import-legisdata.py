import json
import os

import structlog
import typedload
from django.db import transaction
from django_typer.management import TyperCommand
from legisdata import schema
from legisdata.common import (
    ListingClass,
    ListingType,
    archive_exists,
    data_get_path,
    path_generate,
)

from legisweb_viewer import models

logger = structlog.get_logger(__name__)


class Command(TyperCommand):
    def handle(self, year: int, session: int) -> None:
        logger.info("Importing data", year=year, session=session)

        path_base = path_generate(year, session)
        hansard_path = data_get_path(path_base, ListingType.Hansard, ListingClass.PARSE)
        inquiry_path = data_get_path(path_base, ListingType.Inquiry, ListingClass.PARSE)

        assert archive_exists(hansard_path, inquiry_path)

        import_hansard(
            year,
            session,
            [target for target in os.scandir(hansard_path) if target.is_file()],
        )
        import_inquiry(
            year,
            session,
            [target for target in os.scandir(inquiry_path) if target.is_file()],
        )


@transaction.atomic
def import_hansard(year: int, session: int, hansard_list: list[os.DirEntry]) -> None:
    for idx_file, _hansard_file in enumerate(hansard_list):
        logger.info(
            f"Importing hansard {idx_file + 1}/{len(hansard_list)}",
            path=_hansard_file.path,
        )
        with open(_hansard_file) as hansard_file:
            hansard = typedload.load(json.load(hansard_file), schema.Hansard)

        record = models.Hansard.objects.create(
            akn=hansard.akn,
        )
        record.present.add(*[import_person(person) for person in hansard.present])
        record.absent.add(*[import_person(person) for person in hansard.absent])
        record.guest.add(*[import_person(person) for person in hansard.guest])
        record.officer.add(*[import_person(person) for person in hansard.officer])

        for idx_debate, item in enumerate(hansard.debate):
            if isinstance(item, schema.Speech):
                speech = models.Speech.objects.create(
                    idx=idx_debate,
                    hansard=record,
                    by=import_person(item.by),
                    role=item.role,
                )
                for idx, content in enumerate(item.content):
                    models.SpeechContent.objects.create(
                        idx=idx,
                        speech=speech,
                        value=content.value,
                        type=content.type,
                        image=content.image,
                    )

            else:
                questions = models.QuestionSession.objects.create(
                    idx=idx_debate, hansard=record
                )

                for idx_session, item_session in enumerate(item.content):
                    if isinstance(item_session, schema.Question):
                        question = models.Question.objects.create(
                            idx=idx_session,
                            session=questions,
                            inquirer=import_person(item_session.inquirer),
                            role=item_session.role,
                            is_oral=item_session.is_oral,
                        )

                        for idx, content in enumerate(item_session.content):
                            models.QuestionContent.objects.create(
                                idx=idx,
                                question=question,
                                value=content.value,
                                type=content.type,
                                image=content.image,
                            )

                    else:
                        answer = models.Answer.objects.create(
                            idx=idx_session,
                            session=questions,
                            respondent=import_person(item_session.respondent),
                            role=item_session.role,
                        )

                        for idx, content in enumerate(item_session.content):
                            models.AnswerContent.objects.create(
                                idx=idx,
                                answer=answer,
                                value=content.value,
                                type=content.type,
                                image=content.image,
                            )

        record.save()


def import_inquiry(year: int, session: int, inquiry_list: list[os.DirEntry]) -> None:
    for idx_file, _inquiry_file in enumerate(inquiry_list):
        logger.info(
            f"Importing inquiry {idx_file + 1}/{len(inquiry_list)}",
            path=_inquiry_file.path,
        )
        with open(_inquiry_file) as inquiry_file:
            inquiry = typedload.load(json.load(inquiry_file), schema.Inquiry)

        assert inquiry.inquirer and inquiry.respondent

        record = models.Inquiry.objects.create(
            is_oral=inquiry.is_oral,
            inquirer=import_person(inquiry.inquirer),
            respondent=import_person(inquiry.respondent),
            number=inquiry.number,
            title=inquiry.title,
            akn=inquiry.akn,
        )

        for idx_list, item in enumerate(inquiry.inquiries):
            container_list = models.InquiryList.objects.create(
                idx=idx_list, inquiry=record
            )

            for idx, content in enumerate(item):
                models.InquiryContent.objects.create(
                    idx=idx,
                    container_list=container_list,
                    value=content.value,
                    type=content.type,
                    image=content.image,
                )

        for idx_list, item in enumerate(inquiry.responds):
            container_list = models.RespondList.objects.create(
                idx=idx_list, inquiry=record
            )

            for idx, content in enumerate(item):
                models.RespondContent.objects.create(
                    idx=idx,
                    container_list=container_list,
                    value=content.value,
                    type=content.type,
                    image=content.image,
                )


def import_person(person: schema.Person) -> models.Person:
    return models.Person.objects.get_or_create(
        identifier="".join(c.lower() for c in person.raw if c.isalpha()),
        defaults={
            "name": person.name,
            "raw": person.raw,
            "title": person.title,
            "area": person.area,
            "role": person.role,
        },
    )[0]