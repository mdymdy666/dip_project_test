# 身份证鲁棒性测试 PPT 追加说明

## PPT 修改内容
- 基础文件：`E:\OpenCVProjects\tansyqinyrproj\outputs\manual-20260605\presentations\dip-recognition\output\身份证车牌识别数字图像处理答辩_中间交付版.pptx`
- 输出文件：`E:\OpenCVProjects\tansyqinyrproj\outputs\manual-20260605\presentations\dip-recognition\output\身份证车牌识别数字图像处理答辩_身份证鲁棒性测试版.pptx`
- 原 PPT 页数：18
- 新增鲁棒性测试页数：9
- 更新后页数：27

## 新增章节内容
1. 身份证识别鲁棒性测试封面与总体结论
2. 测试数据来源与生成补充样本说明
3. 身份证识别流程与证据链
4. 扰动类型与参数设计
5. 按用户模板生成的鲁棒性测试汇总表
6. 定位成功率与 OCR 准确率统计图
7. 正常光照成功案例
8. 倾斜与噪声失败案例
9. 薄弱点与改进方向

## 证据要求对应
- 每页均嵌入 `UserShow/IdcardRobustness/ppt_assets/` 或 `datas/` 下的实际截图/表格。
- 失败样例未隐藏，已展示倾斜、噪声、遮挡等失败证据。
- 测试结论来自 `tables/idcard_robustness_summary_template.csv` 与 `tables/idcard_robustness_detail.csv`，未编造识别结果。

## 可继续检查的文件
- 汇总表：`tables/idcard_robustness_summary_template.csv`
- 明细表：`tables/idcard_robustness_detail.csv`
- 验证截图：`verification_screenshots/`
- 生成测试图片：`robustness_generated/`
- PPT 页面源图：`ppt_slides/`
