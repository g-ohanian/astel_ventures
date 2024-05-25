from django import forms
from django.forms import Form

from songs.models import Song


class SongSearchForm(Form):
    title = forms.CharField(max_length=255, required=True)
    artist = forms.CharField(max_length=255, required=True)


class SongSaveForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['title', 'artist', 'summary', 'hash_key', 'user']
