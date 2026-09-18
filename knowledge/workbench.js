const $ = id => document.getElementById(id);
let current = null, busy = false, sourceRequest = null, sourceEpoch = 0, sourceTrigger = null;
const names = {gdpr:'GDPR',dsa:'Digital Services Act',dma:'Digital Markets Act','ai-act':'AI Act'};
function el(tag,text,cls) { const node=document.createElement(tag);node.textContent=text;if(cls)node.className=cls;return node; }
function link(url,label) {
  const anchor=el('a',label);
  try {const u=new URL(url);if(u.protocol==='https:'){anchor.href=u.href;anchor.target='_blank';anchor.rel='noopener noreferrer';}}catch{}
  return anchor;
}
function resetSource() {
  sourceRequest?.abort();sourceEpoch++;
  $('source-status').textContent='';
  $('details').replaceChildren(el('p','选择“核对完整条文”，阅读摘录前后的条件。','muted'));
}
async function showSource(hit,trigger) {
  if(trigger)sourceTrigger=trigger;
  sourceRequest?.abort();const epoch=++sourceEpoch;sourceRequest=new AbortController();
  const box=$('details');box.replaceChildren();
  const back=el('button','返回检索结果','secondary');back.onclick=()=>sourceTrigger?.focus();
  box.append(back,el('h3',hit.source_title),link(hit.source_url,'打开官方原文'));
  box.setAttribute('tabindex','-1');box.focus();$('source-status').textContent='正在读取完整条文';
  try {
    const response=await fetch('/sources/'+encodeURIComponent(hit.source_id),{signal:sourceRequest.signal});
    const data=await response.json();if(epoch!==sourceEpoch)return;
    if(!response.ok)throw Error(data.error||'读取失败');
    box.append(el('p',data.text,'original'));
    box.append(el('p',data.document_version==='original_oj'?`原始公报 ${data.publication_date} / ${data.celex}`:'调用者提供的版本','muted'));
    box.append(el('p','采集时间 '+data.retrieved_at,'muted'));
    $('source-status').textContent='已显示完整条文';
  }catch(error) {
    if(epoch!==sourceEpoch||error.name==='AbortError')return;
    $('source-status').textContent='完整条文读取失败，请重试或打开官方原文。';
    const retry=el('button','重新读取','secondary');retry.onclick=()=>showSource(hit);box.append(retry);
  }
}
function stale() {
  current=null;$('export').disabled=true;$('export-json').disabled=true;
  $('status').textContent='问题或范围已修改，请重新检索。';resetSource();
  $('result').replaceChildren(el('p','重新检索后显示当前问题的条文。','muted'));
}
async function loadCoverage() {
  try {
    const response=await fetch('/coverage');if(!response.ok)throw Error();const data=await response.json();
    $('coverage').textContent=`已收录 ${data.sources} 条资料`;
    $('scope-note').textContent=data.document_versions.includes('original_oj')?'查询英文原始公报，核对后续修订后再判断当前义务。':'当前使用示例或调用者提供的资料，请核对出处。';
    for(const id of data.instruments) {const option=el('option',names[id]||id);option.value=id;$('instrument').append(option);}
    for(const source of data.source_catalog) {const li=el('li','');li.append(link(source.source_url,source.source_title));$('catalog').append(li);}
    if(!data.source_catalog.length)$('catalog').append(el('li','旧索引未保存完整条文，请按运行手册重建。'));
  }catch { $('scope-note').textContent='资料范围读取失败，请刷新重试；输入内容留在本地。'; }
}
$('query-form').addEventListener('submit',async event=>{
  event.preventDefault();if(busy)return;busy=true;current=null;resetSource();
  $('query').readOnly=true;$('instrument').disabled=true;$('submit').disabled=true;
  $('export').disabled=true;$('export-json').disabled=true;document.body.setAttribute('aria-busy','true');
  $('status').textContent='正在检索所选资料';$('result').replaceChildren();
  try {
    const response=await fetch('/search',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({query:$('query').value,instrument:$('instrument').value}),signal:AbortSignal.timeout(30000)});
    const data=await response.json();if(!response.ok)throw Error(data.error||'检索失败，请重试。');current=data;
    if(!data.evidence.length)$('result').append(el('h3','需要进一步核对'),el('p',data.next_step));
    for(const hit of data.evidence) {
      const row=el('section','','source');row.append(el('h3',hit.source_title),el('blockquote',hit.text));
      if(hit.document_version==='original_oj')row.append(el('p',`原始公报 ${hit.publication_date} / ${hit.celex}`));
      const button=el('button','核对完整条文','secondary');button.onclick=()=>showSource(hit,button);row.append(button);$('result').append(row);
    }
    if(data.review_candidates?.length){
      const candidates=el('details');candidates.id='candidates';candidates.append(el('summary','其他可能相关条文，需进一步核对'));
      for(const hit of data.review_candidates){const row=el('p');const button=el('button',hit.source_title,'secondary');button.onclick=()=>showSource(hit,button);row.append(button);candidates.append(row);}
      $('result').append(candidates);
    }
    $('status').textContent=data.evidence.length?`找到 ${data.evidence.length} 条摘录，点击核对完整条件。`:data.next_step;
    $('export').disabled=false;$('export-json').disabled=false;
  }catch(error) {
    $('status').textContent=error.name==='TimeoutError'?'检索超时，问题已保留，请重试。':`${error.message} 问题已保留。`;
    $('result').append(el('p','未生成本次结果，重试不会丢失问题。','muted'));
  }finally {
    busy=false;$('query').readOnly=false;$('instrument').disabled=false;$('submit').disabled=false;
    document.body.setAttribute('aria-busy','false');
  }
});
function download(content,type,filename) {
  const url=URL.createObjectURL(new Blob([content],{type})),anchor=document.createElement('a');
  anchor.href=url;anchor.download=filename;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  $('status').textContent='核对单已导出，包含来源、版本和待核对事项。';
}
$('export').onclick=()=>{if(current)download(current.markdown,'text/markdown;charset=utf-8','eu-law-review.md');};
$('export-json').onclick=()=>{if(current)download(JSON.stringify(current,null,2),'application/json','eu-law-evidence.json');};
$('query').addEventListener('input',stale);$('instrument').addEventListener('change',stale);
$('query').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();$('query-form').requestSubmit();}});
loadCoverage();
