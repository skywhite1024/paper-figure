import fs from 'node:fs/promises';
import path from 'node:path';
import { Presentation, PresentationFile } from '@oai/artifact-tool';
const d=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const p=Presentation.create({slideSize:d.canvas});p.theme.defaultFont='Arial';
const slide=p.slides.add();slide.background.fill='#FFFFFF';slide.speakerNotes.text=JSON.stringify(d.provenance,null,2);
const shapes=new Map();
const fill=(v,opacity=1)=>v==='none'?'none':(opacity<1?`${v}/${Math.round(opacity*100)}`:v);
for(const n of d.nodes){
 const position={left:n.x,top:n.y,width:n.width,height:n.height};
 if(n.shape==='image'){
  const b=await fs.readFile(path.resolve(d.asset_base,n.asset));slide.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:n.asset.toLowerCase().endsWith('.png')?'image/png':'image/jpeg',alt:n.alt,position,fit:'fill'});
  shapes.set(n.id,slide.shapes.add({name:n.id,geometry:'rect',position,fill:'none',line:{fill:'none',width:0}}));continue;
 }
 const line={fill:fill(n.shape==='text'?'none':n.stroke||'#334155',n.stroke_opacity),width:n.shape==='text'?0:(n.stroke_width??1.5),style:n.dash?'dashed':'solid'};
 const shape=slide.shapes.add({name:n.id,geometry:{rect:'rect',rounded_rect:'roundRect',ellipse:'ellipse',diamond:'diamond',text:'textbox',path:'custom'}[n.shape],position,fill:fill(n.shape==='text'?'none':n.fill||'#FFFFFF',n.fill_opacity),line,...(n.shape==='path'?{customPaths:[{width:n.width,height:n.height,commands:n.commands}]}:{})});
 if(n.shape!=='path'){
  shape.text=n.label||'';shape.text.style={fontSize:n.font_size||20,typeface:n.font_family||'Arial',bold:!!n.bold,italic:!!n.italic,color:n.text_color||'#111111',alignment:n.align||'center',verticalAlignment:'middle',insets:n.text_inset??2,wrap:n.no_wrap?'none':'square'};
 }
 shapes.set(n.id,shape);
}
for(const e of d.edges){
 const via=(e.waypoints||[]).map((q,i)=>slide.shapes.add({name:`${e.id}-waypoint-${i}`,geometry:'rect',position:{left:q.x-.25,top:q.y-.25,width:.5,height:.5},fill:'none',line:{fill:'none',width:0}}));const chain=[shapes.get(e.source),...via,shapes.get(e.target)];
 for(let i=0;i<chain.length-1;i++){
  const c=slide.shapes.connect(chain[i],chain[i+1],{kind:via.length?'straight':e.kind||'straight',...(i===0?{fromSide:e.source_port||'right'}:{}),...(i===chain.length-2?{toSide:e.target_port||'left'}:{}),line:{fill:e.stroke||'#475569',width:e.stroke_width??2,style:e.dash?'dashed':'solid'},head:{type:e.head_arrow&&i===0?'triangle':'none',width:'med',length:'med'},tail:{type:e.arrow===false||i!==chain.length-2?'none':'triangle',width:'med',length:'med'}});c.bringToFront();
 }
 if(e.label){const a=d.nodes.find(n=>n.id===e.source),b=d.nodes.find(n=>n.id===e.target);const n=slide.shapes.add({geometry:'textbox',position:{left:(a.x+a.width+b.x)/2-70,top:(a.y+b.y+a.height)/2-27,width:140,height:24},fill:'#FFFFFF',line:{fill:'none',width:0}});n.text=e.label;n.text.style={fontSize:16,typeface:'Arial',alignment:'center',insets:0};}
}
await (await PresentationFile.exportPptx(p)).save(d.output);
if(d.preview){const png=await p.export({slide,format:'png',scale:1});await fs.writeFile(d.output.replace(/\.pptx$/,'.png'),new Uint8Array(await png.arrayBuffer()));}
