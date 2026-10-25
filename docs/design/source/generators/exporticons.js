const fs=require('fs');const root='/path/to/work/';
const h=fs.readFileSync(root+'flowdesign/project/Icons.dc.html','utf8');
const m=h.match(/<script type="text\/x-dc"[^>]*>([\s\S]*?)<\/script>/)[1];
class DCLogic{}
const C=new Function('DCLogic',m+'\nreturn Component;')(DCLogic);
const v=new C().renderVals();
const out={};
for(const k in v){ if(Array.isArray(v[k])) {out[k]=v[k].map(g=>({name:g.name,icons:(g.icons||[]).map(i=>({name:i.name,shapes:i.shapes}))}));} }
fs.writeFileSync(root+'tools/icons.json',JSON.stringify(out));
console.log(Object.keys(out), (out.groups||[]).map(g=>g.name+':'+g.icons.length).join(' | '));
