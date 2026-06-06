# PerfectData 联合交付自检

## 覆盖检查
- 已同时整理身份证和车牌，没有只整理车牌。
- 身份证包含原始生成图、最终图、处理步骤、识别截图、表格和分析。
- 车牌包含原始生成图、最终图、处理步骤、识别截图、表格和分析。
- `selected_showcase/` 包含可直接给协作者查看和后续 PPT 使用的精选图。

## 数据质量
- 身份证好结果：26。
- 车牌好结果：100。
- PerfectData 内未混入失败样例；身份证 4 个姓名边界样例已转入 `UserShow/InternalDiagnosis/`。

## 真实性
- 未伪造结果，表格保留 ground truth 与识别输出。
- 车牌 100/100 结论限定于标准虚拟蓝牌数据集，不宣称覆盖所有真实复杂场景。
- 身份证好结果只统计号码和姓名均匹配的样例，不把姓名失败样例放入 PerfectData。

## 文件结构
- `idcard/raw_generated/`
- `idcard/final_images/`
- `idcard/processed_steps/`
- `idcard/recognition_screenshots/`
- `idcard/selected_success_cases/`
- `plate/raw_generated/`
- `plate/final_images/`
- `plate/processed_steps/`
- `plate/recognition_screenshots/`
- `plate/selected_success_cases/`
- `tables/`
- `charts/`
- `selected_showcase/`
