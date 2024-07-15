from abc import ABC
from typing import Any, Literal

from rest_flex_fields import FlexFieldsModelSerializer
from rest_framework import serializers

from legisweb_viewer.documents import (
    AnswerContentDocument,
    InquiryContentDocument,
    InquiryTitleDocument,
    QuestionContentDocument,
    RespondContentDocument,
    SpeechContentDocument,
)
from legisweb_viewer.models import (
    Answer,
    AnswerContent,
    Hansard,
    Inquiry,
    InquiryContent,
    InquiryList,
    Person,
    Question,
    QuestionContent,
    QuestionSession,
    RespondContent,
    RespondList,
    Speech,
    SpeechContent,
)


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            "id",
            "name",
            "raw",
            "identifier",
            "title",
            "area",
            "role",
        ]


class InquiryContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InquiryContent
        fields = ["id", "value", "type", "image"]


class InquiryListSerializer(serializers.ModelSerializer):
    content_list = InquiryContentSerializer(many=True, read_only=True)

    class Meta:
        model = InquiryList
        fields = ["id", "content_list"]


class RespondContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RespondContent
        fields = ["id", "value", "type", "image"]


class RespondListSerializer(serializers.ModelSerializer):
    content_list = RespondContentSerializer(many=True, read_only=True)

    class Meta:
        model = RespondList
        fields = ["id", "content_list"]


class InquirySerializer(FlexFieldsModelSerializer):
    inquirer = PersonSerializer(many=False, read_only=True)
    respondent = PersonSerializer(many=False, read_only=True)

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "is_oral",
            "number",
            "title",
            "inquirer",
            "respondent",
        ]
        expandable_fields = {
            "inquiries": (InquiryListSerializer, {"many": True, "read_only": True}),
            "responds": (RespondListSerializer, {"many": True, "read_only": True}),
        }


class AnswerContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerContent
        fields = ["id", "value", "type", "image"]


class AnswerSerializer(serializers.ModelSerializer):
    content_list = AnswerContentSerializer(many=True, read_only=True)
    respondent = PersonSerializer(many=False, read_only=True)

    class Meta:
        model = Answer
        fields = ["content_list", "respondent", "role"]


class QuestionContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionContent
        fields = ["id", "value", "type", "image"]


class QuestionSerializer(serializers.ModelSerializer):
    content_list = QuestionContentSerializer(many=True, read_only=True)
    inquirer = PersonSerializer(many=False, read_only=True)

    class Meta:
        model = Question
        fields = ["content_list", "inquirer", "role", "is_oral"]


class QuestionSessionSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionSession
        fields = ["questions", "answers"]


class SpeechContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeechContent
        fields = ["id", "value", "type", "image"]


class SpeechSerializer(serializers.ModelSerializer):
    by = PersonSerializer(many=False, read_only=True)
    content_list = SpeechContentSerializer(many=True, read_only=True)

    class Meta:
        model = Speech
        fields = ["by", "role", "content_list"]


class DebateSerializer(serializers.BaseSerializer):
    def to_representation(self, instance: Speech | QuestionSession) -> dict[Any, Any]:
        return {
            "type": type(instance).__name__,
            "value": (
                SpeechSerializer(instance, many=False, read_only=True)
                if isinstance(instance, Speech)
                else QuestionSessionSerializer(instance, many=False, read_only=True)
            ).data,
        }


class HansardSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = Hansard
        fields = ["id"]
        expandable_fields = {
            "present": (PersonSerializer, {"many": True, "read_only": True}),
            "absent": (PersonSerializer, {"many": True, "read_only": True}),
            "guest": (PersonSerializer, {"many": True, "read_only": True}),
            "debate": (DebateSerializer, {"many": True, "read_only": True}),
        }

class ContentElementSearchSerializer(serializers.BaseSerializer, ABC):
    parent_type: Literal["inquiry"] | Literal["hansard"]
    document_type: (
        Literal["inquiry"]
        | Literal["respond"]
        | Literal["question"]
        | Literal["answer"]
        | Literal["speech"]
    )

    def _person(
        self,
        instance: InquiryContentDocument
        | RespondContentDocument
        | SpeechContentDocument
        | QuestionContentDocument
        | AnswerContentDocument,
    ) -> Any:
        result = None

        match self.document_type:
            case "inquiry" | "question":
                result = instance.inquirer

            case "respond" | "answer":
                result = instance.respondent

            case "speech":
                result = instance.by

        return result

    def _parent_id(self, instance) -> str:
        return getattr(
            instance, "inquiry" if self.parent_type == "inquiry" else "hansard"
        ).id

    def to_representation(
        self,
        instance: InquiryContentDocument
        | RespondContentDocument
        | SpeechContentDocument
        | QuestionContentDocument
        | AnswerContentDocument,
    ) -> dict[Any, Any]:
        return {
            self.parent_type: {"id": self._parent_id(instance)}
            if self.parent_type == "hansard"
            else {
                "id": self._parent_id(instance),
                "number": instance.inquiry.number,
                "is_oral": instance.inquiry.is_oral,
                "title": instance.inquiry.title,
            },
            "document_type": self.document_type,
            "content": {
                "id": instance.id,
                "highlight": " ".join(instance.meta.highlight.get("value", "")).strip()
                or None,
                "value": instance.value,
            },
            "person": {
                "name": self._person(instance).name,
                "raw": self._person(instance).raw,
            },
            "meta": instance.meta.to_dict(),
        }


class InquiryContentSearchSerializer(ContentElementSearchSerializer):
    parent_type = "inquiry"
    document_type = "inquiry"


class RespondContentSearchSerializer(ContentElementSearchSerializer):
    parent_type = "inquiry"
    document_type = "respond"


class SpeechContentSearchSerializer(ContentElementSearchSerializer):
    parent_type = "hansard"
    document_type = "speech"


class QuestionContentSearchSerializer(ContentElementSearchSerializer):
    parent_type = "hansard"
    document_type = "question"


class AnswerContentSearchSerializer(ContentElementSearchSerializer):
    parent_type = "hansard"
    document_type = "answer"


class InquiryTitleSearchSerializer(serializers.BaseSerializer):
    def to_representation(self, instance: InquiryTitleDocument) -> dict[Any, Any]:
        return {
            "content": {
                "title": instance.title,
                "highlight": instance.meta.highlight.get("value", "").strip() or None,
                "number": instance.number,
                "is_oral": instance.is_oral,
                "id": instance.id,
            },
            "document_type": "inquiry-title",
            "inquirer": {
                "name": instance.inquirer.name,
                "raw": instance.inquirer.raw,
            },
            "respondent": {
                "name": instance.respondent.name,
                "raw": instance.respondent.raw,
            },
            "meta": instance.meta.to_dict(),
        }