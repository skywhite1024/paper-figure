"""Conservative PDF vector extraction; reviewed crop/region configuration is required.

Images and clipped paths are never silently converted into a full-figure backdrop.
A draft can be extracted but is not evidence of visual QA or source identity.
"""
import hashlib
import json
import math
import re
from pathlib import Path
from .model import ValidationError, require, validate



def source_dash(raw, width, scale):
    """Keep scaled source intervals; PPTX uses an explicitly approximate native preset.

    Draw.io receives absolute intervals normalized to stroke width. Neither backend
    currently carries PDF dash phase or cap semantics. Zero-length PDF dots become
    a tiny positive interval for safe dashPattern rendering; raw source is retained.
    """
    if raw is None:
        raw = '[] 0'
    require(isinstance(raw, str), 'PDF dash pattern must be a string')
    number = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
    match = re.fullmatch(r'\s*\[([^]]*)\]\s*(' + number + r')\s*', raw)
    require(match, 'Unsupported PDF dash syntax')
    tokens = match[1].split()
    require(all(re.fullmatch(number, token) for token in tokens), 'Unsupported PDF dash array syntax')
    values = [float(token) for token in tokens]
    require(math.isfinite(width) and width >= 0 and math.isfinite(scale) and scale > 0, 'Invalid dash width/scale')
    phase = float(match[2])
    require(all(math.isfinite(value) and value >= 0 for value in values) and math.isfinite(phase) and phase >= 0,
            'PDF dash intervals/phase must be finite and nonnegative')
    if not values:
        return {'dash': False, 'source_dash': raw}
    require(any(values) and len(values) <= 32, 'Invalid or oversized PDF dash array')
    if len(values) % 2:
        values *= 2
    unit = width if width > 0 else 1
    on = values[::2]
    if len(on) == 1:
        style = 'dotted' if on[0] / unit <= 1.5 else 'dashed'
    elif len(on) == 2 and on[0] > on[1] * 1.8 and on[1] / unit <= 1.5:
        style = 'dash-dot'
    elif len(on) == 3 and on[0] > max(on[1:]) * 1.8 and max(on[1:]) / unit <= 1.5:
        style = 'dash-dot-dot'
    else:
        style = 'dashed'
    return {'dash': True, 'dash_style': style, 'source_dash': raw,
            'dash_pattern': [max(value * scale, .001) for value in values], 'dash_phase': phase * scale,
            'dash_approximation': 'PPTX uses the closest supported native preset, not exact PDF dash lengths. '
                                  'Draw.io retains interval lengths; PDF phase/caps are not preserved; zero intervals become 0.001 scene units.'}


