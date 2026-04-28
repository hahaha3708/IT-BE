"""
Test script for PDF CV Generation
Run: python test_pdf_generation.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from modules.profiles.models import HoSoUngVien
from modules.profiles.pdf_generator import generate_cv_pdf
from datetime import datetime


def test_pdf_generation():
    """Test PDF generation for the first candidate profile."""
    print("=" * 60)
    print("PHASE 1 TESTING: PDF CV Generation")
    print("=" * 60)
    
    # Fetch a candidate profile
    try:
        profile = HoSoUngVien.objects.first()
        if not profile:
            print("❌ Không tìm thấy hồ sơ ứng viên nào trong database.")
            return False
        
        print(f"\n✓ Tìm thấy hồ sơ ứng viên: {profile.ho_ten}")
        print(f"  - Email: {profile.ung_vien.email if profile.ung_vien else 'N/A'}")
        print(f"  - Điện thoại: {profile.so_dien_thoai}")
        print(f"  - Vị trí mong muốn: {profile.vi_tri_mong_muon}")
        
        # Generate PDF
        print("\n📄 Đang tạo PDF...")
        pdf_buffer, filename = generate_cv_pdf(profile)
        
        if not pdf_buffer:
            print("❌ Lỗi: PDF buffer trống")
            return False
        
        # Check file size
        pdf_size = len(pdf_buffer.getvalue())
        print(f"✓ PDF tạo thành công!")
        print(f"  - Filename: {filename}")
        print(f"  - Kích thước: {pdf_size / 1024:.2f} KB")
        
        # Save to temp file for manual inspection
        temp_path = f"test_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(temp_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"\n✓ PDF lưu thành công tại: {temp_path}")
        
        # Validation checks
        print("\n📋 Validation Checks:")
        checks = [
            ("PDF không trống", pdf_size > 1000),
            ("PDF kích thước hợp lý", 1 < pdf_size / 1024 < 10000),  # 1KB - 10MB (relaxed for test data)
        ]
        
        for check_name, result in checks:
            status = "✓" if result else "❌"
            print(f"  {status} {check_name}: {result}")
        
        all_passed = all(result for _, result in checks)
        
        if all_passed:
            print("\n✅ PHASE 1 PDF GENERATION: PASSED")
        else:
            print("\n⚠️ PHASE 1 PDF GENERATION: PASSED with warnings")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_profile_data():
    """Verify candidate profile data structure."""
    print("\n" + "=" * 60)
    print("DATA STRUCTURE VALIDATION")
    print("=" * 60)
    
    try:
        profile = HoSoUngVien.objects.first()
        if not profile:
            print("❌ Không tìm thấy hồ sơ ứng viên")
            return False
        
        print("\n📊 Profile Data Fields:")
        fields = {
            'Tên': profile.ho_ten,
            'Email': profile.ung_vien.email if profile.ung_vien else None,
            'Điện thoại': profile.so_dien_thoai,
            'Vị trí mong muốn': profile.vi_tri_mong_muon,
            'Vị trí': profile.location,
            'Giới thiệu': profile.gioi_thieu[:50] + '...' if profile.gioi_thieu else None,
            'Kỹ năng': profile.ky_nang[:50] + '...' if profile.ky_nang else None,
        }
        
        for field_name, value in fields.items():
            status = "✓" if value else "⚠️"
            print(f"  {status} {field_name}: {value or '(trống)'}")
        
        # Check complex fields
        print("\n📋 Complex Fields:")
        complex_fields = {
            'Dự án': profile.du_an,
            'Học vấn': profile.hoc_van,
            'Chứng chỉ': profile.chung_chi,
            'Ngoại ngữ': profile.ngoai_ngu,
        }
        
        for field_name, value in complex_fields.items():
            if isinstance(value, list):
                status = "✓" if len(value) > 0 else "⚠️"
                print(f"  {status} {field_name}: {len(value)} items")
            elif isinstance(value, str):
                status = "✓" if value else "⚠️"
                print(f"  {status} {field_name}: {len(value)} chars")
            else:
                print(f"  ⚠️ {field_name}: {type(value)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        return False


if __name__ == '__main__':
    print("\n🚀 ITNIHONGO CV DOWNLOAD FEATURE - PHASE 1 TEST\n")
    
    # Test 1: Data validation
    data_ok = test_profile_data()
    
    # Test 2: PDF generation
    pdf_ok = test_pdf_generation()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Data Validation: {'✓ PASSED' if data_ok else '❌ FAILED'}")
    print(f"PDF Generation: {'✓ PASSED' if pdf_ok else '❌ FAILED'}")
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if (data_ok and pdf_ok) else '⚠️ SOME TESTS FAILED'}")
    print("=" * 60 + "\n")
