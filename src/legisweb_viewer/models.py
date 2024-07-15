from itertools import chain

from django.db import models


class ContentElement(models.Model):
    idx = models.IntegerField()
    type = models.CharField()
    value = models.TextField()
    image = models.TextField(null=True)

    class Meta:
        abstract = True
        ordering = ["idx"]


class ContentElementList(models.Model):
    idx = models.IntegerField()

    class Meta:
        abstract = True
        ordering = ["idx"]


class Person(models.Model):
    name = models.CharField()
    raw = models.CharField()
    identifier = models.CharField(unique=True)
    title = models.JSONField(default=list)
    area = models.CharField(null=True)
    role = models.CharField(null=True)


class Inquiry(models.Model):
    is_oral = models.BooleanField()
    inquirer = models.ForeignKey(
        Person,
        related_name="inquirers",
        related_query_name="inquirer",
        on_delete=models.PROTECT,
    )
    respondent = models.ForeignKey(
        Person,
        related_name="respondents",
        related_query_name="respondent",
        on_delete=models.PROTECT,
    )
    number = models.IntegerField()
    title = models.CharField(null=True)
    akn = models.TextField()

    class Meta:
        ordering = ["number"]


class InquiryList(ContentElementList):
    inquiry = models.ForeignKey(
        Inquiry, related_name="inquiries", on_delete=models.PROTECT
    )


class InquiryContent(ContentElement):
    container_list = models.ForeignKey(
        InquiryList, related_name="content_list", on_delete=models.PROTECT
    )

    @property
    def inquirer(self) -> Person:
        return self.inquiry.inquirer

    @property
    def inquiry(self) -> Inquiry:
        return self.container_list.inquiry


class RespondList(ContentElementList):
    inquiry = models.ForeignKey(
        Inquiry, related_name="responds", on_delete=models.PROTECT
    )


class RespondContent(ContentElement):
    container_list = models.ForeignKey(
        RespondList, related_name="content_list", on_delete=models.PROTECT
    )

    @property
    def respondent(self) -> Person:
        return self.inquiry.respondent

    @property
    def inquiry(self) -> Inquiry:
        return self.container_list.inquiry


class Speech(ContentElementList):
    hansard = models.ForeignKey(
        "Hansard", related_name="speeches", on_delete=models.PROTECT
    )
    by = models.ForeignKey(Person, on_delete=models.PROTECT)
    role = models.CharField(null=True)


class QuestionSession(ContentElementList):
    hansard = models.ForeignKey(
        "Hansard", related_name="sessions", on_delete=models.PROTECT
    )


class Question(ContentElementList):
    session = models.ForeignKey(
        QuestionSession, related_name="questions", on_delete=models.PROTECT
    )

    inquirer = models.ForeignKey(Person, on_delete=models.PROTECT)
    role = models.CharField(null=True)
    is_oral = models.BooleanField()


class Answer(ContentElementList):
    session = models.ForeignKey(
        QuestionSession, related_name="answers", on_delete=models.PROTECT
    )
    respondent = models.ForeignKey(Person, on_delete=models.PROTECT)
    role = models.CharField(null=True)


class Hansard(models.Model):
    present = models.ManyToManyField(
        Person, related_name="hansard_presents", related_query_name="hansard_present"
    )
    absent = models.ManyToManyField(
        Person, related_name="hansard_absents", related_query_name="hansard_absent"
    )
    guest = models.ManyToManyField(
        Person, related_name="hansard_guests", related_query_name="hansard_guest"
    )
    officer = models.ManyToManyField(
        Person, related_name="hansard_officers", related_query_name="hansard_officer"
    )
    akn = models.TextField()

    @property
    def debate(self) -> list[Speech | QuestionSession]:
        return list(
            sorted(
                chain(
                    self.speeches.all(),  # type: ignore
                    self.sessions.all(),  # type: ignore
                ),
                key=lambda item: item.idx,
            )
        )


class SpeechContent(ContentElement):
    speech = models.ForeignKey(
        Speech, related_name="content_list", on_delete=models.PROTECT
    )

    @property
    def by(self) -> Person:
        return self.speech.by

    @property
    def hansard(self) -> Hansard:
        return self.speech.hansard


class QuestionContent(ContentElement):
    question = models.ForeignKey(
        Question, related_name="content_list", on_delete=models.PROTECT
    )

    @property
    def inquirer(self) -> Person:
        return self.question.inquirer

    @property
    def hansard(self) -> Hansard:
        return self.question.session.hansard


class AnswerContent(ContentElement):
    answer = models.ForeignKey(
        Answer, related_name="content_list", on_delete=models.PROTECT
    )

    @property
    def respondent(self) -> Person:
        return self.answer.respondent

    @property
    def hansard(self) -> Hansard:
        return self.answer.session.hansard
