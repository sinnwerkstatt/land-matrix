from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from grid.views.activity_protocol import ActivityQuerySet
from api.query_sets.deals_query_set import DealsQuerySet
from api.query_sets.latest_changes_query_set import LatestChangesQuerySet
from api.query_sets.statistics_query_set import StatisticsQuerySet
from api.serializers import DealSerializer, UserSerializer
from api.pagination import FakeQuerySetPagination
from api.views.base import FakeQuerySetListView


User = get_user_model()


class UserListView(ListAPIView):
    '''
    The users list view is used by the impersonate user feature of the editor.
    '''
    queryset = User.objects.all().order_by('first_name')
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)


class StatisticsListView(FakeQuerySetListView):
    fake_queryset_class = StatisticsQuerySet


class ActivityListView(FakeQuerySetListView):
    fake_queryset_class = ActivityQuerySet


class LatestChangesListView(FakeQuerySetListView):
    '''
    Lists recent changes to the database (add, change, delete or comment)
    '''
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


class GlobalDealsView(APIView):
    """
    Mock required response
    """
    def get(self, request, *args, **kwargs):
        return Response(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "name": "Germany",
                            "deals": 54,
                            "url": "/en/germany",
                            "intention": {
                                "agricultutre": 6,
                                "tourism": 2
                            },
                            "accuracy": {
                                "1km": 3,
                                "10km": 4
                            },
                            "status": {
                                "completed": 3,
                                "failed": 2
                            },
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[9.921906, 54.983104], [9.93958, 54.596642],
                                 [10.950112, 54.363607], [10.939467, 54.008693],
                                 [11.956252, 54.196486], [12.51844, 54.470371],
                                 [13.647467, 54.075511], [14.119686, 53.757029],
                                 [14.353315, 53.248171], [14.074521, 52.981263],
                                 [14.4376, 52.62485], [14.685026, 52.089947],
                                 [14.607098, 51.745188], [15.016996, 51.106674],
                                 [14.570718, 51.002339], [14.307013, 51.117268],
                                 [14.056228, 50.926918], [13.338132, 50.733234],
                                 [12.966837, 50.484076], [12.240111, 50.266338],
                                 [12.415191, 49.969121], [12.521024, 49.547415],
                                 [13.031329, 49.307068], [13.595946, 48.877172],
                                 [13.243357, 48.416115], [12.884103, 48.289146],
                                 [13.025851, 47.637584], [12.932627, 47.467646],
                                 [12.62076, 47.672388], [12.141357, 47.703083],
                                 [11.426414, 47.523766], [10.544504, 47.566399],
                                 [10.402084, 47.302488], [9.896068, 47.580197],
                                 [9.594226, 47.525058], [8.522612, 47.830828],
                                 [8.317301, 47.61358], [7.466759, 47.620582],
                                 [7.593676, 48.333019], [8.099279, 49.017784],
                                 [6.65823, 49.201958], [6.18632, 49.463803],
                                 [6.242751, 49.902226], [6.043073, 50.128052],
                                 [6.156658, 50.803721], [5.988658, 51.851616],
                                 [6.589397, 51.852029], [6.84287, 52.22844],
                                 [7.092053, 53.144043], [6.90514, 53.482162],
                                 [7.100425, 53.693932], [7.936239, 53.748296],
                                 [8.121706, 53.527792], [8.800734, 54.020786],
                                 [8.572118, 54.395646], [8.526229, 54.962744],
                                 [9.282049, 54.830865], [9.921906, 54.983104]]],
                        },
                        "id": "GER"
                    },
                    {
                        "type": "Feature",
                        "id": "MLI",
                        "properties": {
                            "name": "Mail",
                            "deals": 126,
                            "url": "/en/mali",
                            "intention": {
                                "agricultutre": 1,
                                "tourism": 8
                            },
                            "accuracy": {
                                "1km": 6,
                                "10km": 2
                            },
                            "status": {
                                "completed": 4,
                                "failed": 1
                            },
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                         [[-12.17075, 14.616834], [-11.834208, 14.799097],
                          [-11.666078, 15.388208], [-11.349095, 15.411256],
                          [-10.650791, 15.132746], [-10.086846, 15.330486],
                          [-9.700255, 15.264107], [-9.550238, 15.486497],
                          [-5.537744, 15.50169], [-5.315277, 16.201854],
                          [-5.488523, 16.325102], [-5.971129, 20.640833],
                          [-6.453787, 24.956591], [-4.923337, 24.974574],
                          [-1.550055, 22.792666], [1.823228, 20.610809],
                          [2.060991, 20.142233], [2.683588, 19.85623],
                          [3.146661, 19.693579], [3.158133, 19.057364],
                          [4.267419, 19.155265], [4.27021, 16.852227],
                          [3.723422, 16.184284], [3.638259, 15.56812],
                          [2.749993, 15.409525], [1.385528, 15.323561],
                          [1.015783, 14.968182], [0.374892, 14.928908],
                          [-0.266257, 14.924309], [-0.515854, 15.116158],
                          [-1.066363, 14.973815], [-2.001035, 14.559008],
                          [-2.191825, 14.246418], [-2.967694, 13.79815],
                          [-3.103707, 13.541267], [-3.522803, 13.337662],
                          [-4.006391, 13.472485], [-4.280405, 13.228444],
                          [-4.427166, 12.542646], [-5.220942, 11.713859],
                          [-5.197843, 11.375146], [-5.470565, 10.95127],
                          [-5.404342, 10.370737], [-5.816926, 10.222555],
                          [-6.050452, 10.096361], [-6.205223, 10.524061],
                          [-6.493965, 10.411303], [-6.666461, 10.430811],
                          [-6.850507, 10.138994], [-7.622759, 10.147236],
                          [-7.89959, 10.297382], [-8.029944, 10.206535],
                          [-8.335377, 10.494812], [-8.282357, 10.792597],
                          [-8.407311, 10.909257], [-8.620321, 10.810891],
                          [-8.581305, 11.136246], [-8.376305, 11.393646],
                          [-8.786099, 11.812561], [-8.905265, 12.088358],
                          [-9.127474, 12.30806], [-9.327616, 12.334286],
                          [-9.567912, 12.194243], [-9.890993, 12.060479],
                          [-10.165214, 11.844084], [-10.593224, 11.923975],
                          [-10.87083, 12.177887], [-11.036556, 12.211245],
                          [-11.297574, 12.077971], [-11.456169, 12.076834],
                          [-11.513943, 12.442988], [-11.467899, 12.754519],
                          [-11.553398, 13.141214], [-11.927716, 13.422075],
                          [-12.124887, 13.994727], [-12.17075, 14.616834]]]
                        }
                    }
                ]
            }
        )
