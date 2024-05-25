from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.shortcuts import redirect


# Create your views here.
class LoginView(UserPassesTestMixin, BaseLoginView):
    def test_func(self):
        return self.request.user.is_anonymous

    def handle_no_permission(self):
        return redirect("songs")
