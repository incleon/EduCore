# Data Persistence Guide

This document ensures that all data entered into the EduCore CMS is safely stored in MySQL and not lost.

## ✅ How Data is Protected

### 1. **Database Transactions**
- Every data change (CREATE, UPDATE, DELETE) is wrapped in a transaction
- Transactions are **explicitly committed** to ensure durability
- If an error occurs during processing, the entire transaction is rolled back (atomic operations)

```python
# Example from repositories/base.py
def create(self, obj_data: Dict[str, Any]) -> T:
    db_obj = self._model(**obj_data)
    self._db.add(db_obj)
    self._db.commit()           # ← DATA IS PERSISTED HERE
    self._db.refresh(db_obj)    # ← DATA IS VERIFIED
    return db_obj
```

### 2. **Session Management**
- Every HTTP request gets its own database session
- Sessions are automatically closed after the request completes (even if errors occur)
- Uses Python's `finally` block to guarantee cleanup

```python
# Example from core/dependencies.py
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # ← ALWAYS EXECUTED
```

### 3. **Connection Pooling**
- Maintains a pool of reusable connections (10 active + 20 overflow)
- Automatically validates connections before use (`pool_pre_ping=True`)
- Recycles connections every 1 hour to prevent stale connections
- Timeout of 30 seconds prevents hanging requests

### 4. **Foreign Key Constraints**
- MySQL enforces referential integrity at the database level
- A parent record cannot be deleted if child records reference it
- Prevents orphaned data and maintains data consistency

### 5. **Soft Delete Protection**
- Records are marked as "deleted" instead of physically removed
- Archived data remains in database indefinitely
- Can be restored at any time using the `.restore()` method

```python
# Soft delete example
def soft_delete(self, id: int) -> bool:
    db_obj = self.get_by_id(id)
    if db_obj:
        db_obj.is_deleted = True
        db_obj.deleted_at = datetime.now(timezone.utc)
        self._db.commit()  # ← PERSISTED
    return db_obj is not None
```

---

## 📋 Data Safety Checklist

- ✅ **SQLAlchemy ORM** handles all database operations
- ✅ **Explicit commits** in every CRUD operation
- ✅ **Transaction management** (autocommit=False)
- ✅ **Connection pooling** with health checks
- ✅ **Session lifecycle** properly managed
- ✅ **Error handling** prevents partial writes
- ✅ **MySQL database** with persistent storage
- ✅ **Soft deletes** protect data from accidental loss
- ✅ **Timestamps** track creation and modification
- ✅ **Foreign key constraints** maintain data integrity

---

## 🧪 Testing Data Persistence

To verify that data is being saved correctly, run:

```bash
python test_persistence.py
```

This will:
1. Create a test user
2. Verify it's saved in MySQL
3. Update the user
4. Verify the update is persisted
5. Restore original data

Output should show: `✓ All persistence tests PASSED!`

---

## 🔍 Monitoring Persistence

### Log Files
All database operations are logged to `logs/cms.log`:
- `INSERT` statements show new data being added
- `UPDATE` statements show data being modified
- `COMMIT` statements confirm persistence

### Checking MySQL Directly
```bash
mysql -u cms_user -p cms_db
SELECT COUNT(*) FROM users;  -- See total users
SELECT * FROM users WHERE email = 'test@example.com';  -- Find specific user
```

---

## ⚠️ What to Watch Out For

### **DO NOT:**
1. Close the database session without committing
2. Use `autocommit=True` (can lose data)
3. Ignore exceptions from database operations
4. Assume data is saved without explicit commit
5. Modify the connection pool settings without testing

### **DO:**
1. Always call `.commit()` after modifications
2. Use the repository pattern for all data access
3. Let FastAPI manage session lifecycle via `Depends(get_db)`
4. Test changes in a non-production environment first
5. Monitor logs for `COMMIT` statements

---

## 🔄 Data Flow Diagram

```
User Input
   ↓
FastAPI Route Handler
   ↓
Service Layer (business logic)
   ↓
Repository (ORM operations)
   ↓
db.add() / db.query() / etc.
   ↓
db.commit() ← ⭐ DATA PERSISTED HERE
   ↓
db.refresh() ← VERIFY DATA IN DATABASE
   ↓
Return to User
```

---

## 📞 Troubleshooting

### **"Data not showing up after saving"**
- Check logs for `COMMIT` statement
- Verify no exceptions occurred
- Ensure you're querying the same `cms_db` database
- Check that session was not rolled back

### **"Connection timeout"**
- Verify MySQL service is running
- Check `DATABASE_URL` in `.env`
- Monitor connection pool usage in logs
- Increase `pool_size` if many concurrent requests

### **"Lost data after restart"**
- MySQL stores data persistently on disk
- Verify data directory is writable
- Check MySQL error logs
- Ensure proper MySQL backup configuration

---

**Last Updated:** 2026-06-22  
**Database:** MySQL  
**ORM:** SQLAlchemy 2.0.36  
**Status:** ✅ All data is safely persisted
