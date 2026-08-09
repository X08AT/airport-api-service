from django.urls import path, include
from rest_framework import routers

from airport import views


app_name = "airport"

router = routers.DefaultRouter()
router.register("airplane_types", views.AirplaneTypeViewSet)
router.register("airplanes", views.AirplaneViewSet)
router.register("crews", views.CrewViewSet)
router.register("countries", views.CountryViewSet)
router.register("cities", views.CityViewSet)
router.register("airports", views.AirportViewSet)
router.register("routes", views.RouteViewSet)
router.register("flights", views.FlightViewSet)
router.register("orders", views.OrderViewSet)
urlpatterns = [
    path("", include(router.urls)),
]
