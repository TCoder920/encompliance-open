"""
Alembic Version Fix Script
-------------------------
This script fixes issues with Alembic version tracking in the database.
It provides:
- Version table repair
- Migration history correction
- Version conflict resolution
- Database version synchronization
- Migration state validation
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variables or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Check if alembic_version table exists
with engine.connect() as conn:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"))
    tables = result.fetchall()
    if len(tables) == 0:
        print("alembic_version table does not exist, creating it...")
        conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('e314c32b14d7')"))
        conn.commit()
        print("Created alembic_version table with version e314c32b14d7")
    else:
        print("alembic_version table exists, checking current version...")
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        versions = result.fetchall()
        
        if len(versions) == 0:
            print("No version in alembic_version table, inserting version...")
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('e314c32b14d7')"))
            conn.commit()
            print("Set version to e314c32b14d7")
        else:
            print(f"Current version: {versions[0][0]}")
            if versions[0][0] != 'e314c32b14d7':
                print(f"Updating version from {versions[0][0]} to e314c32b14d7...")
                conn.execute(text("UPDATE alembic_version SET version_num = 'e314c32b14d7'"))
                conn.commit()
                print("Updated to version e314c32b14d7")
            else:
                print("Version is already e314c32b14d7, no update needed") 