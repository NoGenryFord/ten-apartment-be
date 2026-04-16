from datetime import timedelta, date
from django import forms
from django.contrib.admin.helpers import ActionForm


class ApartmentActionForm(ActionForm):
    start_date = forms.DateField(
        required=False,
        label="Start date (YYYY-MM-DD)",
        widget=forms.DateInput(attrs={"type": "date"}),
    )


class StartDateForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}),
    )
