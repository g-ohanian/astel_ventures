from django.urls import path

from songs.views import SongView

urlpatterns = [
    path('songs/', SongView.as_view(), name='songs'),
]
