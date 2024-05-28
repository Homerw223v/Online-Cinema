class Queries:
    FILMWORK_DATA = """
    SELECT
        fw.id,
        fw.rating as imdb_rating,
        fw.title,
        fw.description,
        COALESCE (
            json_agg(
                DISTINCT jsonb_build_object(
                    'id', g.id,
                    'name', g.name
                )
            ) FILTER (WHERE g.id IS NOT NULL),
            '[]'
        ) as genre,
        array_remove(ARRAY_AGG(DISTINCT g.name), NULL) as genre_names,
        COALESCE (
            json_agg(
                DISTINCT jsonb_build_object(
                    'id', p.id,
                    'full_name', p.full_name
                )
            ) FILTER (WHERE pfw.role = 'director'),
            '[]'
        ) as directors,
        COALESCE (
            ARRAY_AGG(DISTINCT p.full_name
            ) FILTER (WHERE pfw.role = 'director'),
            '{{}}'
        ) as directors_names,
        COALESCE (
            json_agg(
                DISTINCT jsonb_build_object(
                    'id', p.id,
                    'full_name', p.full_name
                )
            ) FILTER (WHERE pfw.role = 'actor'),
            '[]'
        ) as actors,
        COALESCE (
            ARRAY_AGG(DISTINCT p.full_name
            ) FILTER (WHERE pfw.role = 'actor'),
            '{{}}'
        ) as actors_names,
        COALESCE (
            json_agg(
                DISTINCT jsonb_build_object(
                    'id', p.id,
                    'full_name', p.full_name
                )
            ) FILTER (WHERE pfw.role = 'writer'),
            '[]'
        ) as writers,
        COALESCE (
            ARRAY_AGG(DISTINCT p.full_name
            ) FILTER (WHERE pfw.role = 'writer'),
            '{{}}'
        ) as writers_names,
        array_remove(ARRAY_AGG(DISTINCT sfw.subscription_id), NULL) as subscriptions
    FROM content.film_work fw
    LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
    LEFT JOIN content.person p ON p.id = pfw.person_id
    LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
    LEFT JOIN content.genre g ON g.id = gfw.genre_id
    LEFT JOIN content.subscription_film_work sfw ON sfw.film_work_id = fw.id
    WHERE fw.id IN ({ids})
    GROUP BY fw.id;
    """

    FILMWORK_MODIFIED = """
        SELECT
           fw.id,
           fw.modified
        FROM content.film_work fw
        WHERE fw.modified > %s
        ORDER BY fw.modified;
    """
    PERSON_MODIFIED = """
        SELECT
           id,
           modified
        FROM content.person p
        WHERE p.modified > %s
        ORDER BY modified;
    """
    FILM_BY_PERSON = """
        SELECT
            DISTINCT fw.id
        FROM content.film_work fw
        JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
        WHERE pfw.person_id IN ({ids});"""
    GENRE_MODIFIED = """
        SELECT
           id,
           modified
        FROM content.genre g
        WHERE g.modified > %s
        ORDER BY g.modified;
    """
    FILM_BY_GENRE = """
        SELECT
            DISTINCT fw.id
        FROM content.film_work fw
        JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
        WHERE gfw.genre_id IN ({ids});
    """
    GENRE_DATA = """
        SELECT
            id,
            name
        FROM content.genre g
        WHERE g.id IN ({ids});
    """
    PERSON_BY_FILM = """
    SELECT
        DISTINCT pfw.person_id as id
    FROM content.person_film_work pfw
    JOIN content.film_work fw ON pfw.film_work_id = fw.id
    WHERE fw.id IN ({ids});
    """
    PERSON_DATA = """
    SELECT
        p.id,
        p.full_name,
        COALESCE (
            json_agg(
                DISTINCT jsonb_build_object(
                    'id', pfw.film_work_id,
                    'roles', ARRAY[pfw.role]
                )
            ),
            '[]'
        ) as films
    FROM content.person p
    JOIN content.person_film_work pfw ON pfw.person_id = p.id
    WHERE p.id IN ({ids})
    GROUP BY p.id;
    """
