from app.db.database import engine


with engine.connect() as connection:
    result = connection.exec_driver_sql("SELECT 1")
    print("Database connection successful:", result.scalar())