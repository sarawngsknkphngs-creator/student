import requests
import json
import logging

logger = logging.getLogger("admission.line")

def send_line_notify(token: str, message: str) -> bool:
    """Sends notification via LINE Notify API"""
    if not token or token == "YOUR_LINE_NOTIFY_TOKEN":
        logger.info(f"[LINE Notify Simulated]:\n{message}")
        return True
    
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}
    try:
        res = requests.post(url, headers=headers, data=data, timeout=5)
        return res.status_code == 200
    except Exception as e:
        logger.error(f"Error sending LINE Notify: {e}")
        return False

def notify_new_application(applicant: dict, notify_token: str = ""):
    """Notifies staff group about a new applicant submission"""
    msg = (
        f"\n📢 [มีผู้สมัครใหม่เข้าสู่ระบบ]\n"
        f"เลขที่ใบสมัคร: {applicant['id']}\n"
        f"ชื่อ-สกุล: {applicant['title']}{applicant['first_name']} {applicant['last_name']}\n"
        f"ระดับชั้น: {applicant['level']}\n"
        f"สาขาวิชา: {applicant['major_name']}\n"
        f"โรงเรียนเดิม: {applicant.get('prev_school', '-')}\n"
        f"เบอร์โทร: {applicant['phone']}\n"
        f"ตรวจสอบข้อมูลได้ที่ระบบงานรับสมัคร"
    )
    return send_line_notify(notify_token, msg)

def notify_status_change(applicant: dict, old_status: str, new_status: str, note: str = "", notify_token: str = ""):
    """Notifies applicant/staff of status updates"""
    status_thai = {
        "PENDING_REVIEW": "รอการตรวจสอบเอกสาร",
        "DOCS_INCOMPLETE": "เอกสารไม่ครบถ้วน / กรุณาแก้ไขเอกสาร",
        "QUALIFIED": "ผ่านการคัดเลือก (มีสิทธิ์มอบตัว)",
        "ENROLLED": "มอบตัวเสร็จสมบูรณ์",
        "REJECTED": "ไม่ผ่านคุณสมบัติ"
    }
    msg = (
        f"\n🔔 [แจ้งอัปเดตสถานะใบสมัคร]\n"
        f"ผู้สมัคร: {applicant['title']}{applicant['first_name']} {applicant['last_name']}\n"
        f"เลขที่ใบสมัคร: {applicant['id']}\n"
        f"สถานะปัจจุบัน: {status_thai.get(new_status, new_status)}\n"
    )
    if note:
        msg += f"หมายเหตุ/ข้อความจากเจ้าหน้าที่: {note}\n"
    msg += f"ตรวจสอบและแก้ไขเอกสารได้ที่ระบบรับสมัคร"
    return send_line_notify(notify_token, msg)
