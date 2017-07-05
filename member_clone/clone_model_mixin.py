import arrow

from dateutil.relativedelta import relativedelta
from django.db import models, transaction

from edc_base.utils import age, get_utcnow
from edc_constants.choices import YES_NO_NA, ALIVE
from edc_registration.models import RegisteredSubject

from .choices import DETAILS_CHANGE_REASON
from .constants import HEAD_OF_HOUSEHOLD
from .clone import CloneMembersExistError


class CloneRegisteredSubjectError(Exception):
    pass


class CloneReportDatetimeError(Exception):
    pass


class CloneModelMixin(models.Model):

    cloned = models.BooleanField(
        default=False,
        editable=False,
        help_text=(
            'This instance was initially created by copying member information '
            'from a previous survey.')
    )

    cloned_datetime = models.DateTimeField(
        editable=False,
        null=True)

    personal_details_changed = models.CharField(
        verbose_name=(
            'Have your personal details (name/surname) changed since the '
            'last time we visited you?'),
        max_length=10,
        null=True,
        blank=False,
        choices=YES_NO_NA,
        help_text=('personal details (name/surname)'))

    details_change_reason = models.CharField(
        verbose_name=('If YES, please specify the reason'),
        max_length=30,
        null=True,
        blank=True,
        choices=DETAILS_CHANGE_REASON,
        help_text=('if personal detail changed indicate the reason.'))

    @property
    def clone_updated(self):
        """Returns True if the cloned member instance has been updated.

        Uses `personal_details_changed` as a surrogate value.
        """
        if self.cloned:
            if not self.personal_details_changed:
                return False
        return True

    def clone(self, household_structure, report_datetime, **kwargs):
        """Returns a new unsaved household member instance.

            * household_structure: the 'next' household_structure to
              which the new members will be related.
        """
        with transaction.atomic():
            try:
                self.__class__.objects.get(
                    internal_identifier=self.internal_identifier,
                    household_structure=household_structure)
            except self.__class__.DoesNotExist:
                pass
            else:
                raise CloneMembersExistError(
                    'Cannot clone a household member into a survey '
                    'where the member already exists')
        with transaction.atomic():
            try:
                registered_subject = RegisteredSubject.objects.get(
                    registration_identifier=self.internal_identifier.hex)
            except RegisteredSubject.DoesNotExist:
                raise CloneRegisteredSubjectError(
                    'RegisteredSubject instance unexpectedly missing when '
                    'cloning member! Got internal identifier = {}.'.format(
                        self.internal_identifier))
            else:
                if not registered_subject.dob:
                    born = (self.report_datetime
                            - relativedelta(years=self.age_in_years))
                    age_in_years = age(born, report_datetime).years
                else:
                    age_in_years = age(
                        registered_subject.dob, report_datetime).years

        start = household_structure.survey_schedule_object.rstart
        end = household_structure.survey_schedule_object.rend
        rdate = arrow.Arrow.fromdatetime(
            report_datetime, report_datetime.tzinfo)

        if not (start.to('utc').date()
                <= rdate.to('utc').date()
                <= end.to('utc').date()):
            raise CloneReportDatetimeError(
                'Invalid report datetime. \'{}\' does not fall within '
                'the date range for survey schedule \'{}\'. Expected any date '
                'from \'{}\' to \'{}\'.'.format(
                    report_datetime.strftime('%Y-%m-%d %Z'),
                    household_structure.survey_schedule_object.field_value,
                    start.to('utc').strftime('%Y-%m-%d %Z'),
                    end.to('utc').strftime('%Y-%m-%d %Z')))
        return self.__class__(
            household_structure=household_structure,
            report_datetime=report_datetime,
            first_name=self.first_name,
            initials=self.initials,
            gender=self.gender,
            survival_status=ALIVE if not self.survival_status else self.survival_status,
            age_in_years=age_in_years,
            relation=None if self.relation == HEAD_OF_HOUSEHOLD else self.relation,
            internal_identifier=self.internal_identifier,
            subject_identifier=self.subject_identifier,
            subject_identifier_as_pk=self.subject_identifier_as_pk,
            cloned=True,
            cloned_datetime=get_utcnow(),
            personal_details_changed=None,
            survey_schedule=household_structure.survey_schedule,
            user_created=kwargs.get('user_created', self.user_created),
        )

    class Meta:
        abstract = True
