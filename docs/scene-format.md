# Scene v1 (v0.2 extensions)

Top-level: `schema_version:1`, safe slug `id`, `title`, `canvas:{width,height}`, `provenance`, `nodes`, `edges`. Coordinates are CSS pixels (96 dpi), top-left origin. Canvas is 96–5000 px per dimension. Required provenance: `paper_title`, `paper_url`, `figure`, `page`, `license`, `status` (`figure_recreation`/`conceptual_reconstruction`), `notes`. Figure recreation requires a positive 1-based PDF page and figure label.

Node: unique `id`, `shape`, `x,y,width,height`, optional `label`. Shapes: `rect`, `rounded_rect`, `ellipse`, `diamond`, `text`, `image`, `path`.

Common optional fields: `fill`, `stroke`, `text_color` (#RRGGBB or none), `stroke_width`, `dash`, `fill_opacity`, `stroke_opacity`, `font_size`, `font_family`, `bold`, `italic`, `align` (left/center/right), `text_inset`, `no_wrap`.

Images: `asset` relative to scene directory, `alt`; PNG/JPEG only, no remote or path escape. Images preserve explicit scene bounds; match source aspect ratios. Image labels are not drawn; use separate text nodes. A raster's internal labels remain raster.

Paths: `commands` in local node coordinates, sequence of `{moveTo:{x,y}}`, `{lineTo:{x,y}}`, `{cubicBezTo:{x1,y1,x2,y2,x,y}}`, `{quadBezTo:{x1,y1,x,y}}`, `{close:{}}`. Control points can lie outside the viewport when representing curves; finite coordinates required. Compound fill winding must be visually checked against source.

Edges: unique `id`, `source`, `target`; optional `label`, `arrow`, `head_arrow`, `stroke`, `stroke_width`, `dash`, `kind` (straight/elbow/curved), `source_port`/`target_port` (left/right/top/bottom), `waypoints:[{x,y}]`. PPTX waypoints become attached line segments with transparent helper anchors. Freeform path arrows have no automatic node attachment.

Objects render in listed order, with native connectors above nodes. Source-extracted freeform paths retain source ordering as nodes. Source extraction records `source_seqno` to explain layering.

Manifest: source SHA-256, output hashes, provenance and construction counts. Counts are not fidelity scores; native node totals can include transparent anchor helpers. Freeform-path counts, text-object counts, picture counts and semantic-connector counts are reported separately. Export cannot grant human review, so `visual_review` remains pending.
