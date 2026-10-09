# Conservative source-figure extraction

`research/extract_pdf_figure.py` consumes a reviewed PDF/crop configuration and writes a **draft** scene, discrete assets, and an original comparison PNG. It does not discover the right paper or figure and never certifies fidelity.

Configuration keys: `id`, `paper_title`, `paper_url` (fixed version where available), `figure`, 1-based `page`, `crop: [x0,y0,x1,y1]` in PDF points, `license`, `notes`; optional `scale` (default 2).

- Native paths retain source colors and source paint order; freeform arrows lack semantic node attachments.
- Native text is split by actual character origins to avoid combining distant labels. Source font names are retained; compatible fonts are substituted.
- `outline_fonts: ["CMM", "CMSY", "CMEX"]` preserves selected mathematical fonts as editable glyph paths. These are not live equation/text objects.
- `raster_regions: [{"bbox": [...], "reason": "individual photo", "seqno": 42}]` renders only reviewed discrete source insets. Completely contained text/paths are removed to avoid duplicate visible labels. Large aggregate region coverage is rejected.
- `reviewed_raw_images` allows specifically inspected axis-aligned source image indices. An object `{ "index": 0, "source_seqno": 9, "clip_shape": "ellipse" }` can recover a reviewed source ellipse mask. Unreviewed clipping is never assumed correct.
- Warnings record source clipping groups, crop-boundary paths, rotated text, partial inset intersections, and unhandled images. Every warning needs source-pixel review before publication as a recreation; false positives are explained in per-paper QA.

The source PDF may contain flattened diagrams or bad font encodings. Those require manual native reconstruction/postprocessing, not a full-picture slide. Compare both the exported PNG and actual editor rendering with the original; editor fonts and compound-path fill rules can differ. Configurations and any postprocessor belong beside source evidence, and must be retained with each checkpoint.

## Editable rotated labels

Scene nodes accept `rotation` in clockwise degrees (−360…360). The node's x/y/width/height describe the **unrotated** frame; both editors rotate about its center. Validation checks the resulting visible bounding box, so a negative unrotated frame coordinate is allowed only when the rotated object remains inside the canvas. Use native rotated text for ordinary sideways labels rather than tiny raster text strips.

## Source asset integrity

New export manifests bind both the scene JSON and every referenced raster asset. An input modified while a multi-format export is running cancels publication, leaving prior files intact. Paper-bundle validation also compares draw.io's actual embedded image bytes with scene assets, including older manifests, so replacing an asset without changing its filename cannot silently inherit old QA.

## Manual mathematical transcription

For flattened sources, `research/math_glyph.py` and selected paper-specific reconstructors use Matplotlib/STIX to turn **manually checked LaTeX transcriptions** into native glyph-outline paths. Install the optional `.[math]` extra to rerun those scripts. The resulting formulas support path editing, not live equation editing; their LaTeX is retained in scene metadata. This is not automatic equation recognition. Ordinary prose labels remain native typeable text.

Source stroke widths larger than one tenth of the figure extent now emit a transform-unit warning. Some source PDFs expose Office/EMU-scale widths or rotated-transform artifacts through their drawing API. Review the PDF/SVG paint geometry before applying a paper-specific correction; the generic extractor does not guess a scale.

## Publishing multiple reviewed candidates

`python research/refresh_outputs.py --add-paper build/candidates/a --add-paper build/candidates/b` validates the entire proposed batch before moving any complete paper folder into output. It stages the existing output tree once, avoiding one full archival copy per candidate. Existing paper replacement remains a separate explicit `--from-build ... --paper ...` operation; regeneration invalidates previous QA until the new bytes are reviewed.

Freeform paths intentionally have no attached text in the PPTX backend. Validation rejects nonempty `label` on a path instead of silently losing it; put the label in a separate native text node. This preserves matching visible text across the two export formats.
