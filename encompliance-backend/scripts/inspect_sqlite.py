import sys
import os
from sqlalchemy import create_engine, text

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def inspect_sqlite():
    # Path to the sqlite database
    db_path = "app.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    # Connect to SQLite
    sqlite_url = f"sqlite:///{db_path}"
    engine = create_engine(sqlite_url)
    
    print(f"Inspecting {db_path}...")
    
    try:
        with engine.connect() as conn:
            # Check for facility types count
            result = conn.execute(text("SELECT count(*) FROM facility_types"))
            count = result.scalar()
            print(f"Total Facility Types: {count}")

            # Check for regulations count
            result = conn.execute(text("SELECT count(*) FROM regulations"))
            reg_count = result.scalar()
            print(f"Total Regulations: {reg_count}")
            
            # Sample a few states and their facility types
            query = text("""
                SELECT r.state_territory, ft.name 
                FROM regulations r
                JOIN regulation_facility_types rft ON r.id = rft.regulation_id
                JOIN facility_types ft ON ft.id = rft.facility_type_id
                WHERE r.state_territory IN ('Colorado', 'Maryland', 'Texas', 'California')
                ORDER BY r.state_territory, ft.name
            """)
            
            rows = conn.execute(query).fetchall()
            print("\nSample Data (State -> Facility Type):")
            current_state = ""
            for row in rows:
                state, ft_name = row
                if state != current_state:
                    print(f"\n[{state}]")
                    current_state = state
                print(f" - {ft_name}")

    except Exception as e:
        print(f"Error inspecting database: {e}")

if __name__ == "__main__":
    inspect_sqlite()
