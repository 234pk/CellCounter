# CellCounter 开发与变更记录

## 🔴 当前版本状态 (Current State)
- **核心算法**: 回归至 GitHub v2.1.6 原始稳定版 (`cv2.SimpleBlobDetector`)，移除了不稳定的自适应阈值和背景归一化，确保检测结果可复现。
- **UI 框架**: PySide6 (已完成从 PyQt6 的迁移)。
- **多语言支持**: 支持 中文/English 实时切换，配置自动持久化。
- **数据导出**: 支持表格数据复制 (Ctrl+C) 及一键复制汇总结果。

---

## 📅 变更日志 (Change Log)

### 2026-02-01 (Theme System Update)
- **主题系统升级**:
  - 新增统一的主题管理系统，支持 4 种预设主题：
    - **Dark**: 经典的暗色风格（默认）。
    - **Midnight**: 高对比度的纯黑/深蓝风格，适合夜间使用。
    - **Light**: 类似 macOS 的浅色明亮风格。
    - **Scientific**: 适合学术报告的蓝/白专业风格。
  - 在工具栏新增 **主题切换器**，支持实时预览和切换。
  - 主题偏好自动保存至 `QSettings`，重启后保持。
- **UI 代码重构**:
  - 移除了所有硬编码的 `styleSheet` 样式，改为动态加载。
  - 统一了所有组件（主窗口、查看器、弹窗）的配色逻辑。
- **Bug Fix**:
  - 修复了右键菜单 (QMenu) 和消息弹窗 (QMessageBox) 在暗色主题下出现"白底灰字"的样式问题，强制应用了统一的背景色和边框样式。

### 2026-02-01 (UI Logic Refactor & I18n Fix)
- **GUI 逻辑重构**: 
  - 将 `QComboBox` (计数板、区域、圆度) 的逻辑判断源从 `currentText()` 修改为 `currentData()`。
  - **修复**: 解决了中文环境下因翻译文本变化导致的功能失效（如 "Enabled"->"启用" 导致圆度过滤失效产生杂乱圈选）。
- **设置持久化**: 
  - 配置文件现在保存语言无关的 Key (如 "Enabled")，确保语言切换后用户设置不丢失。
- **稳定性增强**:
  - 增加了 `minArea`/`maxArea` 的双重校验，防止因输入 0 或 min>max 导致的 OpenCV 崩溃。

### 2026-02-01 (Features & Polish)
- **界面优化**: 统一按钮高度与宽度，优化多语言下的显示布局。
- **专业翻译**: 校对并更新了生物医学专业术语（如 Hemocytometer, Dilution Factor）。
- **结果面板增强**: 
  - 新增 "📋 Copy" 按钮，支持一键复制汇总数据。
  - 表格升级为支持多行选中的复制模式。
  - 数据显示精度提升至 4 位有效数字。

### 2026-02-01 (Algorithm Rollback)
- **回滚**: 严格回滚至 GitHub 原始检测算法。
  - 移除了 "自适应阈值"、"背景归一化" 和 "自动优化参数" 功能，因为它们在部分样本上表现不稳定。
  - 恢复 `cv2.SimpleBlobDetector` 原始参数配置 (Threshold 10-220, Step 10)。
- **保留**: 仅保留了 PySide6 架构升级和参数实时预览 (`_update_current_preview`) 功能。

---

## 🗑️ 已移除的实验性功能 (Deprecated/Removed)
*(注：以下功能曾在开发中尝试，但因稳定性原因已移除)*
1. **Auto-Optimize Parameters (智能参数优化)**: 曾用于自动计算 min/max area，因依赖初始检测准确性而被移除。
2. **Background Normalization (背景归一化)**: 曾用于消除光照不均，但会引入边缘伪影。
3. **Adaptive Thresholding (自适应阈值)**: 曾替代 BlobDetector，但在高密度样本下易粘连。
