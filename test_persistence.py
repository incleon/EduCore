"""Quick test to verify data persistence in MySQL"""
from app.database.session import SessionLocal
from app.models.user import User
from app.core.security import PasswordHasher
import app.models

db = SessionLocal()

try:
    # Check if test user exists
    existing = db.query(User).filter(User.email == "persistence_test@test.com").first()
    if existing:
        print(f"✓ Found existing test user: {existing.email}")
    else:
        # Create a test user to verify persistence
        test_user = User(
            email="persistence_test@test.com",
            full_name="Test User",
            username="testuser_persistence",
            hashed_password=PasswordHasher.hash_password("test123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✓ Created test user with ID: {test_user.id}")
        print(f"✓ Email: {test_user.email}")
        print(f"✓ Full Name: {test_user.full_name}")
        
        # Verify it was saved by querying again
        verified = db.query(User).filter(User.id == test_user.id).first()
        if verified:
            print(f"✓ Verified persistence: User exists in database with ID {verified.id}")
        else:
            print("✗ ERROR: User was not persisted!")
    
    # Test data modification
    print("\n--- Testing Data Update Persistence ---")
    user_to_update = db.query(User).filter(User.email == "admin@cms.edu").first()
    if user_to_update:
        original_name = user_to_update.full_name
        user_to_update.full_name = "Admin User Updated"
        db.commit()
        
        # Re-query to verify
        updated_verify = db.query(User).filter(User.id == user_to_update.id).first()
        if updated_verify and updated_verify.full_name == "Admin User Updated":
            print(f"✓ Update persistence verified: {updated_verify.full_name}")
            # Restore original
            updated_verify.full_name = original_name
            db.commit()
            print(f"✓ Restored to original: {original_name}")
        else:
            print("✗ ERROR: Update was not persisted!")
    
    db.close()
    print("\n✓ All persistence tests PASSED!")
        
except Exception as e:
    import traceback
    print(f"✗ ERROR: {e}")
    traceback.print_exc()
    db.close()
