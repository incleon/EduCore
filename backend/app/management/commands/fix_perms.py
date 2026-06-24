from app.database.session import SessionLocal
from app.models.user import Permission, Role, RolePermission

def fix_permissions():
    db = SessionLocal()
    try:
        # Check if manage_timetable exists
        perm = db.query(Permission).filter(Permission.name == "manage_timetable").first()
        if not perm:
            perm = Permission(
                name="manage_timetable",
                resource="timetable",
                action="manage",
                description="Manage all timetables"
            )
            db.add(perm)
            db.flush()
            print("Created manage_timetable permission.")

        # Get Admin role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role:
            # Check if admin has this permission
            rp = db.query(RolePermission).filter(
                RolePermission.role_id == admin_role.id,
                RolePermission.permission_id == perm.id
            ).first()
            if not rp:
                rp = RolePermission(role_id=admin_role.id, permission_id=perm.id)
                db.add(rp)
                print("Granted manage_timetable to Admin.")
        
        db.commit()
        print("Permissions fixed.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_permissions()
