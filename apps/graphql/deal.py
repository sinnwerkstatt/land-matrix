from typing import Any

from graphql import GraphQLResolveInfo

from apps.graphql.tools import get_fields
from apps.greennewdeal.documents import DealDocument


def resolve_deal(obj: Any, info: GraphQLResolveInfo, id):
    deal = DealDocument.search().filter("term", id=id)

    fields = get_fields(info)
    if fields:
        deal = deal.source(fields)

    deal = deal.execute()[0]
    return deal.to_dict()


def resolve_deals(obj: Any, info: GraphQLResolveInfo, sort="id", limit=20):
    limit = max(1, min(limit, 500))
    deals = DealDocument.search().filter("terms", status=[2, 3]).sort(sort)

    fields = get_fields(info)
    if fields:
        deals = deals.source(fields)
    # if after:
    #     deals = deals.filter('range', id={'gt': after})
    deals = [d.to_dict() for d in deals[:limit].execute()]
    return deals