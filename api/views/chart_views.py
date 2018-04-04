from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.schemas import ManualSchema
from rest_framework.views import APIView

import coreapi
import coreschema

from landmatrix.models import Country, Region, AgriculturalProduce, Animal, Mineral, Crop
from grid.forms.choices import (INTENTION_OIL_GAS_EXTRACTION, INTENTION_FOREST_LOGGING,
    NATURE_CONCESSION, NATURE_CONTRACT_FARMING, INTENTION_AGRICULTURE_MAP, INTENTION_FORESTRY_MAP)
from .list_views import ElasticSearchMixin

LONG_COUNTRIES = {
    'United States of America': 'Usa*',
    'United Kingdom of Great Britain and Northern Ireland': 'Uk*',
    'China, Hong Kong Special Administrative Region': 'China, Hong Kong*',
    'China, Macao Special Administrative Region': 'China, Macao*',
    'Lao People\'s Democratic Republic': 'Laos*',
    'United Republic of Tanzania': 'Tanzania*',
    'Democratic Republic of the Congo': 'DRC*',
    'Bolivia (Plurinational State of)': 'Bolivia*',
    'The Former Yugoslav Republic of Macedonia': 'Macedonia*',
    'Venezuela (Bolivarian Republic of)': 'Venezuela*',
    'Republic of Moldova': 'Moldova*',
    'United Arab Emirates': 'Arab Emirates*',
    'Solomon Islands': 'Solomon Iss*',
    'Russian Federation': 'Russian Fed*',
    'Dominican Republic': 'Dominican Rep*',
    'Papua New Guinea': 'Papua New*',
    'Democratic People\'s Republic of Korea': 'North Korea*',
    'United States Virgin Islands': 'Virgin Iss*',
    'Iran (Islamic Republic of)': 'Iran*',
    'Syrian Arab Republic': 'Syria*',
    'Republic of Korea': 'South Korea*',
    'C\xf4te d\'Ivoire': 'Cote d\'Ivoire',
    'British Virgin Islands': 'British Virgin Iss*',
}


class BaseChartView(ElasticSearchMixin,
                    APIView):

    aggregation_field = ''
    exclude_filters = []

    def get_query(self):
        return self.create_query_from_filters(exclude=self.exclude_filters)

    def get_aggregations(self):
        return {
            self.aggregation_field: {
                'terms': {
                    'field': self.aggregation_field,
                    'size': 300,
                },
                'aggs': {
                    'deal_count': {
                        'cardinality': {
                            'field': 'activity_identifier',
                        }
                    },
                    'deal_size_sum': {
                        'sum': {
                            'field': 'deal_size'
                        }
                    }
                }
            }
        }

    def get_results(self, response):
        return response[self.aggregation_field]['buckets']

    def get_result(self, raw_result):
        return {
            'name': raw_result['key'],
            'deals': raw_result['deal_count']['value'],
            'hectares': int(raw_result['deal_size_sum']['value'])
        }

    def get(self, request):
        response = self.execute_elasticsearch_query(self.get_query(),
                                                    aggs=self.get_aggregations(),
                                                    doc_type='deal',
                                                    fallback=False)

        results = []
        for raw_result in self.get_results(response):
            result = self.get_result(raw_result)
            if result:
                results.append(result)

        return Response(results)

    class Meta:
        abstract = True


class NegotiationStatusListView(BaseChartView):
    """
    Get deal aggregations grouped by Negotiation status.
    Used within the charts section.
    """
    aggregation_field = 'current_negotiation_status'
    exclude_filters = ['current_negotiation_status', 'negotiation_status']


class ResourceExtractionView(NegotiationStatusListView):
    """
    Get deal aggregations for Resource Extraction deals grouped by Negotiation status.
    Used within the charts section.
    """
    exclude_filters = ['current_negotiation_status', 'negotiation_status', 'intention']

    def get_query(self):
        query = self.create_query_from_filters(exclude=self.exclude_filters)
        query['bool']['filter'].append({
            'term': {
                'intention': INTENTION_OIL_GAS_EXTRACTION
            }
        })
        return query


