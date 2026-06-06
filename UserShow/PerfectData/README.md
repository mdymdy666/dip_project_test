# PerfectData 身份证 + 车牌中间交付包

## 本轮交付目标
统一整理身份证识别和车牌识别的好结果截图、数据集、处理过程和分析说明，形成可直接交给协作者查看、也可继续用于 PPT 的中间成果。

## 目录内容
- `idcard/`：身份证虚拟样本、最终图、处理步骤、识别截图和成功案例。
- `plate/`：车牌虚拟样本、最终图、处理步骤、识别截图和成功案例。
- `tables/`：身份证与车牌的 ground truth、识别结果和成功样例 CSV。
- `charts/`：身份证/车牌统计图和修复前后对比图。
- `selected_showcase/`：最适合直接给协作者看或放入 PPT 的精选图片。

## 身份证数据集
身份证好结果样本位于 `idcard/`，本轮筛选号码和姓名均匹配的 26 个稳定样例。身份证数据均为虚拟测试数据，不包含真实个人隐私。

## 车牌数据集
车牌好结果样本位于 `plate/`，复用 Codex 已完成修复的标准虚拟蓝牌结果：100/100 个样本完全匹配。

## 推荐查看顺序
1. `selected_showcase/combined_good_results_summary.png`
2. `selected_showcase/idcard_dataset_overview.png`
3. `selected_showcase/idcard_processing_chain.png`
4. `selected_showcase/plate_dataset_overview.png`
5. `selected_showcase/single_sample_processing_chain.png`
6. `tables/*.csv`

## PPT 可用素材
优先使用 `selected_showcase/` 与 `charts/` 下的图片，包括身份证处理链路、车牌处理链路、修复前后对比和汇总统计图。

## 边界说明
本目录只展示当前阶段稳定样例。异常样例、边界样例和后续待优化内容已转入 `UserShow/InternalDiagnosis/`，不混入 PerfectData。
