correct_metrics = (
    {
        "url": "localhost:8000/api/v1/films",
        "action": "click",
        "information": "Additional information",
    },
    {
        "url": "localhost:8000/api/v1/films/9e2a9506-6cc0-4200-aaae-ed60acc6470d",
        "action": "like",
        "information": "Additional information",
    },
    {
        "url": "localhost:8000/api/v1/films",
        "action": "watched",
        "information": "Additional information",
    },
    {
        "url": "localhost:8000/api/v1/films",
        "action": "dislike",
        "information": "Additional information",
    },
)

not_correct_metrics = [
    {
        "action": "click",
        "information": "Additional information",
    },
    {
        "url": "localhost:8000/api/v1/films/9e2a9506-6cc0-4200-aaae-ed60acc6470d",
        "action": "like",
    },
]
