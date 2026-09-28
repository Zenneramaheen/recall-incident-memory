const $ = id => document.getElementById(id);
let example, busy = false;
function status(message, kind = '') { $('status').textContent = message; $('status').className = kind; $('status').hidden = false; }
function setBusy(value) { busy = value; document.querySelectorAll('button, input, textarea').forEach(el => el.disabled = value); }
async function request(path, data, message) {
  if (busy) return;
  setBusy(true); status(message, 'working');
  try {
    const response = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json','X-Incident-App':'1'}, body:JSON.stringify(data)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Request failed.');
    return result;
  } catch (error) { status(error.message, 'error'); throw error; }
  finally { setBusy(false); }
}
function switchView(learn) {
  $('learn-view').hidden = !learn; $('investigate-view').hidden = learn;
  $('nav-learn').classList.toggle('active', learn); $('nav-investigate').classList.toggle('active', !learn);
}
$('nav-learn').onclick = () => switchView(true);
$('nav-investigate').onclick = () => switchView(false);
function resetResults() {
  $('evidence').replaceChildren();
  const empty = document.createElement('div'); empty.className = 'empty';
  const icon = document.createElement('div'); icon.className = 'orbit'; icon.textContent = '◎';
  const heading = document.createElement('h3'); heading.textContent = 'A little history goes a long way.';
  const p = document.createElement('p'); p.textContent = 'Run an investigation to see the facts behind the recommendation.';
  empty.append(icon, heading, p); $('evidence').append(empty);
  $('recommendation').textContent = 'Your diagnostic plan will appear here.';
  $('evidence-count').textContent = '—'; $('result-label').textContent = 'AWAITING AN ALERT'; $('sources-panel').hidden = true;
}
$('bank').addEventListener('input', resetResults);
$('service').addEventListener('input', resetResults);
$('environment').addEventListener('input', resetResults);
$('alert').addEventListener('input', resetResults);
function fillAlert() { if (!example) return; $('alert').value = example.alert; $('service').value = example.incident.service; $('environment').value = example.incident.environment; resetResults(); }
function fillResolution() {
  if (!example) return;
  const i = example.incident;
  for (const [field, value] of Object.entries({'incident-id':i.id,'resolved-service':i.service,'resolved-environment':i.environment,symptoms:i.symptoms,'root-cause':i.root_cause,'successful-fix':i.successful_fix,'failed-attempts':i.failed_attempts.join('\n'),verification:i.verification})) $(field).value = value;
  $('synthetic').checked = true; $('confirmed').checked = false;
}
$('load-sample').onclick = fillAlert; $('load-resolution').onclick = fillResolution;
function showFacts(target, facts) {
  target.replaceChildren();
  if (!facts.length) { const p = document.createElement('p'); p.className = 'placeholder'; p.textContent = 'No matching facts returned. Save a resolution to build memory for this service and environment.'; target.append(p); return; }
  for (const fact of facts) {
    const item = document.createElement('article'); item.className = 'fact';
    const id = document.createElement('div'); id.className = 'fact-id'; id.textContent = fact.id || 'Source memory';
    const text = document.createElement('p'); text.textContent = fact.text; item.append(id, text); target.append(item);
  }
}
// Render a deliberately small Markdown subset using text nodes, never raw model HTML.
function inline(parent, text) {
  for (const part of text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)) {
    if (part.startsWith('**') && part.endsWith('**')) { const node = document.createElement('strong'); node.textContent = part.slice(2,-2); parent.append(node); }
    else if (part.startsWith('`') && part.endsWith('`')) { const node = document.createElement('code'); node.textContent = part.slice(1,-1); parent.append(node); }
    else parent.append(document.createTextNode(part));
  }
}
function markdown(target, text) {
  target.replaceChildren(); let list = null;
  for (const line of text.split('\n')) {
    if (!line.trim()) { list = null; continue; }
    if (/^\s*(---|\*\*\*)\s*$/.test(line)) { target.append(document.createElement('hr')); list = null; continue; }
    const heading = line.match(/^#{1,4}\s+(.+)/), bullet = line.match(/^\s*(?:[-*]|\d+\.)\s+(.+)/);
    if (bullet) { if (!list) { list = document.createElement('ul'); target.append(list); } const li = document.createElement('li'); inline(li, bullet[1]); list.append(li); }
    else { list = null; const node = document.createElement(heading ? (line.startsWith('###') ? 'h3' : 'h2') : 'p'); inline(node, heading ? heading[1] : line); target.append(node); }
  }
}
$('new-bank').onclick = async () => {
  try { const result = await request('/api/new-bank', {}, 'Creating a fresh memory bank…'); $('bank').value = result.bank; resetResults(); status('Fresh bank ready. Investigate the sample alert before saving a resolution.'); } catch {}
};
$('investigate-form').onsubmit = async event => {
  event.preventDefault(); resetResults(); $('result-label').textContent = 'RECALLING EXPERIENCE';
  try {
    const result = await request('/api/investigate', {bank:$('bank').value.trim(),alert:$('alert').value,service:$('service').value.trim(),environment:$('environment').value.trim()}, 'Recalling incidents and preparing diagnostic steps. This can take a minute…');
    showFacts($('evidence'), result.evidence); $('evidence-count').textContent = result.evidence.length;
    markdown($('recommendation'), result.recommendation); $('result-label').textContent = result.evidence.length ? 'GROUNDED IN MEMORY' : 'NO MATCHING MEMORY';
    const sources = result.reflection_sources || []; showFacts($('sources'), sources); $('sources-panel').hidden = !sources.length;
    status(result.evidence.length ? `Investigation complete. ${result.evidence.length} facts recalled from Hindsight.` : 'No matching memory returned. Showing the generic diagnostic checklist.');
  } catch { $('result-label').textContent = 'REQUEST FAILED'; }
};
$('resolution-form').onsubmit = async event => {
  event.preventDefault();
  const incident = {id:$('incident-id').value,service:$('resolved-service').value.trim(),environment:$('resolved-environment').value.trim(),symptoms:$('symptoms').value,root_cause:$('root-cause').value,successful_fix:$('successful-fix').value,failed_attempts:$('failed-attempts').value.split('\n').map(x=>x.trim()).filter(Boolean),verification:$('verification').value,synthetic:$('synthetic').checked};
  try {
    const result = await request('/api/retain', {bank:$('bank').value.trim(),incident}, 'Saving the resolution and extracting memories…');
    resetResults(); $('confirmed').checked = false;
    status(`Saved ${result.incident_id}. Return to Investigate to see what the agent recalls.`);
  } catch {}
};
fetch('/api/example').then(r=>{if(!r.ok)throw new Error(); return r.json();}).then(data=>{example=data; fillAlert(); fillResolution();}).catch(()=>status('Could not load the sample. You can enter an alert manually.', 'error'));
