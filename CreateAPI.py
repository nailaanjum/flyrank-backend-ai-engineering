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

    return {
    "id": row[0],
    "title": row[1],
    "done": bool(row[2])
}


# Stage 3: Create a new task
# Assignment 2 - Stage 2: Create new task in database

@app.put(
    "/tasks/{task_id}",
    description="Updates the title or completion status of a task"
)
async def update_task(task_id: int, task_data: TaskUpdate):

    # Business rule: update body cannot be empty
    if task_data.title is None and task_data.done is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Update body cannot be empty"}
        )

    # If title is provided, it cannot be empty
    if task_data.title is not None:
        title = task_data.title.strip()

        if not title:
            return JSONResponse(
                status_code=400,
                content={"error": "Title cannot be empty"}
            )
    else:
        title = None

    # Get the current task from the database
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    row = cursor.fetchone()

    # Task does not exist
    if row is None:
        conn.close()

        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )

    # Keep existing values if they weren't provided
    current_title = row[1]
    current_done = bool(row[2])

    new_title = title if title is not None else current_title
    new_done = task_data.done if task_data.done is not None else current_done

    # Update the database
    cursor.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, int(new_done), task_id)
    )

    conn.commit()

    conn.close()

    # Return the updated task
    return {
        "id": task_id,
        "title": new_title,
        "done": new_done
    }

# Stage 4: Delete a task
# Stage 3: Delete a task
@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    description="Deletes a task by its ID"
)
async def delete_task(task_id: int):

    conn = get_db()
    cursor = conn.cursor()

    # Check if the task exists
    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    row = cursor.fetchone()

    if row is None:
        conn.close()

        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )

    # Delete the task from the database
    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()

    # Successful DELETE → 204 with empty body
    return Response(status_code=204)