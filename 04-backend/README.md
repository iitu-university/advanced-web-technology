# Lab 4 — Course Catalog API

Самостоятельный backend на FastAPI для каталога из шести курсов. Проект расположен в `04-backend`, не меняет приложения предыдущих лабораторных работ и открывает интерактивную документацию по адресу `/docs`.

## Задание и результат

| Требование лабораторной | Реализация |
| --- | --- |
| Python 3.10+, отдельное окружение и `fastapi[standard]` | Проект запускается в `.venv`; зависимость записана в `requirements.txt`, а окружение исключено через `.gitignore`. |
| Модель `Course` | `models.py`: обязательные `id`, `title`, `description`, `credits`; `is_elective=False` и `likes=0`. |
| Шесть курсов и функции доступа | `data.py`: данные из примера и таблиц Lab 4, `get_all_courses()` возвращает новый список, `find_course()` ищет по строковому идентификатору. |
| Проверка работы сервера | `GET /` возвращает сообщение `Course Catalog API is running`. |
| Список курсов | `GET /courses` с `response_model=list[Course]`, фильтром `is_elective`, сортировкой `popular` или `title` и постраничной выдачей. |
| Один курс и отсутствие курса | `GET /courses/{course_id}` возвращает модель `Course` или HTTP 404 с `{"detail":"Course not found"}`. |
| Пагинация через зависимость | Функция `pagination()` вычисляет `offset` и `limit`; маршрут получает результат через `Depends(pagination)`. |
| Автоматическая документация | FastAPI формирует `/docs`, `/redoc` и `/openapi.json`; в схеме приложения ровно три рабочих маршрута. |
| История работы | Изменения разбиты на осмысленные коммиты: окружение, модель и данные, маршруты, документация. |

В PDF сказано перенести курсы из `lib/courses.ts`, но данные в существующих `02-course-catalog` и `03-tailwind` отличаются от шести курсов, перечисленных в самом Lab 4. Здесь использованы записи из Lab 4: только они дают точные ответы из таблиц проверки, включая `ai-integration` первым и `web-security` на второй странице. Фронтенд не изменялся.

## Структура

```text
04-backend/
├── .gitignore
├── README.md
├── requirements.txt
├── models.py
├── data.py
└── main.py
```

Папка `.venv` создаётся локально и не входит в Git.

## Запуск

Нужен Python 3.10 или новее. В терминале из корня репозитория:

```bash
cd 04-backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
fastapi dev main.py
```

На Windows создайте окружение командой `python -m venv .venv` и активируйте его через `.venv\Scripts\Activate.ps1`. Откройте `http://127.0.0.1:8000/docs` для проверки запросов через **Try it out**. Также доступны `http://127.0.0.1:8000/redoc` и `http://127.0.0.1:8000/openapi.json`.

## Как работает API

Список сначала фильтруется по `is_elective` и, если передан `q`, по подстроке названия без учёта регистра. Затем список сортируется и только после этого разбивается на страницы. По умолчанию `sort=popular`, `page=1`, `page_size=20`. Для `sort=title` используется алфавитный порядок названий; для `popular` — убывание числа лайков. Неуказанный `is_elective` сохраняет обе категории, а `is_elective=false` действительно оставляет только обязательные курсы.

Дополнительно выполнены три необязательных пункта Lab 4: `sort` ограничен значениями `popular` и `title`; `page` должен быть не меньше 1, а `page_size` — от 1 до 100; `q` ищет по названию без учёта регистра. Ошибочные параметры получают HTTP 422. Дополнительный `/stats` не добавлен, поскольку обязательная проверка требует ровно три рабочих маршрута.

## Что проверено

| Запрос | Ожидаемый и полученный результат |
| --- | --- |
| `GET /` | HTTP 200, `{"message":"Course Catalog API is running"}`. |
| `GET /courses` | HTTP 200, 6 курсов; первым идёт `ai-integration`, последним `api-design`. |
| `GET /courses?is_elective=true` | 2 курса: `ai-integration`, `api-design`. |
| `GET /courses?is_elective=false` | 4 курса: `modern-frontend`, `web-security`, `backend-fastapi`, `databases-postgresql`. |
| `GET /courses?sort=title` | `ai-integration`, `api-design`, `backend-fastapi`, `modern-frontend`, `databases-postgresql`, `web-security`. |
| `GET /courses?page=1&page_size=2` | `ai-integration`, `modern-frontend`. |
| `GET /courses?page=2&page_size=2` | `web-security`, `backend-fastapi`. |
| `GET /courses?page=3&page_size=2` | `databases-postgresql`, `api-design`. |
| `GET /courses?page=4&page_size=2` | Пустой список `[]`. |
| `GET /courses/web-security` | HTTP 200, объект курса `web-security` со всеми шестью полями. |
| `GET /courses/nope` | HTTP 404, `{"detail":"Course not found"}`. |
| `GET /courses?q=react` | Только `modern-frontend`. |
| `GET /courses?q=api` | `backend-fastapi`, `api-design`. |
| `GET /courses?sort=banana`, `?page=0`, `?page_size=1000` | HTTP 422 для каждого запроса. |
| `GET /docs`, `GET /redoc`, `GET /openapi.json` | HTTP 200; OpenAPI содержит ровно `/`, `/courses` и `/courses/{course_id}`. |

Также проверяется поведение модели: строка `credits="five"` вызывает ошибку валидации, а `credits="5"` преобразуется в число 5; у нового курса без необязательных полей значения `is_elective=False` и `likes=0`.

Проверка выполнена на Python 3.12.14 и FastAPI 0.142.2: запросы и схему OpenAPI сверили через `TestClient`, затем запустили `fastapi dev main.py` и подтвердили ответы `/`, `/docs`, `/redoc`, `/openapi.json` и 404 обычными HTTP-запросами. Файлы Python также прошли проверку синтаксиса.

## Почему выбрано такое решение

Данные, модель и HTTP-маршруты находятся в отдельных файлах, поэтому изменения схемы или набора курсов не смешиваются с обработкой запросов. Pydantic проверяет данные при создании и описывает ответы в OpenAPI. `response_model` дополнительно гарантирует одинаковую форму каждого курса в ответе. `HTTPException` явно задаёт требуемый код 404. Зависимость `pagination()` держит расчёт смещения вне маршрута и показывает применение `Depends`, которое проверяется в задании. Фильтрация до пагинации гарантирует заполнение страниц результатами выбранного набора. Ограничения `Literal` и `Query` дают понятные ошибки клиенту и точное описание параметров в `/docs`.

Для этой лабораторной данные хранятся в памяти: задание не требует базы данных, а такой вариант позволяет сосредоточиться на FastAPI, Pydantic и маршрутах. Автоматическая документация покрывает ручную проверку без отдельного клиента. Если курсы будут изменяться пользователями, следующим шагом станет постоянное хранилище и отдельные тесты API.
