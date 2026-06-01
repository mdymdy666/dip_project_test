# Codex 运行说明

本文档给后续 Codex 接手本项目时使用，基于 `agent.md` 的修复记录整理。

## 项目结构

- 后端入口：`app.py`
- 后端配置：`config.py`
- 图像处理核心：`core/`
- 前端源码：`firstend/`
- Flask 当前服务的前端构建产物：`firstend/dist/`
- OCR 语言包：`tessdata/*.traineddata`
- 风格迁移模型：`models/*.t7`
- 示例/展示图片：`uploads/`、`firstend/public/img/`、`firstend/dist/static/img/`

## 本地依赖

Python 需要能导入这些包：

```bash
pip install flask flask-cors opencv-python numpy pytesseract
```

本项目的 OCR 还依赖本机安装 Tesseract。必须确认 `config.py` 中的路径和本机实际路径一致：

```python
TESSERACT_OCR = r'D:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'e:\OpenCVProjects\tansyqinyrproj\tessdata'
```

如果项目目录或 Tesseract 安装目录变化，需要同步修改 `config.py`：

- `TESSERACT_OCR` 指向本机 `tesseract.exe`
- `TESSDATA_PREFIX` 指向包含 `eng.traineddata`、`osd.traineddata`、`chi_sim.traineddata` 的目录

## 启动后端和页面

在项目根目录运行：

```bash
python app.py
```

浏览器访问：

```text
http://127.0.0.1:5000/
```

本项目的 Flask 配置已经直接服务 `firstend/dist`，所以只要 `firstend/dist` 存在，就不需要单独启动前端开发服务器。

## 前端重新构建

项目使用 Vue 2 + Webpack 3，新版 Node 可能不兼容。优先使用 Node 12 / npm 6：

```bash
cd firstend
npx -y -p node@12 -p npm@6 npm run build
```

如果依赖不完整，可按 `agent.md` 记录补装兼容版本：

```bash
npm install axios@0.18.1 --legacy-peer-deps
npm install color-convert@2.0.1 --legacy-peer-deps
npm install element-ui@2.15.13 --legacy-peer-deps
```

## Codex 终端注意事项

如果在 Codex/Windows 命令环境里出现 Python socket 或 PowerShell 异常，例如 `WinError 10106`，先不要改源码；用启动命令临时补 Windows 环境变量：

```bat
set SystemRoot=C:\Windows&& set WINDIR=C:\Windows&& python app.py
```

如果本地代理变量影响访问本机服务，测试命令里临时清掉代理：

```bat
set http_proxy=&& set https_proxy=&& curl.exe http://127.0.0.1:5000/
```

## Git 提交范围

需要提交的二进制/大文件包括：

- `models/*.t7`
- `tessdata/*.traineddata`
- `uploads/` 中的示例图片和 README 展示图
- `tmp/ct/`、`tmp/draw/` 中现有的项目样例/处理结果图片
- `firstend/public/img/`
- `firstend/dist/`，因为后端直接服务该构建产物
- 项目报告 `.docx`、`.pdf`

不要提交这些中间文件：

- `.venv/`、`venv/`
- `firstend/node_modules/`
- `__pycache__/`
- `output.txt`
- 运行日志和新产生的无用临时输出

`tmp/` 里现有图片已经作为项目资产提交。后续运行会继续向 `tmp/ct/` 和 `tmp/draw/` 写文件，提交前需要逐个判断：项目演示必需的图片可以提交，单次测试产生的无用输出不要提交。
