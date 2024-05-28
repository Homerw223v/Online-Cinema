import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class CreatedTimeStampedMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class TimeStampedMixin(CreatedTimeStampedMixin):
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_("name"), max_length=255, unique=True)
    description = models.TextField(_("description"), blank=True, null=True)

    class Meta:
        db_table = 'content"."genre'
        verbose_name = _("genre")
        verbose_name_plural = _("genres")

    def __str__(self):
        return f"{self.name}"


class FilmWork(UUIDMixin, TimeStampedMixin):
    class FilmWorkType(models.TextChoices):  # noqa
        MOVIE = "movie", _("movie")
        TV_SHOW = "tv_show", _("tv_show")

    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True, null=True)
    creation_date = models.DateField(_("creation_date"), blank=True, null=True)
    rating = models.FloatField(
        _("rating"),
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    type = models.CharField(_("type"), choices=FilmWorkType.choices)

    class Meta:
        db_table = 'content"."film_work'
        verbose_name = _("filmwork")
        verbose_name_plural = _("filmworks")
        constraints = [
            models.UniqueConstraint(
                fields=["title", "creation_date"],
                name="film_work_title_creation_date_key",
            ),
        ]
        indexes = [
            models.Index(fields=["creation_date"], name="film_work_creation_date_idx"),
        ]

    def __str__(self):
        return f"{self.title}"


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.TextField(_("title"), max_length=255)

    class Meta:
        db_table = 'content"."person'
        verbose_name = _("actor")
        verbose_name_plural = _("actors")
        indexes = [
            models.Index(fields=["full_name"], name="person_full_name_idx"),
        ]

    def __str__(self):
        return f"{self.full_name}"


class GenreFilmWork(UUIDMixin, CreatedTimeStampedMixin):
    film_work = models.ForeignKey("Filmwork", verbose_name=_("filmwork"), on_delete=models.CASCADE)
    genre = models.ForeignKey("Genre", verbose_name=_("genre"), on_delete=models.CASCADE)

    class Meta:
        db_table = 'content"."genre_film_work'
        verbose_name = _("genre_filmwork")
        verbose_name_plural = _("genre_filmworks")
        constraints = [
            models.UniqueConstraint(
                fields=["film_work", "genre"],
                name="genre_film_work_film_work_id_genre_id_key",
            ),
        ]
        indexes = [
            models.Index(fields=["genre"], name="genre_film_work_genre_id_idx"),
        ]

    def __str__(self):
        return ""


class PersonFilmWork(UUIDMixin, CreatedTimeStampedMixin):
    class RoleType(models.TextChoices):  # noqa
        ACTOR = "actor", _("actor")
        DIRECTOR = "director", _("director")
        WRITER = "writer", _("writer")

    film_work = models.ForeignKey("Filmwork", verbose_name=_("filmwork"), on_delete=models.CASCADE)
    role = models.CharField(_("Role"), choices=RoleType.choices)
    person = models.ForeignKey("Person", verbose_name=_("person"), on_delete=models.CASCADE)

    class Meta:
        db_table = 'content"."person_film_work'
        verbose_name = _("person_filmwork")
        verbose_name_plural = _("person_filmworks")
        constraints = [
            models.UniqueConstraint(
                fields=["person", "film_work", "role"],
                name="person_film_work_person_id_film_work_id_role_key",
            ),
        ]
        indexes = [
            models.Index(fields=["person"], name="person_film_work_person_id_idx"),
        ]

    def __str__(self):
        return ""


class Subscription(UUIDMixin):
    name = models.CharField(_("name"), max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'content"."subscription'
        verbose_name = _("subscription")
        verbose_name_plural = _("subscriptions")

    def __str__(self):
        return f"{self.name}"


class SubscriptionFilmWork(UUIDMixin, CreatedTimeStampedMixin):
    film_work = models.ForeignKey("Filmwork", verbose_name=_("filmwork"), on_delete=models.CASCADE)
    subscription = models.ForeignKey("Subscription", verbose_name=_("subscription"), on_delete=models.CASCADE)

    class Meta:
        db_table = 'content"."subscription_film_work'
        verbose_name = _("subscription_filmwork")
        verbose_name_plural = _("subscription_filmworks")
        constraints = [
            models.UniqueConstraint(
                fields=["film_work", "subscription"],
                name="subscription_film_work_film_work_id_subscription_id_key",
            ),
        ]
        indexes = [
            models.Index(fields=["subscription"], name="subs_film_work_subs_id_idx"),
        ]

    def __str__(self):
        return ""
