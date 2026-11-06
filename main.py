import os
import shutil
import sqlite3
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from database import get_db, init_db
from pdf_generator import generate_application_pdf, generate_enrollment_pdf
from export_service import export_to_std02_excel, export_to_std02_csv
from line_service import notify_new_application, notify_status_change

app = FastAPI(title="Vocational Online Admission System")
app.add_middleware(SessionMiddleware, secret_key="vocational-admission-secret-key-2568")

# Ensure required directories exist
init_db()

# Mount Static Files & Templates
app.mount("/static", StaticFiles(directory="d:/sk/static"), name="static")
templates = Jinja2Templates(directory="d:/sk/templates")

def render_template(request: Request, name: str, context: dict = None, status_code: int = 200):
    ctx = context or {}
    return templates.TemplateResponse(request=request, name=name, context=ctx, status_code=status_code)

def validate_thai_national_id(id_str: str) -> bool:
    """Verifies Thai 13-digit National ID using Modulus 11 Checksum formula"""
    clean = "".join([c for c in id_str if c.isdigit()])
    if len(clean) != 13:
        return False
    if clean == clean[0] * 13:
        return False
    total = sum(int(clean[i]) * (13 - i) for i in range(12))
    check = (11 - (total % 11)) % 10
    return check == int(clean[12])

def get_admin_session(request: Request):
    return request.session.get("admin_user")

def get_dashboard_data():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM applicants")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applicants WHERE status = 'PENDING_REVIEW'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applicants WHERE status = 'DOCS_INCOMPLETE'")
    incomplete = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applicants WHERE status = 'QUALIFIED'")
    qualified = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applicants WHERE status = 'ENROLLED'")
    enrolled = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applicants WHERE level = 'ปวช.'")
    voc_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applicants WHERE level = 'ปวส.'")
    dip_count = cursor.fetchone()[0]

    cursor.execute("""
    SELECT m.name, m.quota, COUNT(a.id) as app_count
    FROM majors m
    LEFT JOIN applicants a ON m.id = a.major_id
    GROUP BY m.id
    ORDER BY app_count DESC
    """)
    majors_stats = cursor.fetchall()
    majors_labels = [r[0] for r in majors_stats]
    majors_quotas = [r[1] for r in majors_stats]
    majors_counts = [r[2] for r in majors_stats]

    cursor.execute("""
    SELECT prev_school, prev_school_province, COUNT(*) as count
    FROM applicants
    WHERE prev_school IS NOT NULL AND prev_school != ''
    GROUP BY prev_school
    ORDER BY count DESC
    LIMIT 10
    """)
    top_schools = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
    SELECT referral_source, COUNT(*) as count
    FROM applicants
    WHERE referral_source IS NOT NULL AND referral_source != ''
    GROUP BY referral_source
    ORDER BY count DESC
    """)
    referrals = cursor.fetchall()
    referral_labels = [r[0] for r in referrals] if referrals else ["อาจารย์แนะแนว", "Facebook/โซเชียล", "เพื่อน/รุ่นพี่"]
    referral_counts = [r[1] for r in referrals] if referrals else [0, 0, 0]

    cursor.execute("""
    SELECT a.*, m.name as major_name, m.code as major_code, e.student_id
    FROM applicants a
    JOIN majors m ON a.major_id = m.id
    LEFT JOIN enrollments e ON a.id = e.applicant_id
    ORDER BY a.created_at DESC
    """)
    applicants = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "total": total,
        "pending": pending,
        "incomplete": incomplete,
        "qualified": qualified,
        "enrolled": enrolled,
        "voc_count": voc_count,
        "dip_count": dip_count,
        "majors_labels": json.dumps(majors_labels, ensure_ascii=False),
        "majors_counts": json.dumps(majors_counts),
        "majors_quotas": json.dumps(majors_quotas),
        "top_schools": top_schools,
        "referral_labels": json.dumps(referral_labels, ensure_ascii=False),
        "referral_counts": json.dumps(referral_counts),
        "applicants": applicants
    }

# -------------------------------------------------------------
# Public Front-end Routes
# -------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, tab: Optional[str] = "home"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, code, name, level, quota FROM majors WHERE is_active = 1")
    majors = [dict(row) for row in cursor.fetchall()]
    conn.close()

    stats_data = get_dashboard_data()

    return render_template(request, "index.html", {
        "majors": majors,
        "majors_json": json.dumps(majors, ensure_ascii=False),
        "stats": stats_data,
        "applicants": stats_data["applicants"],
        "active_tab": tab,
        "is_admin_logged_in": bool(get_admin_session(request))
    })

@app.get("/api/applicant-status")
async def api_applicant_status(national_id: str):
    clean_id = "".join([c for c in national_id if c.isdigit()])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, m.name as major_name, m.code as major_code
    FROM applicants a
    JOIN majors m ON a.major_id = m.id
    WHERE a.national_id = ?
    """, (clean_id,))
    applicant_row = cursor.fetchone()

    if not applicant_row:
        conn.close()
        return {"found": False, "message": f"ไม่พบข้อมูลการสมัครของเลขประจำตัวประชาชน {national_id}"}

    applicant = dict(applicant_row)

    cursor.execute("SELECT * FROM documents WHERE applicant_id = ?", (applicant['id'],))
    docs = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM enrollments WHERE applicant_id = ?", (applicant['id'],))
    en_row = cursor.fetchone()
    enrollment = dict(en_row) if en_row else None

    conn.close()
    return {"found": True, "applicant": applicant, "documents": docs, "enrollment": enrollment}

