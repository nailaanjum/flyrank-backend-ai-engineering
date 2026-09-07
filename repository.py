import os

import psycopg
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    return psycopg.connect(DATABASE_URL)


def initialize_database():
    with get_connection() as conn:
        with conn.cursor() as cur:

            # Create the tasks table if it doesn't already exist
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                );
                """
            )

            # Check whether the table already contains data
            cur.execute("SELECT COUNT(*) FROM tasks;")
            count = cur.fetchone()[0]

            # Seed three example tasks only if the table is empty
            if count == 0:
                cur.execute(
                    """
                    INSERT INTO tasks (title, done)
                    VALUES
                        ('Learn FastAPI', FALSE),
                        ('Learn PostgreSQL', FALSE),
                        ('Build CRUD API', FALSE);
                    """
                )

        conn.commit()