# Adbrew Test — TODO app

Solution to the [Adbrew test](https://github.com/adbrew/adb_test): a React (hooks) frontend and a Django REST backend that persist TODOs in MongoDB, all running under Docker Compose.

## Running it

```
git clone https://github.com/Ripperox/adbrew-todo.git
cd adbrew-todo
export ADBREW_CODEBASE_PATH="$PWD/src"
docker-compose build
docker-compose up -d
```

- App: http://localhost:3000 (first start runs `yarn install`, give it a couple of minutes — `docker logs -f app`)
- API: http://localhost:8000/todos/

Tests:

```
docker exec api bash -c "cd /src/rest && python manage.py test rest"
docker exec app bash -c "cd /src/app && CI=true yarn test"
```

## Docker setup: what was broken and what I changed

The original setup built one image (Python + Yarn + MongoDB server) and used it for all three services. On a current machine the build fails, because `python:3.8` now resolves to Debian 12 (bookworm) rather than the Debian 10 (buster) the Dockerfile was written for, and I'm on Apple Silicon (arm64).

| Problem | Cause | Fix |
|---|---|---|
| `Unable to locate package mongodb-org` | MongoDB's buster/4.4 apt repo has no arm64 server packages (only client tools), and the 4.4 buster packages expect OpenSSL 1.1, which bookworm doesn't ship | `mongo` service uses the official `mongo:4.4` image. The API only needs the `pymongo` client, so the server install was removed from the Dockerfile |
| `easy_install: not found` | Removed from modern setuptools; pip is already in `python:3.8` | Removed the line |
| `yarn` not found after removing the Mongo block | The yarn repo was added but `apt-get update` only ran later, inside the Mongo block | Moot after the next change; worth noting that `update` and `install` belong in the same `RUN` |
| React dev server crashes (`ERR_PACKAGE_PATH_NOT_EXPORTED`) | Debian's yarn package pulls in Node 18; `react-scripts 4.0.1` predates Node 17's stricter package exports | `app` service uses the official `node:14` image (ships with yarn), matching the react-scripts 4 era |
| `pandas` fails to build | `pandas==1.1.2` has no aarch64 wheel for Python 3.8, so pip compiles from source, which fails with current toolchains | Bumped to `1.1.5`, the first 1.1.x patch release with an aarch64 cp38 wheel |

The result is one image per runtime: the Dockerfile now only builds the Python API, Mongo and Node use official images. I also replaced the legacy `links` with `depends_on` (Compose networking already resolves service names) and dropped the obsolete `version` key.

**How the pieces connect:** Compose puts the three containers on one network, so the API reaches Mongo at `mongo:27017` (`MONGO_HOST`/`MONGO_PORT` are set in the Dockerfile). `src/` is bind-mounted into `api` and `app`, so code changes hot-reload without rebuilding. Mongo's data directory is mounted to `src/db/` so data survives `docker-compose down` (it's gitignored). The browser talks to the API on `localhost:8000`, which works because port 8000 is published to the host and CORS is open in `settings.py`.

## Backend

```
src/rest/rest/
  db.py            Mongo client (one per process; pymongo pools connections)
  repositories.py  TodoRepository — the only code that knows about Mongo
  services.py      TodoService — validation and business rules
  views.py         TodoListView — HTTP only: parse request, call service, map errors to status codes
  tests.py         service tests with a fake repository, view tests via APIRequestFactory
```

The layering means each piece has one reason to change. Swapping Mongo for another store means writing another repository with the same two methods; the service and view don't change. It also lets the service and view be tested without a database.

### API

`GET /todos/` → `200`, newest first

```json
[{ "id": "66fd…", "description": "Buy milk", "created_at": "2026-10-02T11:45:50.909Z" }]
```

`POST /todos/` with `{"description": "Buy milk"}` → `201` with the created todo

| Case | Response |
|---|---|
| missing, empty or whitespace-only description | `400 {"detail": "description is required"}` |
| description not a string | `400 {"detail": "description must be a string"}` |
| description over 500 chars | `400` |
| body not a JSON object | `400` |
| Mongo unreachable | `503 {"detail": "database unavailable, please try again"}` (logged with traceback) |

Notes: the Mongo `_id` is returned as a string `id` so the API doesn't leak storage details. Timestamps are stored as UTC datetimes and returned as ISO 8601 at millisecond precision, which is what Mongo stores. Error bodies use `detail`, the same key DRF uses for its own errors (e.g. malformed JSON), so clients handle one shape.

## Frontend

```
src/app/src/
  api/todos.js            fetch wrapper; turns network and HTTP errors into Error(message)
  hooks/useTodos.js       todos/loading/error state, refresh(), addTodo()
  components/TodoList.js  loading, error, empty and list states
  components/TodoForm.js  controlled input, blocks blank submits, shows server errors
  App.js                  composition only
```

All function components with hooks. After a successful POST the hook re-fetches the list from the API, as the task asks, rather than appending locally. The form trims input and disables the button while blank or submitting; the backend still validates everything since the UI isn't a security boundary. The API base URL can be overridden with `REACT_APP_API_URL`.

## What I'd do next

- Trim `requirements.txt`: the API uses Django, DRF, django-cors-headers and pymongo; the other ~75 packages (pandas, jupyterlab, matplotlib…) make the image several GB and the build minutes long.
- Upgrade the frontend off `react-scripts 4` / Node 14 (EOL), e.g. to Vite on Node 20.
- Index `created_at` for the sorted list query, and paginate `GET /todos/` once lists get large.
- Restrict CORS to the frontend origin instead of allowing all, and move config (Mongo URI, secret key, debug) to environment variables.
- Production setup: gunicorn/uwsgi instead of `runserver`, a built static frontend instead of the dev server, a Mongo healthcheck so `api` waits for readiness rather than just container start.
