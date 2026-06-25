from django.urls import path

from . import views

urlpatterns = [
    path("google/connect/", views.google_connect, name="google_connect"),
    path("google/callback/", views.google_callback, name="google_callback"),
    path("google/sync/all/", views.google_sync_all, name="google_sync_all"),
    path(
        "google/sync/group/<int:group_id>/",
        views.google_sync_group,
        name="google_sync_group",
    ),
]
