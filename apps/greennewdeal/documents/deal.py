import json

from django_elasticsearch import Document, fields
from django_elasticsearch.registries import registry
from geojson_rewind import rewind

from apps.greennewdeal.models import Contract, DataSource, Deal, Investor, Location


# noinspection PyMethodMayBeStatic
@registry.register_document
class DealDocument(Document):
    class Django:
        model = Deal
        related_models = [Location, Contract, DataSource]
        fields = "__all__"

        # Don't perform an index refresh after every update (overrides global setting):
        # auto_refresh = False

    def prepare_target_country(self, instance: Deal):
        if not instance.target_country:
            return None
        return {"id": instance.target_country.id, "name": instance.target_country.name}

    def prepare_purchase_price_currency(self, instance: Deal):
        if not instance.purchase_price_currency:
            return None
        return {
            "code": instance.purchase_price_currency.code,
            "name": instance.purchase_price_currency.name,
        }

    def prepare_annual_leasing_fee_currency(self, instance: Deal):
        if not instance.annual_leasing_fee_currency:
            return None
        return {
            "code": instance.annual_leasing_fee_currency.code,
            "name": instance.annual_leasing_fee_currency.name,
        }

    def prepare_operating_company(self, instance: Deal):
        oc: Investor = instance.operating_company
        if not oc:
            return None

        country_ret = region_ret = None

        country = oc.country
        if country:
            country_ret = {"id": country.id, "name": country.name}
            region = country.fk_region
            if region:
                region_ret = {"id": region.id, "name": region.name}

        return {
            "id": oc.id,
            "investor_identifier": oc.id,
            "name": oc.name,
            "country": country_ret,
            "region": region_ret,
            "classification": oc.classification,
            "classification_display": oc.get_classification_display(),
            "homepage": oc.homepage,
            "comment": oc.comment,
            "timestamp": oc.timestamp,
            "opencorporates": oc.opencorporates,
        }

    def prepare_export_country1(self, instance: Deal):
        if not instance.export_country1:
            return None
        return {
            "id": instance.export_country1.id,
            "name": instance.export_country1.name,
        }

    def prepare_export_country2(self, instance: Deal):
        if not instance.export_country2:
            return None
        return {
            "id": instance.export_country2.id,
            "name": instance.export_country2.name,
        }

    def prepare_export_country3(self, instance: Deal):
        if not instance.export_country3:
            return None
        return {
            "id": instance.export_country3.id,
            "name": instance.export_country3.name,
        }

    activity_identifier = fields.IntegerField(attr="id")

    locations = fields.NestedField(
        properties={
            "name": fields.TextField(),
            "point": fields.GeoPointField(),
            "intended_area": fields.ObjectField(),
            "production_area": fields.ObjectField(),
            "contract_area": fields.ObjectField(),
            # "intended_area": fields.GeoShapeField(),
            # "production_area": fields.GeoShapeField(),
            # "contract_area": fields.GeoShapeField(),
        }
    )
    # datasources = fields.NestedField(
    #     properties={
    #         "type": fields.ObjectField(),
    #         "type_display": fields.ObjectField(),
    #         "url": fields.ObjectField(),
    #         "file": fields.ObjectField(),
    #         "file_not_public": fields.ObjectField(),
    #         "publication_title": fields.ObjectField(),
    #         "date": fields.ObjectField(),
    #         "name": fields.ObjectField(),
    #         "company": fields.ObjectField(),
    #         "email": fields.ObjectField(),
    #         "phone": fields.ObjectField(),
    #         "includes_in_country_verified_information": fields.ObjectField(),
    #         "open_land_contracts_id": fields.ObjectField(),
    #         "comment": fields.ObjectField(),
    #         "timestamp": fields.ObjectField(),
    #     }
    # )

    geojson = fields.ObjectField()

    def prepare_geojson(self, instance: Deal):
        features = []
        for loc in instance.locations.all():  # type: Location
            if loc.point:
                point = {
                    "type": "Feature",
                    "geometry": (json.loads(loc.point.geojson)),
                    "properties": {"name": loc.name, "type": "point"},
                }
                features += [point]
            if loc.contract_area:
                contract_area = {
                    "type": "Feature",
                    "geometry": (json.loads(loc.contract_area.geojson)),
                    "properties": {"name": loc.name, "type": "contract_area"},
                }
                features += [rewind(contract_area)]
            if loc.intended_area:
                contract_area = {
                    "type": "Feature",
                    "geometry": (json.loads(loc.intended_area.geojson)),
                    "properties": {"name": loc.name, "type": "intended_area"},
                }
                features += [rewind(contract_area)]
            if loc.production_area:
                contract_area = {
                    "type": "Feature",
                    "geometry": (json.loads(loc.production_area.geojson)),
                    "properties": {"name": loc.name, "type": "production_area"},
                }
                features += [rewind(contract_area)]
        if not features:
            return None
        return {"type": "FeatureCollection", "features": features}

    deal_size = fields.IntegerField()

    def prepare_deal_size(self, instance: Deal):
        return instance.get_deal_size()

    top_investors = fields.ObjectField()

    def prepare_top_investors(self, instance: Deal):
        investors = instance.get_top_investors()
        if not investors:
            return None
        return [{"id": inv.id, "name": inv.name} for inv in investors]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Location):
            return related_instance.deal
        if isinstance(related_instance, Contract):
            return related_instance.deal
        if isinstance(related_instance, DataSource):
            return related_instance.deal

    class Index:
        name = "deal"


# noinspection PyMethodMayBeStatic
@registry.register_document
class LocationDocument(Document):
    class Django:
        model = Location
        exclude = [
            "deal",
            "old_group_id",
            "timestamp",
            "intended_area",
            "production_area",
            "contract_area",
        ]
        # ignore_signals = True

    class Index:
        name = "location"

    deal = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "status": fields.IntegerField(),
            "intended_size": fields.TextField(),
            "contract_size": fields.ObjectField(
                properties={"date": fields.TextField(), "value": fields.TextField()}
            ),
            "production_size": fields.ObjectField(
                properties={"date": fields.TextField(), "value": fields.TextField()}
            ),
            "implementation_status": fields.ObjectField(
                properties={"date": fields.TextField(), "value": fields.TextField()}
            ),
            "intention_of_investment": fields.ObjectField(
                properties={"date": fields.TextField(), "value": fields.TextField()}
            ),
            "operating_company": fields.ObjectField(),
        }
    )

    def prepare_deal(self, instance: Location):
        deal = instance.deal
        ret = {
            "id": deal.id,
            "status": deal.status,
            "intended_size": deal.intended_size,
            "contract_size": deal.contract_size,
            "production_size": deal.production_size,
            "implementation_status": deal.implementation_status,
            "intention_of_investment": deal.intention_of_investment,
        }
        oc = deal.operating_company
        if oc:
            ret["operating_company"] = {
                "id": oc.id,
                "investor_identifier": oc.id,
                "name": oc.name,
                "classification": oc.classification,
                "classification_display": oc.get_classification_display(),
                "homepage": oc.homepage,
                "comment": oc.comment,
                "timestamp": oc.timestamp,
                "opencorporates": oc.opencorporates,
            }
        return ret

    # GeoShapeField() is not parsing all of the fields at the moment
    # use ObjectField instead
    intended_area = fields.ObjectField()
    production_area = fields.ObjectField()
    contract_area = fields.ObjectField()
