from django import forms

from .models import Foo


class CreateFooForm(forms.ModelForm):
    class Meta:
        model = Foo
        fields = []


class UpdateFooForm(forms.ModelForm):
    class Meta:
        model = Foo
        fields = []
