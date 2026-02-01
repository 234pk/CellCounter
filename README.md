# CellCounter 🔬

[中文](#中文) | [English](#english)

---

## 中文

血球计数板自动细胞计数软件。支持交互式 ROI 选择、自动检测、手动修正以及浓度自动计算。

### 📋 功能特点
- **多图支持**：支持同时导入 4 张图片（对应计数板的 4 个区域）或整个文件夹。
- **交互式 ROI**：Shift + 左键点击绘制多边形计数区域，右键闭合。
- **高精度识别**：基于 SimpleBlobDetector 的细胞识别算法。
- **手动修正**：按 `M` 进入手动模式，左键增加细胞，右键删除细胞，结果实时同步。
- **自动计算**：内置多种计数板参数（Improved Neubauer, Watson 等），自动计算浓度和样本总数。
- **数据导出**：一键导出包含浓度和总数的 CSV 报告。
- **参数持久化**：自动保存上次使用的识别参数和工作目录。

### 🚀 安装与运行
1. **环境要求**：Python 3.10+
2. **安装依赖**：
   ```bash
   pip install PyQt6 opencv-python numpy
   ```
3. **运行软件**：
   ```bash
   python main.py
   ```

### 📖 使用流程
1. **导入**：点击 "Import Images" 选择图片或文件夹。
2. **划定区域**：按住 **Shift + 左键** 绘制 ROI。
3. **计数**：点击 "Start All Tabs" 开始识别。
4. **修正**：按 `M` 键，通过左右键微调识别结果。
5. **导出**：输入样本总体积，点击 "Export Report" 保存。

### ⌨️ 快捷键
- `1, 2, 3, 4`: 切换页签
- `M`: 切换手动/ROI模式
- `Delete`: 清除当前 ROI
- `Ctrl + Z`: 撤销点
- `+/-`: 缩放图片
- `方向键`: 平移图片

### 📦 Nuitka 打包工作流 (Windows EXE)
为了确保最佳兼容性，请使用以下步骤进行打包：
1. **安装环境**：确保已安装 Python 3.12 (推荐使用官网版，避免 Windows Store 版)。
2. **准备编译器**：Nuitka 需要 MinGW64。脚本会自动下载，或手动配置 `CC` 环境变量。
3. **运行打包脚本**：
   ```powershell
   python build_exe.py
   ```
   或手动执行命令：
   ```bash
   python -m nuitka --standalone --show-progress --windows-console-mode=disable --plugin-enable=pyqt6 --follow-imports --include-package=cv2 --include-package=numpy --output-dir=build --onefile --mingw64 --assume-yes-for-downloads main.py
   ```

### 🚀 后续 Release 计划
- [ ] **v2.2**: 增加荧光图像支持 (多通道融合)。
- [ ] **v2.3**: 引入深度学习模型 (YOLOv8) 替代传统 Blob 检测，提升复杂背景下的识别率。
- [ ] **v2.4**: 支持导出 PDF 详细报告，包含每张图的预览和直方图。

---

## English

Automated cell counter software for hemocytometers. Supports interactive ROI selection, automated detection, manual correction, and concentration calculation.

### 📋 Features
- **Multi-image Support**: Import up to 4 images or an entire folder.
- **Interactive ROI**: Shift + Left Click to draw polygons, Right Click to close.
- **Precision Detection**: Cell recognition based on SimpleBlobDetector.
- **Manual Correction**: Press `M` to toggle manual mode. Left Click to add, Right Click to remove.
- **Auto Calculation**: Built-in parameters for various chambers (Neubauer, Watson, etc.). Calculates concentration and total sample count.
- **Data Export**: Export results to CSV with one click.
- **Persistence**: Automatically saves parameters and last working directory.

### � Setup
1. **Requirements**: Python 3.10+
2. **Dependencies**:
   ```bash
   pip install PyQt6 opencv-python numpy
   ```
3. **Run**:
   ```bash
   python main.py
   ```

### 📖 Workflow
1. **Import**: Click "Import Images".
2. **ROI**: Hold **Shift + Left Click** to draw.
3. **Count**: Click "Start All Tabs".
4. **Edit**: Press `M` and use mouse clicks to fine-tune.
5. **Export**: Enter sample volume and click "Export Report".

### ⌨️ Shortcuts
- `1, 2, 3, 4`: Switch tabs
- `M`: Toggle Manual/ROI mode
- `Delete`: Clear current ROI
- `Ctrl + Z`: Undo point
- `+/-`: Zoom in/out
- `Arrow Keys`: Pan image

### 📦 Nuitka Packaging Workflow (Windows EXE)
To ensure best compatibility, follow these steps:
1. **Environment**: Ensure Python 3.12 (Official CPython) is installed.
2. **Compiler**: Nuitka requires MinGW64. The script handles downloads automatically via `--assume-yes-for-downloads`.
3. **Build**:
   ```powershell
   python build_exe.py
   ```
   Or manually:
   ```bash
   python -m nuitka --standalone --show-progress --windows-console-mode=disable --plugin-enable=pyqt6 --follow-imports --include-package=cv2 --include-package=numpy --output-dir=build --onefile --mingw64 --assume-yes-for-downloads main.py
   ```

### 🚀 Future Releases
- [ ] **v2.2**: Fluorescence image support (multi-channel merging).
- [ ] **v2.3**: Deep learning (YOLOv8) integration for improved detection in noisy backgrounds.
- [ ] **v2.4**: PDF report export with image previews and histograms.
