from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()
DB_NAME = "tasks.db"


def get_db():
    return sqlite3.connect(DB_NAME)


def create_database():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM tasks")
        count = cursor.fetchone()[0]

        if count == 0:
            cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Learn FastAPI", 0))
            cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Build CRUD API", 0))
            cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Learn Git", 1))

        conn.commit()
        conn.close()
        print("Database created/updated successfully.")

    except Exception as e:
        print("ERROR creating database:", e)


create_database()

# In-memory database
tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Build CRUD API", "done": False},
    {"id": 3, "title": "Learn Git", "done": True}
]


# Data model for creating a task
class TaskCreate(BaseModel):
    title: str


# Data model for updating a task
class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


# Stage 1: Root endpoint
@app.get(
    "/",
    description="Returns information about the Task API"
)
async def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


# Stage 1: Health endpoint
@app.get(
    "/health",
    description="Checks whether the API is running"
)
async def health():
    return {"status": "ok"}


# Stage 2: Get all tasks
@app.get(
    "/tasks",
    description="Returns all tasks"
)
async def get_tasks():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")

    rows = cursor.fetchall()

    conn.close()

    return rows


# Stage 2: Get one task
@app.get(
    "/tasks/{task_id}",
    description="Returns one task by its ID"
)
async def get_task(task_id: int):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )

    return row


# Stage 3: Create a new task
@app.post(
    "/tasks",
    status_code=201,
    description="Creates a new task"
)
async def create_task(task_data: TaskCreate):

    title = task_data.title.strip()

    if not title:
        return JSONResponse(
            status_code=400,
            content={"error": "Title cannot be empty"}
        )

    new_id = max(task["id"] for task in tasks) + 1

    new_task = {
        "id": new_id,
        "title": title,
        "done": False
    }

    tasks.append(new_task)

    return new_task


# Stage 4: Update a task
@app.put(
    "/tasks/{task_id}",
    description="Updates the title or completion status of a task"
)
async def update_task(task_id: int, task_data: TaskUpdate):

    for task in tasks:

        if task["id"] == task_id:

            # Empty update body
            if task_data.title is None and task_data.done is None:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Update body cannot be empty"}
                )

            # Update title if provided
            if task_data.title is not None:

                if not task_data.title.strip():
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Title cannot be empty"}
                    )

                task["title"] = task_data.title.strip()

            # Update done if provided
            if task_data.done is not None:
                task["done"] = task_data.done

            return task

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )


# Stage 4: Delete a task
@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    description="Deletes a task by its ID"
)
async def delete_task(task_id: int):

    for task in tasks:

        if task["id"] == task_id:

            tasks.remove(task)

            return Response(status_code=204)

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )