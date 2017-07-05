from django.test import TestCase, tag
from faker import Faker
from survey.site_surveys import site_surveys
from survey.tests import SurveyTestHelper
from survey.tests.surveys import survey_two, survey_one, survey_three
from uuid import uuid4

from .models import HouseholdStructure, HouseholdMember, Household
from survey.iterators import SurveyScheduleIterator

fake = Faker()


class TestIterator(TestCase):

    survey_helper = SurveyTestHelper()

    def setUp(self):
        self.survey_helper.load_test_surveys(load_all=True)
        self.household = Household.objects.create()
        for survey_schedule in site_surveys.get_survey_schedules():
            try:
                HouseholdStructure.objects.get(
                    household=self.household,
                    survey_schedule=survey_schedule.field_value)
            except HouseholdStructure.DoesNotExist:
                HouseholdStructure.objects.create(
                    household=self.household,
                    survey_schedule=survey_schedule.field_value)

    def test_member_next(self):
        """Asserts gets next member in normal 1, 2 sequence.
        """
        internal_identifier = uuid4()
        for household_structure in HouseholdStructure.objects.all():
            HouseholdMember.objects.create(
                household_structure=household_structure,
                internal_identifier=internal_identifier)
        member1 = HouseholdMember.objects.get(
            survey_schedule=survey_one.field_value)
        member2 = HouseholdMember.objects.get(
            survey_schedule=survey_two.field_value)
        member_iterator = SurveyScheduleIterator(
            model_obj=member1, internal_identifier=internal_identifier)
        self.assertEqual(next(member_iterator), member2)

    def test_member_next2(self):
        """Asserts gets next member in 1, 3 sequence.
        """
        internal_identifier = uuid4()
        for household_structure in HouseholdStructure.objects.all():
            HouseholdMember.objects.create(
                household_structure=household_structure,
                internal_identifier=internal_identifier)
        member1 = HouseholdMember.objects.get(
            survey_schedule=survey_one.field_value)
        member2 = HouseholdMember.objects.get(
            survey_schedule=survey_two.field_value)
        member3 = HouseholdMember.objects.get(
            survey_schedule=survey_three.field_value)
        member2.delete()
        member_iterator = SurveyScheduleIterator(
            model_obj=member1, internal_identifier=internal_identifier)
        self.assertEqual(next(member_iterator), member3)

    def test_member_next3(self):
        """Asserts returns None if no "next" member.
        """
        internal_identifier = uuid4()
        for household_structure in HouseholdStructure.objects.all():
            HouseholdMember.objects.create(
                household_structure=household_structure,
                internal_identifier=internal_identifier)
        member1 = HouseholdMember.objects.get(
            survey_schedule=survey_one.field_value)
        member2 = HouseholdMember.objects.get(
            survey_schedule=survey_two.field_value)
        member3 = HouseholdMember.objects.get(
            survey_schedule=survey_three.field_value)
        member2.delete()
        member3.delete()
        member_iterator = SurveyScheduleIterator(
            model_obj=member1, internal_identifier=internal_identifier)
        self.assertRaises(StopIteration, next, member_iterator)

    def test_members_list(self):
        """Asserts returns None if no "next" member.
        """
        internal_identifier = uuid4()
        for household_structure in HouseholdStructure.objects.all():
            HouseholdMember.objects.create(
                household_structure=household_structure,
                internal_identifier=internal_identifier)
        member1 = HouseholdMember.objects.get(
            survey_schedule=survey_one.field_value)
        member2 = HouseholdMember.objects.get(
            survey_schedule=survey_two.field_value)
        member3 = HouseholdMember.objects.get(
            survey_schedule=survey_three.field_value)
        iterable = SurveyScheduleIterator(
            model_obj=member1, internal_identifier=internal_identifier)
        self.assertEqual(list(iterable), [member2, member3])
        self.assertRaises(StopIteration, next, iterable)

    def test_member_previous(self):
        """Asserts gets next member in normal 1, 2 sequence.
        """
        internal_identifier = uuid4()
        for household_structure in HouseholdStructure.objects.all():
            HouseholdMember.objects.create(
                household_structure=household_structure,
                internal_identifier=internal_identifier)
        member1 = HouseholdMember.objects.get(
            survey_schedule=survey_one.field_value)
        member2 = HouseholdMember.objects.get(
            survey_schedule=survey_two.field_value)
        member_iterator = SurveyScheduleIterator(
            model_obj=member1, internal_identifier=internal_identifier)
        self.assertEqual(next(member_iterator), member2)

    def test_member_next_from_model(self):
        """Asserts gets next member in normal 1, 2 sequence.
        """
        internal_identifier = uuid4()
        for household_structure in HouseholdStructure.objects.all():
            HouseholdMember.objects.create(
                household_structure=household_structure,
                internal_identifier=internal_identifier)
        member1 = HouseholdMember.objects.get(
            survey_schedule=survey_one.field_value)
        member2 = HouseholdMember.objects.get(
            survey_schedule=survey_two.field_value)
        self.assertEqual(member2, member1.next)

    def test_member_previous_from_member_2_to_1(self):
        internal_identifier = uuid4()
        for household_structure in HouseholdStructure.objects.all():
            HouseholdMember.objects.create(
                household_structure=household_structure,
                internal_identifier=internal_identifier)
        member1 = HouseholdMember.objects.get(
            survey_schedule=survey_one.field_value)
        member2 = HouseholdMember.objects.get(
            survey_schedule=survey_two.field_value)
        HouseholdMember.objects.get(
            survey_schedule=survey_three.field_value)
        self.assertEqual(member1, member2.previous)

    @tag('1')
    def test_member_previous_from_member_3_to_2(self):
        internal_identifier = uuid4()
        for household_structure in HouseholdStructure.objects.all():
            HouseholdMember.objects.create(
                household_structure=household_structure,
                internal_identifier=internal_identifier)
        HouseholdMember.objects.get(
            survey_schedule=survey_one.field_value)
        member2 = HouseholdMember.objects.get(
            survey_schedule=survey_two.field_value)
        member3 = HouseholdMember.objects.get(
            survey_schedule=survey_three.field_value)
        self.assertEqual(member2, member3.previous)

    @tag('1')
    def test_member_previous_from_member_1_to_none(self):
        """Asserts returns None if no previous.
        """
        internal_identifier = uuid4()
        for household_structure in HouseholdStructure.objects.all():
            HouseholdMember.objects.create(
                household_structure=household_structure,
                internal_identifier=internal_identifier)
        member1 = HouseholdMember.objects.get(
            survey_schedule=survey_one.field_value)
        HouseholdMember.objects.get(
            survey_schedule=survey_two.field_value)
        HouseholdMember.objects.get(
            survey_schedule=survey_three.field_value)
        self.assertEqual(None, member1.previous)

    @tag('1')
    def test_member_previous_skips_over_none(self):
        """Asserts skips from 3 to 1 if 2 does not exist.
        """
        internal_identifier = uuid4()
        for household_structure in HouseholdStructure.objects.all():
            HouseholdMember.objects.create(
                household_structure=household_structure,
                internal_identifier=internal_identifier)
        member1 = HouseholdMember.objects.get(
            survey_schedule=survey_one.field_value)
        member2 = HouseholdMember.objects.get(
            survey_schedule=survey_two.field_value)
        member2.delete()
        member3 = HouseholdMember.objects.get(
            survey_schedule=survey_three.field_value)
        self.assertEqual(member1, member3.previous)
