# 📷 Photo Filter Pro

桌面端照片管理和智能筛选工具。

## 安装

### 1. 安装 Python
下载 Python 3.8+: https://www.python.org/downloads/

**注意**: 安装时勾选 `Add Python to PATH`

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

或者直接双击运行 `启动 Photo Filter Pro.bat`

### 3. 运行
```bash
python -m photofilter.ui.gui
```

## 功能

| 功能 | 说明 |
|------|------|
| 📁 文件夹管理 | 批量加载照片文件夹 |
| 🔍 智能筛选 | 按格式、大小、模糊度、曝光筛选 |
| 🏷️ 语义匹配 | AI 识别照片内容 (可选) |
| 👤 人脸检测 | 自动识别含人脸照片 |
| ⚡ 批量处理 | 后台处理，不卡界面 |
| 📷 EXIF查看 | 查看照片详细信息和拍摄参数 |
| 📝 批量重命名 | 按日期、序号、相机信息批量重命名 |
| 🖼️ 缩略图预览 | 列表显示缩略图 |
| 🖱️ 拖拽支持 | 拖拽文件夹到窗口 |
| ⌨️ 快捷键 | Ctrl+O打开, F5刷新, Delete删除 |
| 👉 右键菜单 | 快速操作 |

## 可选: 启用 AI 语义匹配

编辑 `requirements.txt`，取消注释以下行：
```txt
torch>=2.0.0
transformers>=4.30.0
accelerate>=0.20.0
```

然后重新安装：
```bash
pip install torch transformers accelerate
```

> 注意: AI 功能需要 GPU 支持，无 GPU 会很慢

## 项目结构

```
photo-filter/
├── photofilter/
│   ├── core/           # 核心模块
│   │   ├── photo.py
│   │   ├── image_analyzer.py
│   │   ├── semantic_matcher.py
│   │   └── filter_engine.py
│   ├── ui/
│   │   ├── gui.py      # PyQt5 桌面应用
│   │   └── streamlit_app.py  # Web 版
│   └── config/
├── requirements.txt
├── 启动 Photo Filter Pro.bat
└── README.md
```

## 常见问题

**Q: 双击 bat 文件没反应？**
A: 打开命令提示符 (cmd) 运行，查看错误信息

**Q: PyQt5 安装失败？**
A: 尝试: `pip install PyQt5 --no-binary PyQt5`

**Q: 想用 Web 版而不是桌面版？**
A: 运行 `streamlit run photofilter/ui/streamlit_app.py`

---

*Built with ❤️ for photographers*
