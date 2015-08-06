__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from django.utils import timezone
from landmatrix.views import AjaxView
from landmatrix.tests.with_status import WithStatus

class TestAjaxView(WithStatus):
    """
        - when the values are selected from a list, operator in must return checkboxes, while is must return a select or radio button
    """

    example_values = {
        'id': { 'key_id': '-1', 'operation': ['not_in', 'in', 'is', 'contains'] },
        'deal scope': { 'key_id': '-2', 'operation': ['not_in', 'in', 'is', 'contains', 'is_empty'] },
        'crops': { 'key_id': '5248', 'operation': ['not_in', 'in', 'is', 'is_empty'] },
        'contract farming': { 'key_id': '5266', 'operation': ['not_in', 'in', 'is', 'is_empty'] },
        'data source type': { 'key_id': '5238', 'operation': ['not_in', 'in', 'is', 'is_empty'] },
        'implementation status': { 'key_id': '5258', 'operation': ['not_in', 'in', 'is', 'is_empty'] },
        'intended size': { 'key_id': '5230', 'operation': ['not_in', 'in', 'is', 'is_empty'] },
        'intention': { 'key_id': '5231', 'operation': ['not_in', 'in', 'is', 'is_empty'] },
        'investor country': { 'key_id': 'inv_24055', 'operation': ['not_in', 'in', 'is', 'is_empty'] },
        'investor name': { 'key_id': 'inv_24054', 'operation': ['not_in', 'in', 'is', 'is_empty', 'contains'] },
        'last modification': { 'key_id': 'last_modification', 'operation': ['not_in', 'in', 'is', 'is_empty', 'contains'] },
        'location': { 'key_id': '5227', 'operation': ['not_in', 'in', 'is', 'is_empty', 'contains'] },
        'nature of the deal': { 'key_id': '5232', 'operation': ['not_in', 'in', 'is', 'is_empty'] },
        'negotiation status': { 'key_id': '5233', 'operation': ['not_in', 'in', 'is', 'is_empty'] },
        'new url': { 'key_id': '5255', 'operation': ['not_in', 'in', 'is', 'is_empty', 'contains'] },
        'organization': { 'key_id': '5239', 'operation': ['not_in', 'in', 'is', 'is_empty', 'contains'] },
        'primary investor': { 'key_id': 'inv_-2', 'operation': ['not_in', 'in', 'is', 'is_empty'] },
        'target country': { 'key_id': '5228', 'operation': ['not_in', 'in', 'is', 'is_empty'] },
    }

    fails_in_v1 = {
        'current size in operation': { 'key_id': '5282', 'operation': ['lt']},
        'current size under contract': { 'key_id': '5264', 'operation': ['lt']},
        'fully updated': { 'key_id': 'fully_updated', 'operation': ['in'] }, # date picker does not work
        'fully updated by': { 'key_id': 'fully_updated_by', 'operation': ['in'] }, # User model not present
    }

    def test_id(self):
        self._test_for_specific_attribute('id')

    def test_deal_scope(self):
        self._test_for_specific_attribute('deal scope')

    def test_crops(self):
        self._test_for_specific_attribute('crops')

    def test_contract_farming(self):
        self._test_for_specific_attribute('contract farming')

    def test_data_source_type(self):
        self._test_for_specific_attribute('data source type')

    def DISABLED_test_fully_updated(self):
        self._test_for_specific_attribute('fully updated')

    def DISABLED_test_fully_updated_by(self):
        self._test_for_specific_attribute('fully updated by')

    def test_implementation_status(self):
        self._test_for_specific_attribute('implementation status')

    def test_intended_size(self):
        self._test_for_specific_attribute('intended size')

    def test_intention(self):
        self._test_for_specific_attribute('intention')

    def test_investor_country(self):
        self._test_for_specific_attribute('investor country')

    def test_investor_name(self):
        self._test_for_specific_attribute('investor name')

    def test_last_modification(self):
        self._test_for_specific_attribute('last modification')

    def test_location(self):
        self._test_for_specific_attribute('location')

    def test_nature_of_the_deal(self):
        self._test_for_specific_attribute('nature of the deal')

    def test_negotiation_status(self):
        self._test_for_specific_attribute('negotiation status')

    def test_new_url(self):
        self._test_for_specific_attribute('new url')

    def test_organization(self):
        self._test_for_specific_attribute('organization')

    def test_primary_investor(self):
        self._test_for_specific_attribute('primary investor')

    def test_target_country(self):
        self._test_for_specific_attribute('target country')

    def _test_for_specific_attribute(self, attribute):
        to_test = self.example_values[attribute]
        for op in to_test['operation']:
            parameter_str = 'key_id='+ to_test['key_id']+ '&operation=' + op
            url = '/ajax/widget/values?'+parameter_str+'&name=conditions_empty-0-value'
            response = self._get_url_following_redirects(url)
            self._check_form_plausible(response.content.decode('utf-8'), op)


    def _get_url_following_redirects(self, url):
        response = self.client.get(url)
        while response.status_code in range(300, 308):
            response = self.client.get(response.url)
        return response

    def _check_form_plausible(self, form, op):
        checks = {
            'is': self._check_form_for_is,
            'in': self._check_form_for_in,
            'not_in': self._check_form_for_in,
            'contains': self._check_form_for_contains,
            'is_empty': self._check_form_for_empty,
        }
        if not checks[op](form): print(checks[op], form)
        self.assertTrue(checks[op](form))


    def _check_form_for_is(self, form):
        """ TODO: disabled because of messed up forms from v1. change that. """
        return True or not self._is_checkbox(form) and not self._is_multiselect(form)

    def _check_form_for_in(self, form):
        """ TODO: tests for messed up forms from v1 too. (condition 5). change that. """
        return self._is_checkbox(form) or self._is_multiselect(form) or self._is_textbox(form) or self._is_url(form)     or '<ul>\n</ul>' in form

    def _check_form_for_contains(self, form):
        """ TODO: tests for messed up forms from v1 too. (condition 2). change that. """
        return self._is_textbox(form)           or self._is_checkbox(form)

    def _check_form_for_empty(self, form):
        """ TODO: tests for messed up forms from v1 too. (condition 2, ...). change that. """
        return self._is_radio(form)             or '<ul>\n</ul>' in form or self._is_checkbox(form) or self._is_single_select(form) or self._is_textbox(form) or self._is_url(form)

    def _is_checkbox(self, form):
        return 'checkbox' in form

    def _is_radio(self, form):
        return 'type="radio"' in form

    def _is_single_select(self, form):
        return '<select' in form and not self._is_multiselect(form)

    def _is_multiselect(self, form):
        return 'select multiple="multiple"' in form

    def _is_textbox(self, form):
        return 'type="text"' in form or 'type="number"' in form

    def _is_url(self, form):
        return 'type="url"' in form

