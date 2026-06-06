# 数据集说明

## 样本数量
- 身份证好结果样本：26
- 车牌好结果样本：100

## 数据来源
- 身份证：由项目辅助脚本生成的虚拟居民身份证样本，标识移至非关键区域，避免遮挡 OCR 字段。
- 车牌：由车牌专项修复流程生成的标准虚拟蓝牌样本。

## 虚拟数据说明
所有身份证号、姓名、地址和车牌号均为课程实验用虚拟数据，不对应真实个人或真实车辆登记信息。

## 文件命名规则
- 身份证：`SID001_raw.png`、`SID001_final.png`、`idcard/processed_steps/SID001/01_original.png`。
- 车牌：`plate_001_*.png`、`plate_001_result.png`、`plate/processed_steps/PL001/01_original.png`。

## Ground Truth 保存方式
- 身份证 ground truth：`tables/idcard_ground_truth.csv`
- 身份证识别结果：`tables/idcard_recognition_results.csv`
- 车牌 ground truth：`tables/plate_ground_truth.csv`
- 车牌识别结果：`tables/plate_recognition_results.csv`

## 当前筛选标准
PerfectData 只收录截图清晰、识别输出与 ground truth 匹配、适合中间展示的样例。身份证筛选号码和姓名均匹配；车牌筛选车牌号完全匹配且格式校验通过。
