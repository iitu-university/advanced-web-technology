"""Integration checks for the Lab 5 HTTP contract and CORS middleware."""
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from data import COURSES
from main import ENROLLMENTS, app
from models import Course, EnrollmentIn


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.original_likes = [course.likes for course in COURSES]
        ENROLLMENTS.clear()

    def tearDown(self):
        for course, likes in zip(COURSES, self.original_likes):
            course.likes = likes
        ENROLLMENTS.clear()
        self.client.close()

    def test_six_documented_operations_and_camel_case_schema(self):
        schema = self.client.get('/openapi.json').json()
        self.assertEqual(sum(len(methods) for methods in schema['paths'].values()), 6)
        fields = schema['components']['schemas']['Course']['properties']
        self.assertIn('isElective', fields)
        self.assertNotIn('is_elective', fields)

    def test_catalog_contract_order_filter_and_query_names(self):
        courses = self.client.get('/courses').json()
        self.assertEqual(len(courses), 6)
        self.assertEqual(courses[0]['id'], 'ai-integration')
        self.assertEqual(courses[-1]['id'], 'api-design')
        self.assertEqual(set(courses[0]), {'id', 'title', 'description', 'credits', 'isElective', 'likes'})
        electives = self.client.get('/courses?is_elective=true').json()
        self.assertEqual([course['id'] for course in electives], ['ai-integration', 'api-design'])
        self.assertEqual(len(self.client.get('/courses?isElective=true').json()), 6)
        self.assertEqual(len(self.client.get('/courses?is_elective=false').json()), 4)

    def test_lab_four_search_sort_and_pagination_are_preserved(self):
        courses = self.client.get('/courses?sort=title').json()
        self.assertEqual([course['title'] for course in courses], sorted(course.title for course in COURSES))
        self.assertEqual(len(self.client.get('/courses?page=2&page_size=2').json()), 2)
        self.assertEqual(self.client.get('/courses?q=FASTAPI').json()[0]['id'], 'backend-fastapi')
        for query in ('page=0', 'page_size=101', 'sort=nope'):
            self.assertEqual(self.client.get('/courses?' + query).status_code, 422)

    def test_like_mutates_server_state_and_unknown_course_returns_404(self):
        before = self.client.get('/courses/web-security').json()['likes']
        for offset in (1, 2):
            response = self.client.post('/courses/web-security/like')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['likes'], before + offset)
        self.assertEqual(self.client.get('/courses/web-security').json()['likes'], before + 2)
        for method, path in ((self.client.post, '/courses/nope/like'), (self.client.get, '/courses/nope')):
            response = method(path)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {'detail': 'Course not found'})

    def test_enrollment_creation_validation_and_ids(self):
        response = self.client.post('/enrollments', json={'courseId': 'web-security', 'studentName': 'Aigerim'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {'courseId': 'web-security', 'studentName': 'Aigerim', 'id': 1})
        second = self.client.post('/enrollments', json={'course_id': 'api-design', 'student_name': 'Dana'})
        self.assertEqual(second.status_code, 201)
        self.assertEqual(second.json()['id'], 2)
        rejected = self.client.post('/enrollments', json={'courseId': 'web-security', 'studentName': 'A'})
        self.assertEqual(rejected.status_code, 422)
        self.assertEqual(rejected.json()['detail'][0]['loc'], ['body', 'studentName'])
        self.assertEqual(rejected.json()['detail'][0]['msg'], 'String should have at least 2 characters')
        unknown = self.client.post('/enrollments', json={'courseId': 'nope', 'studentName': 'Aigerim'})
        self.assertEqual(unknown.status_code, 404)
        self.assertEqual(len(self.client.get('/enrollments').json()), 2)
        wrong_content_type = self.client.post('/enrollments', content='{"courseId":"web-security","studentName":"Aigerim"}')
        self.assertEqual(wrong_content_type.status_code, 422)

    def test_allowed_and_foreign_origins(self):
        allowed = self.client.get('/', headers={'Origin': 'http://localhost:3000'})
        self.assertEqual(allowed.headers['access-control-allow-origin'], 'http://localhost:3000')
        self.assertEqual(allowed.headers['vary'], 'Origin')
        foreign = self.client.get('/', headers={'Origin': 'http://evil.example'})
        self.assertEqual(foreign.status_code, 200)
        self.assertNotIn('access-control-allow-origin', foreign.headers)

    def test_json_preflight_and_max_age(self):
        headers = {'Origin': 'http://localhost:3000', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type'}
        response = self.client.options('/enrollments', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['access-control-allow-origin'], 'http://localhost:3000')
        self.assertIn('POST', response.headers['access-control-allow-methods'])
        self.assertEqual(response.headers['access-control-allow-headers'], 'content-type')
        self.assertEqual(response.headers['access-control-max-age'], '600')
        self.assertEqual(self.client.options('/enrollments', headers={**headers, 'Origin': 'http://localhost:3000/'}).status_code, 400)

    def test_models_accept_python_names_and_json_aliases(self):
        for key in ('is_elective', 'isElective'):
            self.assertTrue(Course(id='test', title='Test', description='Test', credits=1, **{key: True}).is_elective)
        self.assertEqual(EnrollmentIn(courseId='web-security', studentName='Dana').course_id, 'web-security')
        with self.assertRaises(ValidationError):
            EnrollmentIn(courseId='web-security', studentName='A')

    def test_bonus_origins_from_environment(self):
        # Importing the module again builds a fresh app using the configured list.
        import importlib.util
        from pathlib import Path
        with patch.dict(os.environ, {'CORS_ORIGINS': 'http://localhost:3000,http://127.0.0.1:3000'}):
            spec = importlib.util.spec_from_file_location('bonus_app', Path(__file__).parents[1] / 'main.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            with TestClient(module.app) as client:
                for origin in ('http://localhost:3000', 'http://127.0.0.1:3000'):
                    response = client.get('/', headers={'Origin': origin})
                    self.assertEqual(response.headers['access-control-allow-origin'], origin)
                self.assertNotIn('access-control-allow-origin', client.get('/', headers={'Origin': 'http://evil.example'}).headers)


if __name__ == '__main__':
    unittest.main()