class LoggingView(NegotiationStatusListView):
    """
    Get deal aggregations for Logging deals grouped by Negotiation status.
    Used within the charts section.
    """
    exclude_filters = ['current_negotiation_status', 'negotiation_status', 'intention', 'nature']

    def get_query(self):
        query = self.create_query_from_filters(exclude=self.exclude_filters)
        query['bool']['filter'].append({
            'bool': {'should': [
                {'term': {'intention': INTENTION_FOREST_LOGGING}},
                {'term': {'nature': NATURE_CONCESSION}},
            ], 'minimum_should_match': 1
            }
        })
        return query


class ContractFarmingView(NegotiationStatusListView):
    """
    Get deal aggregations for Contract Farming deals grouped by Negotiation status.
    Used within the charts section.
    """
    exclude_filters = ['current_negotiation_status', 'negotiation_status', 'nature']

    def get_query(self):
        query = self.create_query_from_filters(exclude=self.exclude_filters)
        query['bool']['must'].append({
            'term': {
                'nature': NATURE_CONTRACT_FARMING
            }
        })
        return query


class ImplementationStatusListView(BaseChartView):
    """
    Get deal aggregations grouped by Implementation status.
    Used within the charts section.
    """
    aggregation_field = 'current_implementation_status'
    exclude_filters = ['current_implementation_status', 'implementation_status']


class InvestmentIntentionListView(BaseChartView):
    """
    Get deal aggregations grouped by Intention.
    Used within the charts section.
    """
    schema = ManualSchema(
        fields=[
            coreapi.Field(
                "intention",
                required=False,
                location="query",
                description="Parent intention",
                schema=coreschema.String(),
            ),
        ]
    )

    aggregation_field = 'intention'
    exclude_filters = ['intention',]

    def get_parent_intention(self, intention):
        if intention in ('Agriculture', 'Forestry'):
            return ''
        elif intention in INTENTION_AGRICULTURE_MAP.keys():
            return _('Agriculture')
        elif intention in INTENTION_FORESTRY_MAP.keys():
            return _('Forestry')
        else:
            return _('Other')

    def get_query(self):
        query = self.create_query_from_filters(exclude=self.exclude_filters)
        parent_intention = self.request.GET.get('intention', None)
        if parent_intention:
            if parent_intention.lower() == 'agriculture':
                intentions = INTENTION_AGRICULTURE_MAP.keys()
            elif parent_intention.lower() == 'forestry':
                intentions = INTENTION_FORESTRY_MAP.keys()
            query['bool']['filter'].append({
                'terms': {
                    'intention': list(intentions)
                }
            })
        return query

    def get_result(self, raw_result):
        if raw_result['key'] in ('Agriculture', 'Forestry'):
            return {}
        else:
            return {
                'name': raw_result['key'],
                'deals': raw_result['deal_count']['value'],
                'hectares': int(raw_result['deal_size_sum']['value']),
                'parent': self.get_parent_intention(raw_result['key']),
            }

    def get_multi_aggregations(self):
        return {
            'deal_count': {
                'cardinality': {
                    'field': 'activity_identifier',
                }
            },
            'deal_size_sum': {
                'sum': {
                    'field': 'deal_size'
                }
            }
        }

    def get(self, request):
        # First: Filter results with one intention
        query = self.get_query()
        query['bool']['filter'].append({
            'bool': {'should': [
                {'bool': {'must': [
                    {'terms': {'intention': ['Agriculture', 'Forestry']}},
                    {'script': {'script': "doc['intention'].values.size() <= 2"}},
                ]}},
                {'bool': {'must': [
                    {'script': {'script': "doc['intention'].values.size() <= 1"}},
                ], 'must_not': [
                    {'terms': {'intention': ['Agriculture', 'Forestry']}},
                ]}},
            ], 'minimum_should_match': 1
        }})
        response = self.execute_elasticsearch_query(query,
                                                    aggs=self.get_aggregations(),
                                                    doc_type='deal',
                                                    fallback=False)
        results = []
        for raw_result in self.get_results(response):
            result = self.get_result(raw_result)
            if result:
                results.append(result)


        # Then: Filter results with multiple intentions
        query = self.get_query()
        query['bool']['filter'].append({
            'bool': {'should': [
                {'bool': {'must': [
                    {'terms': {'intention': ['Agriculture', 'Forestry']}},
                    {'script': {'script': "doc['intention'].values.size() > 2"}},
                ]}},
                {'bool': {'must': [
                    {'script': {'script': "doc['intention'].values.size() > 1"}},
                ], 'must_not': [
                    {'terms': {'intention': ['Agriculture', 'Forestry']}},
                ]}},
            ], 'minimum_should_match': 1
        }})
        response = self.execute_elasticsearch_query(self.get_query(),
                                                    aggs=self.get_multi_aggregations(),
                                                    doc_type='deal',
                                                    fallback=False)
        results.append({
            'name': _('Multiple intentions'),
            'deals': response['deal_count']['value'],
            'hectares': int(response['deal_size_sum']['value']),
            'parent': _('Other'),
        })

        return Response(results)


