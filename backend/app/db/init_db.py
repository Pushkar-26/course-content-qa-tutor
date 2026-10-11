from sqlalchemy import text
from app.db.database import Base, engine
from app.db.models import (
    Chunk,
    Conversation,
    Document,
    Message,
    User,
)

Base.metadata.create_all(bind=engine)
with engine.begin() as connection:
    connection.execute(text("""
        ALTER TABLE documents
        ADD COLUMN IF NOT EXISTS owner_id VARCHAR(36)
        REFERENCES users(id) ON DELETE CASCADE
    """))

    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_documents_owner_id
        ON documents(owner_id)
    """))
print("Database tables created successfully")
with engine.begin() as connection:
    user_count = connection.execute(
        text("SELECT COUNT(*) FROM users")
    ).scalar_one()

    if user_count == 1:
        user_id = connection.execute(
            text("SELECT id FROM users LIMIT 1")
        ).scalar_one()

        result = connection.execute(
            text("""
                UPDATE documents
                SET owner_id = :user_id
                WHERE owner_id IS NULL
            """),
            {"user_id": user_id},
        )

        print(f"Assigned {result.rowcount} existing documents.")

    elif user_count > 1:
        print("Multiple users found. Existing ownership unchanged.")

    else:
        print("No users found. No documents reassigned.")
