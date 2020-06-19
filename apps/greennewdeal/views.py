import warnings

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from reversion.models import Version

from apps.greennewdeal.models import Country, Deal, Location


@cache_page(5)
def vuebase(request, path=None):
    return render(request, template_name="greennewdeal/vuebase.html")


# def gis_export(request):
#     jsons = [
#         x.geojson["features"] for x in Location.objects.filter(deal__status__in=(2, 3))
#     ]
#     import geopandas
#     import fiona
#
#     fiona.supported_drivers["KML"] = "rw"
#     # pts = [x for x in self.geojson["features"] if x["geometry"]["type"] != "Point"]
#     x = geopandas.GeoDataFrame.from_features(jsons)
#     gisdir = mkdtemp(prefix="gis_export")
#     x.to_file("/tmp/mbla.shp")
#     x.to_file("/tmp/bla.kml", driver="KML")
#     return


# def case_statistics(request):
#     Version.objects.get_for_model(Deal).filter(revision__date_created)


def old_api_latest_changes(request):
    warnings.warn("GND Obsoletion Warning", FutureWarning)
    """
    This can be done like so:
    {
      deals(sort:"-timestamp"){
        id
        timestamp
        country { name }
      }
    }
    """
    deals = [
        {
            "action": "Add" if deal["status"] == 2 else "Change",
            "deal_id": deal["id"],
            "change_date": deal["timestamp"],
            "target_country": deal["target_country__name"],
        }
        for deal in Deal.objects.visible()
        .values("id", "timestamp", "country__name", "status")
        .order_by("-timestamp")[:20]
    ]
    return JsonResponse(deals, safe=False)
