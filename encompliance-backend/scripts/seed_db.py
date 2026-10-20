import sys
import os
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set DATABASE_URL to connect to the docker database exposed on localhost
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/encompliance"

from app.database import SessionLocal
from app.models.facility_type import FacilityType
from app.models.regulation import Regulation

def seed_db():
    db = SessionLocal()
    try:
        print("Seeding database...")
        
        # Define common facility types
        common_types = [
            "Child Care Center",
            "Family Child Care Home",
            "Group Child Care Home",
            "School Age Program"
        ]
        
        ft_objects = {}
        for name in common_types:
            ft = db.query(FacilityType).filter_by(name=name).first()
            if not ft:
                ft = FacilityType(name=name)
                db.add(ft)
                print(f"Created FacilityType: {name}")
            else:
                print(f"FacilityType exists: {name}")
            ft_objects[name] = ft
        
        db.flush()

        # Define data for all states
        all_states = [
            "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", 
            "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", 
            "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", 
            "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", 
            "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", 
            "New Hampshire", "New Jersey", "New Mexico", "New York", 
            "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", 
            "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", 
            "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", 
            "West Virginia", "Wisconsin", "Wyoming", "District of Columbia"
        ]

        # Common types for every state (can be customized per state later if needed)
        default_types = ["Child Care Center", "Family Child Care Home"]
        
        # Specific overrides if any (keeping previous specific ones)
        state_specific_types = {
            "New York": ["Child Care Center", "School Age Program"],
            "Maryland": ["Child Care Center", "Family Child Care Home", "Large Family Child Care Home", "Letter of Compliance"],
        }

        for state in all_states:
            # Determine types for this state
            types_to_use = state_specific_types.get(state, default_types)

            # Check if regulation exists for this state
            reg = db.query(Regulation).filter_by(state_territory=state).first()
            if not reg:
                reg = Regulation(
                    state_territory=state,
                    document_title=f"{state} Child Care Regulations",
                    document_type="Regulation",
                    file_name=f"{state}_Regulations_Dummy.pdf",
                    last_updated=datetime.now().date()
                )
                db.add(reg)
                print(f"Created Regulation for {state}")
                
                # Link facility types
                for ft_name in types_to_use:
                    if ft_name in ft_objects:
                        reg.facility_types.append(ft_objects[ft_name])
                    elif ft_name not in ft_objects:
                        # Create new type if it appeared in specific overrides and wasn't in common_types
                        new_ft = FacilityType(name=ft_name)
                        db.add(new_ft)
                        db.flush() # get id
                        ft_objects[ft_name] = new_ft
                        reg.facility_types.append(new_ft)
                        print(f"Created and linked specific FacilityType: {ft_name}")

            else:
                print(f"Regulation exists for {state}, checking linkages...")
                # Ensure linkages exist even if reg exists (idempotency)
                current_linked_names = [ft.name for ft in reg.facility_types]
                for ft_name in types_to_use:
                     if ft_name not in current_linked_names:
                        if ft_name in ft_objects:
                            reg.facility_types.append(ft_objects[ft_name])
                            print(f"  -> Linked missing type {ft_name} to {state}")
                        elif ft_name not in ft_objects:
                             # Create new type if needed
                            new_ft = FacilityType(name=ft_name)
                            db.add(new_ft)
                            db.flush()
                            ft_objects[ft_name] = new_ft
                            reg.facility_types.append(new_ft)
                            print(f"  -> Created and linked specific FacilityType: {ft_name} to {state}")

        db.commit()
        print("Seeding complete.")

    except Exception as e:
        print(f"Error seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
