import sys
from sqlalchemy import text
from app.database.session import engine

def cleanup():
    with engine.begin() as conn:
        conn.execute(text('SET FOREIGN_KEY_CHECKS=0;'))
        conn.execute(text('DROP TABLE IF EXISTS expense_categories, expenses, fee_structures, staff_salaries, student_fees, payments;'))
        conn.execute(text('CREATE TABLE IF NOT EXISTS fees (id INT PRIMARY KEY);'))
        conn.execute(text('SET FOREIGN_KEY_CHECKS=1;'))

if __name__ == '__main__':
    cleanup()
