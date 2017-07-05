from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from survey.iterators import SurveyScheduleIterator


class NextMemberModelMixin(models.Model):

    survey_schedule_iterator = SurveyScheduleIterator

    @property
    def next(self):
        """Returns a household_member instance or None that is the
        cloned household_member instance in the next
        household_structure.
        """
        survey_schedule_iterator = self.survey_schedule_iterator(
            model_obj=self, internal_identifier=self.internal_identifier)
        return next(survey_schedule_iterator)

    @property
    def previous(self):
        """Returns a household_member instance or None that is the
        cloned household_member instance in the previous
        household_structure.
        """
        model_obj = None
        survey_schedule_object = self.survey_schedule_object
        while True:
            survey_schedule_object = survey_schedule_object.previous
            try:
                model_obj = self.__class__.objects.get(
                    internal_identifier=self.internal_identifier,
                    survey_schedule=survey_schedule_object.field_value)
            except ObjectDoesNotExist:
                continue
            except AttributeError:
                break
            else:
                break
        return model_obj
