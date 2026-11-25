import httpx

from lab9_checks import ADMIN, BASE, authorization

QUERIES = [
    ("students → enrollments → course", "{ students { name enrollments { course { title } } } }"),
    ("enrollments → course, student", "{ enrollments { id course { title } student { name } } }"),
]
with httpx.Client(base_url=BASE) as client:
    headers = authorization(client, ADMIN)
    for title, query in QUERIES:
        response = client.post("/graphql", json={"query": query}, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("errors"):
            raise RuntimeError(data["errors"])
        rows = len(next(iter(data["data"].values())))
        print(f"{title:<34} rows: {rows:<3} SQL queries: {response.headers['x-sql-queries']}")
