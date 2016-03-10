from grid.forms.base_form import BaseForm
from grid.widgets import CommentInput, TitleField
from landmatrix.models.country import Country

from landmatrix.models.investor import Investor, InvestorActivityInvolvement

from grid.forms.operational_stakeholder_form import investor_description

from grid.views.profiling_decorators import print_execution_time_and_num_queries

from django.forms.widgets import Select

from django.utils.translation import ugettext_lazy as _
from django import forms
from django.forms.models import ModelChoiceField

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

# Change this to a livesearch widget once you got a working one
class InvestorField(forms.ChoiceField):
    def widget_attrs(self, widget):
        return {'class': 'investorfield'}



class InvestorForm(BaseForm):

    # Investor
    tg_investor = TitleField(required=False, label="", initial=_("Investor"))
    # investor = InvestorField(required=False, label=_("Existing investor"), choices=())#, widget=LivesearchSelect)
    investor = ModelChoiceField(
            required=True, label=_("Existing investor"),
            queryset=Investor.objects.filter(
                    pk__in=InvestorActivityInvolvement.objects.values('fk_investor_id').distinct()
            ).order_by('name'),
            widget=Select(
                attrs={'class': 'form-control investorfield'},
            )
    )
    investor_name = forms.CharField(required=False, label=_("Name"), max_length=255)
    country = forms.ChoiceField(required=False, label=_("Country"), choices=())
    classification = forms.ChoiceField(
            required=False, label=_("Classification"), choices=Investor.classification_choices, widget=forms.RadioSelect
    )
    tg_general_comment = forms.CharField(required=False, label=_("Additional comments"), widget=CommentInput)

    @print_execution_time_and_num_queries
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        investor = kwargs.pop("investor", None)
        self.fields["investor"].initial = investor
        self._fill_investor_choices()
        self._fill_country_choices()

    @classmethod
    def get_data(cls, investor, _=None, __=None):
        data = super().get_data(investor)
        if investor:
            data['investor'] = investor.id
            data['country'] = investor.fk_country_id
            data['classification'] = investor.classification
        return data

    def clean_investor(self):
        if isinstance(self.cleaned_data['investor'], Investor):
            investor = self.cleaned_data['investor'].id
        else:
            investor = int(self.cleaned_data["investor"] or 0)
        if investor and (investor not in [s[0] for s in self.investor_choices]):
            raise forms.ValidationError("%s is no valid investor." % investor)
        return investor

    def clean(self):
        cleaned_data = super().clean()
        investor = cleaned_data.get("investor", None)
        investor_name = cleaned_data.get("investor_name", None)
        if not investor and not investor_name:
            raise forms.ValidationError("Please select an investor or investor name.")

        return cleaned_data

    def has_investor(self):
        if self.initial.get("investor"):
            return True
        elif self.is_valid() and self.cleaned_data.get("investor"):
            return True
        return False

    _investor_choices = None

    @print_execution_time_and_num_queries
    def _fill_investor_choices(self):
        if InvestorForm._investor_choices is None:
            InvestorForm._investor_choices = [
                (investor.id, investor_description(investor))
                for investor in Investor.objects.filter(fk_status_id__in=(2, 3)).order_by('name')
            ]
        self.investor_choices = InvestorForm._investor_choices
        self.fields["investor"].choices = list(self.fields["investor"].choices)[:1]
        self.fields["investor"].choices.extend(self.investor_choices)

    def _fill_country_choices(self):
        self.fields["country"].choices = [
            ("", str(_("---------"))),
            (0, str(_("Multinational enterprise (MNE)")))
        ]
        self.fields["country"].choices.extend([(c.id, c.name) for c in Country.objects.all().order_by("name")])

