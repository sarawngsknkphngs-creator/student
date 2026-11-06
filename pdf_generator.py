import os
import qrcode
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

FONT_REG = "d:/sk/static/fonts/Sarabun-Regular.ttf"
FONT_BOLD = "d:/sk/static/fonts/Sarabun-Bold.ttf"

def register_fonts():
    if os.path.exists(FONT_REG):
        pdfmetrics.registerFont(TTFont("Sarabun", FONT_REG))
    elif os.path.exists("C:/Windows/Fonts/tahoma.ttf"):
        pdfmetrics.registerFont(TTFont("Sarabun", "C:/Windows/Fonts/tahoma.ttf"))

    if os.path.exists(FONT_BOLD):
        pdfmetrics.registerFont(TTFont("Sarabun-Bold", FONT_BOLD))
    elif os.path.exists("C:/Windows/Fonts/tahomabd.ttf"):
        pdfmetrics.registerFont(TTFont("Sarabun-Bold", "C:/Windows/Fonts/tahomabd.ttf"))

register_fonts()

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]

def parse_thai_date(date_str):
    if not date_str:
        return ("", "", "")
    try:
        parts = str(date_str).replace("/", "-").split("-")
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            thai_year = y + 543 if y < 2400 else y
            month_name = THAI_MONTHS[m] if 1 <= m <= 12 else str(m)
            return (str(d), month_name, str(thai_year))
    except Exception:
        pass
    return (str(date_str), "", "")

