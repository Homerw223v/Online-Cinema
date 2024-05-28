from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from movies.models import FilmWork, Genre, GenreFilmWork


class GenreFilter(admin.SimpleListFilter):
    title = _("Genre")
    parameter_name = "id"
    field_name = "id"

    def lookups(self, request, model_admin):
        genres = Genre.objects.distinct()
        yield from ((genre.id, genre.name) for genre in genres)

    def queryset(self, request, queryset):
        field_id = self.value()
        if field_id:
            film_work_ids = GenreFilmWork.objects.filter(genre_id=field_id).values("film_work")
            return queryset.filter(id__in=film_work_ids)
        return queryset


class YearFilter(admin.SimpleListFilter):
    title = _("Year")
    parameter_name = "creation_date"
    field_name = "creation_date"

    def lookups(self, request, model_admin):
        yield from ((dt.year, dt.year) for dt in FilmWork.objects.all().dates("creation_date", "year"))

    def queryset(self, request, queryset):
        year = self.value()
        if year:
            return queryset.filter(creation_date__year=year)
        return queryset
