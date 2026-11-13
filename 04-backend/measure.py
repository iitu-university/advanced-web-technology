import asyncio

import httpx

API = "http://localhost:8000"
STUDENT = 2
MY_COURSES = """
query MyCourses($id: ID!) {
  student(id: $id) {
    name
    enrollments { id course { title credits level } }
  }
}
"""


async def rest(client: httpx.AsyncClient):
    first = await asyncio.gather(
        client.get(f"/students/{STUDENT}"),
        client.get(f"/students/{STUDENT}/enrollments"),
    )
    codes = [enrollment["courseId"] for enrollment in first[1].json()]
    second = await asyncio.gather(*(client.get(f"/courses/{code}") for code in codes))
    return [*first, *second], 2


async def graphql(client: httpx.AsyncClient):
    response = await client.post(
        "/graphql", json={"query": MY_COURSES, "variables": {"id": str(STUDENT)}}
    )
    return [response], 1


async def main():
    print(f"{'':<8} {'requests':<9} {'rounds':<7} {'bytes':<6} SQL queries")
    async with httpx.AsyncClient(base_url=API) as client:
        for name, run in (("REST", rest), ("GraphQL", graphql)):
            responses, rounds = await run(client)
            size = sum(len(response.content) for response in responses)
            sql = sum(int(response.headers["x-sql-queries"]) for response in responses)
            print(f"{name:<8} {len(responses):<9} {rounds:<7} {size:<6} {sql}")


asyncio.run(main())
