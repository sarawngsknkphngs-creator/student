/**
 * Thai National ID Modulus-11 Validator
 */
function validateThaiNationalID(idStr) {
    if (!idStr || typeof idStr !== 'string') return false;
    const cleanId = idStr.replace(/[^0-9]/g, '');
    if (cleanId.length !== 13) return false;

    // Reject all same digits like 1111111111111 or 0000000000000
    if (/^(\d)\1{12}$/.test(cleanId)) return false;

    let sum = 0;
    for (let i = 0; i < 12; i++) {
        sum += parseInt(cleanId.charAt(i), 10) * (13 - i);
    }
    const checkDigit = (11 - (sum % 11)) % 10;
    return checkDigit === parseInt(cleanId.charAt(12), 10);
}

/**
 * Thai Phone Number Validator (10 digits starting with 0)
 */
function validateThaiPhone(phoneStr) {
    if (!phoneStr) return false;
    const cleanPhone = phoneStr.replace(/[^0-9]/g, '');
    return /^0[689]\d{8}$/.test(cleanPhone) || /^0[2-57]\d{7,8}$/.test(cleanPhone);
}

/**
 * Format Thai ID with dashes: 1-2345-67890-12-3
 */
function formatThaiID(idStr) {
    const clean = idStr.replace(/[^0-9]/g, '').slice(0, 13);
    let formatted = '';
    if (clean.length > 0) formatted += clean.substring(0, 1);
    if (clean.length > 1) formatted += '-' + clean.substring(1, 5);
    if (clean.length > 5) formatted += '-' + clean.substring(5, 10);
    if (clean.length > 10) formatted += '-' + clean.substring(10, 12);
    if (clean.length > 12) formatted += '-' + clean.substring(12, 13);
    return formatted;
}

/**
 * Format Phone: 081-234-5678
 */
function formatPhone(phoneStr) {
    const clean = phoneStr.replace(/[^0-9]/g, '').slice(0, 10);
    if (clean.length <= 3) return clean;
    if (clean.length <= 6) return clean.slice(0, 3) + '-' + clean.slice(3);
    return clean.slice(0, 3) + '-' + clean.slice(3, 6) + '-' + clean.slice(6);
}

// Global hook for forms
document.addEventListener('DOMContentLoaded', () => {
    // 1. National ID Input Listener
    const nationalIdInputs = document.querySelectorAll('.thai-id-input');
    nationalIdInputs.forEach(input => {
        const feedbackEl = document.getElementById(input.dataset.feedbackId || 'idFeedback');
        input.addEventListener('input', (e) => {
            const rawVal = input.value.replace(/[^0-9]/g, '');
            input.value = rawVal; // Keep numeric

            if (rawVal.length === 0) {
                if (feedbackEl) {
                    feedbackEl.className = 'text-xs mt-1 text-slate-500';
                    feedbackEl.innerText = 'เลขประจำตัวประชาชน 13 หลัก';
                }
                input.classList.remove('border-red-500', 'border-emerald-500');
                return;
            }

            if (rawVal.length < 13) {
                if (feedbackEl) {
                    feedbackEl.className = 'text-xs mt-1 text-amber-600 font-medium';
                    feedbackEl.innerText = `กรอกอีก ${13 - rawVal.length} หลัก (${rawVal.length}/13)`;
                }
                input.classList.add('border-amber-400');
                input.classList.remove('border-red-500', 'border-emerald-500');
            } else if (rawVal.length === 13) {
                const isValid = validateThaiNationalID(rawVal);
                if (isValid) {
                    if (feedbackEl) {
                        feedbackEl.className = 'text-xs mt-1 text-emerald-600 font-medium flex items-center gap-1';
                        feedbackEl.innerHTML = '✓ เลขประจำตัวประชาชนถูกต้อง';
                    }
                    input.classList.remove('border-amber-400', 'border-red-500');
                    input.classList.add('border-emerald-500');
                } else {
                    if (feedbackEl) {
                        feedbackEl.className = 'text-xs mt-1 text-red-600 font-medium flex items-center gap-1';
                        feedbackEl.innerHTML = '✕ เลขบัตรประชาชนไม่ถูกต้อง (ตามสูตรคำนวณสำนักทะเบียน)';
                    }
                    input.classList.remove('border-amber-400', 'border-emerald-500');
                    input.classList.add('border-red-500');
                }
            }
        });
    });

    // 2. Phone input listener
    const phoneInputs = document.querySelectorAll('.thai-phone-input');
    phoneInputs.forEach(input => {
        input.addEventListener('input', () => {
            input.value = input.value.replace(/[^0-9]/g, '').slice(0, 10);
        });
    });

    // 3. File Preview and Validation Listener
    const fileInputs = document.querySelectorAll('.validated-file-input');
    fileInputs.forEach(input => {
        const previewId = input.dataset.previewId;
        const previewEl = previewId ? document.getElementById(previewId) : null;
        const errorEl = document.getElementById(input.dataset.errorId || '');

        input.addEventListener('change', () => {
            const file = input.files[0];
            if (!file) return;

            // Check size (Max 5MB)
            const maxSize = 5 * 1024 * 1024;
            if (file.size > maxSize) {
                alert(`ไฟล์ "${file.name}" มีขนาดใหญ่เกินไป (${(file.size / (1024*1024)).toFixed(1)}MB) กรุณาใช้ไฟล์ขนาดไม่เกิน 5MB`);
                input.value = '';
                if (previewEl) previewEl.classList.add('hidden');
                return;
            }

            // Check type
            const allowed = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
            if (!allowed.includes(file.type)) {
                alert(`ไม่อนุญาตให้อัปโหลดไฟล์ประเภทนี้ (${file.name})\nกรุณาใช้ไฟล์ภาพ JPG, PNG หรือเอกสาร PDF เท่านั้น`);
                input.value = '';
                if (previewEl) previewEl.classList.add('hidden');
                return;
            }

            // Preview image
            if (previewEl && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    previewEl.src = e.target.result;
                    previewEl.classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            }
        });
    });
});
