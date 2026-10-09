"""Package final validated samples plus a separate durable source archive."""
import hashlib,json,shutil,zipfile,subprocess
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];B=R/'build';FINAL=B/'final-v0.2' if (B/'final-v0.2').exists() else B/'final';release=B/'release-v0.2';release.mkdir(exist_ok=True)
for name,folder in [('aspire-figure-1','aspire'),('roboreact-figure-2','roboreact')]:
 for ext in ['png','drawio']:shutil.copy2(B/folder/(name+'.'+ext),release/(name+'.'+ext))
 shutil.copy2(FINAL/(name+'.pptx'),release/(name+'.pptx'))
 shutil.copy2(B/folder/(name+'.manifest.json'),release/(name+'.manifest.json'))
shutil.copy2(B/'aspire-original.png',release/'aspire-original.png')
# Prefer the source-image path logged by the reconstruction program.
source=R/'research/references/roboreact-original.png'
if not source.exists():source=Path('/tmp/paperfig/roboreact-original.png')
shutil.copy2(source,release/'roboreact-original.png')
(release/'comparison.html').write_text('''<!doctype html><html lang="zh"><meta charset="utf-8"><title>论文图原图与可编辑重建对照</title><style>body{font:16px system-ui;background:#f4f6f8;color:#16212b;margin:24px}main{max-width:1500px;margin:auto}section{background:white;padding:18px;margin:20px 0;border-radius:10px}img{max-width:100%;height:auto;border:1px solid #ddd}h1{font-size:26px}h2{font-size:22px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}a{color:#17629e}small{color:#56636e}@media(max-width:900px){.pair{grid-template-columns:1fr}}</style><main><h1>原图与可编辑重建对照 · v0.2</h1><p>优先保留布局、配色和细节。右侧为重建预览；编辑请打开 PPTX 或 draw.io 文件。图片内部像素不能逐对象编辑，自由路径不等于吸附连接线。</p>'''+''.join(f'''<section><h2>{title}</h2><p><a href="{name}.pptx">PowerPoint</a> · <a href="{name}.drawio">draw.io</a></p><div class="pair"><div><h3>论文原图</h3><img src="{prefix}-original.png" alt="{title} 论文原图"></div><div><h3>可编辑重建预览</h3><img src="{name}.png" alt="{title} 重建预览"><small>{note}</small></div></div></section>''' for name,prefix,title,note in [('aspire-figure-1','aspire','ASPIRE · Figure 1','保留原 PDF 自由路径；字体替换与照片/图标像素边界有说明'),('roboreact-figure-2','roboreact','RoboReact · Figure 2','原图为整幅位图；面板、普通文字及结构图人工重建，照片/图标/公式为独立栅格小图')])+'''<p>这是私下转换，不代表取得公开再发布许可。详见 README.txt 和各图来源说明。</p></main></html>''',encoding='utf-8')
for name in ['paper-figure-v0.2-samples.zip','paper-figure-v0.2-source.zip']:
 dest=B/name
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
  if 'samples' in name:
   for p in sorted(release.rglob('*')):
    if p.is_file():z.write(p,p.relative_to(release))
  else:
   for p in sorted(R.rglob('*')):
    rel=p.relative_to(R)
    if p.is_file() and not any(x in {'build','.git','__pycache__','node_modules','.venv','dist'} or x.endswith('.egg-info') for x in rel.parts):z.write(p,Path('paper-figure')/rel)
 print(dest,dest.stat().st_size,hashlib.sha256(dest.read_bytes()).hexdigest())
# Single durable deliverable: all outputs plus all required source and new local history.
complete=B/'paper-figure-v0.2-complete.zip'
with zipfile.ZipFile(complete,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(release.rglob('*')):
  if p.is_file():z.write(p,Path('samples')/p.relative_to(release))
 for p in sorted(R.rglob('*')):
  rel=p.relative_to(R)
  if p.is_file() and not any(x in {'build','.git','__pycache__','node_modules','.venv','dist'} or x.endswith('.egg-info') for x in rel.parts):z.write(p,Path('source')/rel)
 if (B/'source-history.bundle').exists():z.write(B/'source-history.bundle','source/history.bundle')
print(complete,complete.stat().st_size,hashlib.sha256(complete.read_bytes()).hexdigest())
