import datetime
from django.contrib.auth import get_user_model
from django.forms import CharField, BoundField, CheckboxInput
from django.http import QueryDict
from django.test import TestCase

from grid.fields import YearBasedIntegerField
from grid.forms.deal_spatial_form import DealSpatialForm
from grid.templatetags.custom_tags import *
from landmatrix.models import HistoricalActivity


class CustomTagsTestCase(TestCase):

    fixtures = [
        'countries_and_regions',
        'users_and_groups',
        'status',
        'activities',
    ]

    def test_ensure_list(self):
        self.assertEqual(['a', ], ensure_list('a'))
        self.assertEqual(['a', ], ensure_list(['a', ]))

    def test_get_fields_display(self):
        form = DealSpatialForm(initial={'target_country': '116'})
        user = get_user_model().objects.get(username='reporter')
        expected = [
            {'name': 'tg', 'label': '', 'value': 'Location'},
            {'name': 'target_country', 'label': 'Target country', 'value': 'Cambodia'}
        ]
        self.assertEqual(expected, get_fields_display(form, user))

    def test_get_display_values(self):
        value = [
            'on:2000|off:2010',
            'on:2020',
            'on'
        ]
        expected = [
            '[2000]True',
            '[2010]False',
            '[2020] True',
            'True',
        ]
        self.assertEqual(expected, get_display_values(value, BooleanField()))

    def test_get_display_value_by_field_with_multi_value_field(self):
        field = YearBasedIntegerField()
        self.assertEqual('1:2010:', get_display_value_by_field(field, '1:2010:'))

    def test_get_display_value_by_field_with_choice_field(self):
        field = YearBasedIntegerField()
        self.assertEqual('1:2010:', get_display_value_by_field(field, '1:2010:'))

    def test_get_display_value_by_field_with_multiple_choice_field(self):
        choices = (
            ('value1', 'label1', None),
            ('value2', 'label2', (
                ('value2.1', 'label2.1'),
                ('value2.2', 'label2.2'),
            )),
        )
        field = NestedMultipleChoiceField(choices=choices)
        self.assertEqual(['value1', 'value2.1'], get_display_value_by_field(field, ['value1', 'value2.1']))

    def test_get_display_value_by_field_with_boolean_field(self):
        field = BooleanField()
        self.assertEqual('True', get_display_value_by_field(field, 'on'))

    def test_get_value_from_choices_dict(self):
        self.assertEqual('One', get_value_from_choices_dict({1: 'One', 2: 'Two'}, '1'))
        self.assertEqual('value1', get_value_from_choices_dict({'value1': 'label1', 'value2': 'label2'}, 'value1'))

    def test_naturaltime_from_string(self):
        value = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.assertRegexpMatches(naturaltime_from_string(value), r'(now|seconds ago)$')

    def test_add_or_update_param(self):
        params = QueryDict('key1=value1')
        self.assertEqual('key1=value1&key2=value2', add_or_update_param(params, 'key2', 'value2'))

    def test_add_class_with_choice_field(self):
        form = DealSpatialForm(initial={'location': 'value'})
        field = ChoiceField(choices=(('value', 'label'),), widget=CheckboxInput)
        bound_field = BoundField(form, field, 'location')
        self.assertNotIn('testclass', add_class(bound_field, 'testclass'))

    def test_add_class_with_char_field(self):
        form = DealSpatialForm(initial={'location': 'value'})
        field = CharField()
        bound_field = BoundField(form, field, 'location')
        self.assertIn('testclass', add_class(bound_field, 'testclass'))

    def test_decimalgroupstring(self):
        self.assertEqual('1,000 test', decimalgroupstring('1000 test'))

    def test_random_id(self):
        form = DealSpatialForm(initial={'location': 'test'})
        field = CharField()
        bound_field = BoundField(form, field, 'location')
        self.assertRegexpMatches(random_id(bound_field), r'id=\"id_location_\d+\"')

    def test_get_user_role(self):
        user = get_user_model().objects.get(username='editor-myanmar')
        self.assertEqual('Editor for Myanmar', get_user_role(user))

    def test_history(self):
        item = HistoricalActivity.objects.get(id=10)
        user = get_user_model().objects.get(username='editor')
        self.assertGreater(len(history(item, user)), 0)

    def test_history_count(self):
        item = HistoricalActivity.objects.get(id=10)
        user = get_user_model().objects.get(username='editor')
        self.assertGreater(history_count(item, user), 0)

    def test_is_editable(self):
        item = HistoricalActivity.objects.get(id=10)
        user = get_user_model().objects.get(username='editor')
        self.assertEqual(True, is_editable(item, user))

    def test_get_latest(self):
        item = HistoricalActivity.objects.get(id=10)
        user = get_user_model().objects.get(username='editor')
        self.assertEqual(item, get_latest(item, user))

    def test_deslugify(self):
        self.assertEqual('By Target Country', deslugify('by-target_country'))

    def test_can_approve_reject(self):
        user = get_user_model().objects.get(username='reporter')
        self.assertEqual(False, can_approve_reject(user))

    def test_field_label(self):
        self.assertEqual('username', field_label(get_user_model(), 'username'))
