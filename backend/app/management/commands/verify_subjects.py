from app.database.session import SessionLocal
from app.models.department import Department
from app.models.subject import Subject

db = SessionLocal()
depts = db.query(Department).filter_by(is_deleted=False).all()
all_good = True
for d in depts:
    subs = db.query(Subject).filter_by(department_id=d.id, is_deleted=False).all()
    expected_years = d.course.duration_years.split()[0] if d.course and d.course.duration_years else '3'
    expected_semesters = int(expected_years) * 2 if d.code != 'BT-AS' else 2
    if len(subs) != expected_semesters * 5:
        print(f'{d.code}: expected {expected_semesters*5}, got {len(subs)}')
        all_good = False

if all_good:
    print('SUCCESS: All departments have exactly the correct number of subjects!')

db.close()
