import json

import collections
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.generic import View
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.schemas import ManualSchema
import coreapi
import coreschema

from api.utils import PropertyCounter
from grid.views.activity_protocol import ActivityQuerySet
from api.query_sets.deals_query_set import DealsQuerySet
from api.query_sets.latest_changes_query_set import LatestChangesQuerySet
from api.query_sets.statistics_query_set import StatisticsQuerySet
from api.serializers import DealSerializer, UserSerializer
from api.pagination import FakeQuerySetPagination
from api.views.base import FakeQuerySetListView
from landmatrix.models import Country
from landmatrix.models.activity import ActivityBase

from django.conf import settings

from geojson import FeatureCollection, Feature, Point
from api.filters import load_filters, FILTER_FORMATS_ELASTICSEARCH
from grid.forms.choices import INTENTION_AGRICULTURE_MAP, INTENTION_FORESTRY_MAP
from map.views import MapSettingsMixin

User = get_user_model()

INTENTION_EXCLUDE = list(INTENTION_AGRICULTURE_MAP.keys())
INTENTION_EXCLUDE.extend(list(INTENTION_FORESTRY_MAP.keys()))

class UserListView(ListAPIView):
    """
    The users list view is used by the impersonate user feature of the editor.
    """
    queryset = User.objects.all().order_by('first_name')
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)


class StatisticsListView(FakeQuerySetListView):
    """
    Get deal aggregations grouped by Negotiation status.
    Used by the CMS plugin „statistics“ for homepages and regional/national landing pages.
    """
    schema = ManualSchema(
        fields=[
            coreapi.Field(
                "country",
                required=True,
                location="query",
                description="Country ID",
                schema=coreschema.Integer(),
            ),
            coreapi.Field(
                "region",
                required=False,
                location="query",
                description="Region ID",
                schema=coreschema.Integer(),
            ),
            coreapi.Field(
                "disable_filters",
                required=False,
                location="query",
                description="Set to 1 to disable default filters",
                schema=coreschema.Integer(),
            ),
        ]
    )
    fake_queryset_class = StatisticsQuerySet


class ActivityListView(FakeQuerySetListView):
    """List all activities"""
    fake_queryset_class = ActivityQuerySet


class LatestChangesListView(FakeQuerySetListView):
    """
    Lists recent changes to the database (add, change, delete or comment)
    """
    schema = ManualSchema(
        fields=[
            coreapi.Field(
                "n",
                required=False,
                location="query",
                description="Number of changes",
                schema=coreschema.Integer(),
            ),
            coreapi.Field(
                "target_country",
                required=True,
                location="query",
                description="Target country ID",
                schema=coreschema.Integer(),
            ),
            coreapi.Field(
                "target_region",
                required=True,
                location="query",
                description="Target region ID",
                schema=coreschema.Integer(),
            ),
        ]
    )
    fake_queryset_class = LatestChangesQuerySet


class DealListView(FakeQuerySetListView):
    fake_queryset_class = DealsQuerySet
    serializer_class = DealSerializer
    pagination_class = FakeQuerySetPagination

    def get_queryset(self):
        '''
        Don't call all on the queryset, so that it is passed to the paginator
        before evaluation.
        '''
        return self.fake_queryset_class(self.request)


