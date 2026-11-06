import os
import sqlite3
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

def make_valid_thai_id(prefix12: str) -> str:
    total = sum(int(prefix12[i]) * (13 - i) for i in range(12))
    check = (11 - (total % 11)) % 10
    return prefix12 + str(check)

def create_sample_placeholder_image(path: str, text: str, width=400, height=500, bg=(230, 240, 255)):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, width-10, height-10], outline=(100, 140, 200), width=3)
    draw.text((width//4, height//2), text, fill=(30, 60, 120))
    img.save(path)

def seed():
    conn = sqlite3.connect("d:/sk/admission.db")
    cursor = conn.cursor()

    # Create dummy images
    img_photo1 = "static/uploads/photos/sample_photo1.jpg"
    img_photo2 = "static/uploads/photos/sample_photo2.jpg"
    img_trans1 = "static/uploads/transcripts/sample_trans1.jpg"
    img_id1 = "static/uploads/id_cards/sample_id1.jpg"
    img_house1 = "static/uploads/house_regs/sample_house1.jpg"

    create_sample_placeholder_image(f"d:/sk/{img_photo1}", "Student Photo 1", 300, 400, (220, 235, 252))
    create_sample_placeholder_image(f"d:/sk/{img_photo2}", "Student Photo 2", 300, 400, (252, 235, 220))
    create_sample_placeholder_image(f"d:/sk/{img_trans1}", "Transcript (Por Por 1)", 600, 800, (245, 245, 245))
    create_sample_placeholder_image(f"d:/sk/{img_id1}", "Thai ID Card Copy", 600, 400, (240, 248, 255))
    create_sample_placeholder_image(f"d:/sk/{img_house1}", "House Registration Copy", 600, 800, (250, 250, 250))

    # Clear existing applicants to avoid conflicts if re-seeded
    cursor.execute("DELETE FROM enrollments")
    cursor.execute("DELETE FROM documents")
    cursor.execute("DELETE FROM applicants")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sample_applicants = [
        {
            "id": "APP2568-0001",
            "national_id": make_valid_thai_id("110040012345"),
            "title": "นาย",
            "first_name": "ธนภัทร",
            "last_name": "สุขสำราญ",
            "birth_date": "2008-05-14",
            "phone": "0812345678",
            "email": "tanapat@example.com",
            "gender": "ชาย",
            "gpax": 3.45,
            "level": "ปวช.",
            "major_id": "VOC-AUTO",
            "prev_school": "โรงเรียนเทศบาล 1 (สถาวร)",
            "prev_school_province": "นครปฐม",
            "parent_name": "นายสมภพ สุขสำราญ",
            "parent_relation": "บิดา",
            "parent_phone": "0891112233",
            "referral_source": "อาจารย์แนะแนวไปแนะแนวที่โรงเรียน",
            "referral_teacher": "อ.สุชาติ ช่างชำนาญ",
            "status": "ENROLLED",
            "status_note": "มอบตัวและชำระค่าธรรมเนียมเรียบร้อยแล้ว",
            "photo": img_photo1,
            "student_id": "68201010001"
        },
        {
            "id": "APP2568-0002",
            "national_id": make_valid_thai_id("110050098765"),
            "title": "นางสาว",
            "first_name": "ศิริพร",
            "last_name": "แก้วมณี",
            "birth_date": "2008-08-20",
            "phone": "0823456789",
            "email": "siriporn@example.com",
            "gender": "หญิง",
            "gpax": 3.82,
            "level": "ปวช.",
            "major_id": "VOC-ACCT",
            "prev_school": "โรงเรียนวัดดอนยายหอม",
            "prev_school_province": "นครปฐม",
            "parent_name": "นางมาลี แก้วมณี",
            "parent_relation": "มารดา",
            "parent_phone": "0882223344",
            "referral_source": "Facebook / สื่อออนไลน์",
            "referral_teacher": "เพจวิทยาลัย",
            "status": "QUALIFIED",
            "status_note": "เอกสารถูกต้องครบถ้วน มีสิทธิ์เข้ามอบตัว",
            "photo": img_photo2,
            "student_id": None
        },
        {
            "id": "APP2568-0003",
            "national_id": make_valid_thai_id("173020054321"),
            "title": "นาย",
            "first_name": "กฤษณะ",
            "last_name": "พงษ์พาณิชย์",
            "birth_date": "2006-11-03",
            "phone": "0834567890",
            "email": "kritsana@example.com",
            "gender": "ชาย",
            "gpax": 3.12,
            "level": "ปวส.",
            "major_id": "DIP-IT",
            "prev_school": "วิทยาลัยการอาชีพนครปฐม",
            "prev_school_province": "นครปฐม",
            "parent_name": "นายวิโรจน์ พงษ์พาณิชย์",
            "parent_relation": "บิดา",
            "parent_phone": "0873334455",
            "referral_source": "เพื่อน / รุ่นพี่แนะนำ",
            "referral_teacher": "รุ่นพี่ ปวส. เทคโนโลยีสารสนเทศ",
            "status": "PENDING_REVIEW",
            "status_note": "",
            "photo": img_photo1,
            "student_id": None
        },
        {
            "id": "APP2568-0004",
            "national_id": make_valid_thai_id("110180022334"),
            "title": "นาย",
            "first_name": "อภิสิทธิ์",
            "last_name": "ทองอยู่",
            "birth_date": "2008-02-19",
            "phone": "0845678901",
            "email": "apisit@example.com",
            "gender": "ชาย",
            "gpax": 2.75,
            "level": "ปวช.",
            "major_id": "VOC-ELEC",
            "prev_school": "โรงเรียนพระปฐมวิทยาลัย",
            "prev_school_province": "นครปฐม",
            "parent_name": "นายสมพร ทองอยู่",
            "parent_relation": "บิดา",
            "parent_phone": "0864445566",
            "referral_source": "อาจารย์แนะแนวไปแนะแนวที่โรงเรียน",
            "referral_teacher": "อ.สุชาติ ช่างชำนาญ",
            "status": "DOCS_INCOMPLETE",
            "status_note": "รูปถ่ายใบแสดงผลการเรียน (รบ.) มัวมาก มองไม่เห็นชื่อโรงเรียนและเกรดเฉลี่ย กรุณาถ่ายใหม่ในที่มีแสงสว่างชัดเจน",
            "photo": img_photo2,
            "student_id": None
        },
        {
            "id": "APP2568-0005",
            "national_id": make_valid_thai_id("110020088990"),
            "title": "นางสาว",
            "first_name": "ณัฐธิดา",
            "last_name": "เรืองศรี",
            "birth_date": "2006-09-12",
            "phone": "0856789012",
            "email": "natthida@example.com",
            "gender": "หญิง",
            "gpax": 3.65,
            "level": "ปวส.",
            "major_id": "DIP-DBIZ",
            "prev_school": "โรงเรียนราชินีบูรณะ",
            "prev_school_province": "นครปฐม",
            "parent_name": "นางวิไลพร เรืองศรี",
            "parent_relation": "มารดา",
            "parent_phone": "0855556677",
            "referral_source": "ป้ายประชาสัมพันธ์ / แผ่นพับ",
            "referral_teacher": "",
            "status": "QUALIFIED",
            "status_note": "ผ่านการคัดเลือกโควตาผลการเรียนดีเด่น",
            "photo": img_photo2,
            "student_id": None
        }
    ]

    for app in sample_applicants:
        cursor.execute("""
        INSERT INTO applicants (
            id, national_id, title, first_name, last_name, birth_date, phone, email,
            gender, religion, nationality, address_no, moo, tambon, amphur, province, zipcode,
            prev_school, prev_school_province, gpax, level, major_id,
            parent_name, parent_relation, parent_phone, referral_source, referral_teacher,
            status, status_note, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'พุทธ', 'ไทย', '99/1', '2', 'บ่อพลับ', 'เมือง', 'นครปฐม', '73000',
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app["id"], app["national_id"], app["title"], app["first_name"], app["last_name"],
            app["birth_date"], app["phone"], app["email"], app["gender"],
            app["prev_school"], app["prev_school_province"], app["gpax"], app["level"], app["major_id"],
            app["parent_name"], app["parent_relation"], app["parent_phone"],
            app["referral_source"], app["referral_teacher"],
            app["status"], app["status_note"], now, now
        ))

        # Insert docs
        cursor.execute("INSERT INTO documents (applicant_id, doc_type, file_path, file_name, file_size, status, uploaded_at) VALUES (?, 'PHOTO', ?, 'photo.jpg', 12000, 'APPROVED', ?)", (app["id"], app["photo"], now))
        cursor.execute("INSERT INTO documents (applicant_id, doc_type, file_path, file_name, file_size, status, uploaded_at) VALUES (?, 'TRANSCRIPT', ?, 'transcript.jpg', 45000, 'APPROVED', ?)", (app["id"], img_trans1, now))
        cursor.execute("INSERT INTO documents (applicant_id, doc_type, file_path, file_name, file_size, status, uploaded_at) VALUES (?, 'ID_CARD', ?, 'id_card.jpg', 32000, 'APPROVED', ?)", (app["id"], img_id1, now))
        cursor.execute("INSERT INTO documents (applicant_id, doc_type, file_path, file_name, file_size, status, uploaded_at) VALUES (?, 'HOUSE_REG', ?, 'house_reg.jpg', 41000, 'APPROVED', ?)", (app["id"], img_house1, now))

        # If student has student_id, insert enrollment
        if app.get("student_id"):
            cursor.execute("""
            INSERT INTO enrollments (applicant_id, student_id, guardian_name, guardian_relation, guardian_phone, witness_name, enrollment_date, payment_status, created_at)
            VALUES (?, ?, ?, ?, ?, 'อ.สมคิด มั่นคง (หน.ทะเบียน)', '2026-11-06', 'PAID', ?)
            """, (app["id"], app["student_id"], app["parent_name"], app["parent_relation"], app["parent_phone"], now))

    conn.commit()
    conn.close()
    print("Sample vocational admission data seeded successfully!")

if __name__ == "__main__":
    seed()
