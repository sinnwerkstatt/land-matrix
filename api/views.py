__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

from api.query_sets.intention_query_set import IntentionQuerySet
from api.query_sets.negotiation_status_query_set import NegotiationStatusQuerySet
from landmatrix.models import *

from django.http import HttpResponse
from django.views.generic.base import TemplateView
import json
import decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)




list_of_urls = """
/en/api/transnational_deals.json?negotiation_status=concluded&deal_scope=transnational
/en/api/transnational_deals.json?negotiation_status=intended&deal_scope=transnational
/en/api/transnational_deals.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational
/en/api/transnational_deals.json?negotiation_status=failed&deal_scope=transnational
/en/api/transnational_deals.json?negotiation_status=concluded&deal_scope=transnational&data_source_type=1
/en/api/transnational_deals.json?negotiation_status=intended&deal_scope=transnational&data_source_type=1
/en/api/transnational_deals.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational&data_source_type=1
/en/api/transnational_deals.json?negotiation_status=failed&deal_scope=transnational&data_source_type=1
/en/api/top-10-countries.json?negotiation_status=concluded&deal_scope=transnational
/en/api/top-10-countries.json?negotiation_status=intended&deal_scope=transnational
/en/api/top-10-countries.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational
/en/api/top-10-countries.json?negotiation_status=failed&deal_scope=transnational
/en/api/top-10-countries.json?negotiation_status=concluded&deal_scope=transnational&data_source_type=1
/en/api/top-10-countries.json?negotiation_status=intended&deal_scope=transnational&data_source_type=1
/en/api/top-10-countries.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational&data_source_type=1
/en/api/top-10-countries.json?negotiation_status=failed&deal_scope=transnational&data_source_type=1

/en/api/investor_country_summaries.json?negotiation_status=intended&deal_scope=transnational&deal_scope=domestic
/en/api/investor_country_summaries.json?negotiation_status=concluded&deal_scope=transnational&deal_scope=domestic
/en/api/investor_country_summaries.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational&deal_scope=domestic
/en/api/investor_country_summaries.json?negotiation_status=failed&deal_scope=transnational&deal_scope=domestic
/en/api/investor_country_summaries.json?negotiation_status=intended&deal_scope=transnational&deal_scope=domestic&data_source_type=1
/en/api/investor_country_summaries.json?negotiation_status=concluded&deal_scope=transnational&deal_scope=domestic&data_source_type=1
/en/api/investor_country_summaries.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational&deal_scope=domestic&data_source_type=1
/en/api/investor_country_summaries.json?negotiation_status=failed&deal_scope=transnational&deal_scope=domestic&data_source_type=1

/en/api/target_country_summaries.json?negotiation_status=intended&deal_scope=transnational&deal_scope=domestic
/en/api/target_country_summaries.json?negotiation_status=concluded&deal_scope=transnational&deal_scope=domestic
/en/api/target_country_summaries.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational&deal_scope=domestic
/en/api/target_country_summaries.json?negotiation_status=failed&deal_scope=transnational&deal_scope=domestic
/en/api/target_country_summaries.json?negotiation_status=intended&deal_scope=transnational&deal_scope=domestic&data_source_type=1
/en/api/target_country_summaries.json?negotiation_status=concluded&deal_scope=transnational&deal_scope=domestic&data_source_type=1
/en/api/target_country_summaries.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational&deal_scope=domestic&data_source_type=1
/en/api/target_country_summaries.json?negotiation_status=failed&deal_scope=transnational&deal_scope=domestic&data_source_type=1

/en/api/agricultural-produce.json?negotiation_status=intended&deal_scope=domestic
/en/api/agricultural-produce.json?negotiation_status=intended&deal_scope=transnational
/en/api/agricultural-produce.json?negotiation_status=intended&deal_scope=domestic&deal_scope=transnational
/en/api/agricultural-produce.json?negotiation_status=concluded&deal_scope=domestic
/en/api/agricultural-produce.json?negotiation_status=concluded&deal_scope=transnational
/en/api/agricultural-produce.json?negotiation_status=concluded&deal_scope=domestic&deal_scope=transnational
/en/api/agricultural-produce.json?negotiation_status=intended&negotiation_status=concluded&deal_scope=domestic
/en/api/agricultural-produce.json?negotiation_status=intended&negotiation_status=concluded&deal_scope=transnational
/en/api/agricultural-produce.json?negotiation_status=intended&negotiation_status=concluded&deal_scope=domestic&deal_scope=transnational
/en/api/agricultural-produce.json?negotiation_status=failed&deal_scope=domestic
/en/api/agricultural-produce.json?negotiation_status=failed&deal_scope=transnational
/en/api/agricultural-produce.json?negotiation_status=failed&deal_scope=domestic&deal_scope=transnational
/en/api/agricultural-produce.json?negotiation_status=intended&deal_scope=domestic&data_source_type=1
/en/api/agricultural-produce.json?negotiation_status=intended&deal_scope=transnational&data_source_type=1
/en/api/agricultural-produce.json?negotiation_status=intended&deal_scope=domestic&deal_scope=transnational&data_source_type=1
/en/api/agricultural-produce.json?negotiation_status=concluded&deal_scope=domestic&data_source_type=1
/en/api/agricultural-produce.json?negotiation_status=concluded&deal_scope=transnational&data_source_type=1
/en/api/agricultural-produce.json?negotiation_status=concluded&deal_scope=domestic&deal_scope=transnational&data_source_type=1
/en/api/agricultural-produce.json?negotiation_status=intended&negotiation_status=concluded&deal_scope=domestic&data_source_type=1
/en/api/agricultural-produce.json?negotiation_status=intended&negotiation_status=concluded&deal_scope=transnational&data_source_type=1
/en/api/agricultural-produce.json?negotiation_status=intended&negotiation_status=concluded&deal_scope=domestic&deal_scope=transnational&data_source_type=1
/en/api/agricultural-produce.json?negotiation_status=failed&deal_scope=domestic&data_source_type=1
/en/api/agricultural-produce.json?negotiation_status=failed&deal_scope=transnational&data_source_type=1
/en/api/agricultural-produce.json?negotiation_status=failed&deal_scope=domestic&deal_scope=transnational&data_source_type=1

/en/api/hectares.json?negotiation_status=intended&deal_scope=domestic
/en/api/hectares.json?negotiation_status=intended&deal_scope=transnational
/en/api/hectares.json?negotiation_status=intended&deal_scope=transnational&deal_scope=domestic
/en/api/hectares.json?negotiation_status=concluded&deal_scope=domestic
/en/api/hectares.json?negotiation_status=concluded&deal_scope=transnational
/en/api/hectares.json?negotiation_status=concluded&deal_scope=transnational&deal_scope=domestic
/en/api/hectares.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=domestic
/en/api/hectares.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational
/en/api/hectares.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational&deal_scope=domestic
/en/api/hectares.json?negotiation_status=failed&deal_scope=domestic
/en/api/hectares.json?negotiation_status=failed&deal_scope=transnational
/en/api/hectares.json?negotiation_status=failed&deal_scope=transnational&deal_scope=domestic
/en/api/hectares.json?negotiation_status=intended&deal_scope=domestic&data_source_type=1
/en/api/hectares.json?negotiation_status=intended&deal_scope=transnational&data_source_type=1
/en/api/hectares.json?negotiation_status=intended&deal_scope=transnational&deal_scope=domestic&data_source_type=1
/en/api/hectares.json?negotiation_status=concluded&deal_scope=domestic&data_source_type=1
/en/api/hectares.json?negotiation_status=concluded&deal_scope=transnational&data_source_type=1
/en/api/hectares.json?negotiation_status=concluded&deal_scope=transnational&deal_scope=domestic&data_source_type=1
/en/api/hectares.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=domestic&data_source_type=1
/en/api/hectares.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational&data_source_type=1
/en/api/hectares.json?negotiation_status=concluded&negotiation_status=intended&deal_scope=transnational&deal_scope=domestic&data_source_type=1
/en/api/hectares.json?negotiation_status=failed&deal_scope=domestic&data_source_type=1
/en/api/hectares.json?negotiation_status=failed&deal_scope=transnational&data_source_type=1
/en/api/hectares.json?negotiation_status=failed&deal_scope=transnational&deal_scope=domestic&data_source_type=1
"""


