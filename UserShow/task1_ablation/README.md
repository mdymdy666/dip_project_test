# task1 消融实验：用多种策略论证改进有效性

## 任务意图

参考用户给出的“定量实验设计”截图，本轮对身份证识别流程做 A-E 五组消融实验，用同一批 `UserShow/task1` 测试图验证每一步处理是否带来可量化改进。

## 实验数据

- 数据来源：`UserShow/task1/images/all_samples/`
- 样本数：52
- 评估字段：身份证号 `CARD_NUM`
- 评估口径：定位成功率、OCR 字符准确率、完全正确数、平均耗时、主要失败类型

## 实验组

| 实验组 | 处理流程 | 说明 |
|---|---|---|
| A 对照组 | 直接 OCR | 原图整图输入 OCR，容易受背景干扰 |
| B | 灰度 + 二值 | 降低颜色干扰，但字符断裂/噪声仍明显 |
| C | B + 形态学 | 尝试连接字符区域、消除小噪点 |
| D | C + 轮廓筛选 | 使用长宽比和面积筛选候选身份证号区域 |
| E 完整流程 | D + ROI + 校正 + 白名单 OCR + 格式校验 | 在公平口径下只评估身份证号码字段 |

## 汇总结果

详见：

- `tables/ablation_summary.csv`
- `tables/ablation_detection_records.csv`
- `charts/ablation_quantitative_design_table.png`
- `charts/ablation_metric_trend.png`
- `step_result_cards/`

## 成功案例

成功案例位于：

```text
selected_success_cases/
selected_for_upload/
```

这些案例展示完整流程在候选区域、ROI 校正和 OCR 输出上的稳定性。

## 少量失败案例

失败/边界案例位于：

```text
selected_failure_cases/
```

这些图片保留用于说明低质图片、严重噪声、角度或字符退化仍会影响 OCR，未被包装成成功结果。

## 结论

消融实验不是为了宣称所有样本 100% 成功，而是为了证明：从直接 OCR 到 ROI 校正、字符白名单和格式校验，处理链路逐步减少背景干扰、噪声断裂和误检区域问题。最终展示材料优先选取成功案例，同时保留少量失败案例作为边界说明。
