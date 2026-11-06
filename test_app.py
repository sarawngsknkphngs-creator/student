import os
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from starlette.testclient import TestClient
from main import app

client = TestClient(app)

def test_routes():
    print("Testing routes...")

    # 1. Home
    r = client.get("/")
    assert r.status_code == 200, f"Home failed: {r.status_code}"
    print("[OK] GET / (Home) OK")

    # 2. Apply page
    r = client.get("/apply")
    assert r.status_code == 200, f"Apply page failed: {r.status_code}"
    print("[OK] GET /apply OK")

    # 3. Status page
    r = client.get("/status")
    assert r.status_code == 200, f"Status failed: {r.status_code}"
    print("[OK] GET /status OK")

    # 4. Status with applicant
    r = client.get("/status?national_id=1100400123450")
    assert r.status_code == 200, f"Status check failed: {r.status_code}"
    assert "APP2568-0001" in r.text, "Applicant ID not in status page"
    print("[OK] GET /status?national_id=1100400123450 OK (Found applicant)")

    # 5. Application PDF generation
    r = client.get("/download/application-pdf/APP2568-0001")
    assert r.status_code == 200, f"Application PDF failed: {r.status_code}"
    assert len(r.content) > 1000, "PDF content too small"
    print(f"[OK] GET /download/application-pdf/APP2568-0001 OK ({len(r.content)} bytes)")

    # 6. Enrollment PDF generation
    r = client.get("/download/enrollment-pdf/APP2568-0001")
    assert r.status_code == 200, f"Enrollment PDF failed: {r.status_code}"
    assert len(r.content) > 1000, "Enrollment PDF too small"
    print(f"[OK] GET /download/enrollment-pdf/APP2568-0001 OK ({len(r.content)} bytes)")

    # 7. Admin Login
    login_data = {"username": "admin", "password": "admin123"}
    r = client.post("/admin/login", data=login_data, follow_redirects=False)
    assert r.status_code == 303, f"Admin login failed: {r.status_code}"
    cookies = r.cookies
    print("[OK] POST /admin/login OK (Session created)")

    # 8. Admin Dashboard
    r = client.get("/admin/dashboard", cookies=cookies)
    assert r.status_code == 200, f"Dashboard failed: {r.status_code}"
    print("[OK] GET /admin/dashboard OK")

    # 9. Admin Applicants List
    r = client.get("/admin/applicants", cookies=cookies)
    assert r.status_code == 200, f"Applicants list failed: {r.status_code}"
    print("[OK] GET /admin/applicants OK")

    # 10. Admin Applicant Detail
    r = client.get("/admin/applicant/APP2568-0001", cookies=cookies)
    assert r.status_code == 200, f"Applicant detail failed: {r.status_code}"
    print("[OK] GET /admin/applicant/APP2568-0001 OK")

    # 11. Admin Enrollment Page
    r = client.get("/admin/enrollment", cookies=cookies)
    assert r.status_code == 200, f"Enrollment page failed: {r.status_code}"
    print("[OK] GET /admin/enrollment OK")

    # 12. Export Excel (ศธ.02)
    r = client.get("/admin/export/std02-excel", cookies=cookies)
    assert r.status_code == 200, f"Export Excel failed: {r.status_code}"
    assert len(r.content) > 1000, "Excel content too small"
    print(f"[OK] GET /admin/export/std02-excel OK ({len(r.content)} bytes)")

    # 13. Export CSV (ศธ.02)
    r = client.get("/admin/export/std02-csv", cookies=cookies)
    assert r.status_code == 200, f"Export CSV failed: {r.status_code}"
    assert "\ufeff" in r.text, "UTF-8 BOM missing in CSV"
    print(f"[OK] GET /admin/export/std02-csv OK (BOM verified)")

    print("\nALL 13 TEST SUITES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_routes()