class InvestorCountrySummaryView(BaseChartView):
    """
    Get deal aggregations grouped by Investor country.
    """
    aggregation_field = 'investor_country'

    def get(self, request):
        query = {
            'has_parent': {
                'type': 'deal',
                'query': self.get_query(),
            }
        }
        response = self.execute_elasticsearch_query(query,
                                                    aggs=self.get_aggregations(),
                                                    doc_type='involvement_size',
                                                    fallback=False)

        # FIXME: Maybe make available countries in ES as well
        countries = Country.objects.defer('geom').select_related('fk_region').all()
        countries = dict([(str(c.id), c) for c in countries])
        results = []
        for raw_result in self.get_results(response):
            result = self.get_result(raw_result)
            country = countries.get(raw_result['key'])
            url = reverse("table_list", kwargs={
                "group": "by-investor-country",
                "group_value": country.slug
            })
            result.update({
                'lat_min': country.point_lat_min,
                'lat_max': country.point_lat_max,
                'lon_min': country.point_lon_min,
                'lon_max': country.point_lon_max,
                'lat': country.point_lat,
                'lon': country.point_lon,
                'country': country.name,
                'name': country.name,
                'country_slug': country.slug,
                'region': country.fk_region.name,
                'region_slug': country.fk_region.slug,
                'url': url,
            })
            results.append(result)

        return Response(results)

    def get_aggregations(self):
        return {
            self.aggregation_field: {
                'terms': {
                    'field': self.aggregation_field,
                    'size': 300,
                },
                'aggs': {
                    'deal_count': {
                        'cardinality': {
                            'field': 'activity_identifier',
                        }
                    },
                    'domestic': {
                        'aggs': {
                            'domestic_count': {
                                'cardinality': {
                                    'field': 'activity_identifier',
                                },
                            },
                        },
                        'filter': {
                            'term': {
                                'deal_scope': 'domestic',
                            },
                        }
                    },
                    'deal_size_sum': {
                        'sum': {
                            'field': 'deal_size'
                        }
                    }
                }
            }
        }

    def get_result(self, raw_result):
        deal_count = raw_result['deal_count']['value']
        domestic_count = raw_result['domestic']['domestic_count']['value']
        return {
            'country_id': raw_result['key'],
            'domestic': domestic_count,
            'transnational': deal_count - domestic_count,
            'deals': deal_count,
        }


class InvestorCountriesForTargetCountryView(InvestorCountrySummaryView):
    """
    Get deal aggregations grouped for Investor country.
    """
    schema = ManualSchema(
        fields=[
            coreapi.Field(
                "country_id",
                required=False,
                location="query",
                description="Country ID",
                schema=coreschema.Integer(),
            ),
        ]
    )

    def get_query(self):
        query = super().get_query()
        target_country = self.request.GET.get('country_id', '')
        if target_country:
            query['bool']['filter'].append({
                'term': {
                    'target_country': target_country
                }
            })
        return query