def extract(pdf, config, destination):
    try:
        import fitz
    except ImportError as exc:
        raise ValidationError('PDF extraction requires the pdf optional dependencies') from exc
    pdf, destination = Path(pdf), Path(destination)
    require(isinstance(config, dict), 'configuration must be an object')
    for key in ['id', 'paper_title', 'paper_url', 'figure', 'license', 'notes']:
        require(isinstance(config.get(key), str) and config[key].strip(), key + ' required')
    require(bool(re.fullmatch(r'[A-Za-z0-9_-]+', config['id'])), 'id must be a safe slug')
    page_number = config.get('page')
    require(type(page_number) is int and page_number > 0, '1-based page required')
    crop_values = config.get('crop')
    require(isinstance(crop_values, list) and len(crop_values) == 4 and
            all(type(v) in (int, float) for v in crop_values), 'crop requires four PDF coordinates')
    scale = config.get('scale', 2)
    require(type(scale) in (int, float) and 0 < scale <= 6, 'invalid extraction scale')
    crop = fitz.Rect(crop_values)
    require(not crop.is_empty and not crop.is_infinite, 'invalid crop')
    require(96 <= crop.width*scale <= 5000 and 96 <= crop.height*scale <= 5000, 'canvas dimensions outside 96..5000')
    destination.mkdir(parents=True, exist_ok=True)
    document = fitz.open(pdf)
    require(page_number <= len(document), 'page exceeds PDF length')
    page = document[page_number - 1]
    require(page.rect.contains(crop), 'crop extends beyond page')
    provenance = {key: config[key] for key in ['paper_title', 'paper_url', 'figure', 'license', 'notes']}
    provenance.update(page=page_number, status='figure_recreation', source_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
                      source_crop_pdf_points=crop_values,
                      extraction_review='pending; native geometry extraction is not visual fidelity approval',
                      font_substitutions='Arial or Courier New; source fonts recorded per text object')
    scene = {'schema_version': 1, 'id': config['id'], 'title': config['paper_title'] + ' · ' + config['figure'],
             'canvas': {'width': crop.width * scale, 'height': crop.height * scale},
             'provenance': provenance, 'nodes': [], 'edges': []}
    def color(value):
        if value is None:
            return 'none'
        if isinstance(value, (float, int)):
            value = (value,) * 3
        if len(value) == 1:
            value = value * 3
        require(len(value) == 3, 'unsupported source color space')
        return '#' + ''.join(f'{round(max(0, min(1, component)) * 255):02X}' for component in value)
    def geometry(rect):
        return dict(x=max(0, (rect.x0-crop.x0)*scale), y=max(0, (rect.y0-crop.y0)*scale),
                    width=max(.01, rect.width*scale), height=max(.01, rect.height*scale))
    regions = []
    for index, region in enumerate(config.get('raster_regions', [])):
        require(isinstance(region, dict) and isinstance(region.get('reason'), str) and region['reason'].strip(),
                'raster region needs explicit reason/editability boundary')
        rect = fitz.Rect(region['bbox'])
        require(crop.contains(rect) and 0 < rect.get_area() < crop.get_area() * .8,
                'raster region must be a discrete inset, not a whole-figure background')
        regions.append((rect, region))
    def excluded(rect):
        return any(region.contains(rect) for region, _ in regions)
    require(sum(rect.get_area() for rect, _ in regions) < crop.get_area()*.8, 'Combined raster inset coverage is too large; manual reconstruction required')
    items, warnings = [], []
    clips = [x for x in page.get_drawings(extended=True) if x.get('type') == 'clip' and fitz.Rect(x['scissor']).intersects(crop)]
    if clips:
        warnings.append(f'{len(clips)} source clipping groups intersect crop; extracted paths require explicit clipping review')
    drawings = page.get_drawings()
    require(isinstance(config.get('outline_fonts', []), list) and all(isinstance(f,str) and f for f in config.get('outline_fonts', [])), 'outline_fonts must contain nonempty font names')
    outlined_fonts = tuple(config.get('outline_fonts', []))
    if outlined_fonts:
        from lxml import etree
        positions = [(c[2][0], c[2][1]) for span in page.get_texttrace()
                     if any(font in span['font'] for font in outlined_fonts) for c in span['chars']
                     if crop.contains(fitz.Rect(c[3]))]
        svg = etree.fromstring(page.get_svg_image(text_as_path=True).encode())
        for element in list(svg.iter()):
            if element is svg or any(a.tag.rsplit('}',1)[-1]=='defs' for a in element.iterancestors()): continue
            tag = element.tag.rsplit('}',1)[-1]
            if tag in ('svg', 'defs', 'g'): continue
            keep = False
            if tag == 'use' and element.get('data-text') is not None:
                values = re.findall(r'[-+]?(?:[0-9]*\.)?[0-9]+(?:[eE][-+]?[0-9]+)?', element.get('transform',''))
                if len(values)==6:
                    x,y = map(float, values[-2:])
                    keep = any(abs(x-px)+abs(y-py)<.08 for px,py in positions)
            if not keep and element.getparent() is not None: element.getparent().remove(element)
        vector_svg = fitz.open(stream=etree.tostring(svg), filetype='svg')
        vector_pdf = fitz.open(stream=vector_svg.convert_to_pdf(), filetype='pdf')
        for drawing in vector_pdf[0].get_drawings():
            drawing['seqno'] += 100000
            drawings.append(drawing)
        provenance['outlined_font_families'] = list(outlined_fonts)
        provenance['outlined_math_limit'] = 'Selected source mathematical fonts preserved as editable glyph outlines, not live equation/text objects.'
    for drawing in drawings:
        rect = fitz.Rect(drawing['rect'])
        if not rect.intersects(crop) and not crop.contains(rect):
            continue
        if excluded(rect):
            continue
        if not crop.contains(rect):
            warnings.append('path crosses crop boundary: ' + str(drawing['seqno']))
            continue
        if any(rect.intersects(region) and not rect.contains(region) for region, _ in regions):
            warnings.append('path partially intersects raster inset: ' + str(drawing['seqno']))
        commands, last = [], None
        def point(value):
            return {'x': (value.x-rect.x0)*scale, 'y': (value.y-rect.y0)*scale}
        def move(value):
            nonlocal last
            if last is None or abs(last.x-value.x)+abs(last.y-value.y) > .0001:
                commands.append({'moveTo': point(value)})
            last = value
        for item in drawing['items']:
            kind = item[0]
            if kind == 'l':
                move(item[1]); commands.append({'lineTo': point(item[2])}); last = item[2]
            elif kind == 'c':
                move(item[1]); a, b, c = item[2:]
                commands.append({'cubicBezTo': {'x1': (a.x-rect.x0)*scale, 'y1': (a.y-rect.y0)*scale,
                                               'x2': (b.x-rect.x0)*scale, 'y2': (b.y-rect.y0)*scale, **point(c)}})
                last = c
            elif kind in ('re', 'qu'):
                box = item[1]
                points = [box.tl, box.tr, box.br, box.bl] if kind == 're' else [box.ul, box.ur, box.lr, box.ll]
                if kind == 're' and len(item) > 2 and item[2] > 0:
                    points.reverse()
                commands.append({'moveTo': point(points[0])})
                commands.extend({'lineTo': point(p)} for p in points[1:]); commands.append({'close': {}}); last = None
            else:
                raise ValidationError('Unsupported source path operation: ' + kind)
        if drawing.get('closePath') and commands:
            commands.append({'close': {}})
        if not commands:
            continue
        node = dict(id=f"pdf-path-{drawing['seqno']}", shape='path', commands=commands, **geometry(rect),
                    fill=color(drawing.get('fill')), stroke=color(drawing.get('color')),
                    stroke_width=float(drawing.get('width') or 0)*scale,
                    fill_opacity=drawing.get('fill_opacity', 1) or 0,
                    stroke_opacity=drawing.get('stroke_opacity', 1) or 0,
                    **source_dash(drawing.get('dashes'), float(drawing.get('width') or 0), scale),
                    source_seqno=drawing['seqno'], source_even_odd=bool(drawing.get('even_odd')))
        if node.get('dash_pattern'):
            provenance['dash_fidelity'] = node['dash_approximation']
        if drawing['seqno'] in config.get('split_compound_paths', []):
            groups = []
            for command in commands:
                if 'moveTo' in command: groups.append([])
                require(groups, 'compound source path must begin with moveTo')
                groups[-1].append(command)
            for group_index, group in enumerate(groups):
                items.append((drawing['seqno'], dict(node, id=node['id']+f'-part-{group_index}', commands=group, reviewed_compound_union=True)))
        else:
            items.append((drawing['seqno'], node))
    for index, span in enumerate(page.get_texttrace()):
        if any(font in span['font'] for font in outlined_fonts): continue
        # One PDF text span can contain distant labels or several lines. Split
        # by character origins rather than creating one giant text frame.
        groups = []
        for char in span['chars']:
            if groups:
                previous = groups[-1][-1]
                dy = abs(char[2][1]-previous[2][1])
                gap = char[3][0]-previous[3][2]
                if dy > max(.5, span['size']*.15) or gap > span['size']*.65 or char[2][0] < previous[2][0]-.1:
                    groups.append([])
            else:
                groups.append([])
            groups[-1].append(char)
        for group_index, chars in enumerate(groups):
            rect = fitz.Rect(chars[0][3])
            for char in chars[1:]: rect |= fitz.Rect(char[3])
            if not crop.contains(rect) or excluded(rect): continue
            label = ''
            previous_right = None
            for i, char in enumerate(chars):
                if i and char[3][0]-previous_right > span['size']*.16 and not label.endswith(' ') and chr(char[0]) != ' ':
                    label += ' '
                label += chr(char[0])
                previous_right = max(previous_right or char[3][2], char[3][2])
            if not label.strip(): continue
            if tuple(span.get('dir', (1, 0))) != (1, 0):
                warnings.append('rotated text needs manual reconstruction: ' + label)
            font = span['font']
            family = ('Courier New' if any(t in font for t in ('Mono', 'Courier', 'Consolas')) else
                      'Times New Roman' if any(t in font for t in ('Times', 'NimbusRom', 'CMR', 'CMTI', 'CMBX')) else
                      'Cambria Math' if any(t in font for t in ('CambriaMath', 'CMMI', 'CMSY', 'CMEX')) else 'Arial')
            items.append((span['seqno'], dict(id=f'pdf-text-{index}-{group_index}', shape='text', label=label, **geometry(rect),
                      font_size=span['size']*scale, font_family=family,
                      bold=any(t in font for t in ('Bold', 'Medi', 'CMBX')), italic=any(t in font for t in ('Italic', 'Oblique', 'CMTI')),
                      text_color=color(span['color']), align='left', text_inset=0, no_wrap=True,
                      source_font=font, source_seqno=span['seqno'])))
    image_boxes = [(seq, fitz.Rect(bbox)) for seq, (kind, bbox) in enumerate(page.get_bboxlog()) if kind in ('fill-image', 'fill-shade')]
    raw_image_sequences = set()
    raster_area = sum(rect.get_area() for rect, _ in regions)
    for raw_spec in config.get('reviewed_raw_images', []):
        raw_index = raw_spec.get('index') if isinstance(raw_spec, dict) else raw_spec
        require(type(raw_index) is int and raw_index >= 0, 'raw image index must be integer')
        blocks = [b for b in page.get_text('dict')['blocks'] if b['type'] == 1]
        require(raw_index < len(blocks), 'raw image index exceeds page images')
        block = blocks[raw_index]; rect = fitz.Rect(block['bbox'])
        require(crop.contains(rect), 'raw image must be fully inside crop; clipping requires manual handling')
        raster_area += rect.get_area()
        require(raster_area < crop.get_area()*.8, 'Combined raw image/inset coverage too large; manual reconstruction required')
        a, b, c, d, _, _ = block['transform']
        require(a > 0 and d > 0 and abs(b)+abs(c) < .001, 'transformed raw image requires manual handling')
        matches = [seq for seq, box in image_boxes if all(abs(x-y) < .01 for x,y in zip(rect,box))]
        if isinstance(raw_spec, dict) and 'source_seqno' in raw_spec:
            matches = [raw_spec['source_seqno']]
            require(any(seq == matches[0] for seq, _ in image_boxes), 'Explicit image sequence not found')
        require(len(matches)==1, 'ambiguous image paint order; manual reconstruction required')
        seq = matches[0]; raw_image_sequences.add(seq)
        pix = fitz.Pixmap(block['image'])
        if block.get('mask'):
            # A separate PDF soft mask requires an alpha-free base pixmap.
            if pix.alpha:
                pix = fitz.Pixmap(pix, 0)
            pix = fitz.Pixmap(pix, fitz.Pixmap(block['mask']))
        name = f'{config["id"]}-source-image-{raw_index}.png'; pix.save(destination/name)
        if isinstance(raw_spec, dict) and raw_spec.get('clip_shape') == 'ellipse':
            # A reviewed source ellipse clip applied to this isolated image only.
            from PIL import Image, ImageDraw, ImageChops
            im = Image.open(destination/name).convert('RGBA')
            mask = Image.new('L', (im.width*4, im.height*4))
            ImageDraw.Draw(mask).ellipse((0, 0, mask.width, mask.height), fill=255)
            mask = mask.resize(im.size, Image.Resampling.LANCZOS)
            im.putalpha(ImageChops.multiply(im.getchannel('A'), mask)); im.save(destination/name)
        items.append((seq, dict(id=f'pdf-source-image-{raw_index}', shape='image', asset=name,
                              alt='Reviewed original raster inset; its internal pixels are not editable', **geometry(rect))))
    for seq, rect in image_boxes:
        if seq not in raw_image_sequences and rect.intersects(crop) and not any(region.contains(rect & crop) for region, _ in regions):
            warnings.append(f'unhandled image/shading at seq {seq}: {list(rect)}; requires reviewed raster region')
    for index, (rect, region) in enumerate(regions):
        name = f'{config["id"]}-raster-{index}.png'
        page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False).save(destination/name)
        seq = region.get('seqno', max([s for s, b in image_boxes if b.intersects(rect)], default=0))
        items.append((seq, dict(id=f'pdf-raster-{index}', shape='image', asset=name, alt=region['reason'], **geometry(rect))))
    scene['nodes'] = [node for _, node in sorted(items, key=lambda pair: pair[0])]
    provenance['extraction_warnings'] = warnings
    require(any(node['shape'] != 'image' for node in scene['nodes']), 'No editable source objects; manual reconstruction required')
    validate(scene, destination)
    (destination/(config['id']+'.json')).write_text(json.dumps(scene, ensure_ascii=False, indent=2)+'\n')
    page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=crop, alpha=False).save(destination/(config['id']+'-original.png'))
    document.close()
    return scene
