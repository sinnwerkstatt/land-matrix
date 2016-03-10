
from django.http.request import HttpRequest
from django.http import QueryDict

from grid.views.table_group_view import TableGroupView

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from grid.tests.deals_test_data import DealsTestData

from django.test import TestCase

class TestViewVariables(TestCase, DealsTestData):

    def setUp(self):
        self._call_dispatch('all.csv')

    def test_download_set(self):
        self.assertTrue(self.view.is_download)

    def test_group_value_set_correctly(self):
        self.assertFalse(self.view.group_value.endswith('.csv'))
        self.assertFalse(self.view.group.endswith('.csv'))

    def test_no_download(self):
        self._call_dispatch('all')
        self.assertFalse(self.view.is_download())

    def test_columns(self):
        self.assertEqual(self.view.DOWNLOAD_COLUMNS, self.view.columns)

    def test_columns_2(self):
        self._call_dispatch('all')
        self.assertEqual(self.view.GROUP_COLUMNS_LIST, self.view.columns)

    def test_columns_3(self):
        self._call_dispatch('by-crop')
        self.assertNotEqual(self.view.GROUP_COLUMNS_LIST, self.view.columns)
        self.assertNotEqual(self.view.DOWNLOAD_COLUMNS, self.view.columns)
        self.assertIn('crop', self.view.columns)

    def test_filters_group(self):
        self.assertEqual('all', self.view.filters['group_by'])
        self.assertEqual('all', self.view.group)
        self._call_dispatch('crop')
        self.assertEqual('crop', self.view.filters['group_by'])
        self.assertEqual('crop', self.view.group)

    def test_filters_with_filter_set(self):
        # TODO: find a set of GET Variables that produce non-empty filters
        self._call_dispatch_with_GET('filtered')
        # print('\nfilters:', self.view.filters)
        from grid.views.browse_filter_conditions import BrowseFilterConditions
        BrowseFilterConditions.DEBUG = False
        self._call_dispatch_with_GET(
            'filtered&conditions_empty-0-operator=[in]&conditions_empty-1-operator=[is]&conditions_empty-MAX_NUM_FORMS=[]&' +
            'conditions_empty-0-value=[30,40]&conditions_empty-0-variable=[5233]&conditions_empty-1-variable=[-2]&' +
            'conditions_empty-1-value=[20]&conditions_empty-TOTAL_FORMS=[2]&conditions_empty-INITIAL_FORMS=[2]'
        )
        # print('filters:', self.view.filters)
        BrowseFilterConditions.DEBUG = False

    def test_order_by(self):
        self.assertEqual('deal_id', self.view._order_by())

        self._call_dispatch_with_GET('order_by=crop')
        self.assertEqual('crop', self.view._order_by())

        with self.assertRaises(KeyError):
            self._call_dispatch_with_GET('order_by=sddfgtrejfihrpooitgh')

        self._call_dispatch_with_GET('order_by=all')
        self.assertEqual('deal_id', self.view._order_by())

        self._call_dispatch_with_GET('', group='crop')
        self.assertEqual('crop', self.view._order_by())

        self._call_dispatch_with_GET('order_by=deal_count', group='crop')
        self.assertEqual('deal_count', self.view._order_by())

    def test_limit(self):
        self.assertFalse(self.view._limit_query())
        self._call_dispatch('all')
        self.assertTrue(self.view._limit_query())

    def test_starts_with_unsets_limit(self):
        self._call_dispatch_with_GET('starts_with=10')
        self.assertFalse(self.view._limit_query())
        self._call_dispatch_with_GET('starts_with=10', group='all')
        self.assertFalse(self.view._limit_query())

    def test_load_more(self):
        self.assertFalse(self.view._load_more())
        self.assertFalse(self.view._load_more_amount())
        self._call_dispatch('all')
        self.assertEqual(50, int(self.view._load_more()))
        self._call_dispatch_with_GET('more=10', group='all')
        self.assertEqual(10, int(self.view._load_more()))

    def test_csv_download_mimetype(self):
        self.create_data()
        self.view = TableGroupView()
        response = self.view.dispatch(self._request(), group='all.csv')
        self.assertTrue(response.has_header('Content-Type'))
        self.assertEqual('text/csv', response['Content-Type'])

    def test_csv_download_database(self):
        values = self._get_csv_data('database')

        for key in TableGroupView.DOWNLOAD_COLUMNS:
            self.assertIn(key, values.keys())

        self.assertEqual(values['target_country'], self.country.name)
        self.assertEqual(values['intention'], self.INTENTION)

    def test_csv_download_all(self):
        values = self._get_csv_data('all')

        for key in TableGroupView.DOWNLOAD_COLUMNS:
            self.assertIn(key, values.keys())

        self.assertEqual(values['target_country'], self.country.name)
        self.assertEqual(values['intention'], self.INTENTION)

    def test_csv_download_intention(self):
        values = self._get_csv_data('intention')

        for key in self.view.columns:
            self.assertIn(key, values.keys())

        self.assertEqual(int(values['deal_count']), 1)
        self.assertEqual(values['intention'], self.INTENTION)

    def test_csv_download_target_country(self):
        values = self._get_csv_data('target-country')

        for key in self.view.columns:
            self.assertIn(key, values.keys())

        self.assertEqual(int(values['deal_count']), 1)
        self.assertEqual(values['target_country'], self.country.name)
        self.assertEqual(values['target_region'], self.region.name)
        self.assertEqual(values['intention'], self.INTENTION)

    def test_xml_download_mimetype(self):
        self.create_data()
        self.view = TableGroupView()
        response = self.view.dispatch(self._request(), group='all.xml')
        self.assertTrue(response.has_header('Content-Type'))
        self.assertEqual('text/xml', response['Content-Type'])

    def test_xml_download_contains_keys(self):
        xml = self._get_xml_data('all')
        for key in TableGroupView.DOWNLOAD_COLUMNS:
            self.assertIn(key, xml)

    def test_xml_download_is_valid(self):
        from xml.etree import ElementTree

        xml = self._get_xml_data('all')
        try:
            ElementTree.fromstring(xml)
        except ElementTree.ParseError:
            self.fail('Invalid XML:' + xml)

    def test_xls_download_mimetype(self):
        self.create_data()
        self.view = TableGroupView()
        response = self.view.dispatch(self._request(), group='all.xls')
        self.assertTrue(response.has_header('Content-Type'))
        self.assertEqual('application/ms-excel', response['Content-Type'])

    def _get_xml_data(self, group):
        self.create_data()
        self.view = TableGroupView()
        return self.view.dispatch(self._request(), group=group + '.xml').content.decode('utf-8')

    def _get_csv_data(self, group):
        self.create_data()
        self.view = TableGroupView()
        result = self.view.dispatch(self._request(), group=group+'.csv').content.decode()
        fields = [
            list(map(lambda s: s.strip(), line.split(';')))
            for line in result.strip().split('\n')
            ]
        self.assertEqual(2, len(fields))
        values = dict(zip(fields[0], fields[1]))
        values = {key: eval(value).decode('utf-8') for key, value in values.items()}
        return values

    def _call_dispatch_with_GET(self, get_string, group=None, debug=False):
        self.view = TableGroupView()
        self.view.debug_query = debug
        request = self._request()
        request.GET = QueryDict(get_string)
        self.view.dispatch(request, group=group if group else 'all')

    def _call_dispatch(self, group, **kwargs):
        from django.db.utils import InternalError
        self.view = TableGroupView()
        try:
            return self.view.dispatch(self._request(), group=group, **kwargs).content
        except InternalError:
            pass

    def _request(self):
        class User:
            is_authenticated = lambda x: False

        from django.test.client import RequestFactory
        rf = RequestFactory()

        request = rf.get('')
        request.current_page = 0
        request.user = User()
        request.session = {}
        return request