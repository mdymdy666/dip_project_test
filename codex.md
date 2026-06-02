# Codex 项目接手记录

本文档给后续 Codex 接手 `tansyqinyrproj` 使用，记录运行方式、依赖、模型位置和每次主要修改。

## 运行方式

### Python 依赖

先安装项目依赖：

```bash
pip install -r requirements.txt
```

核心依赖包括：

- Flask / flask-cors：后端服务和跨域
- OpenCV / numpy：图像处理
- pytesseract：身份证 OCR
- hyperlpr3 / onnxruntime：深度学习车牌识别
- requests：测试脚本和接口验证

### Tesseract OCR

身份证 OCR 依赖本地 Tesseract。必须确认 `config.py` 中路径和本机安装路径一致：

```python
TESSERACT_OCR = r'D:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'e:\OpenCVProjects\tansyqinyrproj\tessdata'
```

`tessdata` 目录需要包含：

- `eng.traineddata`
- `osd.traineddata`
- `chi_sim.traineddata`

### HyperLPR3 车牌模型

车牌识别使用 `hyperlpr3`。模型文件已放在项目内：

```text
models/.hyperlpr3/20230229/onnx/
```

包含：

- `y5fu_320x_sim.onnx`
- `y5fu_640x_sim.onnx`
- `rpv3_mdict_160_r3.onnx`
- `litemodel_cls_96x_r1.onnx`

`core/plate_operation.py` 会把 `HOMEPATH` 指向项目 `models` 目录，避免运行时去用户目录重新下载模型。

### 启动项目

在项目根目录运行：

```bash
python app.py
```

访问：

```text
http://127.0.0.1:5000/
```

如果 Codex/Windows shell 出现 socket 或 PowerShell 异常，先补环境变量，不要改源码：

```bat
set SystemRoot=C:\Windows&& set WINDIR=C:\Windows&& set HOME=C:\Users\m&& set USERPROFILE=C:\Users\m&& python app.py
```

如果本地代理影响访问 localhost，测试命令里清掉代理：

```bat
set http_proxy=&& set https_proxy=&& curl.exe http://127.0.0.1:5000/
```

### 前端构建

项目是 Vue 2 + Webpack 3。已有 `firstend/dist` 可由 Flask 直接服务。需要重新构建时：

```bash
cd firstend
npm run build
```

旧项目对 Node 版本敏感，如新版 Node 异常，可参考 `agent.md` 使用 Node 12 / npm 6。

## 数据库

车辆/车主数据库使用 SQLite：

```text
data/vehicle_owner.db
```

初始化逻辑在：

```text
core/vehicle_db.py
```

数据库表：

- `owners`：车主，以身份证号为主键
- `vehicles`：车辆，以车牌号为主键
- `ownership_history`：车主与车辆关系历史，可追溯某时期谁拥有哪辆车

启动 `app.py` 时会自动执行 `vehicle_db.init_database()`。如果需要重置演示数据，可删除 `data/vehicle_owner.db` 后重新启动。

## 测试脚本

### 车牌识别和数据库脚本测试

```bash
python test_plate_vehicle.py
```

验证内容：

- HyperLPR3 模型加载
- `uploads/plate_test.png` 车牌识别
- 识别车牌反查车辆、当前车主和历史记录

### 后端 API 测试

```bash
python test_vehicle_api.py
```

验证内容：

- 数据库初始化
- 车牌号查车主
- 身份证号查车辆
- 关系动态变更
- 关系列表查询

注意：`test_vehicle_api.py` 会真实调用动态变更接口，但脚本现在会在运行前后调用 `vehicle_db.reset_database()`，测试结束后会恢复种子数据。

### 全功能回归测试

```bash
python test_all_features.py
```

验证内容：

- 前端主要路由 HTTP 200
- `/upload/0` 到 `/upload/39` 普通图像处理
- `/upload/51` 到 `/upload/59` 风格迁移
- `/upload/50` 身份证 OCR，要求能返回 `CARD_NUM`
- `/api/plate/recognize` 车牌识别
- 车牌查车主、身份证查车辆、关系变更、关系列表接口

脚本会生成 `uploads/test_small.jpg` 作为快速回归小图，并在运行前后重置车辆/车主数据库。

### 数据库重置和查看

代码侧可用：

```python
from core import vehicle_db

vehicle_db.reset_database()
vehicle_db.database_summary()
```

当前种子数据规模：

- 车主：12 条
- 车辆：14 条
- 关系历史：20 条
- 当前有效车辆关系：14 条

## 更新记录

### 2026-06-01 运行适配

主要任务：让原项目可以稳定运行，并把项目资产提交到远端仓库。

主要内容：

- 按 `agent.md` 梳理项目运行方式
- 使用系统 Python 运行 Flask 后端，避开虚拟环境缺少 `pytesseract` 的问题
- 处理 Codex Windows shell 环境变量问题：`SystemRoot`、`WINDIR`、`HOME`、`USERPROFILE`
- 确认 Flask 可服务 `firstend/dist`
- 确认 OCR、图像处理上传接口能工作
- 将大体积项目资产纳入 Git：图片、`models/*.t7`、`tessdata/*.traineddata`、`firstend/dist`、`tmp` 样例图
- 推送到 GitHub 仓库 `mdymdy666/dip_project_test`

涉及文件/目录：

- `app.py`
- `config.py`
- `core/`
- `firstend/`
- `models/`
- `tessdata/`
- `uploads/`
- `tmp/`
- `.gitignore`
- `agent.md`

