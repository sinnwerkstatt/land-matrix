from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import QueryDict
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from apps.api.filters import Filter, PresetFilter
from apps.api.views import ElasticSearchMixin
from apps.grid.tests.views.base import PermissionsTestCaseMixin
from apps.landmatrix.models.activity import ActivityBase
from apps.landmatrix.models.investor import InvestorBase
from apps.landmatrix.tests.mixins import ElasticSearchFixtureMixin


class ElasticSearchMixinTestCase(
    ElasticSearchFixtureMixin, PermissionsTestCaseMixin, TestCase
):

    act_fixtures = [
        {"id": 10, "activity_identifier": 1, "attributes": {}},
        {"id": 20, "activity_identifier": 2, "attributes": {}},
        {"id": 21, "activity_identifier": 2, "fk_status_id": 1, "attributes": {}},
        {"id": 30, "activity_identifier": 3, "fk_status_id": 2, "attributes": {}},
        {
            "id": 31,
            "activity_identifier": 3,
            "fk_status_id": 3,
            "attributes": {
                "contract_area": {
                    "value": None,
                    "polygon": "0106000020E6100000010000000103000000010000000C0000009A2D2EC012915E40E41DB6BEC8F41E409EF5FB4160915E4076D1079C83FB1E403D7B93A709925E4057EED6779DF61E40F2F9D2A3BC925E40D1AB285076E81E40BE2C035376925E40E08E756779E21E4064B4A98CBA915E40D8EC297FB3E41E4031F66D755F915E401D9D120467E91E4084165EB632915E40B7D9B3BAA3EA1E40E23A6C5F00915E40D1AB285076E81E40E45894D2D6905E4046C1FE6264EA1E4091F1DDD965915E4003AEA649F9F01E409A2D2EC012915E40E41DB6BEC8F41E40",
                }
            },
        },
    ]
    inv_fixtures = [
        {"id": 10, "investor_identifier": 1, "name": "Test Investor #1"},
        {"id": 20, "investor_identifier": 2, "name": "Test Investor #2"},
        {
            "id": 21,
            "investor_identifier": 2,
            "fk_status_id": 1,
            "name": "Test Investor #2",
        },
        {"id": 30, "investor_identifier": 3, "name": "Test Investor #3"},
    ]
    act_inv_fixtures = {"10": "10", "20": "20", "21": "20"}
    inv_inv_fixtures = [
        {"fk_venture_id": "20", "fk_investor_id": "10", "role": "ST"},
        {"fk_venture_id": "30", "fk_investor_id": "20", "role": "IN"},
    ]

    def setUp(self):
        self.mixin = ElasticSearchMixin()

    @classmethod
    def create_fixture(cls):
        cls.create_permissions()

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_filter_doc_type(self):
        self.mixin.doc_type = "investor"
        self.assertEqual(self.mixin.get_filter_doc_type(), "investor")
        self.mixin.doc_type = "location"
        self.assertEqual(self.mixin.get_filter_doc_type(), "deal")

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_load_filters_from_url_with_request_params(self):
        request = RequestFactory()
        params = "variable=activity_identifier&operator=is&value=1"
        params += "&variable=intention&operator=is&value=Mining"
        request.GET = QueryDict(params)
        self.mixin.request = request
        filters = self.mixin.load_filters_from_url(exclude=["intention"])
        self.assertIn("activity_identifier", filters.keys())
        self.assertEqual(
            Filter("activity_identifier", "is", "1"), filters["activity_identifier"]
        )
        self.assertNotIn("intention", filters.keys())

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_load_filters_from_url_without_request_params(self):
        filters = self.mixin.load_filters_from_url()
        self.assertEqual({}, filters)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_load_filters_with_session_filters(self):
        custom_filter = {
            "name": "custom_filter",
            "variable": "activity_identifier",
            "operator": "is",
            "value": "1",
            "label": "Deal ID",
            "key": None,
            "display_value": "1",
        }
        excluded_filter = {
            "name": "excluded_filter",
            "variable": "intention",
            "operator": "is",
            "value": "Mining",
            "label": "Intention is Mining",
            "key": None,
            "display_value": "Mining",
        }
        session = self.client.session
        session["deal:filters"] = {
            "custom_filter": custom_filter,
            "excluded_filter": excluded_filter,
        }
        session.save()

        request = RequestFactory()
        request.GET = QueryDict()
        request.session = session
        self.mixin.request = request

        formatted_filters = self.mixin.load_filters(exclude=["intention"])
        self.assertEqual(
            [{"match_phrase": {"activity_identifier": "1"}}],
            formatted_filters.get("must"),
        )
        self.assertEqual([], formatted_filters.get("filter"))
        self.assertEqual([], formatted_filters.get("must_not"))
        self.assertEqual([], formatted_filters.get("should"))

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_load_filters_with_session_parent_stakeholder_filter(self):
        custom_filter = {
            "name": "custom_filter",
            "variable": "parent_stakeholder_name",
            "operator": "is",
            "value": "Test Investor #1",
        }
        session = self.client.session
        session["deal:filters"] = {"custom_filter": custom_filter}
        session.save()

        request = RequestFactory()
        request.GET = QueryDict()
        request.session = session
        self.mixin.request = request

        formatted_filters = self.mixin.load_filters()
        expected = [{"match_phrase": {"operating_company_id": "20"}}]
        self.assertEqual(expected, formatted_filters.get("must"))
        self.assertEqual([], formatted_filters.get("filter"))
        self.assertEqual([], formatted_filters.get("must_not"))
        self.assertEqual([], formatted_filters.get("should"))

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_load_filters_with_session_tertiary_investor_filter(self):
        custom_filter = {
            "name": "custom_filter",
            "variable": "tertiary_investor_name",
            "operator": "is",
            "value": "Test Investor #2",
        }
        session = self.client.session
        session["deal:filters"] = {"custom_filter": custom_filter}
        session.save()

        request = RequestFactory()
        request.GET = QueryDict()
        request.session = session
        self.mixin.request = request

        formatted_filters = self.mixin.load_filters()
        expected = [{"match_phrase": {"operating_company_id": "30"}}]
        self.assertEqual(expected, formatted_filters.get("must"))
        self.assertEqual([], formatted_filters.get("filter"))
        self.assertEqual([], formatted_filters.get("must_not"))
        self.assertEqual([], formatted_filters.get("should"))

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_load_filters_with_session_preset(self):
        custom_preset = {
            "name": "custom_preset",
            "preset_id": "1",
            "label": "custom_preset",
        }
        session = self.client.session
        session["deal:filters"] = {"custom_preset": custom_preset}
        session.save()

        request = RequestFactory()
        request.GET = QueryDict()
        request.session = session
        self.mixin.request = request

        formatted_filters = self.mixin.load_filters()
        self.assertEqual(
            [{"match": {"intention": "Mining"}}], formatted_filters.get("must_not")
        )
        self.assertEqual([], formatted_filters.get("filter"))
        self.assertEqual([], formatted_filters.get("must"))
        self.assertEqual([], formatted_filters.get("should"))

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_load_filters_without_session_filters(self):
        formatted_filters = self.mixin.load_filters()
        expected = {"must": [], "filter": [], "must_not": [], "should": []}
        self.assertEqual(expected, formatted_filters)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_get_investor_filter(self):
        expected = Filter(
            variable="operational_stakeholder", operator="in", value=["1", "2"]
        )
        self.assertEqual(expected, self.mixin.get_investor_filter(["1", "2"]))

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_format_filters(self):
        filters = [
            Filter(variable="operational_stakeholder", operator="in", value=["1", "2"]),
            PresetFilter(preset=1),  # AND relation
            PresetFilter(preset=10),  # OR relation
        ]
        query = self.mixin.format_filters(filters)
        oc_filter = {
            "{'match_phrase': {'operating_company_id': '1'}}",
            "{'match_phrase': {'operating_company_id': '2'}}",
        }
        init_date_filter = {
            "{'bool': {'must_not': {'exists': {'field': 'init_date'}}}}",
            "{'range': {'init_date': {'gt': '1999-12-31'}}}",
        }
        mining_filter = [{"match": {"intention": "Mining"}}]
        self.assertEqual(
            oc_filter, set(str(f) for f in query["must"][0]["bool"]["should"])
        )
        self.assertEqual(
            init_date_filter, set(str(f) for f in query["must"][1]["bool"]["should"])
        )
        self.assertEqual(mining_filter, query["must_not"])

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_create_query_from_filters(self):
        custom_filter = {
            "name": "custom_filter",
            "variable": "activity_identifier",
            "operator": "is",
            "value": "1",
            "label": "Deal ID",
            "key": None,
            "display_value": "1",
        }
        session = self.client.session
        session["deal:filters"] = {"custom_filter": custom_filter}
        session.save()

        request = RequestFactory()
        params = "variable=intention&operator=is&value=Mining"
        request.GET = QueryDict(params)
        request.session = session
        request.user = AnonymousUser()
        self.mixin.request = request
        query = self.mixin.create_query_from_filters()
        expected = [
            {"match_phrase": {"activity_identifier": "1"}},
            {"match_phrase": {"intention": "Mining"}},
        ]
        self.assertEqual(expected, query.get("bool", {}).get("must", {}))

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_add_request_filters_to_elasticsearch_query(self):
        request = RequestFactory()
        request.user = AnonymousUser()
        request.GET = QueryDict("window=1,2,3,4")
        self.mixin.request = request
        query = {"must": [], "filter": [], "must_not": [], "should": []}
        elasticsearch_query = self.mixin.add_request_filters_to_elasticsearch_query(
            query
        )
        expected = {
            "geo_bounding_box": {
                "geo_point": {
                    "top_left": {"lat": 4.0, "lon": 1.0},
                    "bottom_right": {"lat": 2.0, "lon": 3.0},
                }
            }
        }
        self.assertEqual(expected, elasticsearch_query.get("filter")[0])

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_add_request_filters_to_elasticsearch_query_without_request(self):
        query = {"must": [], "filter": [], "must_not": [], "should": []}
        elasticsearch_query = self.mixin.add_request_filters_to_elasticsearch_query(
            query
        )
        self.assertEqual(
            {"terms": {"status": (2, 3)}}, elasticsearch_query.get("filter")[0]
        )

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_add_status_logic_with_administrator(self):
        request = RequestFactory()
        request.GET = QueryDict("status=1&status=2&status=3")
        request.user = get_user_model().objects.get(username="administrator")
        self.mixin.request = request
        query = {"must": [], "filter": [], "must_not": [], "should": []}
        status_query = self.mixin.add_status_logic(query)
        expected = [{"terms": {"status": [1, 2, 3]}}]
        self.assertEqual(expected, status_query.get("filter"))

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_add_public_logic_with_anonymous(self):
        request = RequestFactory()
        request.user = AnonymousUser()
        self.mixin.request = request
        query = {"must": [], "filter": [], "must_not": [], "should": []}
        public_query = self.mixin.add_public_logic(query)
        expected = [{"bool": {"filter": {"term": {"is_public": "True"}}}}]
        self.assertEqual(expected, public_query.get("filter"))

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_execute_elasticsearch_query(self):
        query = {"bool": {"must": [{"match_phrase": {"activity_identifier": "1"}}]}}
        results = self.mixin.execute_elasticsearch_query(query)
        self.assertEqual(1, len(results))
        self.assertEqual(1, results[0]["_source"]["activity_identifier"])
        self.assertEqual(10, results[0]["_source"]["historical_activity_id"])

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_filter_deals(self):
        self.mixin.status_list = ActivityBase.PUBLIC_STATUSES + (
            ActivityBase.STATUS_PENDING,
        )
        raw_result_list = [
            {
                "_index": "landmatrix_test",
                "_type": "deal",
                "_id": "10",
                "_source": {
                    "activity_identifier": 1,
                    "historical_activity_id": 10,
                    "history_date": "2000-01-01T00:00:00+00:00",
                    "status": 2,
                    "is_public": "True",
                },
            },
            {
                "_index": "landmatrix_test",
                "_type": "deal",
                "_id": "20",
                "_source": {
                    "activity_identifier": 2,
                    "historical_activity_id": 20,
                    "history_date": "2000-01-01T00:00:00+00:00",
                    "status": 3,
                    "is_public": "True",
                },
            },
            {
                "_index": "landmatrix_test",
                "_type": "deal",
                "_id": "21",
                "_source": {
                    "activity_identifier": 2,
                    "historical_activity_id": 21,
                    "history_date": "2000-01-01T01:00:00+00:00",
                    "status": 1,
                    "is_public": "True",
                },
            },
        ]

        result_list = self.mixin.filter_deals(raw_result_list)
        expected = [
            {
                "activity_identifier": 1,
                "historical_activity_id": 10,
                "history_date": "2000-01-01T00:00:00+00:00",
                "status": 2,
                "is_public": "True",
                "id": "10",
            },
            {
                "activity_identifier": 2,
                "historical_activity_id": 21,
                "history_date": "2000-01-01T01:00:00+00:00",
                "status": 1,
                "is_public": "True",
                "id": "21",
            },
        ]
        self.assertEqual(expected, result_list)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_filter_investors(self):
        self.mixin.status_list = InvestorBase.PUBLIC_STATUSES + (
            InvestorBase.STATUS_PENDING,
        )
        raw_result_list = [
            {
                "_index": "landmatrix_test",
                "_type": "investor",
                "_id": "10",
                "_source": {
                    "investor_identifier": 1,
                    "historical_activity_id": 10,
                    "history_date": "2000-01-01T00:00:00+00:00",
                    "fk_status": 2,
                },
            },
            {
                "_index": "landmatrix_test",
                "_type": "investor",
                "_id": "30",
                "_source": {
                    "investor_identifier": 3,
                    "historical_activity_id": 30,
                    "history_date": "2000-01-01T00:00:00+00:00",
                    "fk_status": 3,
                },
            },
            {
                "_index": "landmatrix_test",
                "_type": "investor",
                "_id": "11",
                "_source": {
                    "investor_identifier": 3,
                    "historical_activity_id": 31,
                    "history_date": "2000-01-01T01:00:00+00:00",
                    "fk_status": 1,
                },
            },
        ]
        result_list = self.mixin.filter_investors(raw_result_list)
        expected = [
            {
                "investor_identifier": 1,
                "historical_activity_id": 10,
                "history_date": "2000-01-01T00:00:00+00:00",
                "fk_status": 2,
                "id": "10",
            },
            {
                "investor_identifier": 3,
                "historical_activity_id": 31,
                "history_date": "2000-01-01T01:00:00+00:00",
                "fk_status": 1,
                "id": "11",
            },
        ]
        self.assertEqual(expected, result_list)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_filter_involvements(self):
        raw_result_list = [
            {
                "_index": "landmatrix_test",
                "_type": "involvement",
                "_id": "10",
                "_source": {
                    "fk_investor": 50,
                    "fk_venture": 20,
                    "fk_investor_name": "Test Investor #5",
                    "fk_venture_name": "Test Investor #2",
                },
            },
            {
                "_index": "landmatrix_test",
                "_type": "involvement",
                "_id": "20",
                "_source": {
                    "fk_investor": 60,
                    "fk_venture": 30,
                    "fk_investor_name": "Test Investor #6",
                    "fk_venture_name": "Test Investor #3",
                },
            },
            {
                "_index": "landmatrix_test",
                "_type": "involvement",
                "_id": "30",
                "_source": {
                    "fk_investor": 61,
                    "fk_venture": 31,
                    "fk_investor_name": "Test Investor #6",
                    "fk_venture_name": "Test Investor #3",
                },
            },
        ]
        investors = [{"id": 30}, {"id": 31}, {"id": 60}, {"id": 61}]
        result_list = self.mixin.filter_involvements(
            raw_result_list, investors=investors
        )
        expected = [
            {
                "fk_investor": 61,
                "fk_venture": 31,
                "fk_investor_name": "Test Investor #6",
                "fk_venture_name": "Test Investor #3",
                "id": "30",
            }
        ]
        self.assertEqual(expected, result_list)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_disable_filters(self):
        custom_filter = {
            "name": "custom_filter",
            "variable": "activity_identifier",
            "operator": "is",
            "value": "1",
            "label": "Deal ID",
            "key": None,
            "display_value": "1",
        }
        session = self.client.session
        session["deal:filters"] = {"custom_filter": custom_filter}
        session.save()

        request = RequestFactory()
        request.GET = QueryDict("")
        request.session = session
        self.mixin.request = request
        result_list = self.mixin.disable_filters()
        self.assertEqual(
            {"custom_filter": custom_filter}, session.get("deal:disabled_filters")
        )

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_enable_filters(self):
        custom_filter = {
            "name": "custom_filter",
            "variable": "activity_identifier",
            "operator": "is",
            "value": "1",
            "label": "Deal ID",
            "key": None,
            "display_value": "1",
        }
        session = self.client.session
        session["deal:disabled_filters"] = {"custom_filter": custom_filter}
        session["deal:disabled_set_default_filters"] = False
        session.save()

        request = RequestFactory()
        request.GET = QueryDict("")
        request.session = session
        self.mixin.request = request
        result_list = self.mixin.enable_filters()
        self.assertEqual({"custom_filter": custom_filter}, session.get("deal:filters"))
        self.assertEqual(False, session.get("deal:set_default_filters"))


