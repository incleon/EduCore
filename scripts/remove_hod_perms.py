import os
import sys

# Ensure the app module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.database.session import SessionLocal
from app.models.user import Role, Permission, RolePermission

def remove_hod_permissions():
    db = SessionLocal()
    try:
        hod_role = db.query(Role).filter(Role.name == "hod").first()
        if not hod_role:
            print("HOD role not found.")
            return

        perms_to_remove = ["view_departments", "manage_departments"]
        permissions = db.query(Permission).filter(Permission.name.in_(perms_to_remove)).all()
        
        if not permissions:
            print("Permissions not found.")
            return
            
        perm_ids = [p.id for p in permissions]
        
        # Delete RolePermission entries for the hod role and these permissions
        deleted = db.query(RolePermission).filter(
            RolePermission.role_id == hod_role.id,
            RolePermission.permission_id.in_(perm_ids)
        ).delete(synchronize_session=False)
        
        db.commit()
        print(f"Successfully removed {deleted} permissions from the HOD role.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    remove_hod_permissions()
