from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("notes/", views.notes, name="notes"),
    path("notes/<slug:slug>/", views.note_detail, name="note_detail"),
    path("blog/", views.blog, name="blog"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),
    path("search/", views.search, name="search"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("profile/", views.profile, name="profile"),
    path("saved/", views.saved_content, name="saved_content"),
    path("save/<str:kind>/<slug:slug>/", views.toggle_saved, name="toggle_saved"),
    path("files/<int:asset_id>/", views.download_asset, name="download_asset"),
    path("manage/preview/notes/<slug:slug>/", views.preview_note, name="preview_note"),
    path("manage/preview/blog/<slug:slug>/", views.preview_post, name="preview_post"),
]
