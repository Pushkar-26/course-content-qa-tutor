from sqlalchemy import text

from app.db.database import get_db


db_generator = get_db()
db = next(db_generator)

try:
    result = db.execute(text("SELECT 1"))
    print("Database session working:", result.scalar())
finally:
    db.close()