### 2026-06-02 UI 重设计

主要任务：在不改变原功能接口的前提下，把界面改成和原来完全不同的工作台风格。

主要内容：

- 将原 Element 侧边菜单改为自定义深色功能导航
- 将顶部 Header 改为工作台指标栏
- 将普通图像处理页改为输入/输出双面板
- 将 OCR 页改为身份证资料面板
- 将样例图展示改为独立参考区
- 重新构建 `firstend/dist`

修改文件：

- `firstend/src/components/Layout.vue`
- `firstend/src/components/Header.vue`
- `firstend/src/components/Upload2Show.vue`
- `firstend/src/components/prepic.vue`
- `firstend/src/views/50OCR.vue`
- `firstend/src/assets/style.css`
- `firstend/dist/`

验证：

- `npm run build` 通过
- Flask 首页和功能路由返回 HTTP 200

### 2026-06-02 车牌识别、车辆档案和关系追溯

主要任务：引入深度学习车牌识别，新增车辆/车主数据库和前端车辆档案工作流。

主要内容：

- 安装并验证 `hyperlpr3`
- 下载/保存 HyperLPR3 ONNX 模型到项目目录
- 引入车牌测试图 `uploads/plate_test.png`
- 新增车牌识别模块，识别结果包含车牌号、置信度、类型、检测框和匹配的车辆/车主信息
- 新增 SQLite 数据库初始化，包含车主、车辆和关系历史
- 新增 API：
  - `POST /api/plate/recognize`
  - `GET|POST /api/vehicle/by-plate`
  - `GET|POST /api/owner/by-id-card`
  - `GET /api/relationships`
  - `POST /api/relationships/change-owner`
  - `GET|POST /api/vehicle/init`
- OCR 身份证识别成功后，自动查询该身份证关联车辆
- 新增前端页面：
  - 车牌识别
  - 车牌找车主
  - 身份证找车辆
  - 车主车辆关系变更
- 新增测试脚本和依赖清单

修改/新增文件：

- `app.py`
- `core/main.py`
- `core/plate_operation.py`
- `core/vehicle_db.py`
- `data/vehicle_owner.db`
- `models/.hyperlpr3/20230229/onnx/*.onnx`
- `uploads/plate_test.png`
- `test_plate_vehicle.py`
- `test_vehicle_api.py`
- `requirements.txt`
- `firstend/src/router/index.js`
- `firstend/src/components/Layout.vue`
- `firstend/src/views/50OCR.vue`
- `firstend/src/views/PlateRecognition.vue`
- `firstend/src/views/VehicleLookup.vue`
- `firstend/src/views/OwnerLookup.vue`
- `firstend/src/views/RelationshipManager.vue`
- `firstend/src/assets/style.css`
- `firstend/dist/`
- `codex.md`

验证：

- `python test_plate_vehicle.py` 通过
- `python test_vehicle_api.py` 通过
- `npm run build` 通过
- Flask 新增页面路由 `/plate/recognize`、`/vehicle/search`、`/owner/search`、`/relations` 返回 HTTP 200
- `POST /api/plate/recognize` 使用 `uploads/plate_test.png` 可识别出 `粤Z5A55港` 和 `苏BD0011`

注意：

- `test_vehicle_api.py` 会修改数据库关系历史；如果只是演示查询，优先使用 UI 或只运行 `test_plate_vehicle.py`
- 新增 `hyperlpr3` 后，项目运行环境需要能导入 `onnxruntime`
- 前端页面已构建到 `firstend/dist`，Flask 会直接服务构建结果

### 2026-06-02 Code review、数据扩容和全功能测试

主要任务：审查新增车牌/车辆模块，增大演示数据量，并尽可能完整测试项目功能。

发现和处理：

- 发现 `test_vehicle_api.py` 会污染真实数据库关系历史；已改为测试前后自动重置数据库
- 发现数据库初始化只在空库时写入种子数据，不利于后续扩容；已改为 `INSERT OR IGNORE` 幂等补种子
- 发现测试脚本曾读取错误 OCR 字段名；已改为校验 `CARD_NUM`、`CARD_NAME`
- 给 `change_owner()` 增加重复当前车主保护，避免同一车主被重复过户
- 给 `/api/vehicle/init` 增加 `summary` 返回值，便于确认数据库规模

数据扩容：

- 车主从 4 条扩容到 12 条
- 车辆从 4 条扩容到 14 条
- 关系历史从 6 条扩容到 20 条
- 新增与 OCR 样例相关的身份证号，包括 `110103198211290041`、`43062419900818361X`

修改/新增文件：

- `app.py`
- `core/vehicle_db.py`
- `test_vehicle_api.py`
- `test_all_features.py`
- `uploads/test_small.jpg`
- `tmp/codex/relations_ui.png`
- `codex.md`

验证：

- `python test_plate_vehicle.py` 通过
- `python test_vehicle_api.py` 通过
- `python test_all_features.py` 通过
- 浏览器实测 `/vehicle/search`，输入 `粤Z5A55港` 能查询到当前车主 `刘源`
- 浏览器实测 `/owner/search`，输入 `44030119840217411X` 能查询到关联车辆
- 浏览器实测 `/relations`，确认关系动态变更 UI 可提交并刷新列表
- 测试后已执行 `vehicle_db.reset_database()`，数据库恢复为种子状态：12 个车主、14 辆车、20 条历史关系、14 条当前关系
