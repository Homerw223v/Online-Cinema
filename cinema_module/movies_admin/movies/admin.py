from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from movies.filters import GenreFilter, YearFilter
from movies.models import FilmWork, Genre, GenreFilmWork, Person, PersonFilmWork, Subscription, SubscriptionFilmWork


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class GenreFilmWorkInline(admin.TabularInline):
    model = GenreFilmWork
    verbose_name = _("GenreFilmWork")
    verbose_name_plural = _("GenresFilmWorks")


class PersonFilmWorkInline(admin.TabularInline):
    model = PersonFilmWork
    verbose_name = _("PersonFilmWork")
    verbose_name_plural = _("PersonsFilmWorks")


class SubscriptionFilmWorkInline(admin.TabularInline):
    model = SubscriptionFilmWork
    verbose_name = _("SubscriptionFilmWork")
    verbose_name_plural = _("SubscriptionFilmWorks")


@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):
    inlines = (GenreFilmWorkInline, PersonFilmWorkInline, SubscriptionFilmWorkInline)
    list_display = (
        "title",
        "type",
        "rating",
        "creation_date",
        "modified",
    )
    list_filter = ("type", GenreFilter, YearFilter)
    search_fields = ("title", "description", "id")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    search_fields = ("full_name",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    search_fields = ("name",)
