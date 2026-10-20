"""
Script to fix existing team members by inheriting facility admin profile settings
"""
import asyncio
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.api.routes.auth import associate_user_documents

async def fix_team_members():
    db = SessionLocal()
    try:
        # Get facility admin
        admin = db.query(User).filter(User.email == 'tritruradoimmu-8527@yopmail.com').first()
        if not admin:
            print('Admin not found')
            return
            
        print(f'Admin profile: state={admin.state}, facility_type={admin.facility_type}')
        
        # Get team members that need fixing
        team_members = db.query(User).filter(
            User.facility_id == admin.facility_id,
            User.user_role == UserRole.TEAM_MEMBER,
            User.state.is_(None)
        ).all()
        
        print(f'Found {len(team_members)} team members to fix')
        
        for member in team_members:
            print(f'Fixing {member.email}...')
            member.state = admin.state
            member.facility_type = admin.facility_type
            
            # Associate documents
            if member.state and member.facility_type:
                facility_types = [ft.strip() for ft in member.facility_type.split(',') if ft.strip()]
                await associate_user_documents(db, member.id, member.state, facility_types)
            
            print(f'  Updated state: {member.state}')
            print(f'  Updated facility_type: {member.facility_type}')
        
        db.commit()
        print('All team members updated successfully!')
        
    except Exception as e:
        print(f'Error: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(fix_team_members()) 