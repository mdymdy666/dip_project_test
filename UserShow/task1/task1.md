# task1 身份证识别测试与样例整理

## 任务背景

本次任务聚焦项目中的身份证识别能力，以及识别结果能否形成“车主 - 身份证信息”的基础对应记录。按照要求，本轮不处理车辆牌照相关模块。

## 测试数据来源

- `datas/` 原有可单独测试身份证图片：6 张。
- `datas/robustness_grid.png` 是拼图总览，不作为单张 OCR 测试样本。
- 新增处理图片：46 张，保存于 `datas/task1_processed/`。
- AI 生成身份证图片数量：0 张。
- 最终参与测试图片总量：52 张。

## 数据收集或生成方式说明

用户要求不使用虚拟身份证生成器，因此本轮没有从外部采集真实身份证，也没有生成新的虚拟身份信息。补充图全部基于项目已有 `datas` 真实样式身份证图片进行图像处理得到，包括亮度变化、对比度变化、模糊、小角度旋转、缩放、低分辨率、局部裁剪、局部遮挡和复杂背景边框。

## 数据脱敏与隐私处理说明

本轮不收集、不保存、不上传真实个人身份证隐私信息。新增图仅由项目已有测试图片派生，且所有结果仅用于课程数字图像处理实验分析。文档中不宣称这些图片对应真实人员。

## 测试方法

测试脚本遍历本轮样本集，逐张调用项目身份证识别入口：

```text
core.main.ocr_main(path)
```

该入口内部执行灰度化、二值化、形态学处理、身份证号码候选区域定位和 OCR 识别。由于多数样本没有独立人工标注，本轮统计口径为“是否识别出可用 18 位身份证号码”，不虚构姓名、地址等全字段准确率。

## 统计结果

| 指标 | 数值 |
|---|---:|
| 最终测试图片总量 | 52 |
| 成功样例数 | 30 |
| 失败样例数 | 22 |
| 全量可用身份证号检出率 | 57.69% |
| 展示样例成功数 | 30 |
| 展示样例失败数 | 1 |
| 展示样例成功率 | 96.77% |

展示样例集位于 `selected_showcase/`，按要求以成功样例为主，仅放入少量失败样例用于问题分析；展示样例成功率不低于 95%。

## 成功样例说明

成功样例截图保存在：

```text
images/success/
selected_showcase/
```

成功样例通常来自清晰正面、轻微亮度变化、轻微旋转、轻微裁剪或弱模糊图片。识别出可用身份证号后，可形成车主身份基础记录，即 `owner_id_link_ready=True`。

## 失败样例说明

失败样例截图保存在：

```text
images/failure/
```

失败主要来自低分辨率、噪声、角度较大或关键区域退化等情况。失败样例没有混入成功展示结论，只用于说明系统边界。

## 图表引用

- `charts/source_count_chart.png`：原有 / 新增图片数量统计。
- `charts/success_failure_chart.png`：成功 / 失败数量统计。
- `charts/issue_type_performance_chart.png`：不同图片问题类型识别表现。
- `charts/failure_reason_chart.png`：失败原因分布。

## 结果数据文件

- `results/idcard_detection_results.csv`
- `results/idcard_detection_results.json`
- `results/success_cases.csv`
- `results/failure_cases.csv`
- `results/source_manifest.csv`
- `results/summary.json`

## 主要问题分析

1. 低分辨率会导致号码字符细节不足，OCR 更容易失败。
2. 噪声会破坏二值化后的字符连通性，使候选区域虽然存在但识别为空。
3. 倾斜或裁剪场景中，号码区域定位与 OCR 的误差会放大。
4. 仅凭检测成功不能等同于全字段准确，后续应加入人工标注或字段级 ground truth。

## 后续优化建议

1. 增加身份证外框检测与透视矫正，提升倾斜图片稳定性。
2. 在 OCR 前加入局部增强、去噪和小连通域过滤。
3. 对低分辨率样本加入最小输入尺寸检查或超分/锐化预处理。
4. 建立脱敏人工标注表，后续可统计姓名、号码、地址等字段级准确率。

## 本次生成的文件清单

```text
datas/task1_processed/
UserShow/task1/images/all_samples/
UserShow/task1/images/success/
UserShow/task1/images/failure/
UserShow/task1/results/
UserShow/task1/charts/
UserShow/task1/selected_showcase/
UserShow/task1/task1.md
tools/task1_id_recognition_dataset.py
```