class TargetCountrySummaryView(BaseChartView):
    """
    Get deal aggregations grouped by Target country.
    """
    aggregation_field = 'target_country'

    def get(self, request):
        response = self.execute_elasticsearch_query(self.get_query(),
                                                    aggs=self.get_aggregations(),
                                                    doc_type='deal',
                                                    fallback=False)

        # FIXME: Maybe make available countries in ES as well
        countries = Country.objects.defer('geom').select_related('fk_region').all()
        countries = dict([(str(c.id), c) for c in countries])
        results = []
        for raw_result in self.get_results(response):
            result = self.get_result(raw_result)
            country = countries.get(raw_result['key'])
            url = reverse("table_list", kwargs={
                "group": "by-target-country",
                "group_value": country.slug
            })
            result.update({
                'lat_min': country.point_lat_min,
                'lat_max': country.point_lat_max,
                'lon_min': country.point_lon_min,
                'lon_max': country.point_lon_max,
                'lat': country.point_lat,
                'lon': country.point_lon,
                'country': country.name,
                'name': country.name,
                'country_slug': country.slug,
                'region': country.fk_region.name,
                'region_slug': country.fk_region.slug,
                'url': url,
            })
            results.append(result)

        return Response(results)

    def get_aggregations(self):
        return {
            self.aggregation_field: {
                'terms': {
                    'field': self.aggregation_field,
                    'size': 300,
                },
                'aggs': {
                    'deal_count': {
                        'cardinality': {
                            'field': 'activity_identifier',
                        }
                    },
                    'domestic': {
                        'aggs': {
                            'domestic_count': {
                                'cardinality': {
                                    'field': 'activity_identifier',
                                },
                            },
                        },
                        'filter': {
                            'term': {
                                'deal_scope': 'domestic',
                            },
                        }
                    },
                    'deal_size_sum': {
                        'sum': {
                            'field': 'deal_size'
                        }
                    }
                }
            }
        }

    def get_result(self, raw_result):
        deal_count = raw_result['deal_count']['value']
        domestic_count = raw_result['domestic']['domestic_count']['value']
        return {
            'country_id': raw_result['key'],
            'domestic': domestic_count,
            'transnational': deal_count - domestic_count,
            'deals': deal_count,
        }


class TargetCountriesForInvestorCountryView(TargetCountrySummaryView):
    """
    Get deal aggregations grouped for Target country/region.
    """
    schema = ManualSchema(
        fields=[
            coreapi.Field(
                "country_id",
                required=False,
                location="data",
                description="Country ID",
                schema=coreschema.Integer(),
            ),
            coreapi.Field(
                "region_id",
                required=False,
                location="data",
                description="Region ID",
                schema=coreschema.Integer(),
            ),
        ]
    )

    def get_query(self):
        query = super().get_query()
        investor_country = self.request.GET.get('country_id', '')
        if investor_country:
            query['bool']['filter'].append({
                'has_child': {
                    'type': 'investment_size',
                    'query': {
                        'term': {
                            'investor_country': investor_country
                        }
                    }
                }
            })
        investor_region = self.request.GET.get('region_id', '')
        if investor_region:
            query['bool']['filter'].append({
                'has_child': {
                    'type': 'investment_size',
                    'query': {
                        'term': {
                            'investor_region': investor_region
                        }
                    }
                }
            })
        return query


class Top10CountriesView(BaseChartView):
    """
    Get top 10 Investor or Target countries.
    Used within the charts section.
    """
    def get_query(self):
        query = super().get_query()
        query['bool']['filter'].append({
            'term': {
                'deal_scope': 'transnational',
            }
        })
        return query

    def get_aggregations(self):
        return {
            'target_country': {
                'terms': {
                    'field': 'target_country',
                    'size': 10,
                    'order': {'deal_size_sum': 'desc'},
                },
                'aggs': {
                    'deal_count': {
                        'cardinality': {
                            'field': 'activity_identifier',
                        }
                    },
                    'deal_size_sum': {
                        'sum': {
                            'field': 'deal_size'
                        }
                    }
                }
            },
            'investor_country': {
                'terms': {
                    'field': 'investor_country',
                    'size': 10,
                    'order': {'deal_size_sum': 'desc'},
                },
                'aggs': {
                    'deal_count': {
                        'cardinality': {
                            'field': 'activity_identifier',
                        }
                    },
                    'deal_size_sum': {
                        'sum': {
                            'field': 'deal_size'
                        }
                    }
                }
            },
        }

    def get(self, request):
        response = self.execute_elasticsearch_query(self.get_query(),
                                                    aggs=self.get_aggregations(),
                                                    doc_type='deal',
                                                    fallback=False)

        # FIXME: Maybe make available countries in ES as well
        countries = Country.objects.defer('geom').select_related('fk_region').all()
        countries = dict([(str(c.id), c) for c in countries])
        results = []

        # Get target countries
        target_countries = []
        for raw_result in response['target_country']['buckets']:
            target_country = countries.get(raw_result['key'])
            target_countries.append({
                'id': raw_result['key'],
                'name': LONG_COUNTRIES.get(target_country.name, target_country.name),
                'hectares': raw_result['deal_size_sum']['value'],
                'slug': target_country.slug,
                'deals': raw_result['deal_count']['value'],
            })

        # Get investor countries
        investor_countries = []
        for raw_result in response['investor_country']['buckets']:
            investor_country = countries.get(raw_result['key'])
            investor_countries.append({
                'id': raw_result['key'],
                'name': LONG_COUNTRIES.get(investor_country.name, investor_country.name),
                'hectares': raw_result['deal_size_sum']['value'],
                'slug': investor_country.slug,
                'deals': raw_result['deal_count']['value'],
            })

        return Response({
            'investor_country': investor_countries,
            'target_country': target_countries,
        })


