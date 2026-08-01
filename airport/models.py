from django.db import models

from user.models import User


class AirplaneType(models.Model):
    name = models.CharField(max_length=256)

    class Meta:
        verbose_name = "Airplane Type"
        verbose_name_plural = "Airplane Types"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Airplane(models.Model):
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.CASCADE,
        related_name="airplanes"
    )
    registration_number = models.CharField(max_length=20, unique=True)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Airplane"
        verbose_name_plural = "Airplanes"
        ordering = ("registration_number",)

    @property
    def capacity(self):
        return self.rows * self.seats_in_row

    def __str__(self):
        return f"{self.airplane_type} ({self.registration_number})"


class Flight(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        DELAYED = "delayed", "Delayed"
        BOARDING = "boarding", "Boarding"
        DEPARTED = "departed", "Departed"
        ARRIVED = "arrived", "Arrived"
        CANCELLED = "cancelled", "Cancelled"

    route = models.ForeignKey(
        "Route",
        on_delete=models.CASCADE,
        related_name="flights"
    )
    flight_number = models.CharField(max_length=10, unique=True)
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name="flights"
    )
    crew = models.ManyToManyField("Crew", related_name="flights")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )

    class Meta:
        verbose_name = "Flight"
        verbose_name_plural = "Flights"
        ordering = ("departure_time",)

    def __str__(self):
        return (
            f"{self.flight_number}: "
            f"{self.route} "
            f"({self.departure_time:%d/%m/%Y %H:%M})"
        )


class Crew(models.Model):
    class Position(models.TextChoices):
        CAPTAIN = "captain", "Captain"
        FIRST_OFFICER = "first_officer", "First Officer"
        FLIGHT_ATTENDANT = "flight_attendant", "Flight Attendant"

    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    position = models.CharField(max_length=30, choices=Position.choices)

    class Meta:
        verbose_name = "Crew"
        verbose_name_plural = "Crews"
        ordering = ("first_name", "last_name")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.full_name} ({self.get_position_display()})"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ("created_at",)

    def __str__(self):
        return f"Order #{self.id} ({self.user.email})"


class Ticket(models.Model):
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ("row",)
        constraints = [
            models.UniqueConstraint(
                fields=["flight", "row", "seat"],
                name="unique_ticket"
            )
        ]

    def __str__(self):
        return (
            f"row:{self.row}, "
            f"seat:{self.seat}, "
            f"flight:{self.flight.route}"
        )


class Country(models.Model):
    name = models.CharField(max_length=256, unique=True)

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ("name",)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=256)
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="cities"
    )

    class Meta:
        verbose_name = "City"
        verbose_name_plural = "Cities"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["country", "name"],
                name="unique_city_in_country"
            )
        ]

    def __str__(self):
        return self.name


class Airport(models.Model):
    name = models.CharField(max_length=256)
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="airports"
    )
    iata_code = models.CharField(max_length=3, unique=True)

    class Meta:
        verbose_name = "Airport"
        verbose_name_plural = "Airports"
        ordering = ("city", "name")

    def __str__(self):
        return f"{self.name} ({self.iata_code})"


class Route(models.Model):
    source = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="departures"
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="arrivals"
    )
    distance = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Route"
        verbose_name_plural = "Routes"
        ordering = ("source", "destination")
        constraints = [
            models.UniqueConstraint(
                fields=["source", "destination"],
                name="unique_route"
            )
        ]

    def __str__(self):
        return f"{self.source} -> {self.destination}"
