class AlreadyExistsException(Exception):
    pass  # noqa


class NotFoundException(Exception):
    pass  # noqa


class FilmNotFound(NotFoundException):
    pass  # noqa


class GenreNotFound(NotFoundException):
    pass  # noqa


class PersonNotFound(NotFoundException):
    pass  # noqa


class DatabaseConnectionError(Exception):
    pass  # noqa
