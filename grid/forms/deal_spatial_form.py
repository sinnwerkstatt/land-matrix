from django import forms
from django.forms.models import formset_factory, BaseFormSet
from django.utils.translation import ugettext_lazy as _

from landmatrix.models.activity import Activity
from landmatrix.models.activity_attribute_group import ActivityAttributeGroup
from landmatrix.models.country import Country
from landmatrix.models.deal import Deal
from landmatrix.models.region import Region
from grid.widgets import TitleField, LocationWidget, CountryField, CommentInput
from .base_form import BaseForm


__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class DealSpatialForm(BaseForm):

    form_title = _('Location')
    tg_location = TitleField(
        required=False, label="", initial=_("Location")
    )
    level_of_accuracy = forms.ChoiceField(
        required=False, label=_("Spatial accuracy level"), choices=(
            (_("---------"), _("---------")),
            (_("Country"), _("Country")),
            (_("Administrative region"), _("Administrative region")),
            (_("Approximate location"), _("Approximate location")),
            (_("Exact location"), _("Exact location")),
            (_("Coordinates"), _("Coordinates")),
        )
    )
    location = forms.CharField(
        required=True, label=_("Location"), widget=LocationWidget
    )
    point_lat = forms.CharField(
        required=False, label=_("Latitude"), widget=forms.TextInput, initial=""
    )
    point_lon = forms.CharField(
        required=False, label=_("Longitude"), widget=forms.TextInput, initial=""
    )
    facility_name = forms.CharField(
        required=False, label=_("Facility name"), widget=forms.TextInput, initial=""
    )
    target_country = CountryField(
        required=False, label=_("Target Country")
    )
    target_region = forms.ModelChoiceField(
        required=False, label=_("Target Region"), widget=forms.HiddenInput,
        queryset=Region.objects.all().order_by("name")
    )
    location_description = forms.CharField(
        required=False, label=_("Location description"), widget=forms.TextInput, initial=""
    )
    tg_location_comment = forms.CharField(
        required=False, label=_("Additional comments"), widget=CommentInput
    )

    class Meta:
        name = 'spatial_data'

    def get_attributes(self, request=None):
        attributes = super().get_attributes()
        if 'target_country' in attributes \
                and not isinstance(attributes['target_country'], int) \
                and not attributes['target_country'].isnumeric():
            target_country = Country.objects.get(name=attributes['target_country'])
            attributes['target_country'] = target_country.pk
        return attributes


class DealSpatialBaseFormSet(BaseFormSet):

    form_title = _('Location')

    @classmethod
    def get_data(cls, activity):
        if isinstance(activity, Deal):
            activity = activity.activity
        if isinstance(activity, Activity):
            taggroups = ActivityAttributeGroup.objects.\
                filter(fk_activity=activity).filter(attributes__contains=["location"])
        else:
            taggroups = []
        data = []
        for i, taggroup in enumerate(taggroups):
            form_data = DealSpatialForm.get_data(activity, taggroup=taggroup)
            data.append(form_data)
        return data

    def get_attributes(self, request=None):
        return [form.get_attributes(request) for form in self.forms]

    class Meta:
        name = 'spatial_data'


DealSpatialFormSet = formset_factory(DealSpatialForm, min_num=1,
                                     validate_min=True, extra=0,
                                     formset=DealSpatialBaseFormSet)


class PublicViewDealSpatialForm(DealSpatialForm):

    class Meta:
        name = 'spatial_data'
        fields = (
            "tg_location", "location", "point_lat", "point_lon",
            'tg_location_comment'
        )
        readonly_fields = fields


PublicViewDealSpatialFormSet = formset_factory(PublicViewDealSpatialForm,
                                               formset=DealSpatialBaseFormSet,
                                               extra=0)
