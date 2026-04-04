def memory_classifier(query):

    q = query.lower()

    keywords = [
        "budget",
        "location",
        "destination",
        "preference",
        "travel",
        "plan",
        "vacation",
        "trip",
        "hotel",
        "flight"
    ]

    return any(k in q for k in keywords)