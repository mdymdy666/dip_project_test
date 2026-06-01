import os
UPLOAD_FOLDER = r'./uploads'

# TESSERACT_OCR path
TESSERACT_OCR = r'D:\Program Files\Tesseract-OCR\tesseract.exe'
# 使用项目本地的 tessdata 目录（包含 eng、osd、chi_sim 语言包）
os.environ['TESSDATA_PREFIX'] = r'e:\OpenCVProjects\tansyqinyrproj\tessdata'

