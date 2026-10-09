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

这是用户请求的私下转换，不等于取得全部插图、Logo和照片的公开再发布许可。RoboReact 未核实到开放插图许可证。本次授权上传仅面向此私有仓库；不代表图像取得公开再发布许可。代码整体许可证尚未指定。

## 再现与目录

`paper_figure/` 为 CLI/导出器；`data/diagrams/` 是完整 JSON 和图像资产；`research/` 是特定来源重建程序；`tests/` 是校验与集成测试。

重新导出既有 JSON 不需要原 PDF。重新提取 ASPIRE 需 PyMuPDF、Pillow、lxml（`pip install -e '.[pdf]'`）以及现有 Node.js `sharp`（用于保留 SVG 遮罩/裁切）；`research/extract_aspire_fidelity.py --pdf /path/to/aspire.pdf` 是针对该固定版本论文的受测提取器，不能宣传为任意 PDF 通用转换。

RoboReact 的人工坐标程序 `research/build_roboreact_faithful.py` 使用原图像素作为参考，输入路径详见程序参数。源图和可编辑输出的对照位于各论文文件夹的 `comparison.html`。

## 按论文查看结果

- [ASPIRE](output/aspire/README.md)：PPTX、draw.io、预览、原图对照与原文 PDF（Figure 1，第2页）
- [RoboReact](output/roboreact/README.md)：PPTX、draw.io、预览、原图对照与原文 PDF（Figure 2，第3页）
- [结果总索引](output/README.md)

每篇论文独立一个文件夹（如 `output/aspire/`、`output/srsd/`），新增结果持续进入[总索引](output/README.md)。来源版本、PDF SHA256、图号/页码、可编辑对象统计、校验记录和离线对照均放在对应文件夹，根目录仅保留小型索引/汇总。仓库不提交 ZIP 或 Git bundle。

### 重新生成仍保持按论文归档

```bash
python -m paper_figure export data/diagrams/aspire-figure-1.json --out build/aspire --preview --force
python -m paper_figure export data/diagrams/roboreact-figure-2.json --out build/roboreact --preview --force
python research/refresh_outputs.py --from-build build
```

最后一步核对导出哈希，再更新对应论文文件夹的结果与索引；原文 PDF 与原图对照保留原位。新生成文件不能继承旧人工审核结论，发生变化时验证记录自动设为待审查。

仅刷新索引/哈希清单可运行 `python research/refresh_outputs.py`。可选本地打包：`python research/package_release.py --out build/releases`，生成的包也保持按论文的文件夹结构；complete 包保留仓库根目录布局（output/ 与 data/ 并列），使解压后的相对链接继续有效。这些 ZIP 不上传 GitHub。

## 逐篇处理与可恢复检查点

完整 137 篇目录的进度保存在 `data/queue/<catalog-id>.json`。来源核实、可访问性、图定位、重建、QA、发布分开记录；下载 PDF 或渲染整张图片不会被算作可编辑重建。使用 `python research/queue.py status` 查看动态计数，使用 `python research/queue.py init` 安全补齐新条目。详见 [队列操作与证据门槛](docs/queue.md)。

通用的保守草稿提取：`python research/extract_pdf_figure.py --pdf paper.pdf --config reviewed-config.json --out data/diagrams/paper`。配置必须给出实际检查的页码与裁切范围。图像、源剪裁、数学字体可能需要逐图修正；`outline_fonts` 可保留指定数学字体为可编辑字形路径，字形路径不是可输入新公式的文本框。

批次只重新发布一篇：`python research/refresh_outputs.py --from-build build --paper aspire`。新增论文把完整候选目录（sources、验证、PDF、原图和三种导出）准备好，再运行 `python research/refresh_outputs.py --add-paper build/candidates/paper`；所有引用与哈希通过后才会更新结果索引。用户已授权逐批同步 main；每批重新测试并核实远端哈希。
