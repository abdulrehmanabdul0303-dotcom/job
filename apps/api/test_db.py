#!/usr/bin/env python
"""Test database connection and create database if needed."""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Read DATABASE_URL from .env
db_url = None
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                db_url = line.split('=', 1)[1].strip()
                break

if not db_url:
    print("❌ DATABASE_URL not found in .env")
    sys.exit(1)

print(f"Using: {db_url}")

# Extract database name
db_name = db_url.split('/')[-1]
print(f"Database name: {db_name}")

# Try connecting to target database
try:
    engine = create_engine(db_url, echo=False)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        sys.exit(0)
except (OperationalError, ProgrammingError) as e:
    if "does not exist" in str(e) or "3D000" in str(e):
        print(f"⚠️ Database '{db_name}' does not exist. Attempting to create...")
        
        # Connect to default postgres database to create target database
        default_url = db_url.rsplit('/', 1)[0] + '/postgres'
        try:
            engine = create_engine(default_url, echo=False)
            with engine.begin() as conn:
                # Check if database exists
                result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
                if result.fetchone():
                    print(f"✅ Database '{db_name}' already exists")
                else:
                    print(f"Creating database '{db_name}'...")
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    print(f"✅ Database '{db_name}' created successfully!")
        except Exception as e2:
            print(f"❌ Failed to create database: {e2}")
            sys.exit(1)
    else:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
