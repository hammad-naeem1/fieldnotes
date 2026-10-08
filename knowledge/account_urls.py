from django.contrib.auth import views as auth_views
from django.urls import path

from .rate_limits import rate_limit
from . import views

urlpatterns = [
    path("login/", views.login_view, name="account_login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password_reset/", rate_limit("password-reset", 3, 3600)(auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html", email_template_name="registration/password_reset_email.html", subject_template_name="registration/password_reset_subject.txt")), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),
    path("password_change/", auth_views.PasswordChangeView.as_view(template_name="registration/password_change_form.html"), name="password_change"),
    path("password_change/done/", auth_views.PasswordChangeDoneView.as_view(template_name="registration/password_change_done.html"), name="password_change_done"),
]