class JSONView(TemplateView):

    BASE_FILTER_MAP = {
        "concluded": ("concluded (oral agreement)", "concluded (contract signed)"),
        "intended": ("intended (expression of interest)", "intended (under negotiation)" ),
        "failed": ("failed (contract canceled)", "failed (negotiations failed)"),
    }

    template_name = "plugins/overview.html"

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('type') == 'negotiation_status.json':
            return NegotiationStatusJSONView().dispatch(request, args, kwargs)
        elif kwargs.get('type') == "implementation_status.json":
            return ImplementationStatusJSONView().dispatch(request, args, kwargs)
        elif kwargs.get('type') == "intention_of_investment.json":
            return IntentionOfInvestmentJSONView().dispatch(request, args, kwargs)
        raise ValueError('Could not dispatch: ' + str(kwargs))

    def _get_filter(self, negotiation_status, deal_scope, data_source_type):
        filter_sql = ""
        if len(deal_scope) == 0:
            # when no negotiation stati or deal scope given no deals should be shown at the public interface
            return " AND 1 <> 1 "
        if negotiation_status:
            stati = []
            for n in negotiation_status:
                stati.extend(self.BASE_FILTER_MAP.get(n))
            filter_sql += " AND LOWER(negotiation.attributes->'pi_negotiation_status') IN ('%s') " % "', '".join(stati)
        if len(deal_scope) == 1:
            filter_sql += " AND deal_scope.attributes->'deal_scope' = '%s' " % deal_scope[0]
        if data_source_type:
            filter_sql += """ AND NOT (
            SELECT ARRAY_AGG(data_source_type.attributes->'type')
            FROM %s AS data_source_type
            WHERE a.id = data_source_type.fk_activity_id AND data_source_type.attributes ? 'type'
        ) = ARRAY['Media report']""" % ActivityAttributeGroup._meta.db_table

        return filter_sql