class TransnationalDealListView(BaseChartView):
    """
    Get deal aggregations for transnational deals grouped by country.
    Used within the charts section.
    """
    schema = ManualSchema(
        fields=[
            coreapi.Field(
                "region",
                required=False,
                location="query",
                description="Region ID",
                schema=coreschema.Integer(),
            ),
        ]
    )
    regions = []

    def get_aggregations(self):
        return {
            'target_country': {
                'terms': {
                    'field': 'target_country',
                    'size': 300,
                },
                'aggs': {
                    'investor_country': {
                        'terms': {
                            'field': 'investor_country',
                        },
                    }
                }
            },
            'investor_country': {
                'terms': {
                    'field': 'investor_country',
                    'size': 300,
                },
            },
        }

    def get_query(self):
        query = super().get_query()
        query['bool']['filter'].append({
            'term': {
                'deal_scope': 'transnational',
            }
        })
        regions = self.request.GET.getlist("region", [])
        if regions:
            query['bool']['filter'].append({
                'terms': {
                    'target_region': self.regions
                }
            })
        return query

    def get_country_name(self, country):
        region_id = str(country.fk_region_id)
        if region_id in self.request.GET.getlist("region", []):
            region_id = -1
        return '%s.%s' % (
            region_id,
            LONG_COUNTRIES.get(country.name, country.name)
        )

    def get(self, request):
        response = self.execute_elasticsearch_query(self.get_query(),
                                                    aggs=self.get_aggregations(),
                                                    doc_type='deal',
                                                    fallback=False)

        # FIXME: Maybe make available countries in ES as well
        countries = Country.objects.defer('geom').select_related('fk_region').all()
        countries = dict([(str(c.id), c) for c in countries])
        results = []
        target_countries = []
        # Add target countries
        for raw_result in response['target_country']['buckets']:
            target_country = countries.get(raw_result['key'])
            imports = []
            for raw_term in raw_result['investor_country']['buckets']:
                investor_country = countries.get(raw_term['key'])
                imports.append(self.get_country_name(investor_country))
            results.append({
                'id': raw_result['key'],
                'imports': imports,
                'name': self.get_country_name(target_country),
                'size': 1,
                'slug': target_country.slug,
            })
            target_countries.append(raw_result['key'])
        # Add countries with no deals
        investor_countries = [r['key'] for r in response['investor_country']['buckets']]
        countries_missing = set(investor_countries) - set(target_countries)
        for country_id in countries_missing:
            country = countries.get(country_id)
            results.append({
                'id': country.id,
                'imports': [],
                'size': 1,
                'name': self.get_country_name(country),
                'slug': country.slug,

            })
        return Response(results)


