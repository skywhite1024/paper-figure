// Optional dot-environment validation, separate from portable exporter.
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const root=path.resolve(process.argv[2]||'.');
const skill=process.env.PRESENTATION_SKILL_TOOLS || '/home/agent/.codex/skills/builtins/presentations/container_tools';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'artifact_tool_utils.mjs')).href);
const finalDir=process.env.PAPER_FIGURE_FINAL_DIR||`${root}/build/final`;const receiptSuffix=finalDir.endsWith('/final')?'':'.'+path.basename(finalDir);await fs.mkdir(finalDir,{recursive:true});await fs.mkdir(`${root}/build/validation`,{recursive:true});
for(const name of (process.argv.length>3?process.argv.slice(3):['aspire-figure-1','roboreact-figure-2'])){
 const d=JSON.parse(await fs.readFile(`${root}/data/diagrams/${name}.json`,'utf8'));
 const folder=name.startsWith('aspire')?'aspire':'roboreact';
 const result=await finalizePresentation({workspaceDir:root,candidatePath:`${root}/build/${folder}/${name}.pptx`,finalPath:`${finalDir}/${name}.pptx`,pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,integrityValidatorPath:`${skill}/inspect_presentation_package_integrity.py`,layoutValidatorPath:`${skill}/inspect_presentation_layout_geometry.py`,layoutArgs:['--expected-slide-size-emu',`${Math.round(d.canvas.width*9525)},${Math.round(d.canvas.height*9525)}`,'--validate-bullet-geometry','--validate-heading-fit'],explicitTotalSlideCount:1,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial','Courier New','Consolas']},verifyArtifactToolImport:true,receiptPath:`${root}/build/validation/${name}${receiptSuffix}.validation.json`});
 console.log(name,result.finalSha256);
}
