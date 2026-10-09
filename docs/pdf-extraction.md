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