class NegotiationStatusJSONView(JSONView):

    def dispatch(self, request, *args, **kwargs):
        with_names = list(self.get_negotiation_status(request))
        return HttpResponse(json.dumps(with_names, cls=DecimalEncoder))

    def get_negotiation_status(self, request):
        filter_sql = self._get_filter(request.GET.getlist("negotiation_status", []), request.GET.getlist("deal_scope", []), request.GET.get("data_source_type"))
        queryset = NegotiationStatusQuerySet()
        queryset.set_filter_sql(filter_sql)
        return queryset.all()


from api.query_sets.implementation_status_query_set import ImplementationStatusQuerySet


class ImplementationStatusJSONView(JSONView):


    def dispatch(self, request, *args, **kwargs):
        with_names = list(self.get_implementation_status(request))
        return HttpResponse(json.dumps(with_names, cls=DecimalEncoder))

    def get_implementation_status(self, request):
        filter_sql = self._get_filter(request.GET.getlist("negotiation_status", []), request.GET.getlist("deal_scope", []), request.GET.get("data_source_type"))
        queryset = ImplementationStatusQuerySet()
        queryset.set_filter_sql(filter_sql)
        return queryset.all()


class IntentionOfInvestmentJSONView(JSONView):

    def dispatch(self, request, *args, **kwargs):
        filter_sql = self._get_filter(request.GET.getlist("negotiation_status", []), request.GET.getlist("deal_scope", []), request.GET.get("data_source_type"))
        parent_intention = request.GET.get("intention", "")
        found = self.get_intention(filter_sql, parent_intention)
        return HttpResponse(json.dumps(found, cls=DecimalEncoder))

    def get_intention(self, filter_sql, parent_intention):
        queryset = IntentionQuerySet()
        queryset.set_intention(parent_intention)
        queryset.set_filter_sql(filter_sql)
        return queryset.all()
