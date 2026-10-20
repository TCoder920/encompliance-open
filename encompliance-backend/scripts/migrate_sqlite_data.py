import sys
import os
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set target DB to the Docker Postgres instance
POSTGRES_URL = "postgresql://postgres:postgres@localhost:5432/encompliance"

def migrate_sqlite_to_postgres():
    sqlite_path = "app.db"
    if not os.path.exists(sqlite_path):
        print(f"Error: {sqlite_path} not found.")
        return

    print("Starting migration from SQLite to Postgres...")
    
    # SQLite Connection (Source)
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    
    # Postgres Connection (Target)
    pg_engine = create_engine(POSTGRES_URL)
    
    try:
        with sqlite_engine.connect() as sqlite_conn, pg_engine.connect() as pg_conn:
            # 1. Clear existing data in Postgres (optional, but good for clean slate)
            print("Clearing existing Regulations and FacilityTypes in Postgres...")
            pg_conn.execute(text("TRUNCATE TABLE regulation_facility_types CASCADE"))
            pg_conn.execute(text("TRUNCATE TABLE regulations CASCADE"))
            pg_conn.execute(text("TRUNCATE TABLE facility_types CASCADE"))
            pg_conn.commit()
            
            # 2. Migrate Facility Types
            print("Migrating Facility Types...")
            ft_results = sqlite_conn.execute(text("SELECT * FROM facility_types")).fetchall()
            
            # We need to map old IDs to new IDs to preserve relationships, or just insert with ID if possible.
            # Postgres sequences need to be updated if we insert explicit IDs.
            # Let's try inserting with explicit IDs first.
            
            for row in ft_results:
                # row is a tuple-like result. Access by index or name.
                # Assuming schema: id, name
                ft_id = row.id
                ft_name = row.name
                
                # Check if exists (unlikely after truncate)
                pg_conn.execute(
                    text("INSERT INTO facility_types (id, name) VALUES (:id, :name) ON CONFLICT (name) DO NOTHING"),
                    {"id": ft_id, "name": ft_name}
                )
            print(f"Migrated {len(ft_results)} Facility Types.")

            # 3. Migrate Regulations
            print("Migrating Regulations...")
            # Select columns explicitly to match schema
            reg_query = text("""
                SELECT id, state_territory, document_title, document_type, file_name, last_updated, created_at, updated_at 
                FROM regulations
            """)
            reg_results = sqlite_conn.execute(reg_query).fetchall()
            
            for row in reg_results:
                pg_conn.execute(
                    text("""
                        INSERT INTO regulations (id, state_territory, document_title, document_type, file_name, last_updated, created_at, updated_at) 
                        VALUES (:id, :state, :title, :dtype, :fname, :last_up, :created, :updated)
                    """),
                    {
                        "id": row.id,
                        "state": row.state_territory,
                        "title": row.document_title,
                        "dtype": row.document_type,
                        "fname": row.file_name,
                        "last_up": row.last_updated,
                        "created": row.created_at,
                        "updated": row.updated_at
                    }
                )
            print(f"Migrated {len(reg_results)} Regulations.")

            # 4. Migrate Association Table (regulation_facility_types)
            print("Migrating Association Table...")
            assoc_results = sqlite_conn.execute(text("SELECT * FROM regulation_facility_types")).fetchall()
            
            for row in assoc_results:
                pg_conn.execute(
                    text("INSERT INTO regulation_facility_types (regulation_id, facility_type_id) VALUES (:reg_id, :ft_id)"),
                    {"reg_id": row.regulation_id, "ft_id": row.facility_type_id}
                )
            print(f"Migrated {len(assoc_results)} Associations.")
            
            # 5. Fix Sequences
            print("Updating sequences...")
            pg_conn.execute(text("SELECT setval('facility_types_id_seq', (SELECT MAX(id) FROM facility_types))"))
            pg_conn.execute(text("SELECT setval('regulations_id_seq', (SELECT MAX(id) FROM regulations))"))
            
            pg_conn.commit()
            print("Migration complete successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate_sqlite_to_postgres()
