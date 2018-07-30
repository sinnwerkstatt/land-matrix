from django.utils.translation import ugettext_lazy as _
from django.db.models.fields import BLANK_CHOICE_DASH
from django import forms
from django.utils import timezone

from landmatrix.models.investor import Investor, HistoricalInvestor
from landmatrix.models.country import Country
from grid.forms.base_model_form import BaseModelForm
from grid.widgets import CommentInput
from grid.utils import get_display_value

INVESTOR_CLASSIFICATION_CHOICES = BLANK_CHOICE_DASH + list(
    HistoricalInvestor.INVESTOR_CLASSIFICATIONS)
STAKEHOLDER_CLASSIFICATION_CHOICES = BLANK_CHOICE_DASH + list(
    HistoricalInvestor.STAKEHOLDER_CLASSIFICATIONS)


# TODO: move to fields.
# TODO: Change this to a livesearch widget
class InvestorField(forms.ChoiceField):
    def widget_attrs(self, widget):
        return {'class': 'investorfield'}


class BaseInvestorForm(BaseModelForm):
    form_title = _('Investor')

    # We use ID to build related form links
    id = forms.CharField(required=False, label=_("ID"), widget=forms.HiddenInput())
    name = forms.CharField(required=False, label=_("Name"), max_length=255)
    classification = forms.ChoiceField(
        required=False, label=_("Classification"),
        choices=INVESTOR_CLASSIFICATION_CHOICES + STAKEHOLDER_CLASSIFICATION_CHOICES)
    fk_country = forms.ModelChoiceField(
        required=False, label=_("Country of registration/origin"),
        queryset=Country.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control countryfield'}))
    comment = forms.CharField(
        required=False, label=_("Comment"), widget=CommentInput)

    class Meta:
        model = HistoricalInvestor
        exclude = ('id', 'fk_status', 'subinvestors', 'investor_identifier', 'history_date',
                   'history_user')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Show given/current value only, rest happens via ajax
        valid_choice = self.data.get('fk_country', self.initial.get('fk_country', None))
        if valid_choice:
            self.fields['fk_country'].queryset = Country.objects.filter(pk=valid_choice)

    def save(self, commit=True):
        '''
        Force status to pending on update.
        '''
        instance = super().save(commit=False)
        instance.fk_status_id = HistoricalInvestor.STATUS_PENDING
        # Create new historical investor
        instance.id = None
        instance.history_date = timezone.now()
        instance.history_user = None # FIXME: Set current user
        if commit:
            instance.save()

        return instance

    def get_attributes(self, **kwargs):
        return {
            'comment': self.cleaned_data.get('comment'),
        }

    @classmethod
    def get_data(cls, investor):
        return {}

    def clean(self):
        cleaned_data = super(BaseInvestorForm, self).clean()

        # Prevent duplicate names
        # FIXME: Make model field unique in the future
        name = self.cleaned_data['name']
        duplicates = Investor.objects.filter(name=name)
        investor_identifier = self.instance.investor_identifier
        if investor_identifier:
            duplicates = duplicates.exclude(investor_identifier=investor_identifier)
        if duplicates.count() > 0:
            self.add_error('name', "This name exists already.")

        return cleaned_data


class ExportInvestorForm(BaseInvestorForm):
    exclude_in_export = ('id', 'fk_status', 'subinvestors', 'history_date', 'history_user')

    fk_country = forms.ModelChoiceField(
        required=False, label=_("Country of registration/origin"),
        queryset=Country.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control countryfield'}))

    @classmethod
    def get_display_properties(cls, doc, prefix=''):
        """Get field value for export"""
        output = {}
        for field_name, field in cls.base_fields.items():
            field_name = '%s%s' % (prefix, field_name)
            key = '%s_display' % field_name
            values = doc.get('%s' % field_name)
            if not values:
                output[key] = []
                continue
            if not isinstance(values, (list, tuple)):
                values = [values,]
            # Remove # in name
            if field_name == '%sname' % prefix:
                values = [v.replace('#', '') for v in values]
            value = get_display_value(field, values)
            if value:
                output[key] = value

            # Set target region
            if field_name == 'operating_company_fk_country' and values:
                output['operating_company_region'] = []
                output['operating_company_region_display'] = []
                for value in values:
                    region = Country.objects.get(pk=value).fk_region
                    output['operating_company_region'].append(region.id)
                    output['operating_company_region_display'].append(region.name)

        return output

    class Meta:
        model = HistoricalInvestor
        exclude = ()


class ParentInvestorForm(BaseInvestorForm):
    form_title = _('Tertiary investor/lender')
    classification = forms.ChoiceField(
        required=False, label=_("Classification"),
        choices=INVESTOR_CLASSIFICATION_CHOICES)

    class Meta:
        model = HistoricalInvestor
        exclude = (
            'fk_status', 'subinvestors', 'investor_identifier',
            'parent_relation', 'history_date', 'history_user'
        )


class ParentStakeholderForm(ParentInvestorForm):
    form_title = _('Parent company')
    classification = forms.ChoiceField(
        required=False, label=_("Classification"),
        choices=STAKEHOLDER_CLASSIFICATION_CHOICES)


class OperationalCompanyForm(BaseInvestorForm):
    form_title = _('Operational company')
    classification = forms.ChoiceField(
        required=False, label=_("Classification"),
        choices=STAKEHOLDER_CLASSIFICATION_CHOICES)