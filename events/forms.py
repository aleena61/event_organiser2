# forms.py
from django import forms
from .models import Event, EventPhoto, OldPhoto, Competition,Category
from django.contrib.auth.forms import AuthenticationForm
class EventForm(forms.ModelForm):
    category = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),  # Allow users to select multiple categories
               widget=forms.CheckboxSelectMultiple(),  # This will display checkboxes
        required=True  # Ensure at least one category is selected
    )
    class Meta:
        model = Event
        fields = ['name', 'place', 'date','category', 'description','latitude','longitude','address','phone','email','end_date','start_time','end_time','entry_fee','website']

        
        


class CompetitionForm(forms.ModelForm):
    category = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.SelectMultiple(attrs={"multiple": True})
    )

    class Meta:
        model = Competition
        fields = ['name', 'date', 'place', 'description','category']

class EventPhotoForm(forms.ModelForm):
    class Meta:
        model = EventPhoto
        fields = ['image']

class OldPhotoForm(forms.ModelForm):
    class Meta:
        model = OldPhoto
        fields = ['image']
        
class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))



from django import forms
from django.contrib.auth.models import User

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']


    # events/forms.py

from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