class ElasticSearchView(View):
    doc_type = 'deal'
    
    # default status are the public ones. will only get replaced if well formed and allowed
    status_list = ActivityBase.PUBLIC_STATUSES
    
    def get_queryset(self):
        '''
        Don't call all on the queryset, so that it is passed to the paginator
        before evaluation.
        '''
        return self.fake_queryset_class(self.request)
    
    def create_query_from_filters(self):
        # load filters from session
        elasticsearch_query = load_filters(self.request, filter_format=FILTER_FORMATS_ELASTICSEARCH)
        # add filters from request
        elasticsearch_query = self.add_request_filters_to_elasticsearch_query(elasticsearch_query)
        
        query = {'bool': elasticsearch_query}
        return query
    
    def add_request_filters_to_elasticsearch_query(self, elasticsearch_query):
        request = self.request
        
        window = None
        if self.request.GET.get('window', None):
            lon_min, lat_min, lon_max, lat_max = self.request.GET.get('window').split(',')
            try:
                lat_min, lat_max = float(lat_min), float(lat_max)
                lon_min, lon_max = float(lon_min), float(lon_max)
                # respect the 180th meridian
                if lon_min > lon_max:
                    lon_max, lon_min = lon_min, lon_max
                if lat_min > lat_max:
                    lat_max, lat_min = lat_min, lat_max
                window = (lon_min, lat_min, lon_max, lat_max)
            except ValueError:
                pass
        
        # add geo_point window match:
        if window:
            elasticsearch_query['filter'].append({
                "geo_bounding_box" : {
                    "geo_point" : {
                        "top_left" : {
                            "lat" : float(window[3]),
                            "lon" : float(window[0])
                        },
                        "bottom_right" : {
                            "lat" : float(window[1]),
                            "lon" : float(window[2])
                        }
                    }
                }
            })
        
        # collect a proper and authorized-for-that-user status list from the requet paramert
        request_status_list = self.request.GET.getlist('status', []) 
        if self.request.user.is_staff:
            status_list_get = [int(status) for status in request_status_list if (status.isnumeric() and int(status) in dict(ActivityBase.STATUS_CHOICES).keys())]
            if status_list_get:
                self.status_list = status_list_get
                
        elasticsearch_query['filter'].append({
            "bool": {
                'should': [
                    {'match': {'status': status}} for status in self.status_list
                ]
            }
        })

        # Public user?
        if request.user.is_anonymous():
            elasticsearch_query['filter'].append({
                "bool": {
                    "filter": {
                        "term": {
                            "is_public": 'true'
                        }
                    }
                }
            })
        
        # TODO: these were at some point in the UI. add the missing filters!
        request_filters = {
            'deal_scope': request.GET.getlist('deal_scope', ['domestic', 'transnational']),
            'limit': request.GET.get('limit'),
            'investor_country': request.GET.get('investor_country'),
            'investor_region': request.GET.get('investor_region'),
            'target_country': request.GET.get('target_country'),
            'target_region': request.GET.get('target_region'),
            'attributes': request.GET.getlist('attributes', []),
        }
        
        return elasticsearch_query
        
    def get(self, request, *args, **kwargs):
        query = self.create_query_from_filters()
        raw_result_list = self.execute_elasticsearch_query(query, self.doc_type)
        
        # filter results
        result_list = self.filter_returned_results(raw_result_list)
        # parse results
        features = filter(None, [self.create_feature_from_result(result) for result in result_list])
        response = Response(FeatureCollection(features))
        return response
    
    def execute_elasticsearch_query(self, query, doc_type='deal', fallback=True, sort=[]):
        from api.elasticsearch import es_search as es
        es.refresh_index()
        
        print('\n\n\n>> This is the executed elasticsearch query:\n')
        from pprint import pprint
        pprint(query)
        
        try:
            raw_result_list = es.search(query, doc_type=doc_type, sort=sort)
        except Exception as e:
            raise
        return raw_result_list
    
    def filter_returned_results(self, raw_result_list):
        """ Additional filtering and exclusion of unwanted results """
        result_list = []
        for raw_result in raw_result_list:
            result = raw_result['_source']
            if not raw_result['_type'] == 'deal':
                continue
            #if not 'point_lat' in result or not 'point_lon' in result:
            #    continue
            #if not result.get('intention', None): # TODO: should we hide results with no intention field value?
            #    continue
            result['id'] = raw_result['_id']
            result_list.append(result)

        # we have a special filter mode for status=STATUS_PENDING type searches, 
        # if pending deals are to be shown, matched deals with status PENDING hide all other deals
        # with the same activity_identifier that are not PENDING
        if ActivityBase.STATUS_PENDING in self.status_list:
            pending_act_ids = [res['activity_identifier'] for res in result_list if res['status'] == ActivityBase.STATUS_PENDING]
            for i in reversed(range(len(result_list))):
                res = result_list[i]
                if not res['status'] == ActivityBase.STATUS_PENDING:
                    actitvity_identifier = res['activity_identifier']
                    # this match might be hidden if there is a pending match of PENDING status
                    if actitvity_identifier in pending_act_ids:
                        print('removed ', res)
                        result_list = result_list[:-1]
        
        return result_list


