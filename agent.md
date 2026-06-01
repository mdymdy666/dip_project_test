# 项目修复记录

## 概述

本文档记录了在 `tansyqinyrproj` 项目中做出的所有改动和解决的重要问题。

---

## 一、前端构建问题

### 1.1 Node.js 版本兼容性
- **问题**：项目使用的是 Vue.js 2 + Webpack 3，与新版本 Node.js 不兼容
- **解决方案**：使用 Node.js 12 版本运行构建
- **命令**：`npx -y -p node@12 -p npm@6 npm run build`

### 1.2 依赖版本问题
- **问题**：部分依赖包版本过高，与项目不兼容
- **解决方案**：安装兼容版本
    - `npm install axios@0.18.1 --legacy-peer-deps`
    - `npm install color-convert@2.0.1 --legacy-peer-deps`
    - `npm install element-ui@2.15.13 --legacy-peer-deps`

---

## 二、Flask 后端配置

### 2.1 路由配置（支持 Vue Router History 模式）
- **文件**：`app.py`
- **改动**：添加 catch-all 路由
- **代码**：
```python
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return send_from_directory('./firstend/dist', 'index.html')
```

### 2.2 静态文件配置
- **文件**：`app.py`
- **改动**：配置静态文件路径
- **代码**：
```python
app = Flask(__name__, template_folder='./firstend/dist', 
            static_folder='./firstend/dist/static', static_url_path='/static')
```

---

## 三、NumPy 兼容性修复

### 3.1 `np.int0` 已废弃问题
- **问题**：NumPy 2.0+ 版本中 `np.int0` 已被移除
- **文件**：`core/functions.py`
- **位置**：第 298, 536, 571, 609 行
- **改动**：将 `np.int0()` 替换为 `np.int32()`

---

## 四、Tesseract OCR 配置

### 4.1 语言包配置
- **问题**：系统中没有安装中文语言包
- **解决方案**：
    1. 创建项目本地 tessdata 目录：`e:\OpenCVProjects\tansyqinyrproj\tessdata`
    2. 复制语言包：eng.traineddata, osd.traineddata, chi_sim.traineddata
    3. 更新配置文件指向新路径

- **文件**：`config.py`
- **代码**：
```python
os.environ['TESSDATA_PREFIX'] = r'e:\OpenCVProjects\tansyqinyrproj\tessdata'
```

### 4.2 命令行参数格式
- **问题**：新版本 Tesseract 使用 `--psm` 而非 `-psm`
- **文件**：`core/functions.py`
- **位置**：第 548, 550, 581, 583, 619, 621 行
- **改动**：将 `-psm` 替换为 `--psm`

---

## 五、代码语法修复

### 5.1 异常抛出语法
- **问题**：`raise('xxx')` 语法错误
- **文件**：`core/functions.py`
- **位置**：第 401, 424 行
- **改动**：改为 `raise Exception('xxx')`

### 5.2 HistGram 数组访问
- **问题**：`HistGram[Y]` 返回数组而非标量
- **文件**：`core/functions.py`
- **位置**：第 92, 95 行
- **改动**：改为 `float(HistGram[Y][0])`

---

## 六、前端错误处理

### 6.1 OCR 错误响应处理
- **问题**：OCR 失败时前端崩溃
- **文件**：`firstend/src/views/50OCR.vue`
- **改动**：添加状态检查，失败时显示友好提示

---

## 七、新项目复制

### 7.1 创建新项目目录
- **位置**：`e:\OpenCVProjects\tansyqinyrproj\new_tansyqinyrproj`
- **包含文件**：
    - `app.py` - Flask 入口
    - `config.py` - 配置文件（已更新路径）
    - `core/` - 核心功能模块
    - `firstend/` - 前端代码
    - `tessdata/` - 语言包目录
    - `uploads/` - 上传文件目录

### 7.2 配置更新
- **文件**：`new_tansyqinyrproj/config.py`
- **改动**：更新 TESSDATA_PREFIX 指向新项目目录

---

## 八、已解决的错误列表

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `net::ERR_ABORTED static/css/app...css` | 静态文件路径配置错误 | 配置正确的 static_folder |
| `Error: Request failed with status code 500` | 多种原因 | 见各节描述 |
| `module 'numpy' has no attribute 'int0'` | NumPy 版本兼容性 | 替换为 np.int32 |
| `Error, unknown command line argument '-psm'` | Tesseract 参数格式变化 | 替换为 --psm |
| `Error opening data file ... tessdata/eng.traineddata` | 语言包路径错误 | 配置正确的 TESSDATA_PREFIX |
| `身份证识别失败！！！` | 上传的图片不是身份证 | 提示用户上传正确图片 |

---

## 九、当前项目状态

| 项目 | 状态 | 说明 |
|------|:----:|------|
| 后端服务 | ✅ 运行中 | Flask 服务器 |
| 前端页面 | ✅ 正常 | Vue.js 应用 |
| OCR 功能 | ✅ 正常 | 支持中英文识别 |
| 图像处理 | ✅ 正常 | 39 个基础功能 + 9 种风格迁移 |

---

## 十、访问方式

- **地址**：http://127.0.0.1:5000
- **OCR 功能**：上传身份证图片到 `/upload/50`
- **图像处理**：选择对应功能路径

---

## 十二、GitHub 推送问题解决

### 12.1 SSL/TLS 握手失败
- **问题**：SSL/TLS 连接失败，无法推送代码到 GitHub
- **解决方案**：
  1. 配置 Git 使用 Windows 内置的 SSL 后端 (schannel)
  2. 临时禁用 SSL 验证（仅用于此项目）
  3. 增加缓冲区大小以支持大文件推送
  
- **配置命令**：
```bash
git config --local http.sslBackend schannel
git config --local http.sslVerify false
git config --local http.postBuffer 524288000
```

### 12.2 分支同步
- **问题**：远程默认分支是 `main` 而本地是 `master`
- **解决方案**：重命名本地分支并强制推送
```bash
git branch -M main
git push -u origin main --force
```

### 12.3 推送辅助脚本
- **文件**：`push.bat` - Windows 批处理脚本
- **文件**：`push_helper.ps1` - PowerShell 脚本
- **说明**：用于快速配置并推送代码

---

## 十三、注意事项

1. **身份证识别**：请上传真实的身份证图片，系统会进行有效性验证
2. **图片格式**：仅支持 PNG 和 JPG 格式
3. **语言包**：已配置中文语言包，可识别中文姓名和地址
4. **Node.js 版本**：构建前端时建议使用 Node.js 12
5. **Git 配置**：已配置本地 Git 设置以避免 SSL 问题
