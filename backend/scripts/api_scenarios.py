"""Exercise TaskFlow API and WebSocket flows against a running server."""

import asyncio
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import websockets

BASE = "http://127.0.0.1:8000"
WS = "ws://127.0.0.1:8000"
STAMP = str(int(time.time()))
results = []


def record(name, ok, detail=""):
    results.append((ok, name, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"{mark}  {name}" + (f" — {detail}" if detail else ""))


def call(method, path, token=None, body=None, expected=200):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        BASE + path,
        data=data,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode()
            payload = json.loads(raw) if raw else None
            return response.status, payload
    except urllib.error.HTTPError as error:
        raw = error.read().decode()
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        return error.code, payload


def expect(name, method, path, expected, token=None, body=None):
    status, payload = call(method, path, token=token, body=body)
    ok = status == expected
    detail = "" if ok else f"got {status} {payload}"
    record(name, ok, detail)
    return payload


async def ws_once(path, token=None, timeout=2.5):
    async with websockets.connect(WS + path) as socket:
        if token is not None:
            await socket.send(json.dumps({
                "type": "authenticate",
                "token": token
            }))

        try:
            message = await asyncio.wait_for(socket.recv(), timeout=timeout)
            return "message", json.loads(message)
        except websockets.ConnectionClosed as closed:
            return "closed", closed.code


def future_due():
    return (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()


def past_due():
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


async def main():
    health = expect("health database", "GET", "/health/database", 200)
    record("database connected", health and health.get("database") == "Connected successfully")

    owner_email = f"owner.{STAMP}@example.com"
    member_email = f"member.{STAMP}@example.com"
    outsider_email = f"outsider.{STAMP}@example.com"
    password = "Secret123"

    owner = expect(
        "register owner",
        "POST",
        "/api/auth/register",
        201,
        body={"name": "Owner", "email": owner_email, "password": password}
    )
    expect(
        "reject duplicate email",
        "POST",
        "/api/auth/register",
        409,
        body={"name": "Owner", "email": owner_email, "password": password}
    )
    expect(
        "reject weak password",
        "POST",
        "/api/auth/register",
        422,
        body={"name": "Weak", "email": f"weak.{STAMP}@example.com", "password": "password"}
    )
    expect(
        "reject bad login",
        "POST",
        "/api/auth/login",
        401,
        body={"email": owner_email, "password": "WrongPass1"}
    )

    member = expect(
        "register member",
        "POST",
        "/api/auth/register",
        201,
        body={"name": "Member", "email": member_email, "password": password}
    )
    outsider = expect(
        "register outsider",
        "POST",
        "/api/auth/register",
        201,
        body={"name": "Outsider", "email": outsider_email, "password": password}
    )

    owner_access = owner["access_token"]
    owner_refresh = owner["refresh_token"]
    member_access = member["access_token"]
    outsider_access = outsider["access_token"]

    expect("unauthenticated projects", "GET", "/api/projects", 401)
    expect(
        "reject refresh token as access token",
        "GET",
        "/api/projects",
        401,
        token=owner_refresh
    )

    refreshed = expect(
        "refresh tokens",
        "POST",
        "/api/auth/refresh",
        200,
        body={"refresh_token": owner_refresh}
    )
    owner_access = refreshed["access_token"]
    expect(
        "reject reused refresh token",
        "POST",
        "/api/auth/refresh",
        401,
        body={"refresh_token": owner_refresh}
    )
    expect(
        "reject access token on refresh",
        "POST",
        "/api/auth/refresh",
        401,
        body={"refresh_token": owner_access}
    )

    project = expect(
        "create project",
        "POST",
        "/api/projects",
        201,
        token=owner_access,
        body={"name": "Launch", "description": "Board"}
    )
    project_id = project["id"]
    expect("list projects", "GET", "/api/projects", 200, token=owner_access)
    expect("get project", "GET", f"/api/projects/{project_id}", 200, token=owner_access)
    expect(
        "outsider cannot read project",
        "GET",
        f"/api/projects/{project_id}",
        403,
        token=outsider_access
    )
    expect(
        "update project",
        "PUT",
        f"/api/projects/{project_id}",
        200,
        token=owner_access,
        body={"name": "Launch updated", "description": "Live board"}
    )
    expect(
        "empty project update rejected",
        "PUT",
        f"/api/projects/{project_id}",
        400,
        token=owner_access,
        body={}
    )

    expect(
        "invite unknown email",
        "POST",
        f"/api/projects/{project_id}/members",
        404,
        token=owner_access,
        body={"email": f"missing.{STAMP}@example.com"}
    )
    membership = expect(
        "invite member",
        "POST",
        f"/api/projects/{project_id}/members",
        201,
        token=owner_access,
        body={"email": member_email}
    )
    expect(
        "reject duplicate invite",
        "POST",
        f"/api/projects/{project_id}/members",
        409,
        token=owner_access,
        body={"email": member_email}
    )
    expect(
        "member cannot invite",
        "POST",
        f"/api/projects/{project_id}/members",
        403,
        token=member_access,
        body={"email": outsider_email}
    )
    members = expect(
        "list members",
        "GET",
        f"/api/projects/{project_id}/members",
        200,
        token=member_access
    )
    record("member can see project", isinstance(members, list) and len(members) == 2)

    expect(
        "reject past due date",
        "POST",
        f"/api/projects/{project_id}/tasks",
        422,
        token=owner_access,
        body={"title": "Late", "due_date": past_due()}
    )
    expect(
        "reject empty title",
        "POST",
        f"/api/projects/{project_id}/tasks",
        422,
        token=owner_access,
        body={"title": "   "}
    )
    expect(
        "reject outsider assignee",
        "POST",
        f"/api/projects/{project_id}/tasks",
        400,
        token=owner_access,
        body={"title": "Blocked", "assignee_id": outsider["user"]["id"]}
    )

    task = expect(
        "create assigned task",
        "POST",
        f"/api/projects/{project_id}/tasks",
        201,
        token=owner_access,
        body={
            "title": "Ship API",
            "description": "Cover the endpoints",
            "priority": "HIGH",
            "due_date": future_due(),
            "assignee_id": member["user"]["id"]
        }
    )
    task_id = task["id"]

    listed = expect(
        "filter search and sort tasks",
        "GET",
        f"/api/projects/{project_id}/tasks?priority=HIGH&search=Ship&sort_by=priority&sort_order=desc&limit=5&offset=0",
        200,
        token=member_access
    )
    record(
        "task list is paginated",
        listed and listed["total"] == 1 and listed["items"][0]["id"] == task_id
    )

    expect(
        "member cannot mark someone else's task done",
        "PATCH",
        f"/api/projects/{project_id}/tasks/{task_id}/status",
        403,
        token=outsider_access,
        body={"status": "DONE"}
    )
    # Outsider is not a member, so this is 403 for membership.
    # Create a second member who is not the assignee.
    extra = expect(
        "register extra member",
        "POST",
        "/api/auth/register",
        201,
        body={"name": "Extra", "email": f"extra.{STAMP}@example.com", "password": password}
    )
    expect(
        "invite extra member",
        "POST",
        f"/api/projects/{project_id}/members",
        201,
        token=owner_access,
        body={"email": extra["user"]["email"]}
    )
    expect(
        "non-assignee member cannot mark done",
        "PATCH",
        f"/api/projects/{project_id}/tasks/{task_id}/status",
        403,
        token=extra["access_token"],
        body={"status": "DONE"}
    )

    moved = expect(
        "assignee marks task done",
        "PATCH",
        f"/api/projects/{project_id}/tasks/{task_id}/status",
        200,
        token=member_access,
        body={"status": "DONE"}
    )
    record("completed date recorded", bool(moved and moved.get("completed_at")))

    reopened = expect(
        "assignee reopens task",
        "PATCH",
        f"/api/projects/{project_id}/tasks/{task_id}/status",
        200,
        token=member_access,
        body={"status": "IN_PROGRESS"}
    )
    record("completed date cleared", reopened and reopened.get("completed_at") is None)

    reassigned = expect(
        "reassign task",
        "PATCH",
        f"/api/projects/{project_id}/tasks/{task_id}/assignee",
        200,
        token=owner_access,
        body={"assignee_id": extra["user"]["id"]}
    )
    record("assignee changed", reassigned and reassigned["assignee_id"] == extra["user"]["id"])

    assigned = expect(
        "assigned to me for new assignee",
        "GET",
        "/api/tasks/assigned-to-me?status=IN_PROGRESS&priority=HIGH",
        200,
        token=extra["access_token"]
    )
    record(
        "assigned view contains task",
        any(item["id"] == task_id for item in assigned["items"])
    )
    old_assigned = expect(
        "former assignee no longer sees task",
        "GET",
        "/api/tasks/assigned-to-me",
        200,
        token=member_access
    )
    record(
        "old assignee list excludes task",
        all(item["id"] != task_id for item in old_assigned["items"])
    )

    expect(
        "empty comment rejected",
        "POST",
        f"/api/projects/{project_id}/tasks/{task_id}/comments",
        422,
        token=member_access,
        body={"content": "   "}
    )
    expect(
        "add comment",
        "POST",
        f"/api/projects/{project_id}/tasks/{task_id}/comments",
        201,
        token=member_access,
        body={"content": "Looks good"}
    )
    comments = expect(
        "list comments",
        "GET",
        f"/api/projects/{project_id}/tasks/{task_id}/comments",
        200,
        token=owner_access
    )
    record("comment visible to owner", comments and comments[0]["author_name"] == "Member")

    activities = expect(
        "activity feed",
        "GET",
        f"/api/projects/{project_id}/activities?limit=20",
        200,
        token=owner_access
    )
    types = {item["activity_type"] for item in activities}
    record(
        "activity includes key events",
        {"TASK_CREATED", "TASK_ASSIGNED", "TASK_STATUS_CHANGED", "MEMBER_INVITED", "COMMENT_ADDED"} <= types,
        str(sorted(types))
    )
    expect(
        "outsider cannot read activity",
        "GET",
        f"/api/projects/{project_id}/activities",
        403,
        token=outsider_access
    )

    expect(
        "transfer to non-member rejected",
        "PUT",
        f"/api/projects/{project_id}/transfer-ownership",
        400,
        token=owner_access,
        body={"new_owner_id": outsider["user"]["id"]}
    )
    transferred = expect(
        "transfer ownership",
        "PUT",
        f"/api/projects/{project_id}/transfer-ownership",
        200,
        token=owner_access,
        body={"new_owner_id": member["user"]["id"]}
    )
    record("new owner recorded", transferred and transferred["owner_id"] == member["user"]["id"])
    expect(
        "former owner cannot delete project",
        "DELETE",
        f"/api/projects/{project_id}",
        403,
        token=owner_access
    )

    kind, payload = await ws_once(f"/ws/projects/{project_id}", timeout=12)
    record("websocket auth timeout closes 4401", kind == "closed" and payload == 4401, str(payload))

    kind, payload = await ws_once(f"/ws/projects/{project_id}", token="not-a-jwt")
    record("malformed token closes 4401", kind == "closed" and payload == 4401, str(payload))

    kind, payload = await ws_once(f"/ws/projects/{project_id}", token=refreshed["refresh_token"])
    record("refresh token on socket closes 4401", kind == "closed" and payload == 4401, str(payload))

    kind, payload = await ws_once(f"/ws/projects/{project_id}", token=outsider_access)
    record("non-member socket closes 4403", kind == "closed" and payload == 4403, str(payload))

    kind, payload = await ws_once(f"/ws/projects/{project_id}", token=member_access)
    record("member project socket connects", kind == "message" and payload.get("type") == "CONNECTED")

    kind, payload = await ws_once("/ws/users/me", token=extra["access_token"])
    record("user socket connects", kind == "message" and payload.get("scope") == "user")

    async with websockets.connect(WS + "/ws/users/me") as personal:
        await personal.send(json.dumps({
            "type": "authenticate",
            "token": member_access
        }))
        connected = json.loads(await asyncio.wait_for(personal.recv(), timeout=3))
        record("personal socket authenticated", connected.get("type") == "CONNECTED")

        expect(
            "assign task back to original member",
            "PATCH",
            f"/api/projects/{project_id}/tasks/{task_id}/assignee",
            200,
            token=member_access,
            body={"assignee_id": member["user"]["id"]}
        )
        event = json.loads(await asyncio.wait_for(personal.recv(), timeout=3))
        record(
            "personal socket receives assignment",
            event.get("type") == "ASSIGNED_TASKS_CHANGED",
            str(event)
        )

    expect(
        "remove extra member",
        "DELETE",
        f"/api/projects/{project_id}/members/{extra['user']['id']}",
        200,
        token=member_access
    )
    kind, payload = await ws_once(f"/ws/projects/{project_id}", token=extra["access_token"])
    record("removed member cannot reconnect", kind == "closed" and payload == 4403, str(payload))

    expect(
        "delete task",
        "DELETE",
        f"/api/projects/{project_id}/tasks/{task_id}",
        204,
        token=member_access
    )
    expect(
        "deleted task is gone",
        "GET",
        f"/api/projects/{project_id}/tasks/{task_id}",
        404,
        token=member_access
    )
    expect(
        "delete project",
        "DELETE",
        f"/api/projects/{project_id}",
        200,
        token=member_access
    )

    logout_refresh = member["refresh_token"]
    expect(
        "logout",
        "POST",
        "/api/auth/logout",
        200,
        body={"refresh_token": logout_refresh}
    )
    expect(
        "logged out refresh token rejected",
        "POST",
        "/api/auth/refresh",
        401,
        body={"refresh_token": logout_refresh}
    )

    failed = [item for item in results if not item[0]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