@app.get("/apply", response_class=HTMLResponse)
async def apply_form(request: Request, level: Optional[str] = "ปวช."):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, code, name, level, quota FROM majors WHERE is_active = 1")
    majors = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template(request, "apply.html", {
        "default_level": level,
        "majors_json": json.dumps(majors, ensure_ascii=False),
        "is_admin_logged_in": bool(get_admin_session(request))
    })

@app.post("/apply")
async def process_apply(
    request: Request,
    level: str = Form(...),
    major_id: str = Form(...),
    national_id: str = Form(...),
    title: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    birth_date: str = Form(...),
    gender: str = Form(...),
    religion: str = Form("พุทธ"),
    nationality: str = Form("ไทย"),
    phone: str = Form(...),
    email: Optional[str] = Form(None),
    address_no: Optional[str] = Form(""),
    moo: Optional[str] = Form(""),
    tambon: Optional[str] = Form(""),
    amphur: Optional[str] = Form(""),
    province: Optional[str] = Form(""),
    zipcode: Optional[str] = Form(""),
    prev_school: str = Form(...),
    prev_school_province: str = Form(...),
    gpax: float = Form(...),
    parent_name: str = Form(...),
    parent_relation: str = Form(...),
    parent_phone: str = Form(...),
    referral_source: Optional[str] = Form(""),
    referral_teacher: Optional[str] = Form(""),
    file_photo: UploadFile = File(...),
    file_transcript: UploadFile = File(...),
    file_id_card: UploadFile = File(...),
    file_house_reg: UploadFile = File(...)
):
    clean_id = "".join([c for c in national_id if c.isdigit()])
    if not validate_thai_national_id(clean_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, code, name, level, quota FROM majors WHERE is_active = 1")
        majors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return render_template(request, "apply.html", {
            "error_message": "เลขประจำตัวประชาชน 13 หลัก ไม่ถูกต้องตามสูตรคำนวณของสำนักทะเบียน",
            "default_level": level,
            "majors_json": json.dumps(majors, ensure_ascii=False),
            "is_admin_logged_in": bool(get_admin_session(request))
        }, status_code=400)

    conn = get_db()
    cursor = conn.cursor()

    # Check duplicate application
    cursor.execute("SELECT id FROM applicants WHERE national_id = ?", (clean_id,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return RedirectResponse(url=f"/status?national_id={clean_id}", status_code=status.HTTP_303_SEE_OTHER)

    # Generate sequential application ID (e.g. APP2568-0001)
    cursor.execute("SELECT COUNT(*) FROM applicants")
    count = cursor.fetchone()[0] + 1
    applicant_id = f"APP2568-{count:04d}"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Insert applicant record
    cursor.execute("""
    INSERT INTO applicants (
        id, national_id, title, first_name, last_name, birth_date, phone, email,
        gender, religion, nationality, address_no, moo, tambon, amphur, province, zipcode,
        prev_school, prev_school_province, gpax, level, major_id,
        parent_name, parent_relation, parent_phone, referral_source, referral_teacher,
        status, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING_REVIEW', ?, ?)
    """, (
        applicant_id, clean_id, title, first_name, last_name, birth_date, phone, email,
        gender, religion, nationality, address_no, moo, tambon, amphur, province, zipcode,
        prev_school, prev_school_province, gpax, level, major_id,
        parent_name, parent_relation, parent_phone, referral_source, referral_teacher,
        now_str, now_str
    ))

    # Helper function to save file
    def save_doc(file_obj: UploadFile, folder: str, doc_type: str):
        if not file_obj or not file_obj.filename:
            return None
        ext = os.path.splitext(file_obj.filename)[1].lower()
        if not ext:
            ext = ".jpg"
        save_name = f"{applicant_id}_{doc_type}{ext}"
        rel_path = f"static/uploads/{folder}/{save_name}"
        full_path = f"d:/sk/{rel_path}"
        with open(full_path, "wb") as f:
            shutil.copyfileobj(file_obj.file, f)
        
        cursor.execute("""
        INSERT INTO documents (applicant_id, doc_type, file_path, file_name, file_size, status, uploaded_at)
        VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
        """, (applicant_id, doc_type, rel_path, file_obj.filename, os.path.getsize(full_path), now_str))
        return rel_path

    save_doc(file_photo, "photos", "PHOTO")
    save_doc(file_transcript, "transcripts", "TRANSCRIPT")
    save_doc(file_id_card, "id_cards", "ID_CARD")
    save_doc(file_house_reg, "house_regs", "HOUSE_REG")

    conn.commit()

    # Query major name for notification
    cursor.execute("SELECT name FROM majors WHERE id = ?", (major_id,))
    major_row = cursor.fetchone()
    major_name = major_row[0] if major_row else major_id

    # LINE notification
    notify_new_application({
        "id": applicant_id,
        "title": title,
        "first_name": first_name,
        "last_name": last_name,
        "level": level,
        "major_name": major_name,
        "prev_school": prev_school,
        "phone": phone
    })

    conn.close()

    return RedirectResponse(url=f"/apply/success?id={applicant_id}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/apply/success", response_class=HTMLResponse)
async def apply_success(request: Request, id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, m.name as major_name, m.code as major_code
    FROM applicants a
    JOIN majors m ON a.major_id = m.id
    WHERE a.id = ?
    """, (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return RedirectResponse(url="/")

    return render_template(request, "apply_success.html", {
        "applicant": dict(row),
        "is_admin_logged_in": bool(get_admin_session(request))
    })

@app.get("/status", response_class=HTMLResponse)
async def check_status(request: Request, national_id: Optional[str] = None):
    if not national_id:
        return render_template(request, "status.html", {
            "is_admin_logged_in": bool(get_admin_session(request))
        })

    clean_id = "".join([c for c in national_id if c.isdigit()])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, m.name as major_name, m.code as major_code
    FROM applicants a
    JOIN majors m ON a.major_id = m.id
    WHERE a.national_id = ?
    """, (clean_id,))
    applicant_row = cursor.fetchone()

    if not applicant_row:
        conn.close()
        return render_template(request, "status.html", {
            "searched_id": national_id,
            "error_message": f"ไม่พบข้อมูลการสมัครของเลขประจำตัวประชาชน {national_id} ในระบบ กรุณาตรวจสอบเลขบัตรหรือกรอกใบสมัครใหม่",
            "is_admin_logged_in": bool(get_admin_session(request))
        })

    applicant = dict(applicant_row)

    # Fetch documents
    cursor.execute("SELECT * FROM documents WHERE applicant_id = ?", (applicant['id'],))
    docs = [dict(r) for r in cursor.fetchall()]

    # Fetch enrollment record if any
    cursor.execute("SELECT * FROM enrollments WHERE applicant_id = ?", (applicant['id'],))
    enrollment_row = cursor.fetchone()
    enrollment = dict(enrollment_row) if enrollment_row else None

    conn.close()

    return render_template(request, "status_detail.html", {
        "applicant": applicant,
        "documents": docs,
        "enrollment": enrollment,
        "is_admin_logged_in": bool(get_admin_session(request))
    })

@app.post("/reupload-doc")
async def reupload_document(
    applicant_id: str = Form(...),
    national_id: str = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...)
):
    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    folder_map = {
        "PHOTO": "photos",
        "TRANSCRIPT": "transcripts",
        "ID_CARD": "id_cards",
        "HOUSE_REG": "house_regs"
    }
    folder = folder_map.get(doc_type, "other")
    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    save_name = f"{applicant_id}_{doc_type}_reuploaded_{int(datetime.now().timestamp())}{ext}"
    rel_path = f"static/uploads/{folder}/{save_name}"
    full_path = f"d:/sk/{rel_path}"

    with open(full_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Insert new document record
    cursor.execute("""
    INSERT INTO documents (applicant_id, doc_type, file_path, file_name, file_size, status, uploaded_at)
    VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
    """, (applicant_id, doc_type, rel_path, file.filename, os.path.getsize(full_path), now_str))

    # Reset applicant status back to PENDING_REVIEW
    cursor.execute("""
    UPDATE applicants
    SET status = 'PENDING_REVIEW', status_note = 'ผู้สมัครได้แนบเอกสารใหม่แล้ว รอเจ้าหน้าที่ตรวจสอบ', updated_at = ?
    WHERE id = ?
    """, (now_str, applicant_id))

    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/status?national_id={national_id}", status_code=status.HTTP_303_SEE_OTHER)

# -------------------------------------------------------------
# PDF Downloads
# -------------------------------------------------------------

@app.get("/download/application-pdf/{applicant_id}")
async def download_app_pdf(request: Request, applicant_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, m.name as major_name, m.code as major_code
    FROM applicants a
    JOIN majors m ON a.major_id = m.id
    WHERE a.id = ?
    """, (applicant_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Applicant not found")

    applicant = dict(row)

    # Find photo file if any
    cursor.execute("SELECT file_path FROM documents WHERE applicant_id = ? AND doc_type = 'PHOTO' ORDER BY id DESC LIMIT 1", (applicant_id,))
    photo_row = cursor.fetchone()
    if photo_row and photo_row[0]:
        applicant["photo_path"] = f"d:/sk/{photo_row[0]}"

    conn.close()

    pdf_filename = f"ใบสมัคร_{applicant['id']}_{applicant['first_name']}.pdf"
    pdf_path = f"d:/sk/static/generated_pdfs/{pdf_filename}"
    base_url = str(request.base_url).rstrip("/")
    generate_application_pdf(applicant, pdf_path, base_url=base_url)

    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_filename)

@app.get("/download/enrollment-pdf/{applicant_id}")
async def download_enroll_pdf(request: Request, applicant_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, m.name as major_name, m.code as major_code
    FROM applicants a
    JOIN majors m ON a.major_id = m.id
    WHERE a.id = ?
    """, (applicant_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Applicant not found")

    applicant = dict(row)

    cursor.execute("SELECT * FROM enrollments WHERE applicant_id = ?", (applicant_id,))
    en_row = cursor.fetchone()
    enrollment = dict(en_row) if en_row else {}

    conn.close()

    pdf_filename = f"ใบมอบตัว_{applicant['id']}_{applicant['first_name']}.pdf"
    pdf_path = f"d:/sk/static/generated_pdfs/{pdf_filename}"
    base_url = str(request.base_url).rstrip("/")
    generate_enrollment_pdf(applicant, enrollment, pdf_path, base_url=base_url)

    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_filename)

# -------------------------------------------------------------
# Back-end / Admin Routes
# -------------------------------------------------------------

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return render_template(request, "admin/login.html", {
        "is_admin_logged_in": False
    })

@app.post("/admin/login")
async def admin_login_process(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, full_name, role FROM admin_users WHERE username = ? AND password_hash = ?", (username, pwd_hash))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return render_template(request, "admin/login.html", {
            "error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง",
            "is_admin_logged_in": False
        }, status_code=400)

    request.session["admin_user"] = {
        "username": user[0],
        "full_name": user[1],
        "role": user[2]
    }
    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    admin = get_admin_session(request)
    if not admin:
        return RedirectResponse(url="/admin/login")

    stats_data = get_dashboard_data()

    return render_template(request, "admin/dashboard.html", {
        "stats": stats_data,
        "is_admin_logged_in": True
    })

@app.get("/admin/applicants", response_class=HTMLResponse)
async def admin_applicants_list(
    request: Request,
    q: Optional[str] = None,
    level: Optional[str] = None,
    status: Optional[str] = None
):
    admin = get_admin_session(request)
    if not admin:
        return RedirectResponse(url="/admin/login")

    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT a.*, m.name as major_name, m.code as major_code, e.student_id
    FROM applicants a
    JOIN majors m ON a.major_id = m.id
    LEFT JOIN enrollments e ON a.id = e.applicant_id
    WHERE 1=1
    """
    params = []

    if q:
        query += " AND (a.id LIKE ? OR a.first_name LIKE ? OR a.last_name LIKE ? OR a.national_id LIKE ?)"
        wild = f"%{q}%"
        params.extend([wild, wild, wild, wild])

    if level:
        query += " AND a.level = ?"
        params.append(level)

    if status:
        query += " AND a.status = ?"
        params.append(status)

    query += " ORDER BY a.created_at DESC"

    cursor.execute(query, params)
    applicants = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return render_template(request, "admin/applicants.html", {
        "applicants": applicants,
        "query_q": q,
        "query_level": level,
        "query_status": status,
        "is_admin_logged_in": True
    })

@app.get("/admin/applicant/{applicant_id}", response_class=HTMLResponse)
async def admin_applicant_detail(request: Request, applicant_id: str):
    admin = get_admin_session(request)
    if not admin:
        return RedirectResponse(url="/admin/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, m.name as major_name, m.code as major_code
    FROM applicants a
    JOIN majors m ON a.major_id = m.id
    WHERE a.id = ?
    """, (applicant_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Applicant not found")

    applicant = dict(row)

    cursor.execute("SELECT * FROM documents WHERE applicant_id = ?", (applicant_id,))
    documents = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM enrollments WHERE applicant_id = ?", (applicant_id,))
    en_row = cursor.fetchone()
    enrollment = dict(en_row) if en_row else None

    conn.close()

    return render_template(request, "admin/applicant_detail.html", {
        "applicant": applicant,
        "documents": documents,
        "enrollment": enrollment,
        "is_admin_logged_in": True
    })

@app.post("/admin/applicant/{applicant_id}/update-status")
async def update_applicant_status(
    request: Request,
    applicant_id: str,
    status: str = Form(...),
    status_note: Optional[str] = Form(""),
    send_line: Optional[str] = Form(None)
):
    admin = get_admin_session(request)
    if not admin:
        return RedirectResponse(url="/admin/login")

    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("SELECT * FROM applicants WHERE id = ?", (applicant_id,))
    app_row = cursor.fetchone()
    if not app_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Not found")

    old_status = app_row["status"]

    cursor.execute("""
    UPDATE applicants
    SET status = ?, status_note = ?, updated_at = ?
    WHERE id = ?
    """, (status, status_note, now_str, applicant_id))

    conn.commit()

    if send_line:
        notify_status_change(dict(app_row), old_status, status, status_note)

    conn.close()
    return RedirectResponse(url=f"/admin/applicant/{applicant_id}", status_code=303)

@app.get("/admin/enrollment", response_class=HTMLResponse)
async def admin_enrollment_page(request: Request, applicant_id: Optional[str] = None):
    admin = get_admin_session(request)
    if not admin:
        return RedirectResponse(url="/admin/login")

    conn = get_db()
    cursor = conn.cursor()

    # Get qualified applicants who have not yet enrolled
    cursor.execute("""
    SELECT a.*, m.name as major_name, m.code as major_code
    FROM applicants a
    JOIN majors m ON a.major_id = m.id
    WHERE a.status = 'QUALIFIED'
    ORDER BY a.created_at ASC
    """)
    qualified = [dict(r) for r in cursor.fetchall()]

    # Selected applicant if passed
    selected = None
    proposed_id = ""
    if applicant_id:
        cursor.execute("""
        SELECT a.*, m.name as major_name, m.code as major_code
        FROM applicants a
        JOIN majors m ON a.major_id = m.id
        WHERE a.id = ?
        """, (applicant_id,))
        sel_row = cursor.fetchone()
        if sel_row:
            selected = dict(sel_row)
            cursor.execute("SELECT COUNT(*) FROM enrollments")
            seq = cursor.fetchone()[0] + 1
            proposed_id = f"68{selected['major_code']}{seq:04d}"

    # Enrolled list
    cursor.execute("""
    SELECT e.*, a.title, a.first_name, a.last_name, a.level, m.name as major_name
    FROM enrollments e
    JOIN applicants a ON e.applicant_id = a.id
    JOIN majors m ON a.major_id = m.id
    ORDER BY e.created_at DESC
    """)
    enrolled_list = [dict(r) for r in cursor.fetchall()]

    conn.close()

    today_str = datetime.now().strftime("%Y-%m-%d")

    return render_template(request, "admin/enrollment.html", {
        "qualified_applicants": qualified,
        "selected_applicant": selected,
        "proposed_student_id": proposed_id,
        "enrolled_list": enrolled_list,
        "today_str": today_str,
        "is_admin_logged_in": True
    })

@app.post("/admin/enrollment/save")
async def save_enrollment(
    request: Request,
    applicant_id: str = Form(...),
    student_id: str = Form(...),
    guardian_name: str = Form(...),
    guardian_relation: str = Form(...),
    guardian_phone: Optional[str] = Form(""),
    witness_name: Optional[str] = Form("อาจารย์หัวหน้างานทะเบียน"),
    enrollment_date: str = Form(...),
    payment_status: str = Form("PAID")
):
    admin = get_admin_session(request)
    if not admin:
        return RedirectResponse(url="/admin/login")

    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO enrollments (applicant_id, student_id, guardian_name, guardian_relation, guardian_phone, witness_name, enrollment_date, payment_status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(applicant_id) DO UPDATE SET
        student_id=excluded.student_id,
        guardian_name=excluded.guardian_name,
        guardian_relation=excluded.guardian_relation,
        guardian_phone=excluded.guardian_phone,
        witness_name=excluded.witness_name,
        enrollment_date=excluded.enrollment_date,
        payment_status=excluded.payment_status
    """, (applicant_id, student_id, guardian_name, guardian_relation, guardian_phone, witness_name, enrollment_date, payment_status, now_str))

    # Update applicant status to ENROLLED
    cursor.execute("""
    UPDATE applicants
    SET status = 'ENROLLED', updated_at = ?
    WHERE id = ?
    """, (now_str, applicant_id))

    conn.commit()
    conn.close()

    return RedirectResponse(url="/admin/enrollment", status_code=303)

# -------------------------------------------------------------
# Exports (ศธ.02)
# -------------------------------------------------------------

@app.get("/admin/export/std02-excel")
async def export_excel(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, m.name as major_name, m.code as major_code, e.student_id
    FROM applicants a
    JOIN majors m ON a.major_id = m.id
    LEFT JOIN enrollments e ON a.id = e.applicant_id
    ORDER BY a.created_at ASC
    """)
    applicants = [dict(r) for r in cursor.fetchall()]
    conn.close()

    output = export_to_std02_excel(applicants)
    filename = f"Std02_Applicants_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/admin/export/std02-csv")
async def export_csv(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, m.name as major_name, m.code as major_code, e.student_id
    FROM applicants a
    JOIN majors m ON a.major_id = m.id
    LEFT JOIN enrollments e ON a.id = e.applicant_id
    ORDER BY a.created_at ASC
    """)
    applicants = [dict(r) for r in cursor.fetchall()]
    conn.close()

    csv_data = export_to_std02_csv(applicants)
    filename = f"Std02_Applicants_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return Response(
        content=csv_data.encode('utf-8'),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
