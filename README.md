# TaskFlow

TaskFlow is a collaborative project and task management app. Users can create project boards, invite teammates, assign and track tasks, discuss work with comments, and see project activity update live.

## Features

- Account registration and login with short lived access tokens and refresh tokens.
- Project ownership, membership, join requests, and ownership transfer.
- Task assignment, status and priority updates, filtering, sorting, and comments.
- Project activity history and WebSocket notifications for live changes.
- User profiles and a personal assigned tasks view.

## Architecture

```text
React + Vite (frontend, port 5173)
       | HTTP /api and WebSocket /ws
       v
FastAPI (backend, port 8000)
       | SQLAlchemy ORM
       v
PostgreSQL (database: taskflow_db)
```

- `frontend/src/pages` contains the screens; `frontend/src/api` wraps HTTP calls; `frontend/src/context` manages authentication; and `frontend/src/hooks` and `frontend/src/services` handle WebSocket updates.
- `backend/app/routers` exposes REST and WebSocket endpoints. Routers delegate business rules to `backend/app/services` and validate request and response data through `backend/app/schemas`.
- `backend/app/models` defines SQLAlchemy entities and relationships. `backend/app/database` manages database sessions, and `backend/alembic/versions` contains schema migrations.
- Authentication uses signed JWTs and Argon2 password hashes. The API docs are available at `/docs` while the backend is running.

## Requirements

- Python 3.12 or later
- Node.js 20 or later and npm
- PostgreSQL 14 or later

## Setup

### 1. Create the database

Create a PostgreSQL database named `taskflow_db` (or choose another name and use it in `DATABASE_URL`). For example, from `psql`:

```sql
CREATE DATABASE taskflow_db;
```

### 2. Configure the backend

From the repository root, copy the example environment file and edit the database URL and JWT secret:

```powershell
Copy-Item .env.example backend/.env
```

```sh
cp .env.example backend/.env
```

Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL, for example `postgresql+psycopg2://postgres:your-password@localhost:5432/taskflow_db`. Set `JWT_SECRET_KEY` to a private random value. The example values are placeholders and must be replaced for any non-local deployment. Keep `backend/.env` private.

Install Python dependencies and apply the migrations from the backend directory:

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
```

On macOS or Linux, use:

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
alembic upgrade head
```

### 3. Add evaluator demo data

With the backend virtual environment active and the current directory set to `backend`:

```sh
python -m scripts.seed
```

This safely inserts or refreshes the two demo accounts, the shared project, and four sample tasks. The accounts are:

| Name | Email | Password |
| --- | --- | --- |
| Maya Chen | `maya@example.com` | `TaskFlow123!` |
| Arjun Rao | `arjun@example.com` | `TaskFlow123!` |

Maya owns the shared project; Arjun is a member. Tasks are assigned between both accounts so evaluators can check the board and each user's assigned tasks. The password is for local evaluation only.

To discard all TaskFlow rows and recreate a clean demo dataset, use `python -m scripts.seed --reset`. **Reset deletes all users, projects, memberships, tasks, comments, activity logs, join requests, and refresh tokens in the configured database.** It keeps the database and migration history. Confirm `DATABASE_URL` points to a disposable/local database before using `--reset`.

### 4. Start the backend

From `backend` with the virtual environment active:

```sh
uvicorn app.main:app --reload
```

The API is at `http://localhost:8000`, interactive API documentation is at `http://localhost:8000/docs`, and the database health check is at `http://localhost:8000/health/database`.

### 5. Start the frontend

In a second terminal, from the repository root:

```sh
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite, usually `http://localhost:5173`. The development server proxies `/api` and `/ws` requests to `http://localhost:8000`. To use another API URL, copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_BASE_URL`.

## Evaluator walkthrough

1. Sign in as Maya and open the **TaskFlow Collaboration Demo** project. Review the board, task statuses, priority labels, members, and activity view.
2. Open **Assigned** to see tasks assigned to Maya. Open a task to update its status or add a comment.
3. Sign out and sign in as Arjun. Check his assigned tasks and open the same shared project.
4. With both accounts open in separate browser sessions, make a task or membership change and observe live project/user notifications.
5. Explore project settings and profile pages. Use `/docs` to inspect and exercise the API directly if needed.

## Useful commands

Run these from `backend` with its virtual environment active:

```sh
alembic current          # show the applied migration
alembic history          # list schema migration history
python -m scripts.seed   # idempotently seed demo data
```

Run these from `frontend`:

```sh
npm run lint
npm run build
```

## Troubleshooting

- **Database connection fails:** confirm PostgreSQL is running, the database exists, and `backend/.env` has the correct `DATABASE_URL`.
- **Missing table errors:** activate the backend environment and run `alembic upgrade head` from `backend`.
- **Login returns 401:** seed the demo accounts again with `python -m scripts.seed`, then use the listed email and password.
- **Frontend cannot reach the API:** start the backend on port 8000 and load the Vite URL on port 5173.
