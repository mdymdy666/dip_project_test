import cv2
import pytesseract
import os
import sys

# 设置 Tesseract 路径
pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'D:\Program Files\Tesseract-OCR\tessdata'

# 添加 core 目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ocr():
    print("=== Test OCR Function ===")
    
    # Test 1: Check Tesseract version
    try:
        version = pytesseract.get_tesseract_version()
        print("[OK] Tesseract version:", version)
    except Exception as e:
        print("[FAIL] Failed to get Tesseract version:", str(e))
        return False
    
    # Test 2: Check available languages
    try:
        langs = pytesseract.get_languages()
        print("[OK] Available languages:", langs)
    except Exception as e:
        print("[FAIL] Failed to get languages:", str(e))
        return False
    
    # Test 3: Test OCR with core module
    try:
        import core.main as core_main
        
        test_image_path = 'firstend/dist/static/img/50.a3e9ea7.jpg'
        if os.path.exists(test_image_path):
            print("[OK] Testing OCR with core module...")
            result = core_main.ocr_main(test_image_path)
            print("[OK] OCR result:", result)
        else:
            print("[FAIL] Test image not found:", test_image_path)
            return False
            
    except Exception as e:
        print("[FAIL] OCR with core module failed:", str(e))
        import traceback
        traceback.print_exc()
        return False
    
    print("\n=== OCR Function Test PASSED ===")
    return True

if __name__ == "__main__":
    success = test_ocr()
    exit(0 if success else 1)
