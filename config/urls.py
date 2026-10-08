from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from knowledge import views

admin.site.site_header = "Fieldnotes publishing"
admin.site.site_title = "Fieldnotes administration"
admin.site.index_title = "Content and site management"

handler404 = "knowledge.views.not_found"
handler500 = "knowledge.views.server_error"

urlpatterns = [
    path("manage/", views.dashboard, name="dashboard"),
    path("manage/content/", admin.site.urls),
    path("accounts/", include("knowledge.account_urls")),
    path("", include("knowledge.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
