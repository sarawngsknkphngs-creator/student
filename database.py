import sqlite3
import os
from datetime import datetime

DB_PATH = "d:/sk/admission.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs("d:/sk/static/uploads/photos", exist_ok=True)
    os.makedirs("d:/sk/static/uploads/id_cards", exist_ok=True)
    os.makedirs("d:/sk/static/uploads/transcripts", exist_ok=True)
    os.makedirs("d:/sk/static/uploads/house_regs", exist_ok=True)
    os.makedirs("d:/sk/static/uploads/other", exist_ok=True)
    os.makedirs("d:/sk/static/generated_pdfs", exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()

    # 1. Majors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS majors (
        id TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        level TEXT NOT NULL, -- ปวช. หรือ ปวส.
        quota INTEGER DEFAULT 40,
        is_active INTEGER DEFAULT 1
    )
    """)

    # 2. Applicants Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applicants (
        id TEXT PRIMARY KEY, -- APP2568-0001
        national_id TEXT UNIQUE NOT NULL, -- 13 หลัก
        title TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        birth_date TEXT NOT NULL, -- YYYY-MM-DD
        phone TEXT NOT NULL,
        email TEXT,
        gender TEXT NOT NULL,
        religion TEXT DEFAULT 'พุทธ',
        ethnicity TEXT DEFAULT 'ไทย',
        nationality TEXT DEFAULT 'ไทย',
        address_no TEXT,
        moo TEXT,
        tambon TEXT,
        amphur TEXT,
        province TEXT,
        zipcode TEXT,
        prev_school TEXT,
        prev_school_province TEXT,
        gpax REAL,
        level TEXT NOT NULL, -- ปวช. หรือ ปวส.
        major_id TEXT NOT NULL,
        parent_name TEXT,
        parent_relation TEXT,
        parent_phone TEXT,
        referral_source TEXT,
        referral_teacher TEXT,
        status TEXT DEFAULT 'PENDING_REVIEW', 
        -- PENDING_REVIEW: รอตรวจสอบเอกสาร
        -- DOCS_INCOMPLETE: เอกสารไม่ครบ/ต้องแก้ไข
        -- QUALIFIED: ผ่านการตรวจสอบ/มีสิทธิ์มอบตัว
        -- ENROLLED: มอบตัวแล้ว
        -- REJECTED: ไม่ผ่านเกณฑ์
        status_note TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (major_id) REFERENCES majors(id)
    )
    """)

    # 3. Documents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        applicant_id TEXT NOT NULL,
        doc_type TEXT NOT NULL, -- PHOTO, TRANSCRIPT, ID_CARD, HOUSE_REG
        file_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        status TEXT DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED
        note TEXT,
        uploaded_at TEXT NOT NULL,
        FOREIGN KEY (applicant_id) REFERENCES applicants(id)
    )
    """)

    # 4. Enrollments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        applicant_id TEXT UNIQUE NOT NULL,
        student_id TEXT UNIQUE, -- รหัสนักศึกษา เช่น 68201010001
        guardian_name TEXT,
        guardian_relation TEXT,
        guardian_phone TEXT,
        witness_name TEXT,
        enrollment_date TEXT,
        payment_status TEXT DEFAULT 'PAID', -- PAID, PENDING, WAIVED
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (applicant_id) REFERENCES applicants(id)
    )
    """)

    # 5. Admin Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT DEFAULT 'REGISTRAR' -- ADMIN, REGISTRAR, STAFF
    )
    """)

    # 6. Activity Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        actor TEXT NOT NULL,
        details TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()

    # Seed initial majors if empty
    cursor.execute("SELECT COUNT(*) FROM majors")
    if cursor.fetchone()[0] == 0:
        seed_majors = [
            # ปวช.
            ("VOC-AUTO", "20101", "สาขาวิชาช่างยนต์", "ปวช.", 45, 1),
            ("VOC-ELEC", "20104", "สาขาวิชาช่างไฟฟ้ากำลัง", "ปวช.", 40, 1),
            ("VOC-ELTR", "20105", "สาขาวิชาช่างอิเล็กทรอนิกส์", "ปวช.", 35, 1),
            ("VOC-ACCT", "20201", "สาขาวิชาการบัญชี", "ปวช.", 40, 1),
            ("VOC-MKT",  "20202", "สาขาวิชาการตลาด", "ปวช.", 35, 1),
            ("VOC-DBIZ", "20204", "สาขาวิชาเทคโนโลยีธุรกิจดิจิทัล", "ปวช.", 40, 1),
            ("VOC-HOTL", "20701", "สาขาวิชาการโรงแรม", "ปวช.", 35, 1),
            # ปวส.
            ("DIP-AUTO", "30101", "สาขาวิชาเทคนิคเครื่องกล", "ปวส.", 35, 1),
            ("DIP-ELEC", "30104", "สาขาวิชาไฟฟ้า", "ปวส.", 35, 1),
            ("DIP-IT",   "30901", "สาขาวิชาเทคโนโลยีสารสนเทศ", "ปวส.", 40, 1),
            ("DIP-ACCT", "30201", "สาขาวิชาการบัญชี", "ปวส.", 35, 1),
            ("DIP-DBIZ", "30204", "สาขาวิชาการจัดการธุรกิจดิจิทัล", "ปวส.", 35, 1),
            ("DIP-TOUR", "30701", "สาขาวิชาการท่องเที่ยวและการโรงแรม", "ปวส.", 30, 1)
        ]
        cursor.executemany("""
        INSERT INTO majors (id, code, name, level, quota, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """, seed_majors)
        conn.commit()

    # Seed default admin user (admin / admin123)
    cursor.execute("SELECT COUNT(*) FROM admin_users")
    if cursor.fetchone()[0] == 0:
        # For simplicity in prototype, using basic hash / demo credential
        import hashlib
        pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("""
        INSERT INTO admin_users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
        """, ("admin", pwd_hash, "เจ้าหน้าที่งานรับสมัครและทะเบียน", "ADMIN"))
        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
