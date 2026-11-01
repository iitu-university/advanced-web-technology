DROP TABLE IF EXISTS registrations;
CREATE TABLE registrations (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_name text,
    student_email text,
    course_id text,
    course_title text,
    credits integer
);
INSERT INTO registrations (student_name, student_email, course_id, course_title, credits) VALUES
  ('Aigerim Sadykova', 'aigerim@example.com', 'modern-frontend', 'Modern Frontend: React & Next.js', 5),
  ('Aigerim Sadykova', 'aigerim@example.com', 'ai-integration', 'AI/LLM Integration', 5),
  ('Daniyar Bekov', 'daniyar@example.com', 'modern-frontend', 'Modern Frontend: React & Next.js', 5),
  ('Daniyar Bekov', 'daniyar@example.com', 'backend-fastapi', 'Backend Foundations: FastAPI', 5),
  ('Daniyar Bekov', 'daniyar@example.com', 'ai-integration', 'AI/LLM Integration', 5),
  ('Asel Omarova', 'asel@example.com', 'ai-integration', 'AI/LLM Integration', 5);

BEGIN;
UPDATE registrations SET course_title='Modern Frontend: React 19 & Next.js 16'
WHERE student_name='Daniyar Bekov' AND course_id='modern-frontend';
SELECT DISTINCT course_id, course_title FROM registrations WHERE course_id='modern-frontend';
ROLLBACK;

BEGIN;
DELETE FROM registrations WHERE student_name='Daniyar Bekov' AND course_id='backend-fastapi';
SELECT * FROM registrations WHERE course_id='backend-fastapi';
ROLLBACK;

BEGIN;
INSERT INTO registrations (course_id, course_title, credits) VALUES ('web-security','Web Security Essentials',4);
SELECT student_name, course_id FROM registrations WHERE course_id='web-security';
ROLLBACK;

\ir ../schema.sql
INSERT INTO students (name,email)
SELECT student_name,student_email FROM registrations
GROUP BY student_name,student_email ORDER BY min(id);
INSERT INTO courses (id,title,description,credits)
SELECT DISTINCT course_id,course_title,'',credits FROM registrations;
INSERT INTO enrollments (course_id,student_id)
SELECT r.course_id,s.id FROM registrations r
JOIN students s ON s.email=r.student_email ORDER BY r.id;
SELECT (SELECT count(*) FROM courses) AS courses,
       (SELECT count(*) FROM students) AS students,
       (SELECT count(*) FROM enrollments) AS enrollments;
