from faker import Faker
from dateutil.relativedelta import relativedelta
from uuid import uuid4
from django.test import TestCase, tag
from model_mommy import mommy

from edc_constants.constants import YES
from edc_registration.models import RegisteredSubject
from survey.iterators import SurveyScheduleIterator
from survey.site_surveys import site_surveys
from survey.tests import SurveyTestHelper
from survey.tests.surveys import survey_one, survey_two, survey_three

from ..clone import Clone, CloneMembersExistError, CloneAmbiguousOptionsError
from ..model_mixins import CloneRegisteredSubjectError, CloneReportDatetimeError
from .models import HouseholdMember, HouseholdStructure, Household

fake = Faker()


@tag('clone')
class TestCloneMembers(TestCase):

    survey_helper = SurveyTestHelper()

    def setUp(self):
        self.survey_helper.load_test_surveys(load_all=True)
        self.household = Household.objects.create()

        for survey_schedule in site_surveys.get_survey_schedules():
            HouseholdStructure.objects.create(
                household=self.household,
                survey_schedule=survey_schedule)

        self.first_household_structure = HouseholdStructure.objects.get(
            household=self.household, survey_schedule=survey_one.field_value)
        for _ in range(0, 3):
            subject_identifier = fake.credit_card_number()
            subject_identifier_as_pk = uuid4().hex
            internal_identifier = uuid4().hex
            RegisteredSubject.objects.create(
                subject_identifier=subject_identifier,
                registration_identifier=internal_identifier)
            mommy.make_recipe(
                'member_clone.tests.householdmember',
                household_structure=self.first_household_structure,
                subject_identifier=subject_identifier,
                subject_identifier_as_pk=subject_identifier_as_pk,
                internal_identifier=internal_identifier,
                report_datetime=survey_one.start)

    def test_clone_members_ambiguous_options_raises(self):
        next_household_structure = self.first_household_structure.next
        self.assertRaises(
            CloneAmbiguousOptionsError,
            Clone,
            household=self.household,
            household_structure=next_household_structure,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')

    def test_clone_members_ambiguous_options_raises2(self):
        next_household_structure = self.first_household_structure.next
        self.assertRaises(
            CloneAmbiguousOptionsError,
            Clone,
            household_structure=next_household_structure,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')

    def test_clone_members_with_model_as_cls(self):
        next_household_structure = self.first_household_structure.next
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model=HouseholdMember)
        self.assertEqual(clone.members.filter(
            survey_schedule=survey_two.field_value).count(), 3)

    def test_clone_members_with_householdstructure_as_option(self):
        next_household_structure = self.first_household_structure.next
        clone = Clone(
            household_structure=self.first_household_structure.next,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')
        self.assertEqual(clone.members.filter(
            survey_schedule=survey_two.field_value).count(), 3)

    def test_clone_members_with_household_as_option(self):
        next_household_structure = self.first_household_structure.next
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')
        self.assertEqual(clone.members.filter(
            survey_schedule=survey_two.field_value).count(), 3)

    def test_attempt_to_reclone_existing_members_raises(self):
        next_household_structure = self.first_household_structure.next
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')
        self.assertEqual(clone.members.filter(
            survey_schedule=survey_two.field_value).count(), 3)
        self.assertRaises(
            CloneMembersExistError,
            Clone,
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')

    def test_attempt_to_reclone_existing_members_raises2(self):
        next_household_structure = self.first_household_structure.next
        report_datetime = next_household_structure.survey_schedule_object.start
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=report_datetime,
            model='member_clone.householdmember')
        member = HouseholdMember.objects.get(id=clone.members[0].id)
        self.assertRaises(
            CloneMembersExistError,
            member.clone,
            household_structure=next_household_structure,
            report_datetime=report_datetime)

    def test_clone_members_but_have_no_previous(self):
        """Asserts returns [] if no previous members to clone;
        that is, does not create members if no previous ones exist.
        """
        HouseholdMember.objects.all().delete()
        next_household_structure = self.first_household_structure.next
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model=HouseholdMember)
        self.assertEqual(clone.members.filter(
            survey_schedule=survey_two.field_value).count(), 0)
        self.assertEqual(HouseholdMember.objects.all().count(), 0)

    def test_clone_members_but_have_no_previous2(self):
        """Asserts returns [] if no previous members to clone;
        that is, does not create members if no previous ones exist.
        """
        HouseholdMember.objects.all().delete()
        next_household_structure = self.first_household_structure.next
        next_household_structure = next_household_structure.next
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model=HouseholdMember)
        self.assertEqual(clone.members.filter(
            survey_schedule=survey_two.field_value).count(), 0)
        self.assertEqual(HouseholdMember.objects.all().count(), 0)

    def test_clone_members_but_have_no_registered_subject(self):
        RegisteredSubject.objects.all().delete()
        next_household_structure = self.first_household_structure.next
        self.assertRaises(
            CloneRegisteredSubjectError,
            Clone,
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model=HouseholdMember)

    def test_clone_members_but_have_no_registered_subject_dob(self):
        for obj in RegisteredSubject.objects.all():
            obj.dob = None
            obj.save()
        for obj in HouseholdMember.objects.all():
            obj.age_in_years = 25
            obj.save()
        next_household_structure = self.first_household_structure.next
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model=HouseholdMember)
        self.assertEqual(
            [obj.age_in_years for obj in clone.members], [26, 26, 26])

    def test_clone_members_but_have_no_member_age_in_years(self):
        for member in HouseholdMember.objects.all():
            rs = RegisteredSubject.objects.get(
                registration_identifier=member.internal_identifier.hex)
            rs.dob = (member.report_datetime
                      - relativedelta(years=member.age_in_years)).date()
            rs.save()
            member.age_in_years = None
            member.save()
        next_household_structure = self.first_household_structure.next
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model=HouseholdMember)
        self.assertEqual(
            [obj.age_in_years for obj in clone.members], [26, 26, 26])

    def test_clone_members_to_last_household_structure(self):
        for household_structure in SurveyScheduleIterator(
                model_obj=self.first_household_structure, household=self.household):
            pass
        clone = Clone(
            household=self.household,
            survey_schedule=household_structure.survey_schedule_object,
            report_datetime=household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')
        self.assertEqual(clone.members.filter(
            survey_schedule=survey_three.field_value).count(), 3)

    def test_clone_members_attrs(self):
        next_household_structure = self.first_household_structure.next
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')
        for member in clone.members.all():
            self.assertIsNotNone(member.first_name)
            self.assertIsNotNone(member.gender)
            self.assertIsNotNone(member.age_in_years)
            self.assertIsNotNone(member.internal_identifier)
            self.assertIsNotNone(member.subject_identifier)
            self.assertIsNotNone(member.subject_identifier_as_pk)
            self.assertTrue(member.cloned)
            self.assertIsNotNone(member.cloned_datetime)
            self.assertFalse(member.personal_details_changed)

    def test_clone_members_attr_clone_updated(self):
        next_household_structure = self.first_household_structure.next
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')
        for member in clone.members.all():
            self.assertFalse(member.clone_updated)

    def test_clone_members_attr_clone_updated_sets_to_true(self):
        next_household_structure = self.first_household_structure.next
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')
        for member in clone.members.all():
            member.personal_details_changed = YES
            member.save()
        for member in clone.members.all():
            self.assertTrue(member.clone_updated)

    def test_clone_members_create(self):
        next_household_structure = self.first_household_structure.next
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model='member_clone.householdmember',
            create=False)
        # returns a list of non-persisted model instances
        for member in clone.members:
            member.save()

    def test_clone_members_internal_identifier(self):
        # get members from enumerated household_structure
        household_structure = self.household.householdstructure_set.get(
            survey_schedule=survey_one.field_value)
        members = HouseholdMember.objects.filter(
            household_structure=household_structure)
        members_internal_identifiers = [m.internal_identifier for m in members]
        members_internal_identifiers.sort()

        next_household_structure = self.first_household_structure.next
        # clone members from enumerated household_structure
        clone = Clone(
            household=self.household,
            survey_schedule=next_household_structure.survey_schedule_object,
            report_datetime=next_household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')
        new_members_internal_identifiers = [
            m.internal_identifier for m in clone.members.all()]
        new_members_internal_identifiers.sort()
        self.assertEqual(
            members_internal_identifiers, new_members_internal_identifiers)

    def test_next_household_member(self):
        household_member = self.first_household_structure.householdmember_set.all().first()
        household_structure = self.first_household_structure.next
        Clone(
            household_structure=household_structure,
            report_datetime=household_structure.survey_schedule_object.start,
            model='member_clone.householdmember')
        try:
            next_household_member = HouseholdMember.objects.get(
                household_structure=household_structure,
                internal_identifier=household_member.internal_identifier)
        except HouseholdMember.DoesNotExist:
            self.fail('HouseholdMember.DoesNotExist unexpectedly raised. '
                      'household_structure={}'.format(household_structure))
        self.assertEqual(next_household_member, household_member.next)

    def test_next_household_member2(self):
        household_structure = HouseholdStructure.objects.get(
            household=self.household,
            survey_schedule=survey_one.field_value)
        Clone(
            household_structure=household_structure.next,
            report_datetime=household_structure.next.survey_schedule_object.next.start,
            model='member_clone.householdmember')
        for household_member in household_structure.householdmember_set.all():
            self.assertEqual(
                household_member.internal_identifier,
                household_member.next.internal_identifier)
            self.assertNotEqual(household_member.pk, household_member.next.pk)

    def test_clone_bad_report_datetime_in_new_survey_schedule(self):
        household_structure = HouseholdStructure.objects.get(
            household=self.household,
            survey_schedule=survey_one.field_value)
        report_datetime = (household_structure.survey_schedule_object.next.start
                           - relativedelta(days=1))
        self.assertRaises(
            CloneReportDatetimeError,
            Clone,
            household_structure=household_structure.next,
            report_datetime=report_datetime,
            model='member_clone.householdmember')

    def test_clone_good_report_datetime_in_new_survey_schedule(self):
        household_structure = HouseholdStructure.objects.get(
            household=self.household,
            survey_schedule=survey_one.field_value)
        report_datetime = household_structure.survey_schedule_object.next.start
        try:
            Clone(
                household_structure=household_structure.next,
                report_datetime=report_datetime,
                model='member_clone.householdmember')
        except CloneReportDatetimeError:
            self.fail('CloneModelError unexpectedly raised')

    def test_household_member_internal_identifier(self):
        household_structure = HouseholdStructure.objects.get(
            household=self.household,
            survey_schedule=survey_one.field_value)
        household_member = household_structure.householdmember_set.all().first()
        self.assertIsNotNone(household_member.internal_identifier)
