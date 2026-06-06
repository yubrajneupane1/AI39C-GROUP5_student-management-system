from app.models.database import Database
from datetime import datetime, date

class FeeModel:
    def __init__(self):
        self.db = Database()

    def add_fee_record(self, student_id, amount, description, due_date, late_fee=0):
        """Add a fee record"""
        existing = self.db.fetchone("""
            SELECT id FROM fee_records
            WHERE student_id=%s AND description=%s AND amount=%s 
            AND due_date >= DATE_SUB(%s, INTERVAL 7 DAY)
        """, (student_id, description, amount, due_date))
        
        if existing:
            return False, "Duplicate fee record detected"
        
        self.db.execute("""
            INSERT INTO fee_records (student_id, amount, description, due_date, late_fee)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, amount, description, due_date, late_fee))
        
        return True, "Fee record added successfully"

    def process_payment(self, fee_record_id, amount, payment_method, received_by, remarks=None):
        """Process a payment"""
        fee = self.db.fetchone("SELECT * FROM fee_records WHERE id=%s", (fee_record_id,))
        
        if not fee:
            return False, "Fee record not found"
        
        total_due = fee['amount'] + fee['late_fee']
        
        if amount < total_due:
            status = 'partial'
        else:
            status = 'paid'
        
        receipt_number = f"RCP-{datetime.now().strftime('%Y%m%d')}-{fee_record_id:04d}"
        
        self.db.execute("""
            INSERT INTO payments 
            (fee_record_id, amount, payment_date, payment_method, receipt_number, remarks, received_by)
            VALUES (%s, %s, CURDATE(), %s, %s, %s, %s)
        """, (fee_record_id, amount, payment_method, receipt_number, remarks, received_by))
        
        if status == 'paid':
            self.db.execute("""
                UPDATE fee_records SET status='paid', updated_at=NOW()
                WHERE id=%s
            """, (fee_record_id,))
        elif status == 'partial':
            self.db.execute("""
                UPDATE fee_records SET status='partial', updated_at=NOW()
                WHERE id=%s
            """, (fee_record_id,))
        
        self.db.execute("""
            INSERT INTO receipts (payment_id, receipt_number, receipt_date)
            VALUES (LAST_INSERT_ID(), %s, CURDATE())
        """, (receipt_number,))
        
        return True, f"Payment processed successfully. Receipt: {receipt_number}"

    def get_student_fees(self, student_id, status=None):
        """Get fee records for a student"""
        query = "SELECT * FROM fee_records WHERE student_id = %s"
        params = [student_id]
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY due_date DESC"
        
        return self.db.fetch(query, tuple(params))

    def get_due_fees(self, student_id=None):
        """Get all due fees"""
        query = """
            SELECT fr.*, u.fullname as student_name, u.id as student_id
            FROM fee_records fr
            JOIN users u ON fr.student_id = u.id
            WHERE fr.status IN ('unpaid', 'partial')
        """
        params = []
        
        if student_id:
            query += " AND fr.student_id = %s"
            params.append(student_id)
        
        query += " ORDER BY fr.due_date ASC"
        
        return self.db.fetch(query, tuple(params) if params else None)

    def check_overdue_fees(self):
        """Check and update overdue fees"""
        due_fees = self.db.fetch("""
            SELECT id, due_date FROM fee_records
            WHERE status IN ('unpaid', 'partial') AND due_date < CURDATE()
        """)
        
        for fee in due_fees:
            self.db.execute("""
                UPDATE fee_records SET status='overdue', updated_at=NOW()
                WHERE id=%s
            """, (fee['id'],))
            
            days_overdue = (date.today() - fee['due_date']).days
            
            if days_overdue >= 7:
                fee_record = self.db.fetchone(
                    "SELECT late_fee FROM fee_records WHERE id=%s",
                    (fee['id'],)
                )
                if fee_record['late_fee'] == 0:
                    late_fee_amount = 10.00
                    self.db.execute("""
                        UPDATE fee_records SET late_fee=%s, updated_at=NOW()
                        WHERE id=%s
                    """, (late_fee_amount, fee['id']))

    def get_payment_history(self, student_id):
        """Get payment history for a student"""
        return self.db.fetch("""
            SELECT p.*, fr.description, fr.amount as total_amount,
                   u.fullname as received_by_name
            FROM payments p
            JOIN fee_records fr ON p.fee_record_id = fr.id
            LEFT JOIN users u ON p.received_by = u.id
            WHERE fr.student_id = %s
            ORDER BY p.payment_date DESC
        """, (student_id,))

    def get_receipt(self, receipt_number):
        """Get receipt details"""
        return self.db.fetchone("""
            SELECT r.*, p.*, fr.*, u.fullname as student_name
            FROM receipts r
            JOIN payments p ON r.payment_id = p.id
            JOIN fee_records fr ON p.fee_record_id = fr.id
            JOIN users u ON fr.student_id = u.id
            WHERE r.receipt_number = %s
        """, (receipt_number,))

    def close(self):
        self.db.close()