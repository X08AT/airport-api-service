from django.contrib import admin

from airport.models import (
    AirplaneType,
    Airplane,
    Crew,
    Order,
    Country,
    City,
    Airport,
    Route,
    Flight,
    Ticket,
)


@admin.register(AirplaneType)
class AirplaneTypeAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    list_display = [
        "registration_number",
        "airplane_type",
        "capacity",
        "rows",
        "seats_in_row",
    ]
    list_filter = ["airplane_type"]
    search_fields = ["registration_number", "airplane_type__name"]
    list_select_related = ["airplane_type"]


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ["full_name", "position"]
    list_filter = ["position"]
    search_fields = ["first_name", "last_name"]


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "created_at", "user"]
    list_filter = ["user"]
    search_fields = ["user__email"]
    list_select_related = ["user"]
    inlines = [TicketInline]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "country"]
    list_filter = ["country"]
    search_fields = ["name", "country__name"]
    list_select_related = ["country"]


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ["name", "iata_code", "city"]
    list_filter = ["city"]
    search_fields = ["name", "iata_code", "city__name"]
    list_select_related = ["city", "city__country"]


class FlightInline(admin.TabularInline):
    model = Flight
    extra = 0


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ["source", "destination", "distance"]
    list_filter = ["source", "destination"]
    search_fields = ["source__name", "destination__name"]
    list_select_related = ["source", "destination"]


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = [
        "flight_number",
        "route",
        "airplane",
        "departure_time",
        "arrival_time",
        "status",
        "get_crew",
    ]
    list_filter = ["airplane", "status", "departure_time", "arrival_time"]
    search_fields = [
        "flight_number",
        "route__source__iata_code",
        "route__destination__iata_code",
        "airplane__registration_number",
    ]
    list_select_related = [
        "airplane",
        "route__source",
        "route__destination",
    ]
    list_editable = ["status"]

    @admin.display(description="Crew")
    def get_crew(self, obj):
        return ", ".join(crew.full_name for crew in obj.crew.all())

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("crew")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["row", "seat", "flight", "order"]
    list_filter = ["flight", "order"]
    list_select_related = ["flight", "order"]
    search_fields = ["flight__flight_number", "order__user__email"]
