import os
import qrcode
from io import BytesIO
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
    file_path = f"d:/sk/static/generated_pdfs/qr/qr_{hash(data_text)}.png"
    img.save(file_path)
    return file_path

def generate_application_pdf(applicant: dict, output_path: str, base_url: str = "http://localhost:8000"):
    """
    Generates official A4 Application Form (ใบสมัครเข้าศึกษาต่อ)
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
    
    title_style = ParagraphStyle(
        'ThaiTitle',
        fontName='Sarabun-Bold',
        fontSize=18,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor('#1e3a8a')
    )
    subtitle_style = ParagraphStyle(
        'ThaiSubtitle',
        fontName='Sarabun',
        fontSize=12,
        leading=16,
        alignment=1,
        textColor=colors.HexColor('#475569')
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        fontName='Sarabun-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1e40af'),
        spaceBefore=6,
        spaceAfter=4
    )
    normal_style = ParagraphStyle(
        'ThaiNormal',
        fontName='Sarabun',
        fontSize=11,
        leading=15,
        textColor=colors.black
    )
    bold_style = ParagraphStyle(
        'ThaiBold',
        fontName='Sarabun-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.black
    )

    story = []

    # 1. Header with QR code and Applicant ID
    qr_url = f"{base_url}/status?national_id={applicant['national_id']}"
    qr_path = generate_qr_image(qr_url)
    
    # Top info table
    header_data = [
        [
            Paragraph("<b>วิทยาลัยอาชีวศึกษา (Vocational College)</b><br/>ระบบรับสมัครนักเรียน นักศึกษาใหม่ ประจำปีการศึกษา 2568", subtitle_style),
            RLImage(qr_path, width=1.8*cm, height=1.8*cm)
        ]
    ]
    header_table = Table(header_data, colWidths=[14*cm, 3*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT')
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3*cm))

    # Main Title Box
    story.append(Paragraph("<b>ใบสมัครเข้าศึกษาต่อ</b>", title_style))
    story.append(Paragraph(f"เลขที่ใบสมัคร: <b>{applicant['id']}</b> &nbsp;|&nbsp; วันที่สมัคร: {applicant['created_at'][:10]}", subtitle_style))
    story.append(Spacer(1, 0.4*cm))

    # 2. Level & Major Box
    choice_data = [
        [
            Paragraph(f"<b>ระดับชั้นที่สมัคร:</b> {applicant['level']}", normal_style),
            Paragraph(f"<b>สาขาวิชาที่เลือก:</b> {applicant['major_name']} (รหัส: {applicant['major_code']})", normal_style)
        ]
    ]
    choice_table = Table(choice_data, colWidths=[6.5*cm, 10.5*cm])
    choice_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(choice_table)
    story.append(Spacer(1, 0.3*cm))

    # 3. Personal Information
    story.append(Paragraph("1. ข้อมูลส่วนตัวของผู้สมัคร", section_title))
    
    # Check if photo exists
    photo_cell = Paragraph("<br/><br/>[ติดรูปถ่าย<br/>1 - 1.5 นิ้ว]", ParagraphStyle('PBox', fontName='Sarabun', fontSize=10, alignment=1, textColor=colors.gray))
    if applicant.get('photo_path') and os.path.exists(applicant['photo_path']):
        try:
            photo_cell = RLImage(applicant['photo_path'], width=2.8*cm, height=3.6*cm)
        except Exception:
            pass

    personal_rows = [
        [
            Paragraph(f"<b>ชื่อ-นามสกุล:</b> {applicant['title']}{applicant['first_name']} {applicant['last_name']}", normal_style),
            Paragraph(f"<b>เลขประจำตัวประชาชน:</b> {applicant['national_id']}", normal_style),
            photo_cell
        ],
        [
            Paragraph(f"<b>วัน/เดือน/ปีเกิด:</b> {applicant['birth_date']}", normal_style),
            Paragraph(f"<b>เพศ:</b> {applicant['gender']} &nbsp;&nbsp; <b>ศาสนา:</b> {applicant['religion']}", normal_style),
            ""
        ],
        [
            Paragraph(f"<b>เบอร์โทรศัพท์:</b> {applicant['phone']}", normal_style),
            Paragraph(f"<b>อีเมล:</b> {applicant.get('email') or '-'}", normal_style),
            ""
        ],
        [
            Paragraph(f"<b>ที่อยู่ปัจจุบัน:</b> {applicant.get('address_no','')} ม.{applicant.get('moo','-')} ต.{applicant.get('tambon','')} อ.{applicant.get('amphur','')} จ.{applicant.get('province','')} {applicant.get('zipcode','')}", normal_style),
            "",
            ""
        ]
    ]
    personal_table = Table(personal_rows, colWidths=[7*cm, 7*cm, 3*cm])
    personal_table.setStyle(TableStyle([
        ('SPAN', (2,0), (2,2)), # Photo spans 3 rows
        ('SPAN', (0,3), (1,3)), # Address spans 2 columns
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BOX', (2,0), (2,2), 0.5, colors.HexColor('#94a3b8')),
    ]))
    story.append(personal_table)
    story.append(Spacer(1, 0.2*cm))

    # 4. Educational Background
    story.append(Paragraph("2. ข้อมูลการศึกษาเดิม", section_title))
    edu_data = [
        [
            Paragraph(f"<b>สำเร็จการศึกษาจากโรงเรียน:</b> {applicant.get('prev_school') or '-'}", normal_style),
            Paragraph(f"<b>จังหวัด:</b> {applicant.get('prev_school_province') or '-'}", normal_style),
            Paragraph(f"<b>เกรดเฉลี่ย (GPAX):</b> {applicant.get('gpax') or '-'}", normal_style)
        ]
    ]
    edu_table = Table(edu_data, colWidths=[8*cm, 5*cm, 4*cm])
    edu_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(edu_table)
    story.append(Spacer(1, 0.2*cm))

    # 5. Parent / Guardian Info
    story.append(Paragraph("3. ข้อมูลผู้ปกครอง & ช่องทางการรับรู้", section_title))
    parent_data = [
        [
            Paragraph(f"<b>ชื่อ-สกุลผู้ปกครอง:</b> {applicant.get('parent_name') or '-'}", normal_style),
            Paragraph(f"<b>ความสัมพันธ์:</b> {applicant.get('parent_relation') or '-'}", normal_style),
            Paragraph(f"<b>เบอร์โทรผู้ปกครอง:</b> {applicant.get('parent_phone') or '-'}", normal_style)
        ],
        [
            Paragraph(f"<b>ช่องทางที่รู้จักวิทยาลัย:</b> {applicant.get('referral_source') or '-'}", normal_style),
            Paragraph(f"<b>ครูแนะแนว/ผู้แนะนำ:</b> {applicant.get('referral_teacher') or '-'}", normal_style),
            ""
        ]
    ]
    parent_table = Table(parent_data, colWidths=[7*cm, 5*cm, 5*cm])
    parent_table.setStyle(TableStyle([
        ('SPAN', (1,1), (2,1)),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(parent_table)
    story.append(Spacer(1, 0.4*cm))

    # 6. Applicant Statement & Signatures
    story.append(Paragraph("<b>คำรับรอง:</b> ข้าพเจ้าขอรับรองว่าข้อมูลและเอกสารหลักฐานที่ยื่นไว้เป็นความจริงทุกประการ หากตรวจสอบพบว่าเป็นเท็จ ข้าพเจ้ายินยอมให้ตัดสิทธิ์การเข้าศึกษาต่อทันที", ParagraphStyle('Notice', fontName='Sarabun', fontSize=9, leading=13, textColor=colors.HexColor('#334155'))))
    story.append(Spacer(1, 0.5*cm))

    sig_data = [
        [
            Paragraph("ลงชื่อ .............................................................. ผู้สมัคร<br/>( .............................................................. )<br/>วันที่ ........ / .................... / ...........", ParagraphStyle('Sig', fontName='Sarabun', fontSize=10, leading=16, alignment=1)),
            Paragraph("ลงชื่อ .............................................................. ผู้รับสมัคร/เจ้าหน้าที่<br/>( .............................................................. )<br/>วันที่ ........ / .................... / ...........", ParagraphStyle('Sig', fontName='Sarabun', fontSize=10, leading=16, alignment=1))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[8.5*cm, 8.5*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(sig_table)

    doc.build(story)
    return output_path

def generate_enrollment_pdf(applicant: dict, enrollment: dict, output_path: str, base_url: str = "http://localhost:8000"):
    """
    Generates official A4 Student Enrollment & Contract Form (ใบมอบตัวและสัญญาการเป็นนักศึกษา)
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
    title_style = ParagraphStyle('ThaiTitle', fontName='Sarabun-Bold', fontSize=17, leading=22, alignment=1, textColor=colors.HexColor('#065f46'))
    subtitle_style = ParagraphStyle('ThaiSub', fontName='Sarabun', fontSize=11, leading=15, alignment=1, textColor=colors.HexColor('#475569'))
    section_title = ParagraphStyle('Sec', fontName='Sarabun-Bold', fontSize=12, leading=16, textColor=colors.HexColor('#047857'), spaceBefore=8, spaceAfter=4)
    normal_style = ParagraphStyle('Norm', fontName='Sarabun', fontSize=10, leading=15, textColor=colors.black)
    body_style = ParagraphStyle('Body', fontName='Sarabun', fontSize=10, leading=15, alignment=4) # Justified

    story = []

    # Header
    story.append(Paragraph("<b>วิทยาลัยอาชีวศึกษา (Vocational College)</b>", title_style))
    story.append(Paragraph("<b>ใบมอบตัวและสัญญาการเป็นนักเรียน นักศึกษา ประจำปีการศึกษา 2568</b>", title_style))
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
    story.append(Spacer(1, 0.6*cm))

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
