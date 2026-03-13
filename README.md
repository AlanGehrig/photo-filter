# Photo Filter

高度可自定义的智能照片筛选工具。

## 功能

- 多维度照片筛选（分辨率、模糊度、曝光、噪点）
- 人脸检测
- CLIP 语义匹配（可选）
- YAML 规则配置
- **Windows 图形界面**
- CLI 命令行
- Web UI (Streamlit)

## 安装

```bash
pip install -r requirements.txt
```

## Windows 图形界面

双击 `run.bat` 启动

或命令行:
```bash
python -m photofilter.ui.gui
```

## CLI 使用

```bash
photo-filter --config ./rules/social_media.yaml --input ./photos --output ./output
```

## Web UI

```bash
streamlit run photofilter/ui/streamlit_app.py
```

## 配置文件示例

见 `examples/rules/` 目录