class GlobalDealsView(APIView, ElasticSearchView):
    """
    Get all deals from elasticsearch index.
    Used within the map section.
    """
    schema = ManualSchema(
        fields=[
            coreapi.Field(
                "window",
                required=False,
                location="query",
                description="Longitude min/max and Latitude min/max (e.g. 0,0,0,0)  ",
                schema=coreschema.String(),
            ),

        ]
    )

    def create_feature_from_result(self, result):
        """ Create a GeoJSON-conform result. """
        
        intended_size = result.get('intended_size', None)
        intended_size = intended_size and intended_size[0] # saved as an array currently?
        contract_size = result.get('contract_size', None)
        contract_size = contract_size and contract_size[0] # saved as an array currently?
        production_size = result.get('production_size', None)
        production_size = production_size and production_size[0] # saved as an array currently?
        investor = result.get('operational_stakeholder', None)
        investor = investor and investor[0] # saved as an array currently?

        # Remove subcategories from intention
        intention = filter(lambda i: i not in INTENTION_EXCLUDE, result.get('intention', ['Unknown']))

        try:
            geometry = (float(result['point_lon']), float(result['point_lat']))
        except ValueError:
            return None
        return Feature(
            # Do not use ID for feature. Duplicate IDs lead to problems in
            # Openlayers.
            geometry=Point(geometry),
            properties={
                "url": reverse('deal_detail', kwargs={
                    'deal_id': result['activity_identifier']}),
                "intention": intention,
                "implementation": result.get('implementation_status', 'Unknown'),
                "intended_size": intended_size,
                "contract_size": contract_size,
                "production_size": production_size,
                "investor": investor,
                "identifier": result.get('activity_identifier'),
                "level_of_accuracy": result.get('level_of_accuracy', 'Unknown'),
            },
        )


class CountryDealsView(GlobalDealsView, APIView):
    """
    Get all deals grouped by country.
    Used within the map section.
    """

    def get(self, request, *args, **kwargs):
        """
        Reuse methods from globaldealsview, but group results by country.
        """
        query = self.create_query_from_filters()
        raw_result_list = self.execute_elasticsearch_query(query, self.doc_type)

        # filter results
        result_list = self.filter_returned_results(raw_result_list)

        target_countries = collections.defaultdict(PropertyCounter)

        for result in result_list:
            if result.get('target_country'):
                target_countries[result['target_country']].increment(**result)

        filter_country = self.request.GET.get('country_id')
        country_ids = [filter_country] if filter_country else target_countries.keys()
        countries = self.get_countries(*country_ids)

        features = []
        for country in countries:
            properties = {
                'name': country.name,
                'deals': target_countries[str(country.id)].counter,
                'url': country.get_absolute_url(),
                'centre_coordinates': [country.point_lon, country.point_lat],
            }
            properties.update(target_countries[str(country.id)].get_properties())
            features.append({
                'type': 'Feature',
                'id': country.code_alpha3,
                # 'geometry': json.loads(country.geom),
                'properties': properties
            })

        return Response(FeatureCollection(features))

    def get_countries(self, *ids):
        """
        Get countries with simplified geometry, to reduce size of response.
        """
        return Country.objects.defer('geom').filter(id__in=ids)


class CountryGeomView(APIView):
    """
    Get minimal geojson of requested country. This works for one country only
    due to response size but can probably be reduced with ST_dump / ST_union for
    multiple countries.
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

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        return Response(
            data={
                'type': 'Feature',
                'geometry': json.loads(self.get_queryset().simple_geom)
            }
        )

    def get_queryset(self):
        try:
            return Country.objects.extra(
                select={'simple_geom': 'ST_AsGeoJSON(ST_Simplify(geom, 0.01))'}
            ).get(
                id=self.request.GET.get('country_id')
            )
        except Country.DoesNotExist:
            raise Http404


class PolygonGeomView(GlobalDealsView, APIView):
    """
    Get a GeoJSON representation of polygons. The polygon field is provided
    through kwargs, only fields defined in the MapSettingsMixin are valid.
    Currently no filtering is in place, all polygons encountered are returned.
    If this becomes too big, spatial filtering needs to be implemented.
    """
    schema = ManualSchema(
        fields=[
            coreapi.Field(
                "polygon_field",
                required=True,
                location="path",
                description="Polygon field (contract_area, intended_area, production_area)",
                schema=coreschema.String(),
            ),
        ]
    )
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        polygon_field = kwargs.get('polygon_field')

        valid_polygon_fields = MapSettingsMixin.get_polygon_layers().keys()
        if polygon_field not in valid_polygon_fields:
            raise Http404

        # Reuse methods from GlobalDealsView

        # Get the basic query filter for Elasticsearch
        query = {}#self.create_query_from_filters()

        # Filter all objects which have an existing polygon field
        # TODO: Is there a better place and way for this?
        query = {
            'exists': {
                'field': polygon_field
            }
        }

        raw_result_list = self.execute_elasticsearch_query(query, self.doc_type)
        result_list = self.filter_returned_results(raw_result_list)

        features = []
        for result in result_list:
            feature = result.get(polygon_field)
            if feature is None:
                continue

            # Again, case sensitive: multipolygon in ES needs to be MultiPolygon
            # in GeoJSON.
            feature = json.loads(feature)
            feature['type'] = 'MultiPolygon'
            features.append(feature)

        return Response(FeatureCollection(features))
