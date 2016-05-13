from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from landmatrix.models.filter_preset import FilterPreset as FilterPresetModel
from api.filters import Filter, PresetFilter
from api.serializers import FilterPresetSerializer


__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class FilterView(APIView):

    def get_object(self):
        return self.request.session.get('filters', {})

    def post(self, request, *args, **kwargs):
        '''
        TODO: make this a PATCH, and more RESTful
        '''
        stored_filters = self.get_object()

        values = dict(request.data)
        action = values.pop('action', '')
        if isinstance(action, list):
            action = action.pop()
        name = values.get('name', [None]).pop()

        if action.lower() == 'set':
            if 'preset' in values:
                new_filter = PresetFilter(values['preset'], name)
            else:
                new_filter = Filter(
                    values['variable'], values['operator'], values['value'],
                    name)

            stored_filters[new_filter.name] = new_filter
        elif action.lower() == 'remove':
            stored_filters.pop(name)

        request.session['filters'] = stored_filters

    def get(self, request, *args, **kwargs):
        filters = self.get_object()

        return Response(filters)


class FilterPresetView(ListAPIView):
    '''
    The filter preset view returns a list of presets, filtered by group.
    If the show_groups query param is present, it instead returns a list of
    groups.
    '''
    serializer_class = FilterPresetSerializer

    def get_queryset(self):
        queryset = FilterPresetModel.objects.all()
        group_name = self.request.query_params.get('group', None)
        if group_name and 'show_groups' not in self.request.query_params:
            queryset = queryset.filter(group=group_name)

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if 'show_groups' in request.query_params:
            groups = queryset.values_list('group', flat=True).distinct()
            response = Response(groups)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)

        return response


class DashboardFilterView(APIView):

    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.session.get('dashboard_filters', {})

    def post(self, request, *args, **kwargs):
        '''
        TODO: user PATCH/DELETE here
        '''
        new_filters = {}
        action = request.data.get('action', 'clear').lower()

        if action == 'set':
            if 'country' in request.data:
                new_filters['country'] = request.data.getlist('country')
            elif 'region' in request.data:
                new_filters['region'] = request.data.getlist('region')
            elif 'user' in request.data:
                new_filters['user'] = request.data.getlist('user')

        self.request.session['dashboard_filters'] = new_filters

        return Response(new_filters)

    def get(self, request, *args, **kwargs):
        filters = self.get_object()

        return Response(filters)