class TransnationalDealsByCountryView(BaseChartView):
    """
    Get deal aggregations for transnational deals of given country grouped by role (Investor or Target country).
    Used within the charts section.
    """
    def get_query(self):
        query = super().get_query()
        query['bool']['filter'].append({
            'term': {
                'deal_scope': 'transnational',
            }
        })
        return query

    def get_aggregations(self):
        country = self.request.GET.get('country')
        if not country:
            raise ValidationError('No country specified')
        return {
            'investor_country': {
                'filter': {
                    'term': {
                        'investor_country': country,
                    }
                },
                'aggs': {
                    'target_region': {
                        'terms': {
                            'field': 'target_region',
                            'size': 300,
                            'order': {'deal_size_sum': 'desc'},
                        },
                        'aggs': {
                            'deal_count': {
                                'cardinality': {
                                    'field': 'activity_identifier',
                                }
                            },
                            'deal_size_sum': {
                                'sum': {
                                    'field': 'deal_size'
                                }
                            }
                        }
                    }
                }
            },
            'target_country': {
                'filter': {
                    'term': {
                        'target_country': country,
                    }
                },
                'aggs': {
                    'investor_region': {
                        'terms': {
                            'field': 'investor_region',
                            'size': 300,
                            'order': {'deal_size_sum': 'desc'},
                        },
                        'aggs': {
                            'deal_count': {
                                'cardinality': {
                                    'field': 'activity_identifier',
                                }
                            },
                            'deal_size_sum': {
                                'sum': {
                                    'field': 'deal_size'
                                }
                            }
                        }
                    }
                }
            }
        }

    def get(self, request):
        response = self.execute_elasticsearch_query(self.get_query(),
                                                    aggs=self.get_aggregations(),
                                                    doc_type='deal',
                                                    fallback=False)

        # FIXME: Maybe make available regions in ES as well
        regions = dict([(str(r.id), r) for r in Region.objects.all()])

        # Get target regions
        target_regions = []
        for raw_result in response['investor_country']['target_region']['buckets']:
            target_region = regions.get(raw_result['key'])
            target_regions.append({
                'region_id': raw_result['key'],
                'slug': target_region.slug,
                'region': target_region.name,
                'hectares': raw_result['deal_size_sum']['value'],
                'deals': raw_result['deal_count']['value'],
            })

        # Get investor regions
        investor_regions = []
        for raw_result in response['target_country']['investor_region']['buckets']:
            investor_region = regions.get(raw_result['key'])
            investor_regions.append({
                'region_id': raw_result['key'],
                'slug': investor_region.slug,
                'region': investor_region.name,
                'hectares': raw_result['deal_size_sum']['value'],
                'deals': raw_result['deal_count']['value'],
            })

        return Response({
            'investor_country': target_regions,
            'target_country': investor_regions,
        })


class HectaresView(BaseChartView):
    """
    Get global deal aggregations (no. of deals and size in hectares).
    Used within the charts section.
    """

    def get(self, request):
        response = self.execute_elasticsearch_query(self.get_query(),
                                                    aggs=self.get_aggregations(),
                                                    doc_type='deal',
                                                    fallback=False)
        result = {
            'deals': response['deal_count']['value'],
            'hectares': int(response['deal_size_sum']['value']),
        }
        return Response(result)

    def get_aggregations(self):
        return {
            'deal_count': {
                'cardinality': {
                    'field': 'activity_identifier',
                }
            },
            'deal_size_sum': {
                'sum': {
                    'field': 'deal_size'
                }
            }
        }


