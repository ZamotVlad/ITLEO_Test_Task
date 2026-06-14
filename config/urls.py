from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from payments.views import PaymentViewSet
from schedule.views import GroupViewSet, ScheduleViewSet
from students.views import CourseViewSet, StudentViewSet

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"groups", GroupViewSet, basename="group")
router.register(r"schedule", ScheduleViewSet, basename="schedule")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
