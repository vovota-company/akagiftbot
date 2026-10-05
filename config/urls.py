from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from drf_spectacular.utils import OpenApiResponse, extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


@extend_schema(
    tags=["System"],
    operation_id="healthCheck",
    summary="API health check",
    description=(
        "Returns the basic application health status. "
        "This endpoint does not require authentication."
    ),
    responses={
        200: OpenApiResponse(
            description="Application is running.",
        ),
    },
)
def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "health/",
        health,
        name="health",
    ),

    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema"
        ),
        name="swagger-ui",
    ),

    path(
        "api/v1/",
        include("api.urls"),
    ),
]
