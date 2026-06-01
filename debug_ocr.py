import os
os.environ['TESSDATA_PREFIX'] = r'e:\OpenCVProjects\tansyqinyrproj\tessdata'
import cv2
import numpy as np
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'

# 测试图片路径
test_image_path = 'firstend/dist/static/img/50.a3e9ea7.jpg'

print(f"Testing OCR on: {test_image_path}")
print(f"File exists: {os.path.exists(test_image_path)}")

# 读取图片
img = cv2.imread(test_image_path)
if img is None:
    print("ERROR: 无法读取图片！")
else:
    print(f"图片尺寸: {img.shape}")
    
    # 转化成灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f"灰度图尺寸: {gray.shape}")
    
    # 测试直接OCR识别
    print("\n--- 直接OCR测试 ---")
    text = pytesseract.image_to_string(gray)
    print(f"直接识别结果: '{text}'")
    
    text_clean = ''.join(char for char in text if char.isalnum())
    print(f"清理后: '{text_clean}'")
    
    # 测试带参数的OCR
    print("\n--- 带参数OCR测试 ---")
    text_psm6 = pytesseract.image_to_string(gray, config='--psm 6')
    print(f"--psm 6 识别结果: '{text_psm6}'")
    
    text_psm8 = pytesseract.image_to_string(gray, config='--psm 8')
    print(f"--psm 8 识别结果: '{text_psm8}'")
    
    # 尝试二值化处理
    print("\n--- 二值化处理测试 ---")
    ret, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text_binary = pytesseract.image_to_string(binary, config='--psm 6')
    print(f"二值化后识别结果: '{text_binary}'")
    
    # 尝试形态学处理
    print("\n--- 形态学处理测试 ---")
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilation = cv2.dilate(binary, kernel, iterations=1)
    erosion = cv2.erode(dilation, kernel, iterations=1)
    text_morph = pytesseract.image_to_string(erosion, config='--psm 6')
    print(f"形态学处理后识别结果: '{text_morph}'")

print("\n--- 测试完成 ---")
