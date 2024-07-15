from django_opensearch_dsl import Document, fields
from django_opensearch_dsl.registries import registry

from .models import (
    AnswerContent,
    Inquiry,
    InquiryContent,
    QuestionContent,
    RespondContent,
    SpeechContent,
)


@registry.register_document
class InquiryTitleDocument(Document):
    inquirer = fields.ObjectField(
        properties={"name": fields.TextField(), "raw": fields.TextField()}
    )
    respondent = fields.ObjectField(
        properties={"name": fields.TextField(), "raw": fields.TextField()}
    )

    class Index:
        name = "inquiry-title"

    class Django:
        model = Inquiry
        fields = ["id", "title", "number", "is_oral"]


@registry.register_document
class InquiryContentDocument(Document):
    inquirer = fields.ObjectField(
        properties={"name": fields.TextField(), "raw": fields.TextField()}
    )
    inquiry = fields.ObjectField(
        properties={
            "title": fields.TextField(),
            "id": fields.IntegerField(),
            "number": fields.IntegerField(),
            "is_oral": fields.BooleanField(),
        }
    )

    class Index:
        name = "inquiry"

    class Django:
        model = InquiryContent
        fields = ["id", "value"]


@registry.register_document
class RespondContentDocument(Document):
    respondent = fields.ObjectField(
        properties={"name": fields.TextField(), "raw": fields.TextField()}
    )
    inquiry = fields.ObjectField(
        properties={
            "title": fields.TextField(),
            "id": fields.IntegerField(),
            "number": fields.IntegerField(),
            "is_oral": fields.BooleanField(),
        }
    )

    class Index:
        name = "respond"

    class Django:
        model = RespondContent
        fields = ["id", "value"]


@registry.register_document
class SpeechContentDocument(Document):
    by = fields.ObjectField(
        properties={"name": fields.TextField(), "raw": fields.TextField()}
    )
    hansard = fields.ObjectField(properties={"id": fields.IntegerField()})

    class Index:
        name = "speech"

    class Django:
        model = SpeechContent
        fields = ["id", "value"]


@registry.register_document
class QuestionContentDocument(Document):
    inquirer = fields.ObjectField(
        properties={"name": fields.TextField(), "raw": fields.TextField()}
    )
    hansard = fields.ObjectField(properties={"id": fields.IntegerField()})

    class Index:
        name = "question"

    class Django:
        model = QuestionContent
        fields = ["id", "value"]


@registry.register_document
class AnswerContentDocument(Document):
    respondent = fields.ObjectField(
        properties={"name": fields.TextField(), "raw": fields.TextField()}
    )
    hansard = fields.ObjectField(properties={"id": fields.IntegerField()})

    class Index:
        name = "answer"

    class Django:
        model = AnswerContent
        fields = ["id", "value"]