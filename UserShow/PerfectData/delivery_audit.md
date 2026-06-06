# PerfectData 交付前审查报告

- 审查时间：2026-06-06 12:42:04
- 审查目录：`E:\OpenCVProjects\tansyqinyrproj\dip_project_te\UserShow\PerfectData`
- 文件总数：1236
- 总大小：51.68 MB
- 图片可打开数量：1221
- 审查结论：通过

## 目录与数量核对
- idcard/raw_generated png: 26
- idcard/final_images png: 26
- idcard/processed_steps sample dirs: 26
- idcard/recognition_screenshots png: 26
- plate/raw_generated png: 100
- plate/final_images png: 100
- plate/processed_steps sample dirs: 100
- plate/recognition_screenshots png: 100

## 文件类型统计
- `.csv`: 6
- `.json`: 4
- `.md`: 5
- `.png`: 1221

## CSV 表格核对
- `tables/idcard_ground_truth.csv`: 26 行，字段：sample_id, raw_image, expected, expected_name, condition，空白行：0
- `tables/idcard_recognition_results.csv`: 26 行，字段：sample_id, input_path, expected, recognized, expected_name, recognized_name, condition, id_number_correct, name_correct, elapsed_ms, error_type, raw_image, final_image, recognition_screenshot, processed_dir, overall_correct，空白行：0
- `tables/idcard_success_cases.csv`: 26 行，字段：sample_id, input_path, expected, recognized, expected_name, recognized_name, condition, id_number_correct, name_correct, elapsed_ms, error_type, raw_image, final_image, recognition_screenshot, processed_dir, overall_correct，空白行：0
- `tables/plate_ground_truth.csv`: 100 行，字段：sample_id, raw_image, expected_plate, province, city_letter, tail, condition, generation_params，空白行：0
- `tables/plate_recognition_results.csv`: 100 行，字段：sample_id, raw_image, final_image, recognition_screenshot, processed_dir, expected_plate, recognized_plate, province, city_letter, tail, condition, detected, format_valid, province_correct, overall_correct, avg_confidence, bbox, elapsed_ms, error_type, generation_params，空白行：0
- `tables/plate_success_cases.csv`: 100 行，字段：sample_id, raw_image, final_image, recognition_screenshot, processed_dir, expected_plate, recognized_plate, province, city_letter, tail, condition, detected, format_valid, province_correct, overall_correct, avg_confidence, bbox, elapsed_ms, error_type, generation_params，空白行：0

## 风险项检查
- PPT 文件：未发现
- 敏感字段：未发现 token/password/secret/cookie 等配置字段
- 图片可读性：全部可打开
- 失败样例隔离：PerfectData 仅收录稳定好结果，内部诊断样例位于 `UserShow/InternalDiagnosis/`

## 问题
- 未发现阻塞交付的问题。

## 提醒
- 未发现需要特别提醒的命名或格式问题。
