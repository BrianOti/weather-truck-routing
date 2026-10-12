from django.urls import path

from weather_routing.views import index, plan_route

urlpatterns = [
    path("", index, name="index"),
    path("api/plan/", plan_route, name="plan-route"),
]
