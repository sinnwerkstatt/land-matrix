from django.http import JsonResponse
from django.urls import re_path, path
from wagtail.core.rich_text import expand_db_html

from apps.landmatrix.views.greennewdeal import vuebase, gis_export
from apps.message.views import messages_json


def rootpage_json(request):
    from apps.wagtailcms.models import WagtailRootPage

    rp: WagtailRootPage = WagtailRootPage.objects.first()
    return JsonResponse(
        {
            "map_introduction": rp.map_introduction,
            "data_introduction": rp.data_introduction,
            "footer_columns": [
                expand_db_html(rp.footer_column_1),
                expand_db_html(rp.footer_column_2),
                expand_db_html(rp.footer_column_3),
                expand_db_html(rp.footer_column_4),
            ],
        }
    )


urlpatterns = [
    re_path(r"^newdeal/(?P<path>.*)/$", vuebase),
    path("newdeal/data.geojson", gis_export),
    path("newdeal/", vuebase),
    path("newdeal_legacy/rootpage/", rootpage_json),
    path("newdeal_legacy/messages/", messages_json),
]


# oldroutes = [
#     (r"/deal/(?P<deal_id>\d*)/$", DealDetailView.as_view()),
#     (r"/deal/(?P<deal_id>\d*)/(?P<history_id>\d+)/$", DealDetailView.as_view()),
#     (r"/investor/(?P<investor_id>\d*)/$", InvestorDetailView.as_view()),
#     (
#         r"/investor/(?P<investor_id>\d*)/(?P<history_id>\d+)/$",
#         InvestorDetailView.as_view(),
#     ),
# ]
#
#
# def gnd_switch(request, *args, **kwargs):
#     gnd_toggle = request.COOKIES.get("gnd_toggle") or "off"
#     if gnd_toggle == "on":
#         return vuebase(request)
#     else:
#         for route, target in oldroutes:
#             if re.match(route, request.path):
#                 return target(request, *args, **kwargs)
#
#
# def toggle_gnd(request):
#     gnd_toggle = request.COOKIES.get("gnd_toggle") or "off"
#     response = HttpResponseRedirect(redirect_to=request.GET.get("next") or "/")
#     response.set_cookie("gnd_toggle", "on" if gnd_toggle == "off" else "off")
#     return response
#
#
# urlpatterns = [
#     path("toggle_gnd/", toggle_gnd),
#     # re_path(r"^(?P<path>.*)/$", vuebase), path("", vuebase),
#     path("deal/<int:deal_id>/", gnd_switch, name="deal_detail"),
#     path("deal/<int:deal_id>/<int:history_id>/", gnd_switch, name="deal_detail"),
#     path("investor/<int:investor_id>/", gnd_switch, name="investor_detail"),
#     path(
#         "investor/<int:investor_id>/<int:history_id>/",
#         gnd_switch,
#         name="investor_detail",
#     ),
# ]