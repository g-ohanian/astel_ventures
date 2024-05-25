import json

from django.contrib.auth.mixins import UserPassesTestMixin
from django.forms.models import model_to_dict
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from songs.forms import SongSearchForm, SongSaveForm
from songs.services import SongSummerizerService
from utils.helper import clean_string


# Create your views here.


class SongView(UserPassesTestMixin, TemplateView):
    template_name = "songs/songs.html"
    song_form_class = SongSearchForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['song_search_form'] = self.song_form_class()
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        user = request.user
        context = self.get_context_data(**kwargs)

        form = self.song_form_class(request.POST)
        if not form.is_valid():
            context['song_search_form'] = form
            return render(request, self.template_name, context)

        title = form.cleaned_data['title']
        artist = form.cleaned_data['artist']
        key = clean_string(f"{title}{artist}{request.user.id}")

        context['song_search_form'] = self.song_form_class()
        song_summary = user.song_set.filter(hash_key=key).first()
        if song_summary:
            return self.__update_context_and_render(model_to_dict(song_summary), context)

        song_summary = SongSummerizerService().search_for_song(title, artist)
        existing_form = self.__save_form(title=title, artist=artist, song_summary=song_summary, hash_key=key)
        return self.__update_context_and_render(existing_form, context)

    def __update_context_and_render(self, data: dict, context):
        data["summary"] = json.loads(data["summary"])
        context["existing_song"] = data
        return render(self.request, self.template_name, context)

    def __save_form(self, title: str, artist: str, hash_key: str, song_summary: dict) -> dict:

        form = SongSaveForm({
            "title": title,
            "artist": artist,
            "summary": json.dumps(song_summary),
            "hash_key": hash_key,
            "user": self.request.user
        })
        summary_values = list(song_summary.values())
        existing_errors = [summary_value["error"] for summary_value in summary_values]
        if form.is_valid() and not any(existing_errors):
            form.save()
        return form.data

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect("home")
