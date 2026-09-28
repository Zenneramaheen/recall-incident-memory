const $ = id => document.getElementById(id);
let session, state, busy = false;
const buttons = [...document.querySelectorAll('button')];
function notice(text, error=false) { $('notice').hidden=false; $('notice').textContent=text; $('notice').className=error?'error':''; }
async function api(path, payload={}) {
  const response = await fetch('/api/lab/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Incident-App':'1'},body:JSON.stringify({session,...payload})});
  const data = await response.json();
  // Checkout deliberately returns HTTP 503 on a simulated failure.
  if (!response.ok && !data.checkout_status) throw new Error(data.error || 'Request failed.');
  return data;
}
function guide(n,title,copy){$('step-number').textContent=n;$('guide-title').textContent=title;$('guide-copy').textContent=copy;}
function textNode(tag,text,className){const n=document.createElement(tag);n.textContent=text;if(className)n.className=className;return n;}
function inline(parent,text){for(const part of text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)){if(part.startsWith('**')&&part.endsWith('**'))parent.append(textNode('strong',part.slice(2,-2)));else if(part.startsWith('`')&&part.endsWith('`'))parent.append(textNode('code',part.slice(1,-1)));else parent.append(document.createTextNode(part));}}
function markdown(parent,text){
  parent.replaceChildren(); let list=null,table=null;
  for(const line of text.split('\n')){
    if(!line.trim()){list=null;continue;}
    if(/^\s*(---|\*\*\*)\s*$/.test(line)){parent.append(document.createElement('hr'));table=null;continue;}
    if(line.trim().startsWith('|')&&line.trim().endsWith('|')){
      const cells=line.trim().slice(1,-1).split('|').map(x=>x.trim());
      if(cells.every(x=>/^:?-+:?$/.test(x)))continue;
      const first=!table;
      if(!table){table=document.createElement('table');parent.append(table);}
      const row=document.createElement('tr');
      for(const cell of cells){const td=document.createElement(first?'th':'td');inline(td,cell);row.append(td);}
      table.append(row);list=null;continue;
    }
    table=null;
    const h=line.match(/^#{1,4}\s+(.+)/),b=line.match(/^\s*(?:[-*]|\d+\.)\s+(.+)/);
    if(b){if(!list){list=document.createElement('ul');parent.append(list);}const li=document.createElement('li');inline(li,b[1]);list.append(li);}
    else{list=null;const n=document.createElement(h?'h3':'p');inline(n,h?h[1]:line);parent.append(n);}
  }
}
function renderComparison(comparison) {
  const panel = $('comparison'); panel.replaceChildren();
  if (!comparison) { panel.hidden = true; return; }
  panel.hidden = false; panel.className = 'comparison '+comparison.status;
  const eyebrow = textNode('span', 'WHY MEMORY '+(comparison.status === 'applies' ? 'APPLIES' : comparison.status === 'conflict' ? 'DOES NOT APPLY' : 'IS NOT AVAILABLE'), 'comparison-eyebrow');
  const title = textNode('h3', comparison.title);
  const summary = textNode('p', comparison.summary, 'comparison-summary');
  panel.append(eyebrow, title, summary);
  const grid = document.createElement('div'); grid.className = 'comparison-grid';
  const addColumn = (heading, values, kind) => { const column=document.createElement('section'); column.className='comparison-column '+kind; column.append(textNode('h4',heading)); if(values.length){const list=document.createElement('ul'); for(const value of values) list.append(textNode('li',value)); column.append(list);} else column.append(textNode('p','No conflicting signals found.')); grid.append(column); };
  addColumn('Signals that match', comparison.matches, 'match');
  addColumn('Signals that conflict', comparison.conflicts, 'conflict');
  panel.append(grid);
  const decision = document.createElement('div'); decision.className='comparison-decision'; decision.append(textNode('strong','Decision: '),document.createTextNode(comparison.decision)); panel.append(decision);
}
function renderScorecard(scorecard) {
  const items = [
    ['score-first', scorecard.first_investigated],
    ['score-repeat', scorecard.repeat_recalled],
    ['score-different', scorecard.different_rejected],
  ];
  let complete = 0;
  for (const [id, passed] of items) {
    const item = $(id); item.classList.toggle('complete', passed);
    item.querySelector('.score-icon').textContent = passed ? '✓' : '○';
    if (passed) complete++;
  }
  $('score-total').textContent = complete+' / 3 complete';
}
function render(){
  if(!state)return;
  const m=state.metrics;
  renderScorecard(state.scorecard);
  $('db').replaceChildren(document.createTextNode(m.database_connections+' '),textNode('small','/ '+m.database_capacity));
  $('db').className=m.database_connections===m.database_capacity?'bad':'';
  $('db-description').textContent=m.database_connections===m.database_capacity?'Pool exhausted':'Capacity available';
  $('gateway').textContent=m.payment_gateway==='reachable'?'Reachable':'Unreachable';$('gateway').className=m.payment_gateway==='reachable'?'':'bad';
  $('health-label').textContent=m.checkout==='healthy'?'Checkout ready':'Checkout degraded';$('health-dot').className='dot'+(m.checkout==='healthy'?'':' bad');$('orders').textContent=state.orders+' demo orders';
  if(state.last_checkout){$('checkout-result').textContent='HTTP '+state.last_checkout.status+' · '+state.last_checkout.message;$('checkout-result').className='checkout-result '+(state.last_checkout.status===200?'success':'failed');}else{$('checkout-result').textContent='No money is charged. No personal details needed.';$('checkout-result').className='checkout-result';}
  $('logs').replaceChildren();for(const log of state.logs){const p=document.createElement('p');p.append(textNode('time',log.time),document.createTextNode(log.message));if(log.message.startsWith('ERROR'))p.className='error';$('logs').append(p);}if(!state.logs.length)$('logs').append(textNode('p','Place an order to generate the first event.'));$('logs').scrollTop=$('logs').scrollHeight;
  $('bank-label').textContent=state.bank_ready?'Hindsight bank: '+state.bank:'Memory bank will be created when you ask the agent or save a lesson.';
  const d=state.diagnosis;
  $('memory-count').textContent=d?d.evidence.length+' recalled facts':'No investigation yet';
  if(d){renderComparison(d.comparison);markdown($('agent-result'),d.recommendation);$('evidence-panel').hidden=!d.evidence.length;$('memories').replaceChildren();for(const fact of d.evidence){const n=document.createElement('article');n.className='memory';n.append(textNode('code',fact.id),textNode('p',fact.text));$('memories').append(n);}if(d.reflection_sources?.length){$('memories').append(textNode('h3','Sources used by reflection'));for(const fact of d.reflection_sources){const n=document.createElement('article');n.className='memory';n.append(textNode('code',fact.id||'Memory'),textNode('p',fact.text));$('memories').append(n);}}}
  else{renderComparison(null);$('evidence-panel').hidden=true;$('agent-result').replaceChildren(textNode('div','◎','empty-symbol'),textNode('h3',state.resolved?'Checkout recovered. Keep the lesson.':state.failure_observed?'The checkout failed. Let’s find out why.':'First, give it a problem to investigate.'),textNode('p',state.resolved?'The demo order succeeded after your fix. Save the outcome, then try another chapter.':'The agent will examine the checkout logs and search its memory.'));}
  buttons.forEach(b=>b.disabled=busy);
  $('investigate').disabled=busy||!state.failure_observed||state.resolved;
  $('learn').disabled=busy||!state.can_learn||state.learned;
  for(const id of ['restart','connection-fix','payment-fix'])$(id).disabled=busy||!state.failure_observed||state.resolved;
  $('repeat').disabled=busy||!state.lessons_saved;$('different').disabled=busy||!state.lessons_saved;
  $('learn-help').textContent=state.learned?'Lesson saved in Hindsight. Try the next chapter to see how memory changes the answer.':state.can_learn?'Recovery verified with a successful demo order. Save the observed cause, fix, and failed attempts.':'After a successful fix, place an order to verify recovery. Then save the lesson.';
  if(state.learned)guide('05','Now test what it learned.','Choose “Same problem again” to test recall, or “Looks similar. Isn’t.” to test a different cause.');
  else if(state.can_learn)guide('04','It works again. Remember the lesson.','Click “Save this lesson to Hindsight” below. This stores what failed, what worked, and how recovery was verified.');
  else if(state.failure_observed&&m.checkout==='healthy')guide('04','Check whether the fix holds.','Place a demo order. After a restart, place another: a temporary recovery is not a permanent fix.');
  else if(state.failure_observed)guide('03','The customer sees a timeout. What caused it?','Click “Ask the incident agent”. Then open “Try a fix yourself” and choose an action based on the evidence.');
  else if(state.round)guide('02','Checkout is now broken. Try it.','Click “Place demo order”. Watch the error and the evidence appear side by side.');
  else if(state.orders)guide('02','The shop works. Now break it.','Click “First failure” above to inject a simulated checkout bug.');
  else guide('01','Try buying something.','Click “Place demo order”. Nothing costs money—this is a safe simulation.');
}
async function act(path,payload={},message='Working…'){
  if(busy)return;busy=true;render();notice(message);
  if(path==='investigate'){$('agent-result').replaceChildren(textNode('p','Reading current evidence and recalling past incidents… This may take a minute.','working'));$('agent-panel').scrollIntoView({behavior:'smooth',block:'start'});}
  try{const data=await api(path,payload);state=data.state;notice(path==='learn'?'Lesson saved. The next investigation can use this experience.':path==='investigate'?'Investigation complete. Read the agent’s answer below.':path==='checkout'?state.last_checkout.message:'Simulator updated. Follow the next step above.');}
  catch(e){notice(e.message,true);if(path==='investigate')state.diagnosis={evidence:[],recommendation:'Investigation failed: '+e.message};}
  finally{busy=false;render();}
}
for(const id of ['first','repeat','different'])$(id).onclick=()=>{document.querySelectorAll('.scenario').forEach(b=>b.classList.toggle('active',b.id===id));act('fault',{scenario:id},'Changing the simulated deployment…');};
$('checkout').onclick=()=>act('checkout',{},'Placing a demo order…');
$('investigate').onclick=()=>act('investigate',{},'Asking Hindsight. This can take a minute…');
for(const id of ['restart','connection-fix','payment-fix'])$(id).onclick=()=>act('action',{action:id},'Applying the selected fix to the simulator…');
$('learn').onclick=()=>act('learn',{},'Saving the verified resolution to Hindsight…');
async function start(fresh=false){busy=true;buttons.forEach(b=>b.disabled=true);try{session=fresh?null:sessionStorage.getItem('checkout-lab-session');let data;if(session){try{data=await api('state');}catch{session=null;}}if(!session){data=await api('start');session=data.session;sessionStorage.setItem('checkout-lab-session',session);}state=data.state;$('notice').hidden=true;}catch(e){notice(e.message,true);}finally{busy=false;render();}}
$('reset').onclick=()=>start(true);
start();
