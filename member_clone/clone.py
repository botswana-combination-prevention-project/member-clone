from django.apps import apps as django_apps


class CloneAmbiguousOptionsError(Exception):
    pass


class CloneMembersExistError(Exception):
    pass


class Clone:

    model = 'member.householdmember'

    def __init__(self, household=None, survey_schedule=None, report_datetime=None,
                 household_structure=None, create=None, model=None):
        """Clone household members for a new survey_schedule.

            * survey_schedule: adds new members for this survey_schedule.
        """
        self.model = model or self.model
        create = True if create is None else create
        if household and household_structure:
            raise CloneAmbiguousOptionsError(
                'Ambiguous. Either specify household or household_structure, not both')
        if survey_schedule and household_structure:
            raise CloneAmbiguousOptionsError(
                'Ambiguous. Either specify survey_schedule or household_structure, not both')
        try:
            self.household = household_structure.household
            self.survey_schedule = household_structure.survey_schedule_object
        except AttributeError:
            self.household = household
            self.survey_schedule = survey_schedule
        self.report_datetime = report_datetime
        self.members = self.clone(create=create)

    def clone(self, create=None):
        """Returns a queryset or list of household_members, depending on `create`.

            * create: Default: True

        If created=True, returns a QuerySet, else a list of non-persisted
        model instances.
        """
        household_members = []
        self.safe_to_clone_or_raise()
        household_structure = self.household.householdstructure_set.get(
            survey_schedule=self.survey_schedule.field_value)

        survey_schedule = self.survey_schedule.previous
        while survey_schedule:
            previous_household_structure = self.household.householdstructure_set.get(
                survey_schedule=survey_schedule.field_value)
            previous_members = previous_household_structure.householdmember_set.all()
            for obj in previous_members:
                new_obj = obj.clone(
                    household_structure=household_structure,
                    report_datetime=self.report_datetime,
                    user_created=household_structure.user_created)
                if create:
                    new_obj.save()
                else:
                    household_members.append(new_obj)
            if previous_members.count() > 0:
                break
            else:
                survey_schedule = survey_schedule.previous
        if create:
            return self.model_cls.objects.filter(
                household_structure__household=self.household,
                survey_schedule=self.survey_schedule.field_value)
        return household_members

    def safe_to_clone_or_raise(self):
        current = self.household.householdstructure_set.get(
            survey_schedule=self.survey_schedule.field_value)
        if current.householdmember_set.all().count() > 0:
            raise CloneMembersExistError(
                'Cannot clone household. Members already exist in '
                'household for {}.'.format(self.survey_schedule))

    @property
    def model_cls(self):
        try:
            return django_apps.get_model(*self.model.split('.'))
        except AttributeError:
            return self.model
