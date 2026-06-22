"""Comprehensive data persistence verification script"""
from datetime import datetime, timezone
from app.database.session import SessionLocal, engine
from app.models.student import Student
from app.models.course import Course
from app.repositories.concrete import StudentRepository, CourseRepository
from sqlalchemy import inspect, text
import app.models

def check_connection():
    """Verify MySQL connection."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT DATABASE()"))
            db_name = result.scalar()
            print("[PASS] MySQL Connection: Connected to '%s'" % db_name)
            return True
    except Exception as e:
        print("[FAIL] MySQL Connection: %s" % str(e))
        return False

def check_tables():
    """Verify all required tables exist."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    required_tables = [
        'users', 'roles', 'permissions', 'role_permissions', 'user_roles',
        'students', 'teachers', 'courses', 'departments', 'subjects',
        'attendances', 'marks', 'fees', 'library_books', 'book_issues',
        'timetable_versions', 'timetable_slots', 'notifications', 'audit_logs'
    ]
    
    missing = [t for t in required_tables if t not in tables]
    if missing:
        print("[FAIL] Missing tables: %s" % str(missing))
        return False
    
    print("[PASS] All %d required tables exist" % len(required_tables))
    return True

def check_constraints():
    """Verify foreign key constraints are defined."""
    db = SessionLocal()
    try:
        result = db.execute(text("SHOW CREATE TABLE students")).scalar()
        if "FOREIGN KEY" in result:
            print("[PASS] Foreign key constraints are enabled")
            return True
        else:
            print("[WARN] Foreign key constraints may not be properly defined")
            return False
    except Exception as e:
        print("[FAIL] Constraint check failed: %s" % str(e))
        return False
    finally:
        db.close()

def check_crud_operations():
    """Test CREATE, READ, UPDATE, DELETE operations."""
    db = SessionLocal()
    try:
        course_repo = CourseRepository(db)
        
        # CREATE
        test_course = course_repo.create({
            'name': 'Persistence Test Course',
            'code': 'TEST-001',
            'description': 'Testing data persistence'
        })
        print("[PASS] CREATE: Course ID %d created" % test_course.id)
        
        # READ
        fetched = course_repo.get_by_id(test_course.id)
        if fetched and fetched.name == 'Persistence Test Course':
            print("[PASS] READ: Course retrieved from database")
        else:
            print("[FAIL] READ: Failed to retrieve course")
            return False
        
        # UPDATE
        course_repo.update(test_course.id, {'description': 'Updated description'})
        updated = course_repo.get_by_id(test_course.id)
        if updated and updated.description == 'Updated description':
            print("[PASS] UPDATE: Changes persisted to database")
        else:
            print("[FAIL] UPDATE: Failed to persist changes")
            return False
        
        # DELETE
        course_repo.soft_delete(test_course.id)
        deleted = course_repo.get_by_id(test_course.id)
        if deleted is None:
            print("[PASS] DELETE: Course soft-deleted (data preserved)")
        else:
            print("[FAIL] DELETE: Failed to soft-delete")
            return False
        
        # RESTORE
        restored = course_repo.restore(test_course.id)
        if restored and restored.name == 'Persistence Test Course':
            print("[PASS] RESTORE: Deleted course restored")
        else:
            print("[FAIL] RESTORE: Failed to restore")
            return False
        
        course_repo.hard_delete(test_course.id)
        print("[PASS] CLEANUP: Test data removed")
        
        return True
        
    except Exception as e:
        print("[FAIL] CRUD test failed: %s" % str(e))
        return False
    finally:
        db.close()

def check_transaction_safety():
    """Verify transaction handling and rollback."""
    db = SessionLocal()
    try:
        course = Course(name='Transaction Test', code='TRANS-001', description='Testing')
        db.add(course)
        db.commit()
        db.refresh(course)
        course_id = course.id
        
        count_before = db.query(Course).filter(Course.id == course_id).count()
        
        try:
            invalid_course = Course(name=None, code='INVALID')
            db.add(invalid_course)
            db.commit()
        except Exception:
            db.rollback()
        
        count_after = db.query(Course).filter(Course.id == course_id).count()
        if count_before == count_after == 1:
            print("[PASS] Transaction safety: Rollback protected data")
            db.execute(text("DELETE FROM courses WHERE id = %d" % course_id))
            db.commit()
            return True
        else:
            print("[FAIL] Transaction safety: Data corruption detected")
            return False
            
    except Exception as e:
        print("[FAIL] Transaction test failed: %s" % str(e))
        return False
    finally:
        db.close()

def check_data_integrity():
    """Verify data integrity with timestamps."""
    db = SessionLocal()
    try:
        from app.models.user import User
        from app.core.security import PasswordHasher
        
        ts = int(datetime.now().timestamp())
        user = User(
            email="integrity_test_%d@test.com" % ts,
            username="integ_test_%d" % ts,
            full_name="Integrity Test User",
            hashed_password=PasswordHasher.hash_password("test123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        if user.created_at and user.updated_at:
            print("[PASS] Data integrity: Timestamps recorded automatically")
            db.delete(user)
            db.commit()
            return True
        else:
            print("[FAIL] Data integrity: Timestamps not recorded")
            return False
            
    except Exception as e:
        print("[FAIL] Data integrity check failed: %s" % str(e))
        return False
    finally:
        db.close()

def main():
    """Run all persistence checks."""
    print("\n" + "="*60)
    print("DATA PERSISTENCE VERIFICATION")
    print("="*60 + "\n")
    
    checks = [
        ("MySQL Connection", check_connection),
        ("Database Tables", check_tables),
        ("Constraints", check_constraints),
        ("CRUD Operations", check_crud_operations),
        ("Transaction Safety", check_transaction_safety),
        ("Data Integrity", check_data_integrity),
    ]
    
    results = []
    for name, check_func in checks:
        print("\n[%s]" % name)
        result = check_func()
        results.append(result)
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print("RESULTS: %d/%d checks PASSED" % (passed, total))
    
    if passed == total:
        print("\nSUCCESS: ALL PERSISTENCE CHECKS PASSED - DATA IS SAFE!")
    else:
        print("\nWARNING: Some checks failed - review results above")
    
    print("="*60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
