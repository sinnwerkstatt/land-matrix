from typing import Any

from ariadne import ObjectType
from graphql import GraphQLResolveInfo
from reversion.models import Version

from apps.graphql.tools import get_fields, parse_filters
from apps.landmatrix.models import Investor, InvestorVentureInvolvement, Country


def _resolve_investors_prefetching(info: GraphQLResolveInfo):
    qs = Investor.objects.visible(info.context.user)

    fields = get_fields(info)
    if "country" in fields:
        qs = qs.prefetch_related("country")
    if "deals" in fields:
        qs = qs.prefetch_related("deals")
    return qs


def resolve_investor(obj: Any, info: GraphQLResolveInfo, id):
    investor = _resolve_investors_prefetching(info)
    return investor.get(id=id)


def resolve_investors(obj, info: GraphQLResolveInfo, filters=None, sort="id", limit=20):
    qs = _resolve_investors_prefetching(info).order_by(sort)
    if filters:
        qs = qs.filter(**parse_filters(filters))

    # limit = max(1, min(limit, 500))
    if limit != 0:
        qs = qs[:limit]
    return qs


investor_type = ObjectType("Investor")
investor_type.set_field("deals", lambda obj, info: obj.deals.all())


def _resolve_field_dict_fetch(field_dict):
    if "country_id" in field_dict and not field_dict["country_id"] is None:
        try:
            c = Country.objects.get(id=field_dict["country_id"])
            field_dict["country"] = c.to_dict(deep=True)
        except Country.DoesNotExist:
            pass

    return field_dict


def resolve_investorversions(obj, info: GraphQLResolveInfo, filters=None):
    qs = Version.objects.get_for_model(Investor)  # .filter(revision__date_created="")
    # qs = _resolve_deals_prefetching(info).order_by(sort)
    if filters:
        qs = qs.filter(**parse_filters(filters))

    return [
        {
            "id": x.id,
            "investor": _resolve_field_dict_fetch(x.field_dict),
            "revision": x.revision,
        }
        for x in qs
    ]


class InvolvementNetwork:
    def __init__(self):
        self.seen_investors = set()

    def get_network(self, investor_id, exclude=None, depth=10):
        if depth <= 0:
            return

        # find all involvements
        involvements = []
        qs = (
            InvestorVentureInvolvement.objects.filter(status__in=(2, 3))
            .filter(investor__status__in=(2, 3), venture__status__in=(2, 3))
            .prefetch_related("investor")
            .prefetch_related("investor__deals")
            .prefetch_related("venture")
            .prefetch_related("venture__deals")
        )

        # traverse over the investors
        network_investors = qs.filter(venture_id=investor_id).exclude(
            investor_id=exclude
        )
        for inv in network_investors:
            if inv.id in self.seen_investors:
                continue
            involvement = inv.to_dict()
            involvement["involvement_type"] = "INVESTOR"
            investor = inv.investor.to_dict()
            investor["involvements"] = self.get_network(
                inv.investor_id, investor_id, depth - 1
            )
            involvement["investor"] = investor
            involvements += [involvement]
            self.seen_investors.add(inv.id)

        # traverse over the ventures
        network_ventures = qs.filter(investor_id=investor_id).exclude(
            venture_id=exclude
        )
        for inv in network_ventures:
            if inv.id in self.seen_investors:
                continue
            involvement = inv.to_dict()
            involvement["involvement_type"] = "VENTURE"
            venture = inv.venture.to_dict()
            venture["involvements"] = self.get_network(
                inv.venture_id, investor_id, depth - 1
            )
            involvement["investor"] = venture
            involvements += [involvement]
            self.seen_investors.add(inv.id)

        return involvements


@investor_type.field("involvements")
def resolve_involvements_network(obj: Any, info: GraphQLResolveInfo, depth):
    investors = InvolvementNetwork().get_network(obj.id, depth=depth)
    # print(dict(investors))
    return investors


def resolve_involvements(
    obj, info: GraphQLResolveInfo, filters=None, sort="id", limit=20
):
    qs = InvestorVentureInvolvement.objects.visible(info.context.user)

    if filters:
        qs = qs.filter(**parse_filters(filters))
    if limit != 0:
        qs = qs[:limit]
    return qs
