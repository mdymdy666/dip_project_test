# 数据集与测试样本说明

## 样本来源

- 原始样本来自项目根目录 `datas/`。
- 补充测试样本由脚本 `scripts/idcard_robustness_test.py` 基于 `datas/normal.png` 生成，仅用于鲁棒性测试。
- 本轮没有使用真实个人隐私数据；样本为课程测试用虚拟身份证图片。

## 样本数量

| 类型 | 数量 | 保存目录 | 说明 |
|---|---:|---|---|
| 原始身份证样本 | 6 | `source_datas/` | 正常光照、偏暗、过曝、加噪声、倾斜 10°、低分辨率 |
| 生成扰动样本 | 16 | `robustness_generated/` | 基于正常样本生成的亮度、噪声、模糊、旋转等扰动 |
| 验证截图 | 22 | `verification_screenshots/` | 每个样本一张完整运行证据图 |
| 中间处理目录 | 22 | `processed_steps/` | 每个样本包含输入、灰度、二值化、形态学/候选区域等图像 |

## 扰动覆盖

本轮覆盖：原图识别、亮度变化、对比度变化、高斯噪声、椒盐噪声、模糊处理、小角度旋转、缩放变化、透视变换或轻微倾斜、局部遮挡、图像裁剪、JPEG 压缩失真、组合扰动。

## Ground Truth 与结果记录

- 汇总表：`tables/idcard_robustness_summary_template.csv`。
- 逐样本结果：`tables/idcard_robustness_detail.csv`。
- 机器可读 JSON：`tables/idcard_robustness_results.json`。
- 文件清单与校验：`tables/file_manifest.csv`。

## 统计口径

- “定位成功”指程序能够定位身份证号码候选区域。
- “OCR 准确”指身份证号码字段与期望号码完全一致。
- 定位成功不等于 OCR 成功，两项在表格中分开统计。
