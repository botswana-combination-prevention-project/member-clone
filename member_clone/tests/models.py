from django.db import models
from uuid import uuid4

from edc_base.model_mixins import BaseUuidModel
from edc_base.utils import get_utcnow
from survey.iterators import SurveyScheduleIterator
from survey.model_mixins import SurveyScheduleModelMixin

from ..model_mixins import CloneModelMixin, NextMemberModelMixin


class Household(BaseUuidModel):

    household_identifier = models.CharField(max_length=25, default=uuid4)


class HouseholdStructure(SurveyScheduleModelMixin, BaseUuidModel):

    household = models.ForeignKey(Household)

    @property
    def next(self):
        """Returns the next household structure instance or None in
        the survey_schedule sequence."""
        try:
            next_obj = next(SurveyScheduleIterator(
                model_obj=self, household=self.household))
        except StopIteration:
            next_obj = None
        return next_obj


class HouseholdMember(SurveyScheduleModelMixin, CloneModelMixin,
                      NextMemberModelMixin, BaseUuidModel):

    household_structure = models.ForeignKey(HouseholdStructure)

    internal_identifier = models.UUIDField()

    report_datetime = models.DateTimeField(default=get_utcnow)

    subject_identifier = models.CharField(max_length=25, null=True)

    subject_identifier_as_pk = models.CharField(max_length=25, null=True)

    relation = models.CharField(max_length=25, null=True)

    first_name = models.CharField(max_length=25, null=True)

    initials = models.CharField(max_length=25, null=True)

    survival_status = models.CharField(max_length=25, null=True)

    gender = models.CharField(max_length=25, null=True)

    age_in_years = models.IntegerField(null=True)

    relation = models.CharField(max_length=25, null=True)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.survey_schedule})'

    def save(self, *args, **kwargs):
        self.survey_schedule = self.household_structure.survey_schedule
        super().save(*args, **kwargs)
