import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import csv
from io import StringIO, BytesIO

def export_to_std02_excel(applicants: list) -> BytesIO:
    """
    Exports applicant list formatted specifically for the Vocational Registry System (ศธ.02)
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ข้อมูลนักศึกษาใหม่_ศธ02"

    # Header styling
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Sarabun", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Sarabun", size=10)
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    headers = [
        "ลำดับ",
        "เลขที่ใบสมัคร",
        "รหัสนักศึกษา",
        "เลขประจำตัวประชาชน",
        "คำนำหน้า",
        "ชื่อ",
        "นามสกุล",
        "เพศ",
        "วันเดือนปีเกิด",
        "สัญชาติ",
        "ศาสนา",
        "ที่อยู่ปัจจุบัน",
        "เบอร์โทรศัพท์",
        "โรงเรียนเดิม",
        "จังหวัดโรงเรียนเดิม",
        "เกรดเฉลี่ย (GPAX)",
        "ระดับชั้น",
        "รหัสสาขา ศธ.02",
        "ชื่อสาขาวิชา",
        "ชื่อผู้ปกครอง",
        "ความสัมพันธ์",
        "เบอร์โทรผู้ปกครอง",
        "ผู้แนะนำ/ครูแนะแนว",
        "สถานะใบสมัคร",
        "วันที่สมัคร"
    ]

    ws.append(headers)

    # Style Header Row
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    
    ws.row_dimensions[1].height = 28

    # Status translation mapping
    status_map = {
        "PENDING_REVIEW": "รอตรวจสอบเอกสาร",
        "DOCS_INCOMPLETE": "เอกสารไม่ครบ/รอแก้ไข",
        "QUALIFIED": "ผ่านการคัดเลือก",
        "ENROLLED": "มอบตัวแล้ว",
        "REJECTED": "ไม่ผ่านคุณสมบัติ"
    }

    # Append data rows
    for idx, app in enumerate(applicants, start=1):
        full_address = f"{app.get('address_no','')} ม.{app.get('moo','-')} ต.{app.get('tambon','')} อ.{app.get('amphur','')} จ.{app.get('province','')} {app.get('zipcode','')}".strip()
        
        row_data = [
            idx,
            app.get('id', ''),
            app.get('student_id', '-'),
            str(app.get('national_id', '')),
            app.get('title', ''),
            app.get('first_name', ''),
            app.get('last_name', ''),
            app.get('gender', ''),
            app.get('birth_date', ''),
            app.get('nationality', 'ไทย'),
            app.get('religion', 'พุทธ'),
            full_address,
            str(app.get('phone', '')),
            app.get('prev_school', ''),
            app.get('prev_school_province', ''),
            app.get('gpax', ''),
            app.get('level', ''),
            str(app.get('major_code', '')),
            app.get('major_name', ''),
            app.get('parent_name', ''),
            app.get('parent_relation', ''),
            str(app.get('parent_phone', '')),
            app.get('referral_teacher', '') or app.get('referral_source', ''),
            status_map.get(app.get('status', ''), app.get('status', '')),
            app.get('created_at', '')[:10]
        ]
        ws.append(row_data)

        # Style data row
        row_num = idx + 1
        ws.row_dimensions[row_num].height = 20
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.font = data_font
            cell.border = thin_border
            # Format text for IDs so Excel doesn't show scientific notation (e.g. 1.23E+12)
            if col_num in (3, 4, 13, 18, 22):
                cell.number_format = '@'
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_num in (1, 8, 9, 16, 17, 24, 25):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Auto-fit column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            max_len = max(max_len, len(val_str.encode('utf-8')) // 2)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output

def export_to_std02_csv(applicants: list) -> str:
    """
    Exports applicant list formatted for CSV (with UTF-8 BOM for Excel compatibility)
    """
    output = StringIO()
    writer = csv.writer(output)

    headers = [
        "ลำดับ", "เลขที่ใบสมัคร", "รหัสนักศึกษา", "เลขประจำตัวประชาชน",
        "คำนำหน้า", "ชื่อ", "นามสกุล", "เพศ", "วันเดือนปีเกิด",
        "สัญชาติ", "ศาสนา", "ที่อยู่", "เบอร์โทรศัพท์",
        "โรงเรียนเดิม", "จังหวัดโรงเรียนเดิม", "เกรดเฉลี่ย", "ระดับชั้น",
        "รหัสสาขา_ศธ02", "ชื่อสาขาวิชา", "ชื่อผู้ปกครอง", "ความสัมพันธ์",
        "เบอร์โทรผู้ปกครอง", "ผู้แนะนำ", "สถานะ", "วันที่สมัคร"
    ]
    writer.writerow(headers)

    status_map = {
        "PENDING_REVIEW": "รอตรวจสอบเอกสาร",
        "DOCS_INCOMPLETE": "เอกสารไม่ครบ/รอแก้ไข",
        "QUALIFIED": "ผ่านการคัดเลือก",
        "ENROLLED": "มอบตัวแล้ว",
        "REJECTED": "ไม่ผ่านคุณสมบัติ"
    }

    for idx, app in enumerate(applicants, start=1):
        full_address = f"{app.get('address_no','')} ม.{app.get('moo','-')} ต.{app.get('tambon','')} อ.{app.get('amphur','')} จ.{app.get('province','')} {app.get('zipcode','')}".strip()
        writer.writerow([
            idx,
            app.get('id', ''),
            app.get('student_id', '-'),
            f"'{app.get('national_id', '')}", # Prefix with quote to preserve 13 digits
            app.get('title', ''),
            app.get('first_name', ''),
            app.get('last_name', ''),
            app.get('gender', ''),
            app.get('birth_date', ''),
            app.get('nationality', 'ไทย'),
            app.get('religion', 'พุทธ'),
            full_address,
            f"'{app.get('phone', '')}",
            app.get('prev_school', ''),
            app.get('prev_school_province', ''),
            app.get('gpax', ''),
            app.get('level', ''),
            app.get('major_code', ''),
            app.get('major_name', ''),
            app.get('parent_name', ''),
            app.get('parent_relation', ''),
            f"'{app.get('parent_phone', '')}",
            app.get('referral_teacher', '') or app.get('referral_source', ''),
            status_map.get(app.get('status', ''), app.get('status', '')),
            app.get('created_at', '')[:10]
        ])

    return "\ufeff" + output.getvalue()
