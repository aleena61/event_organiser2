# forms.py
from django import forms
from .models import Event, EventPhoto, OldPhoto, Competition
from django.contrib.auth.forms import AuthenticationForm
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'place', 'date', 'description']

class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = ['name', 'date', 'place', 'description']

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

