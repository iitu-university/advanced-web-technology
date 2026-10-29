-- Example values for each API route. Writes roll back; identity gaps are normal.
-- 1. GET /courses?is_elective=false&sort=popular&page=1&page_size=3
SELECT id, title, credits, likes FROM courses
WHERE is_elective = false
ORDER BY likes DESC, id LIMIT 3 OFFSET 0;

-- 1b. The second page.
SELECT id, title, credits, likes FROM courses
WHERE is_elective = false
ORDER BY likes DESC, id LIMIT 3 OFFSET 3;

-- 2. GET /courses/{course_id}
SELECT id, title, credits, is_elective, likes FROM courses WHERE id = 'api-design';
-- 2b. No row means HTTP 404 at the API boundary.
SELECT id, title, credits, is_elective, likes FROM courses WHERE id = 'no-such-course';

-- 3. POST /courses/{course_id}/like: one atomic increment.
BEGIN;
UPDATE courses SET likes = likes + 1 WHERE id = 'api-design' RETURNING id, likes;
-- 3b. UPDATE 0 means HTTP 404.
UPDATE courses SET likes = likes + 1 WHERE id = 'no-such-course' RETURNING id, likes;
ROLLBACK;

-- 4. POST /enrollments: let PostgreSQL assign id and enrolled_at.
BEGIN;
INSERT INTO enrollments (course_id, student_id)
VALUES ('web-security', 3) RETURNING id, course_id, student_id;
ROLLBACK;

-- 5. GET /enrollments: normalized facts are joined at read time.
SELECT e.id, s.name AS student, c.title AS course
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN courses c ON c.id = e.course_id
ORDER BY e.id;

-- 6. Statistics, including courses with zero enrollments.
SELECT c.id, count(e.id) AS enrolled
FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id
GROUP BY c.id ORDER BY enrolled DESC, c.id;

-- Bonus 4, query 7: courses without enrollments.
SELECT c.id FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id
WHERE e.id IS NULL ORDER BY c.id;

-- Bonus 4, query 8: HAVING filters groups after aggregation.
SELECT s.name, count(*) AS courses
FROM students s JOIN enrollments e ON e.student_id = s.id
GROUP BY s.id HAVING count(*) > 1 ORDER BY courses DESC, s.id;
