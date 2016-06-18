from django.db import models
from django.utils.translation import ugettext_lazy as _

#from simple_history.models import HistoricalRecords

from landmatrix.models.default_string_representation import DefaultStringRepresentation
from landmatrix.models.status import Status
from landmatrix.models.activity_attribute_group import ActivityAttribute
from landmatrix.models.investor import Investor, InvestorActivityInvolvement, InvestorVentureInvolvement


__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

class ActivityBase(DefaultStringRepresentation, models.Model):
    activity_identifier = models.IntegerField(_("Activity identifier"), db_index=True)
    availability = models.FloatField(_("availability"), blank=True, null=True)
    fully_updated = models.DateTimeField(_("Fully updated"), blank=True, null=True)#, auto_now_add=True)
    fk_status = models.ForeignKey("Status", verbose_name=_("Status"), default=1)

    class Meta:
        abstract = True

    @classmethod
    def get_latest_activity(cls, activity_identifier):
        return cls.objects.filter(activity_identifier=activity_identifier).order_by('-id').first()

    @classmethod
    def get_latest_active_activity(cls, activity_identifier):
        return cls.objects.filter(activity_identifier=activity_identifier).\
            filter(fk_status__name__in=("active", "overwritten", "deleted")).order_by('-id').first()

    @property
    def operational_stakeholder(self):
        involvements = InvestorActivityInvolvement.objects.filter(fk_activity_id=self.id)
        if len(involvements) > 1:
            raise MultipleObjectsReturned('More than one OP for activity %s: %s' % (str(self), str(involvements)))
        if len(involvements) < 1:
            raise ObjectDoesNotExist('No OP for activity %s: %s' % (str(self), str(involvements)))
        return Investor.objects.get(pk=involvements[0].fk_investor_id)

    @property
    def stakeholders(self):
        stakeholder_involvements = InvestorVentureInvolvement.objects.filter(fk_venture=self.operational_stakeholder.pk)
        return [Investor.objects.get(pk=involvement.fk_investor_id) for involvement in stakeholder_involvements]

class Activity(ActivityBase):
    class Meta:
        verbose_name = _('Activity')
        verbose_name_plural = _('Activities')

class HistoricalActivity(ActivityBase):
    history_date = models.DateTimeField()
    history_user = models.ForeignKey('auth.User', blank=True, null=True)

    #@property
    #def attributes(self):
    #    return ActivityAttribute.history.filter(fk_activity_id=self.id).latest()

    class Meta:
        verbose_name = _('Historical activity')
        verbose_name_plural = _('Historical activities')
        get_latest_by = 'history_date'
