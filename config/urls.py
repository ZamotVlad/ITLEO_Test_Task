from functools import partial

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from accounts.views import CustomTokenObtainPairView, UserViewSet
from config.views import preview_error_page
from dashboard.views import DashboardStatsView
from notifications.views import NotificationViewSet
from payments.views import PaymentViewSet
from schedule.views import GroupViewSet, ScheduleViewSet
from students.views import CourseViewSet, ParentViewSet, StudentViewSet

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"groups", GroupViewSet, basename="group")
router.register(r"schedule", ScheduleViewSet, basename="schedule")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"users", UserViewSet, basename="user")
router.register(r"parents", ParentViewSet, basename="parent")

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/auth/token/", obtain_auth_token),
    path("api/auth/jwt/create/", CustomTokenObtainPairView.as_view(), name="jwt-create"),
    path("api/auth/jwt/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
    path("api/auth/jwt/verify/", TokenVerifyView.as_view(), name="jwt-verify"),
    path("api/dashboard/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("integrations/", include("integrations.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("debug/errors/400/", partial(preview_error_page, template_name="400.html")),
        path("debug/errors/403/", partial(preview_error_page, template_name="403.html")),
        path("debug/errors/404/", partial(preview_error_page, template_name="404.html")),
        path("debug/errors/500/", partial(preview_error_page, template_name="500.html")),
    ]
