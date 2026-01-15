#!/usr/bin/env python
"""Create database using asyncpg (matches our async driver)."""
import asyncio
import os
import sys

async def main():
    try:
        import asyncpg
    except ImportError:
        print("Installing asyncpg...")
        os.system("pip install asyncpg --quiet")
        import asyncpg
    
    # Read config
    db_url = None
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                if line.startswith('DATABASE_URL='):
                    db_url = line.split('=', 1)[1].strip()
                    break
    
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return False
    
    # Parse connection details
    # postgresql+asyncpg://user:password@host:port/dbname
    parts = db_url.replace('postgresql+asyncpg://', '').split('@')
    if len(parts) != 2:
        print(f"❌ Invalid DATABASE_URL format")
        return False
    
    creds = parts[0].split(':')
    host_port_db = parts[1].split('/')
    
    user, password = creds[0], creds[1] if len(creds) > 1 else None
    host, port = host_port_db[0].split(':')[0], int(host_port_db[0].split(':')[1])
    db_name = host_port_db[1]
    
    print(f"Connecting to PostgreSQL: {user}@{host}:{port}")
    print(f"Target database: {db_name}")
    
    try:
        # Connect to postgres (system DB)
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database='postgres'
        )
        
        # Check if database exists
        exists = await conn.fetchval(f"SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = '{db_name}')")
        
        if exists:
            print(f"✅ Database '{db_name}' already exists")
        else:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Database '{db_name}' created successfully!")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