def generate_qr_image(data_text: str, size: int = 100) -> str:
    """Generates a temporary QR code image file and returns its path."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    os.makedirs("d:/sk/static/generated_pdfs/qr", exist_ok=True)
    file_path = f"d:/sk/static/generated_pdfs/qr/qr_{abs(hash(data_text))}.png"
    img.save(file_path)
    return file_path

def val_or_dots(val, default_dots="................................................"):
    if val is not None and str(val).strip() and str(val).strip() != "-":
        return f"<b>{str(val).strip()}</b>"
    return default_dots

def generate_application_pdf(applicant: dict, output_path: str, base_url: str = "http://localhost:8000"):
    """
    Generates official A4 Application Form (ใบสมัครเข้ารับคัดเลือกเพื่อศึกษาต่อเป็นกรณีพิเศษ - โควตา)
    วิทยาลัยเทคนิคท่าหลวงซิเมนต์ไทยอนุสรณ์
    Replicating the exact physical paper form layout on a single A4 page.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.2*cm,
        bottomMargin=1.0*cm
    )

    styles = getSampleStyleSheet()
    
    header_title_style = ParagraphStyle(
        'HeaderTitle',
        fontName='Sarabun-Bold',
        fontSize=13,
        leading=18,
        alignment=1, # Center
        textColor=colors.black
    )
    
    line_style = ParagraphStyle(
        'FormLine',
        fontName='Sarabun',
        fontSize=10.5,
        leading=17,
        textColor=colors.black
    )
    
    bold_line_style = ParagraphStyle(
        'FormBoldLine',
        fontName='Sarabun-Bold',
        fontSize=10.5,
        leading=17,
        textColor=colors.black
    )

    right_sig_style = ParagraphStyle(
        'RightSig',
        fontName='Sarabun',
        fontSize=10.5,
        leading=17,
        alignment=2, # Right
        textColor=colors.black
    )

    story = []

    # ---------------------------------------------------------
    # 1. Header: Logo (Left) + Center Titles + Photo Box (Right)
    # ---------------------------------------------------------
    logo_path = "d:/sk/static/vec_logo.png"
    if os.path.exists(logo_path):
        logo_cell = RLImage(logo_path, width=2.2*cm, height=2.2*cm)
    else:
        logo_cell = Paragraph("<b>[ สอศ. ]</b>", ParagraphStyle('LG', fontName='Sarabun-Bold', fontSize=10, alignment=1))

    title_html = (
        "<b>ใบสมัครเข้ารับคัดเลือกเพื่อศึกษาต่อเป็นกรณีพิเศษ (โควตา)</b><br/>"
        "<b>วิทยาลัยเทคนิคท่าหลวงซิเมนต์ไทยอนุสรณ์ ประจำปีการศึกษา ๒๕๖๘</b>"
    )
    title_cell = Paragraph(title_html, header_title_style)

    # Photo Box
    photo_path = applicant.get('photo_path') or ""
    if photo_path and os.path.exists(photo_path):
        try:
            photo_cell = RLImage(photo_path, width=2.4*cm, height=3.0*cm)
        except Exception:
            photo_cell = Paragraph("รูปถ่าย<br/>ขนาด ๑ นิ้ว", ParagraphStyle('PB', fontName='Sarabun', fontSize=9, leading=12, alignment=1))
    else:
        photo_cell = Paragraph("รูปถ่าย<br/>ขนาด ๑ นิ้ว", ParagraphStyle('PB', fontName='Sarabun', fontSize=9, leading=12, alignment=1))

    header_table = Table(
        [[logo_cell, title_cell, photo_cell]],
        colWidths=[2.6*cm, 12.8*cm, 2.6*cm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'CENTER'),
        ('BOX', (2,0), (2,0), 0.75, colors.black),
        ('TOPPADDING', (2,0), (2,0), 10),
        ('BOTTOMPADDING', (2,0), (2,0), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4*cm))

    # ---------------------------------------------------------
    # 2. Checkboxes for Study Level & Track
    # ---------------------------------------------------------
    level = applicant.get('level', '')
    apply_track = applicant.get('apply_track', '')

    check_dip_direct = "[ &nbsp; ]"
    check_dip_other  = "[ &nbsp; ]"
    check_voc        = "[ &nbsp; ]"

    if level == "ปวช." or "ปวช" in apply_track:
        check_voc = "[ ✓ ]"
    elif "ต่างสาขา" in apply_track or "ม.6" in apply_track or "ม.๖" in apply_track:
        check_dip_other = "[ ✓ ]"
    else:
        # Default or Direct track
        check_dip_direct = "[ ✓ ]"

    track_html = (
        f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<b>{check_dip_direct}</b>&nbsp;&nbsp;ระดับ ปวส. ( สายตรง )<br/>"
        f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<b>{check_dip_other}</b>&nbsp;&nbsp;ระดับ ปวส. ( ม.๖/ปวช. ต่างสาขา )<br/>"
        f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<b>{check_voc}</b>&nbsp;&nbsp;ระดับ ปวช."
    )
    story.append(Paragraph(track_html, line_style))
    story.append(Spacer(1, 0.4*cm))

    # ---------------------------------------------------------
    # 3. Form Items ๑ - ๖
    # ---------------------------------------------------------
    # Date parsing
    b_day, b_month, b_year = parse_thai_date(applicant.get('birth_date'))
    full_name = f"{applicant.get('title','')}{applicant.get('first_name','')} {applicant.get('last_name','')}"

    # Item 1: ชื่อ-นามสกุล
    item_1 = (
        f"๑. ชื่อ-นามสกุล {val_or_dots(full_name, '....................................................................')} "
        f"เกิดวันที่ {val_or_dots(b_day, '............')} "
        f"เดือน {val_or_dots(b_month, '............................')} "
        f"พ.ศ. {val_or_dots(b_year, '...............')}"
    )
    story.append(Paragraph(item_1, line_style))

    # Item 2: บิดา
    f_name = applicant.get('father_name') or (applicant.get('parent_name') if applicant.get('parent_relation') == 'บิดา' else '')
    f_age = applicant.get('father_age') or ''
    f_job = applicant.get('father_job') or ''
    item_2 = (
        f"๒. ชื่อ-สกุลบิดา {val_or_dots(f_name, '....................................................................')} "
        f"อายุ {val_or_dots(f_age, '............')} ปี "
        f"อาชีพ {val_or_dots(f_job, '.............................................')}"
    )
    story.append(Paragraph(item_2, line_style))

    # Item 3: มารดา
    m_name = applicant.get('mother_name') or (applicant.get('parent_name') if applicant.get('parent_relation') == 'มารดา' else '')
    m_age = applicant.get('mother_age') or ''
    m_job = applicant.get('mother_job') or ''
    item_3 = (
        f"๓. ชื่อ-สกุลมารดา {val_or_dots(m_name, '...................................................................')} "
        f"อายุ {val_or_dots(m_age, '............')} ปี "
        f"อาชีพ {val_or_dots(m_job, '.............................................')}"
    )
    story.append(Paragraph(item_3, line_style))

    # Item 4: ที่อยู่
    addr_no = applicant.get('address_no', '')
    moo = applicant.get('moo', '')
    soi = applicant.get('soi', '')
    road = applicant.get('road', '')
    tambon = applicant.get('tambon', '')
    amphur = applicant.get('amphur', '')
    province = applicant.get('province', '')
    zipcode = applicant.get('zipcode', '')
    phone = applicant.get('phone', '')

    item_4a = (
        f"๔. ที่อยู่ปัจจุบันที่สามารถติดต่อได้ บ้านเลขที่ {val_or_dots(addr_no, '.......')} "
        f"หมู่ {val_or_dots(moo, '.......')} "
        f"ซอย {val_or_dots(soi, '.................')} "
        f"ถนน {val_or_dots(road, '...........................')}"
    )
    item_4b = (
        f"&nbsp;&nbsp;&nbsp;&nbsp;ตำบล {val_or_dots(tambon, '.....................................')} "
        f"อำเภอ {val_or_dots(amphur, '..................................')} "
        f"จังหวัด {val_or_dots(province, '...........................................')}"
    )
    item_4c = (
        f"&nbsp;&nbsp;&nbsp;&nbsp;รหัสไปรษณีย์ {val_or_dots(zipcode, '........................')} "
        f"หมายเลขโทรศัพท์ {val_or_dots(phone, '................................................')}"
    )
    story.append(Paragraph(item_4a, line_style))
    story.append(Paragraph(item_4b, line_style))
    story.append(Paragraph(item_4c, line_style))

    # Item 5: โรงเรียนเดิม
    curr_grade = applicant.get('current_grade') or ('ม.3' if level == 'ปวช.' else 'ปวช.3 / ม.6')
    school_name = applicant.get('prev_school', '')
    sch_no = applicant.get('school_address_no', '')
    sch_tambon = applicant.get('school_tambon', '')
    sch_amphur = applicant.get('school_amphur', '')
    sch_prov = applicant.get('school_province') or applicant.get('prev_school_province', '')
    gpax = applicant.get('gpax', '')
    curr_major = applicant.get('current_major', '')

    item_5a = (
        f"๕. กำลังศึกษาอยู่ในระดับชั้น {val_or_dots(curr_grade, '...............................')} "
        f"โรงเรียน {val_or_dots(school_name, '..................................................................')}"
    )
    item_5b = (
        f"&nbsp;&nbsp;&nbsp;&nbsp;ตั้งอยู่เลขที่ {val_or_dots(sch_no, '.....................')} "
        f"ตำบล {val_or_dots(sch_tambon, '................................')} "
        f"อำเภอ {val_or_dots(sch_amphur, '................................')} "
        f"จังหวัด {val_or_dots(sch_prov, '.....................')}"
    )
    item_5c = (
        f"&nbsp;&nbsp;&nbsp;&nbsp;ผลการเรียนเฉลี่ยสะสม {val_or_dots(gpax, '...................................')} "
        f"สาขาวิชา {val_or_dots(curr_major, '....................................................................')}"
    )
    story.append(Paragraph(item_5a, line_style))
    story.append(Paragraph(item_5b, line_style))
    story.append(Paragraph(item_5c, line_style))

    # Item 6: สาขาวิชาที่ต้องการสมัคร
    major_name = applicant.get('major_name', '')
    major_second = applicant.get('major_second_choice', '')

    dip_major = major_name if level == "ปวส." else ""
    voc_major_1 = major_name if level == "ปวช." else ""
    voc_major_2 = major_second if level == "ปวช." else ""

    item_6a = f"๖. ต้องการสมัครเข้าเรียน ระดับ ปวส. สาขาวิชา {val_or_dots(dip_major, '..............................................................................')}"
    item_6b = f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ระดับ ปวช. สาขาวิชาลำดับที่ ๑. {val_or_dots(voc_major_1, '...................................................................')}"
    item_6c = f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;สาขาวิชาลำดับที่ ๒. {val_or_dots(voc_major_2, '...................................................................')}"
    story.append(Paragraph(item_6a, line_style))
    story.append(Paragraph(item_6b, line_style))
    story.append(Paragraph(item_6c, line_style))
    story.append(Spacer(1, 0.3*cm))

    # ---------------------------------------------------------
    # 4. Required Documents Checklist
    # ---------------------------------------------------------
    docs_html = (
        "<b>หลักฐานประกอบการสมัคร</b> "
        "๑. เอกสารแสดงผลการเรียนเฉลี่ยสะสม ๕ ภาคเรียน จำนวน ๑ ฉบับ<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "๒. สำเนาบัตรประชาชน / สำเนาทะเบียนบ้าน จำนวน ๑ ฉบับ<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "๓. สำเนาเกียรติบัตร/ใบรับรองความสามารถพิเศษ/ใบประกาศ (ถ้ามี)"
    )
    story.append(Paragraph(docs_html, line_style))
    story.append(Spacer(1, 0.4*cm))

    # ---------------------------------------------------------
    # 5. Signatures (Applicant)
    # ---------------------------------------------------------
    now = datetime.now()
    cur_d = str(now.day)
    cur_m = THAI_MONTHS[now.month]
    cur_y = str(now.year + 543)

    sig_html = (
        f"ลงชื่อ ......................................................... ผู้สมัคร<br/>"
        f"( {val_or_dots(full_name, '.........................................................')} )<br/>"
        f"วันที่ {cur_d} เดือน {cur_m} พ.ศ. {cur_y}"
    )

    # Place QR Code and Applicant ID at Bottom Left for verification audit
    qr_url = f"{base_url}/status?national_id={applicant['national_id']}"
    qr_path = generate_qr_image(qr_url)
    qr_img = RLImage(qr_path, width=1.6*cm, height=1.6*cm)

    bottom_table = Table(
        [
            [
                qr_img,
                Paragraph(f"<font size=8 color='#64748b'>เลขที่ใบสมัคร: <b>{applicant['id']}</b><br/>สแกนตรวจสอบสถานะออนไลน์</font>", ParagraphStyle('QRSub', fontName='Sarabun', fontSize=8, leading=11)),
                Paragraph(sig_html, right_sig_style)
            ]
        ],
        colWidths=[1.8*cm, 6.2*cm, 10.0*cm]
    )
    bottom_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
    ]))
    story.append(bottom_table)

    doc.build(story)
    return output_path