class AgriculturalProduceListView(BaseChartView):
    """
    Get deal aggregations grouped by Agricultural Produce.
    Used within the charts section.
    """
    def get_aggregations(self):
        return {
            'target_region': {
                'terms': {
                    'field': 'target_region',
                    'size': 10,
                    'order': {'deal_size_sum': 'desc'},
                },
                'aggs': {
                    'agricultural_produce': {
                        'terms': {
                            'field': 'agricultural_produce',
                            'size': 10,
                        },
                        'aggs': {
                            'deal_count': {
                                'cardinality': {
                                    'field': 'activity_identifier',
                                }
                            },
                            'deal_size_sum': {
                                'sum': {
                                    'field': 'deal_size'
                                }
                            }
                        }
                    },
                    'deal_count': {
                        'cardinality': {
                            'field': 'activity_identifier',
                        }
                    },
                    'deal_size_sum': {
                        'sum': {
                            'field': 'deal_size'
                        }
                    }
                }
            }
        }

    def slugify(self, ap):
        if ap:
            ap = ap.lower().replace('-', '_').replace(' ', '_')
            if ap == 'multi_crop':
                return 'multiple_use'
            else:
                return ap
        else:
            return None

    def get(self, request):

        # TODO: Availability

        response = self.execute_elasticsearch_query(self.get_query(),
                                                    aggs=self.get_aggregations(),
                                                    doc_type='deal',
                                                    fallback=False)

        # FIXME: Maybe make available regions in ES as well
        regions = dict([(str(r.id), r) for r in Region.objects.all()])
        agricultural_produces = dict((self.slugify(ap.name), 0) for ap in
                                     AgriculturalProduce.objects.all())
        agricultural_produces['multiple_use'] = 0

        # Get target regions
        target_regions = {}
        for id, region in regions.items():
            target_regions[id] = {
                'available': 0,
                'not_available': 0,
                'region': region.slug,
                'deals': agricultural_produces.copy(),
                'hectares': agricultural_produces.copy(),
            }
        overall = {
            'available': 0,
            'not_available': 0,
            'region': 'overall',
            'agricultural_produce': agricultural_produces.copy(),
            'hectares': agricultural_produces.copy(),
        }
        for raw_result in response['target_region']['buckets']:
            region = regions.get(raw_result['key'])
            ratios, hectares = agricultural_produces.copy(), agricultural_produces.copy()

            # First get totals
            available_sum, not_available_sum = 0, 0
            for ap in raw_result['agricultural_produce']['buckets']:
                ap_slug = self.slugify(ap['key'])
                if ap_slug:
                    available_sum += float(ap['deal_size_sum']['value'])
                else:
                    not_available_sum = float(ap['deal_size_sum']['value'])

            # Then set data and ratios
            for ap in raw_result['agricultural_produce']['buckets']:
                ap_slug = self.slugify(ap['key'])
                hectares[ap_slug] = ap['deal_size_sum']['value']
                ratios[ap_slug] = round(float(hectares[ap_slug])/available_sum*100)
                overall['hectares'][ap_slug] += ap['deal_size_sum']['value']
                overall['available'] += ap['deal_size_sum']['value']
                overall['not_available'] += ap['deal_size_sum']['value']
            target_regions[raw_result['key']] = {
                'available': available_sum,
                'not_available': not_available_sum,
                'region': region.slug,
                'agricultural_produce': ratios,
                'hectares': hectares,
            }
        for ap_slug, hectares in overall['hectares'].items():
            ratio = round(float(hectares) / overall['available'] * 100)
            overall['agricultural_produce'][ap_slug] = ratio
        target_regions['overall'] = overall

        return Response(list(target_regions.values()))
    #
    # def __init__(self, get_data):
    #     self.get_data = get_data
    #
    # def all(self):
    #     output = []
    #     for region, value in self.REGIONS.items():
    #         ap_region = {
    #             "food_crop": 0,
    #             "non_food": 0,
    #             "flex_crop": 0,
    #             "multiple_use": 0,
    #         }
    #         hectares = {
    #             "food_crop": 0,
    #             "non_food": 0,
    #             "flex_crop": 0,
    #             "multiple_use": 0,
    #         }
    #         ap_list = self.get_agricultural_produces(self.get_data, value)
    #         available_sum, not_available_sum = self.calculate_sums(ap_list)
    #
    #         for ap in ap_list:
    #             if ap['agricultural_produce']:
    #                 ap_name = ap['agricultural_produce'].lower().replace(" ", "_").replace("-", "_")
    #                 ap_region[ap_name] = round(float(ap['hectares'])/available_sum*100)
    #                 hectares[ap_name] = ap['hectares']
    #
    #         output.append({
    #             "region": region,
    #             "available": available_sum,
    #             "not_available": not_available_sum,
    #             "agricultural_produce": ap_region,
    #             "hectares": hectares,
    #         })
    #     return output
    #
    # def calculate_sums(self, ap_list):
    #     available_sum, not_available_sum = 0, 0
    #     for ap in ap_list:
    #         if ap['agricultural_produce']:
    #             available_sum += float(ap['hectares'])
    #         else:
    #             not_available_sum += float(ap['hectares'])
    #     return available_sum, not_available_sum
    #
    # def get_agricultural_produces(self, get, region_ids):
    #     queryset = AgriculturalProduceQuerySet(get, region_ids)
    #     sanitized_values = [
    #         {
    #             'agricultural_produce': item['agricultural_produce'] or 0.0,
    #             'deals': item['deals'] or 0,
    #             'hectares': item['hectares'] or 0.0,
    #         }
    #         for item in queryset.all()
    #     ]
    #     return sanitized_values


