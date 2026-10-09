# Source provenance and faithful reconstruction

## Repository catalog

All 137 date-prefixed paper entries are transcribed from the exact README at commit `bec07f586ad17c7d3285c7b5b38af863a646971a`:
https://github.com/EDEM-AI/Awesome-Papers-for-Robotic-SKill-Discovery/blob/bec07f586ad17c7d3285c7b5b38af863a646971a/README.md

Recovered again on 2026-10-09. Six category counts are 3,39,18,23,26,28. Date/title/project/code fields reproduce the README; they are not independently verified bibliographic records. Missing links remain null. A catalog entry does not claim that its figure has been reconstructed.

## ASPIRE

Lu et al., *ASPIRE: Agentic /Skills Discovery for Robotics*, arXiv:2607.00272v1, Figure 1, PDF page 2.
https://arxiv.org/abs/2607.00272v1

Actual PDF page rendered and inspected. Source includes native text and vector graphics alongside raster robot/photo panels and some miniature diagrams. Source layout crop approximately (61,84,534,368) PDF points. Text fonts include NVIDIA Sans, Consolas, Courier New and Helvetica Neue; font substitutions must be disclosed where used.

The arXiv license link is CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
The PDF also prints © 2026 NVIDIA. All rights reserved. Preserve source attribution; do not assume independent logo rights.

## RoboReact

He et al., *RoboReact: Agentic Skill Distillation from Generated Egocentric Videos for Generalizable Whole-Body Manipulation*, arXiv:2608.03387v2, Figure 2, PDF page 3.
https://arxiv.org/abs/2608.03387v2

Actual page and original pixels inspected. The entire source figure is one 2256×1000 raster image, xref184, mapped to PDF bbox (54,54.003,557.9904,277.403). Its labels and graph primitives cannot be recovered as PDF vector objects.

The revised figure manually recreates source panel arrangement, colors, labels and keyframe graphs as native editable shapes/text/connectors. All source photograph panels are retained as individual crops. Thirty small raster assets remain:17 photo/depth/pose panels,12 decorative icons/marks,and1 mathematical equation strip. Those pixel contents, fine diagnostic overlays, and equation symbols are not editable. Four blue iteration arrows and the large orange execution arrow are native freeform shapes. Policy graph circles and connectors are native; curve shape and dash spacing approximate the original. These are disclosed modifications rather than a claim of pixel-exactness.

ArXiv links only its non-exclusive distribution license: https://arxiv.org/licenses/nonexclusive-distrib/1.0/
No open figure-reuse license was verified. This is a private user-requested adaptation, not permission for public redistribution. No public GitHub upload is requested or performed.

Earlier semantic reconstruction remains separately under the legacy examples. It must not be presented as the newly faithful version.

## Reference-only item

Agentic Skill Discovery, arXiv:2405.15019v2, Figure2/page3 was inspected in earlier research. Its source license is CC BY-NC-ND4.0. No modified figure deliverable is included; the catalog records the caveat.

## Reproduction

`source-provenance.json` records source hashes and versions. PDFs remain temporary source material, not bundled bulk literature. `build_roboreact_faithful.py` records the manual coordinates and original-image crop rectangles; it accepts `--pdf PATH` for the versioned source PDF or `--image PATH` for the original 2256×1000 figure image, validates source dimensions, and records its SHA-256. The portable export inputs are committed scene JSON and individual assets, not the temporary source file. PPTX and draw.io previews require independent visual QA; structural editability alone does not prove source fidelity.