def generate_enrollment_pdf(applicant: dict, enrollment: dict, output_path: str, base_url: str = "http://localhost:8000"):
    """
    Generates official A4 Student Enrollment & Contract Form (ใบมอบตัวและสัญญาการเป็นนักศึกษา)
    วิทยาลัยเทคนิคท่าหลวงซิเมนต์ไทยอนุสรณ์
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('ThaiTitle', fontName='Sarabun-Bold', fontSize=16, leading=21, alignment=1, textColor=colors.HexColor('#065f46'))
    subtitle_style = ParagraphStyle('ThaiSub', fontName='Sarabun', fontSize=11, leading=15, alignment=1, textColor=colors.HexColor('#475569'))
    section_title = ParagraphStyle('Sec', fontName='Sarabun-Bold', fontSize=12, leading=16, textColor=colors.HexColor('#047857'), spaceBefore=8, spaceAfter=4)
    normal_style = ParagraphStyle('Norm', fontName='Sarabun', fontSize=10, leading=15, textColor=colors.black)
    body_style = ParagraphStyle('Body', fontName='Sarabun', fontSize=10, leading=15, alignment=4) # Justified

    story = []

    # Header
    story.append(Paragraph("<b>วิทยาลัยเทคนิคท่าหลวงซิเมนต์ไทยอนุสรณ์</b>", title_style))
    story.append(Paragraph("<b>ใบมอบตัวและสัญญาการเป็นนักเรียน นักศึกษา ประจำปีการศึกษา ๒๕๖๘</b>", title_style))
    story.append(Paragraph(f"เลขที่ใบสมัคร: {applicant['id']} &nbsp;|&nbsp; วันที่ทำสัญญา: {enrollment.get('enrollment_date') or applicant['created_at'][:10]}", subtitle_style))
    story.append(Spacer(1, 0.4*cm))

    # Assigned Student ID Banner
    student_id = enrollment.get('student_id') or "รอออกรหัสในวันมอบตัว"
    id_box = [
        [
            Paragraph(f"<b>รหัสประจำตัวนักเรียน/นักศึกษา:</b> <font size=14 color='#065f46'><b>{student_id}</b></font>", ParagraphStyle('ID', fontName='Sarabun-Bold', fontSize=12, alignment=1)),
            Paragraph(f"<b>ระดับ:</b> {applicant['level']} &nbsp;&nbsp; <b>สาขาวิชา:</b> {applicant['major_name']}", ParagraphStyle('ID2', fontName='Sarabun', fontSize=11, alignment=1))
        ]
    ]
    id_table = Table(id_box, colWidths=[8.5*cm, 8.5*cm])
    id_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ecfdf5')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#10b981')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(id_table)
    story.append(Spacer(1, 0.3*cm))

    # Student & Guardian Details
    story.append(Paragraph("1. ข้อมูลนักเรียน/นักศึกษา และ ผู้ปกครองผู้ทำสัญญา", section_title))
    details = [
        [
            Paragraph(f"<b>ชื่อ-นามสกุลนักศึกษา:</b> {applicant['title']}{applicant['first_name']} {applicant['last_name']}", normal_style),
            Paragraph(f"<b>เลขประจำตัวประชาชน:</b> {applicant['national_id']}", normal_style)
        ],
        [
            Paragraph(f"<b>ชื่อ-สกุลผู้ปกครองผู้มอบตัว:</b> {enrollment.get('guardian_name') or applicant.get('parent_name')}", normal_style),
            Paragraph(f"<b>ความเกี่ยวข้อง:</b> {enrollment.get('guardian_relation') or applicant.get('parent_relation')}", normal_style)
        ],
        [
            Paragraph(f"<b>เบอร์โทรศัพท์ผู้ปกครอง:</b> {enrollment.get('guardian_phone') or applicant.get('parent_phone')}", normal_style),
            Paragraph(f"<b>สถานะการชำระเงิน/เงินประกัน:</b> {enrollment.get('payment_status') or 'เรียบร้อย'}", normal_style)
        ]
    ]
    det_table = Table(details, colWidths=[9*cm, 8*cm])
    det_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(det_table)
    story.append(Spacer(1, 0.2*cm))

    # Terms & Conditions
    story.append(Paragraph("2. ข้อตกลงและระเบียบปฏิบัติของสถานศึกษา", section_title))
    terms_text = (
        "ข้าพเจ้า (ผู้ปกครอง) ได้นำนักเรียน/นักศึกษาผู้นี้ เข้ามอบตัวเพื่อเข้าศึกษาต่อในสถานศึกษา และสัญญาว่าจะกำกับดูแลให้นักเรียน/นักศึกษาปฏิบัติตามระเบียบ วินัย และข้อบังคับของสถานศึกษาอย่างเคร่งครัด "
        "ทั้งในเรื่องการแต่งกาย การเข้าเรียน ความประพฤติ และไม่ยุ่งเกี่ยวกับสิ่งเสพติดหรือการก่อเหตุทะเลาะวิวาทใดๆ ทั้งสิ้น "
        "หากนักเรียน/นักศึกษาฝ่าฝืนระเบียบสถานศึกษา ข้าพเจ้ายินยอมให้ทางสถานศึกษาดำเนินการลงโทษตามระเบียบ หรือพิจารณาให้พ้นสภาพจากการเป็นนักเรียน/นักศึกษาตามขั้นตอนของสถานศึกษาต่อไป"
    )
    story.append(Paragraph(terms_text, body_style))
    story.append(Spacer(1, 0.5*cm))

    # Signatures
    story.append(Paragraph("3. ลายมือชื่อผู้ทำสัญญาและเจ้าหน้าที่", section_title))
    sig_data = [
        [
            Paragraph("ลงชื่อ .............................................................. นักเรียน/นักศึกษา<br/>( .............................................................. )", ParagraphStyle('S1', fontName='Sarabun', fontSize=9, leading=15, alignment=1)),
            Paragraph("ลงชื่อ .............................................................. ผู้ปกครองผู้มอบตัว<br/>( .............................................................. )", ParagraphStyle('S2', fontName='Sarabun', fontSize=9, leading=15, alignment=1))
        ],
        [
            Paragraph("<br/>ลงชื่อ .............................................................. พยานฝ่ายสถานศึกษา<br/>( .............................................................. )", ParagraphStyle('S3', fontName='Sarabun', fontSize=9, leading=15, alignment=1)),
            Paragraph("<br/>ลงชื่อ .............................................................. นายทะเบียน/ผู้อำนวยการ<br/>( .............................................................. )", ParagraphStyle('S4', fontName='Sarabun', fontSize=9, leading=15, alignment=1))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[8.5*cm, 8.5*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(sig_table)

    doc.build(story)
    return output_path
