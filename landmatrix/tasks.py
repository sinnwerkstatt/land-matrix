from __future__ import absolute_import

from celery import shared_task
from api.elasticsearch import es_save

@shared_task
def index_activity(activity_id):
    es_save.index_activity_by_id(activity_id=activity_id)


@shared_task
def delete_activity(activity_identifier):
    es_save.delete_activity(activity_identifier=activity_identifier)
