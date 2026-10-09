论文结构图可编辑重建 v0.2

优先保留原图的布局、配色、文字和细节。打开 comparison.html 可离线对照论文原图与重建预览。实际编辑请打开 PPTX 或 draw.io；PNG 仅用于预览。

ASPIRE · Figure 1 · PDF 第 2 页
来源：https://arxiv.org/abs/2607.00272v1
Lu et al. (2026), ASPIRE: Agentic /Skills Discovery for Robotics
保留原 PDF 的圆弧箭头、圆角面板、放大框、虚线、配色和主要文字位置。代码片段与进化搜索小图从原像素重新建立为原生文字/形状/连线。代码每行使用一个原生文本框，语法颜色简化，以免字体替换导致符号重叠。
66 个原生自由路径、62 个原生文本对象、6 条吸附连线；另有21个独立照片/图标等栅格对象。源曲线箭头大多是可编辑自由路径，不会自动吸附/重排。
原 arXiv 链接 CC BY 4.0；PDF 另有 NVIDIA 版权声明。保留来源署名，Logo/第三方图像权利没有单独核实。

RoboReact · Figure 2 · PDF 第 3 页
来源：https://arxiv.org/abs/2608.03387v2
He et al. (2026), RoboReact: Agentic Skill Distillation from Generated Egocentric Videos for Generalizable Whole-Body Manipulation
原 PDF 的整张图是单个位图。此版本按实际原图重新建立面板、普通文字、关键帧图、迭代箭头和流程连接，并保留原照片布局。
74 个原生文本对象、5 个原生自由路径、75 条语义连线；30个独立小栅格对象包括17个照片/深度/姿态面板、12个装饰图标、1个公式条。其内部像素、诊断叠加和公式字符不能逐对象编辑。
未核实到开放插图复用许可证。此私下转换不代表已获得公开再发布许可。

编辑说明
- PPTX 自由形状可使用 Edit Points；文字保持原生文本框，图片可单独替换
- draw.io 自由路径是原生 custom stencil，可移动、缩放、改色；细致路径编辑使用 Edit Shape/XML
- 多折点连接线在 PPTX 中使用附着线段和透明路径锚点；移动端点不保证所有折点自动重排
- 字体替换、小箭头/虚线节距、排版与曲线可能因软件变化；不声称像素级完全一致
- 已完成结构校验、源图对照、预览检查及 LibreOffice 打开/渲染；尚未完整手动验证 Microsoft PowerPoint 的所有编辑操作

此私有仓库的根目录包含源码、JSON 场景、所有图像资产、论文目录、测试与文档；output/ 是解压后的原始结果文件夹。这里不上传 ZIP 或 Git bundle。旧语义简化版单独保存在 data/diagrams/legacy/，不能当作本次高保真版本。

运行：在仓库根目录执行 python -m paper_figure；详见根目录 README.md。draw.io 导出仅需标准 Python；重新生成 PPTX 需单独可用的 Artifact Tool 运行时，普通 pip 安装不会提供它。生成后的 PPTX 可直接在 Office/LibreOffice 打开。

论文目录137条：134未审查、2已重建、1受限阻塞。重建状态不等于所有原图细节已经人工完全验证。本次上传仅限已获授权的私有仓库开发分支；未公开发布。
