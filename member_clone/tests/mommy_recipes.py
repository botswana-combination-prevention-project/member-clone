# coding=utf-8

from faker import Faker
from model_mommy.recipe import Recipe

from edc_base.utils import get_utcnow
from edc_constants.constants import FEMALE

from .models import HouseholdMember


fake = Faker()


householdmember = Recipe(
    HouseholdMember,
    report_datetime=get_utcnow,
    first_name=fake.first_name,
    age_in_years=25,
    gender=FEMALE,
    relation='cousin',
)
