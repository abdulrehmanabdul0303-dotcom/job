"""
Initialize database tables for SQLite development.
Run this script once to create all tables.
"""
import asyncio
from app.core.database import init_db
# Import all models to register them with Base.metadata
import app.models  # This imports all models

async def main():
    print("Initializing database tables...")
    try:
        await init_db()
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