class ProduceInfoView(BaseChartView):
    """
    Get deal aggregations grouped by Animals, Minerals and Crops.
    Used within the charts section.
    """
    # """
    # Returns: {
    #     "animals": [
    #         {"name": "Birds", "size": 3938},
    #         {"name": "Apes", "size": 3812},
    #         {"name": "Sheep", "size": 6714},
    #         {"name": "Mules", "size": 743}
    #     ],
    #     "minerals": [
    #         {"name": "Iron", "size": 17010},
    #         {"name": "Aluminium", "size": 5842},
    #         {"name": "Titanium", "size": 1041},
    #         {"name": "Gold", "size": 5176}
    #     ],
    #     "crops": [
    #         {"name": "Salad", "size": 721},
    #         {"name": "Carrots", "size": 4294},
    #         {"name": "Peas", "size": 9800},
    #         {"name": "Cabbage", "size": 1314},
    #         {"name": "Radish", "size": 2220}
    #     ]
    # }
    # """
    # def __init__(self, request):
    #     self.request = request
    #
    # def all(self):
    #     response = {}
    #     animals = AnimalsQuerySet(self.request).all()#[:20]
    #     minerals = MineralsQuerySet(self.request).all()#[:20]
    #     crops = CropsQuerySet(self.request).all()#[:20]
    #     response = {
    #         "animals": filter(lambda a: a['size'] > 0, animals),
    #         "minerals": filter(lambda m: m['size'] > 0, minerals),
    #         "crops": filter(lambda c: c['size'] > 0, crops)
    #     }
    #     return response

    def get_aggregations(self):
        return {
            'crops': {
                'terms': {
                    'field': 'crops',
                    'size': 50,
                    'order': {'deal_size_sum': 'desc'},
                },
                'aggs': {
                    'deal_count': {
                        'cardinality': {
                            'field': 'activity_identifier',
                        }
                    },
                    'deal_size_sum': {
                        'sum': {
                            'field': 'deal_size'
                        }
                    }
                }
            },
            'minerals': {
                'terms': {
                    'field': 'minerals',
                    'size': 50,
                    'order': {'deal_size_sum': 'desc'},
                },
                'aggs': {
                    'deal_count': {
                        'cardinality': {
                            'field': 'activity_identifier',
                        }
                    },
                    'deal_size_sum': {
                        'sum': {
                            'field': 'deal_size'
                        }
                    }
                }
            },
            'animals': {
                'terms': {
                    'field': 'animals',
                    'size': 50,
                    'order': {'deal_size_sum': 'desc'},
                },
                'aggs': {
                    'deal_count': {
                        'cardinality': {
                            'field': 'activity_identifier',
                        }
                    },
                    'deal_size_sum': {
                        'sum': {
                            'field': 'deal_size'
                        }
                    }
                }
            }
        }

    def get(self, request):
        response = self.execute_elasticsearch_query(self.get_query(),
                                                    aggs=self.get_aggregations(),
                                                    doc_type='deal',
                                                    fallback=False)

        results = {
            'crops': [],
            'animals': [],
            'minerals': [],
        }
        # Crops
        crops = dict([(str(c.id), c) for c in Crop.objects.all()])
        for raw_result in response['crops']['buckets']:
            crop = crops.get(raw_result['key'])
            if crop:
                results['crops'].append({
                    'name': crop.name,
                    'size': int(raw_result['deal_size_sum']['value']),
                })
        # Animals
        animals = dict([(str(a.id), a) for a in Animal.objects.all()])
        for raw_result in response['animals']['buckets']:
            animal = animals.get(raw_result['key'])
            if animal:
                results['animals'].append({
                    'name': animal.name,
                    'size': int(raw_result['deal_size_sum']['value']),
                })
        # Minerals
        minerals = dict([(str(m.id), m) for m in Mineral.objects.all()])
        for raw_result in response['minerals']['buckets']:
            mineral = minerals.get(raw_result['key'])
            if mineral:
                results['minerals'].append({
                    'name': mineral.name,
                    'size': int(raw_result['deal_size_sum']['value']),
                })

        return Response(results)