from .base_form import BaseForm
from grid.widgets import CommentInput, TitleField

from django import forms
from django.utils.translation import ugettext_lazy as _

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class DealGenderRelatedInfoForm(BaseForm):

    form_title = _('Gender-related info')

    tg_gender_specific_info = TitleField(
        required=False, label="",
        initial=_("Any gender-specific information about the investment and its impacts"))
    tg_gender_specific_info_comment = forms.CharField(
        required=False, label=_("Gender-related info comments"),
        widget=CommentInput)

    class Meta:
        name = 'gender-related_info'