class ListViewsTestCase(ElasticSearchFixtureMixin, TestCase):
    maxDiff = 5000

    act_fixtures = [
        {
            "id": 10,
            "activity_identifier": 1,
            "attributes": {
                "contract_size": {"value": "200"},
                "implementation_status": {
                    "value": ActivityBase.IMPLEMENTATION_STATUS_IN_OPERATION,
                    "date": "2000",
                },
            },
        },
        {"id": 20, "activity_identifier": 2, "attributes": {}},
        {
            "id": 21,
            "activity_identifier": 2,
            "fk_status_id": 1,
            "attributes": {
                "contract_area": {
                    "value": None,
                    "polygon": "0106000020E6100000010000000103000000010000000C0000009A2D2EC012915E40E41DB6BEC8F41E409EF5FB4160915E4076D1079C83FB1E403D7B93A709925E4057EED6779DF61E40F2F9D2A3BC925E40D1AB285076E81E40BE2C035376925E40E08E756779E21E4064B4A98CBA915E40D8EC297FB3E41E4031F66D755F915E401D9D120467E91E4084165EB632915E40B7D9B3BAA3EA1E40E23A6C5F00915E40D1AB285076E81E40E45894D2D6905E4046C1FE6264EA1E4091F1DDD965915E4003AEA649F9F01E409A2D2EC012915E40E41DB6BEC8F41E40",
                }
            },
        },
    ]
    inv_fixtures = [
        {"id": 10, "investor_identifier": 1, "name": "Test Investor #1"},
        {"id": 20, "investor_identifier": 2, "name": "Test Investor #2"},
        {
            "id": 21,
            "investor_identifier": 2,
            "fk_status_id": 1,
            "name": "Test Investor #2",
        },
        {"id": 30, "investor_identifier": 3, "name": "Test Investor #3"},
    ]
    act_inv_fixtures = {"10": "10", "20": "20", "21": "20"}
    inv_inv_fixtures = [
        {"fk_venture_id": "10", "fk_investor_id": "20", "role": "ST"},
        {"fk_venture_id": "10", "fk_investor_id": "30", "role": "IN"},
    ]

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_user_list_view(self):
        self.client.login(username="administrator-staff", password="test")
        response = self.client.get(reverse("users_api"))
        self.client.logout()
        self.assertEqual(200, response.status_code)
        self.assertGreater(len(response.data), 0)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_statistics_view(self):
        response = self.client.get(reverse("statistics_api"))
        self.assertEqual(200, response.status_code)
        expected = [["Contract signed", 2, 400]]
        self.assertEqual(expected, response.data)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_statistics_view_with_country(self):
        data = QueryDict("country=104")
        response = self.client.get(reverse("statistics_api"), data)
        self.assertEqual(200, response.status_code)
        expected = [["Contract signed", 2, 400]]
        self.assertEqual(expected, response.data)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_statistics_view_with_region(self):
        data = QueryDict("region=142")
        response = self.client.get(reverse("statistics_api"), data)
        self.assertEqual(200, response.status_code)
        expected = [["Contract signed", 2, 400]]
        self.assertEqual(expected, response.data)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_statistics_view_with_disable_filters(self):
        data = QueryDict("disable_filters=1")
        response = self.client.get(reverse("statistics_api"), data)
        self.assertEqual(200, response.status_code)
        expected = [["Contract signed", 2, 400]]
        self.assertEqual(expected, response.data)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_latest_changes_view(self):
        response = self.client.get(reverse("latest_changes_api"))
        self.assertEqual(200, response.status_code)
        expected = [
            {
                "action": "add",
                "deal_id": 1,
                "change_date": "2000-01-01T00:00:00+00:00",
                "target_country": "Myanmar",
            },
            {
                "action": "add",
                "deal_id": 2,
                "change_date": "2000-01-01T00:00:00+00:00",
                "target_country": "Myanmar",
            },
        ]
        self.assertEqual(expected, response.data)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_latest_changes_view_with_country(self):
        data = QueryDict("target_country=104")
        response = self.client.get(reverse("latest_changes_api"), data)
        self.assertEqual(200, response.status_code)
        expected = [
            {
                "action": "add",
                "deal_id": 1,
                "change_date": "2000-01-01T00:00:00+00:00",
                "target_country": "Myanmar",
            },
            {
                "action": "add",
                "deal_id": 2,
                "change_date": "2000-01-01T00:00:00+00:00",
                "target_country": "Myanmar",
            },
        ]
        self.assertEqual(expected, response.data)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_latest_changes_view_with_region(self):
        data = QueryDict("target_region=142")
        response = self.client.get(reverse("latest_changes_api"), data)
        self.assertEqual(200, response.status_code)
        expected = [
            {
                "action": "add",
                "deal_id": 1,
                "change_date": "2000-01-01T00:00:00+00:00",
                "target_country": "Myanmar",
            },
            {
                "action": "add",
                "deal_id": 2,
                "change_date": "2000-01-01T00:00:00+00:00",
                "target_country": "Myanmar",
            },
        ]
        self.assertEqual(expected, response.data)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_global_deals_view(self):
        response = self.client.get(reverse("deals_api"))
        self.assertEqual(200, response.status_code)
        self.assertEqual("FeatureCollection", response.data.get("type"))
        features = [
            {
                "geometry": {"coordinates": [4.0, 3.0], "type": "Point"},
                "properties": {
                    "contract_size": "200",
                    "identifier": 1,
                    "implementation": ["In operation (production)"],
                    "intended_size": "1",
                    "intention": ["Agriculture"],
                    "investor": "10",
                    "level_of_accuracy": "Country",
                    "production_size": "3",
                    "url": "/legacy/deal/1/",
                },
                "type": "Feature",
            },
            {
                "geometry": {"coordinates": [4.0, 3.0], "type": "Point"},
                "properties": {
                    "contract_size": "200",
                    "identifier": 2,
                    "implementation": ["Project not started"],
                    "intended_size": "1",
                    "intention": ["Agriculture"],
                    "investor": "10",
                    "level_of_accuracy": "Country",
                    "production_size": "3",
                    "url": "/legacy/deal/2/",
                },
                "type": "Feature",
            },
        ]
        for i, feature in enumerate(response.data.get("features")):
            self.assertEqual("Feature", feature.get("type"))
            # self.assertEqual(features[i]['geometry'], feature.get('geometry'))
            self.assertEqual(features[i]["properties"], feature.get("properties"))

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_country_deals_view(self):
        response = self.client.get(reverse("country_deals_api"))
        self.assertEqual(200, response.status_code)
        self.assertEqual("FeatureCollection", response.data.get("type"))
        country_feature = {
            "type": "Feature",
            "id": "MMR",
            "properties": {
                "name": "Myanmar",
                "deals": 2,
                "url": "/legacy/country/myanmar/",
                "centre_coordinates": [
                    Decimal("95.956223000000"),
                    Decimal("21.913965000000"),
                ],
                "intention": {"Agriculture": 2},
                "implementation": {
                    "In operation (production)": 1,
                    "Project not started": 1,
                },
                "level_of_accuracy": {"Country": 2},
            },
        }
        self.assertIsInstance(response.data.get("features"), (tuple, list))
        self.assertGreater(len(response.data.get("features")), 0)
        self.assertEqual(country_feature, response.data.get("features")[0])

    # this test failes with different postgres versions. nuisance
    # @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    # def test_country_geom_view(self):
    #     response = self.client.get(
    #         reverse("countries_geom_api"), data={"country_id": 104}
    #     )
    #     self.assertEqual(200, response.status_code)
    #     expected = {
    #         "type": "Feature",
    #         "geometry": {
    #             "type": "MultiPolygon",
    #             "coordinates": [
    #                 [
    #                     [
    #                         [36.0885822034013, -8.36020665747141],
    #                         [36.1409202428711, -8.34329312096451],
    #                         [36.1716999946545, -8.37026028087353],
    #                         [36.1237574442138, -8.43754673237533],
    #                         [36.1033320145246, -8.41956074195487],
    #                         [36.1047254298611, -8.37465375610683],
    #                         [36.0885822034013, -8.36020665747141],
    #                     ]
    #                 ]
    #             ],
    #         },
    #     }
    #     self.assertEqual(expected, response.data)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_country_geom_view_with_invalid_country(self):
        response = self.client.get(
            reverse("countries_geom_api"), data={"country_id": 9999}
        )
        self.assertEqual(404, response.status_code)

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_polygon_geom_view(self):
        response = self.client.get(
            reverse("polygon_geom_api", kwargs={"polygon_field": "contract_area"})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("FeatureCollection", response.data.get("type"))
        coordinates = [
            [
                [
                    [122.26676945218642, 7.739047031274342],
                    [122.27150010686316, 7.745619237878023],
                    [122.28183926966172, 7.740835068219517],
                    [122.29276366809043, 7.727013828737612],
                    [122.2884719401363, 7.721166245031526],
                    [122.27701107571335, 7.723340975698385],
                    [122.2714513372273, 7.727932037006465],
                    [122.26872023762013, 7.729140202738953],
                    [122.26564775056207, 7.727013828737612],
                    [122.26311172949823, 7.728898569869051],
                    [122.27184149431402, 7.735325957105945],
                    [122.26676945218642, 7.739047031274342],
                ]
            ]
        ]
        self.assertEqual("MultiPolygon", response.data.get("features")[0].get("type"))
        self.assertEqual(
            coordinates, response.data.get("features")[0].get("coordinates")
        )

    @override_settings(ELASTICSEARCH_INDEX_NAME="landmatrix_test")
    def test_polygon_geom_view_with_invalid_field(self):
        response = self.client.get(
            reverse("polygon_geom_api", kwargs={"polygon_field": "invalid_area"})
        )
        self.assertEqual(404, response.status_code)
