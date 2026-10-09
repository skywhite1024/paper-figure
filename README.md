# Paper Figure v0.2

将论文结构图转换成可编辑 PowerPoint / draw.io。v0.2 优先尽量保持原图布局、配色和细节。

## 这版有什么变化

- ASPIRE Fig. 1：从真实 PDF 保留原生曲线路径、颜色、布局、图中文字；逐张提取照片并保留原裁切/遮罩，恢复缩略放大框和弧形箭头
- RoboReact Fig. 2：原 PDF 整张图是一个位图，因此按原图坐标人工重建原生面板、文字、关键帧图和箭头；照片、少量图标及公式仍是单独栅格小图
- 旧语义简化版单独保存在 `data/diagrams/legacy/`，不冒充高保真版本
- 支持可编辑 Bézier 自由形状、字体/粗斜体、颜色/透明度、线宽和虚线
- 源码、场景和照片资产一起归档；见 [恢复记录](docs/RECOVERY.md)

**不是任意截图的一键无损矢量化。** 不同来源需不同方案；照片和源图中无法恢复的像素细节不能逐对象编辑。

## 快速开始

Python 3.10+。draw.io 导出和核心校验仅依赖 Python 标准库。

```bash
python -m paper_figure validate examples/minimal.json
python -m paper_figure export examples/minimal.json --format drawio --out build/demo
python -m paper_figure export data/diagrams/aspire-figure-1.json --format drawio --out build/aspire
python -m paper_figure catalog data/catalog.json
python -m unittest discover -s tests -v
```

也可 `pip install -e .` 后使用 `paper-figure`。

### PPTX

PPTX 使用 Node.js + 预装 `@oai/artifact-tool`。它不是本仓库保证可公开安装的依赖。dot 自动使用 `CODEX_PRIMARY_RUNTIME_NODE` / `CODEX_PRIMARY_RUNTIME_NODE_MODULES`；其他已有授权运行时可设置 `PAPER_FIGURE_NODE_MODULES`。普通 `pip install` 不会提供这个后端。缺少它时仍可生成 draw.io；已经生成的 PPTX 不依赖此工具即可打开。

```bash
python -m paper_figure export data/diagrams/aspire-figure-1.json --out build/aspire --preview
python -m paper_figure export data/diagrams/roboreact-figure-2.json --out build/roboreact --preview
python -m paper_figure batch data/catalog.json --out build/catalog --preview
PAPER_FIGURE_TEST_PPTX=1 python -m unittest discover -s tests -v
```

默认两种格式；`--format drawio|pptx` 选择，`--preview` 生成 PNG，`--force` 允许覆盖。生成器先暂存再移动输出，失败不伪造完整结果。

## 可编辑性与高保真边界

- PPTX：原生文本、形状和自由路径；自由形状可通过 Edit Points 修改。照片是单独图片
- draw.io：文本/普通形状/连接线可编辑；自由路径是原生 custom stencil，可移动、缩放、改色，细致路径修改使用 Edit Shape/XML
- 从 PDF 提取的箭头路径保留原曲线，但没有自动吸附到语义节点；这与原生连接线不同，指标单独报告
- 图中照片、图标、诊断叠加、少量公式等像素内容不因此成为可编辑矢量
- 字体替换、换行、箭头样式、虚线节距和小图细节可能与原图有差异；不声称像素级完全相同
- `recreated` 表示已有重建，`verified` 才表示完成规定人工目标软件检查；导出不会自动升级状态
- 论文目录固定到来源 commit，137 条记录不是137张已经转换的图

## 来源与权利

来源：[Awesome Papers for Robotic Skill Discovery](https://github.com/EDEM-AI/Awesome-Papers-for-Robotic-SKill-Discovery)。详细图号、页码、版本、许可证线索、改绘说明见 [来源记录](research/PROVENANCE.md) 与各场景 `provenance`。

这是用户请求的私下转换，不等于取得全部插图、Logo和照片的公开再发布许可。RoboReact 未核实到开放插图许可证。本次授权上传仅面向此私有仓库的开发分支；不代表图像取得公开再发布许可。代码整体许可证尚未指定。

## 再现与目录

`paper_figure/` 为 CLI/导出器；`data/diagrams/` 是完整 JSON 和图像资产；`research/` 是特定来源重建程序；`tests/` 是校验与集成测试。

重新导出既有 JSON 不需要原 PDF。重新提取 ASPIRE 需 PyMuPDF、Pillow、lxml（`pip install -e '.[pdf]'`）以及现有 Node.js `sharp`（用于保留 SVG 遮罩/裁切）；`research/extract_aspire_fidelity.py --pdf /path/to/aspire.pdf` 是针对该固定版本论文的受测提取器，不能宣传为任意 PDF 通用转换。

RoboReact 的人工坐标程序 `research/build_roboreact_faithful.py` 使用原图像素作为参考，输入路径详见程序参数。源图和可编辑输出的对照位于样例包中的 `comparison.html`。

## 原始结果文件夹

`output/` 包含两张图的 PPTX、draw.io、PNG、原图对照、离线 `comparison.html`、来源/验证说明。仓库不提交 ZIP 或 Git bundle，源码直接位于仓库根目录。

### 原文 PDF

对照用固定版本原文保存在 [`output/source-papers/`](output/source-papers/README.md)：ASPIRE v1 的 Figure 1 位于第2页，RoboReact v2 的 Figure 2 位于第3页。该目录记录原始官方 URL、SHA256 与页码，保留原文权利声明。
