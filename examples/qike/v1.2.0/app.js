'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const KEY = 'qike-focus-demo-v1';
  let saveAvailable = true, toastTimeout;
  const seed = () => ({tasks:[{id:'reading',title:'阅读 20 页',done:false},{id:'writing',title:'梳理工作想法',done:false}],sessions:[],duration:25,timer:null});
  let state = seed();
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || 'null');
    if (saved && Array.isArray(saved.tasks) && Array.isArray(saved.sessions)) {
      state.tasks = saved.tasks.filter(t => t && typeof t.id==='string' && typeof t.title==='string' && t.title.length<=40).map(t=>({...t,done:!!t.done}));
      state.sessions = saved.sessions.filter(s => s && typeof s.task==='string' && Number.isFinite(s.seconds) && s.seconds>=0 && Number.isFinite(s.endedAt));
      state.duration = [15,25,45].includes(saved.duration) ? saved.duration : 25;
      const t = saved.timer;
      if (t && Number.isFinite(t.totalMs) && t.totalMs>0 && Number.isFinite(t.remainingMs) && t.remainingMs>=0 && (t.endAt===null || Number.isFinite(t.endAt)) && typeof t.task==='string') state.timer=t;
    }
  } catch { saveAvailable=false; }
  function save() {
    try { localStorage.setItem(KEY,JSON.stringify(state)); }
    catch { saveAvailable=false; }
    if (!saveAvailable) { $('save-warning').hidden=false; $('save-warning').textContent='当前浏览器无法保存数据。你仍可使用，关闭页面后本次变更可能丢失。'; }
  }
  function toast(text) {
    $('toast').textContent=text; $('toast').classList.add('visible');
    clearTimeout(toastTimeout); toastTimeout=setTimeout(()=>$('toast').classList.remove('visible'),2800);
  }
  const icon = name => { const s=document.createElementNS('http://www.w3.org/2000/svg','svg'); s.setAttribute('aria-hidden','true'); const use=document.createElementNS(s.namespaceURI,'use');use.setAttribute('href','#'+name);s.append(use);return s; };
  function taskName(){return state.tasks.find(t=>!t.done)?.title || '给自己一点安静的时间';}
  function renderTasks() {
    $('task-list').replaceChildren();
    for (const task of state.tasks) {
      const li=document.createElement('li');li.className='task-item';
      const button=document.createElement('button');button.type='button';button.className='task-check';button.setAttribute('aria-label',(task.done?'取消完成 ':'完成 ')+task.title);button.setAttribute('aria-pressed',String(task.done));
      if(task.done)button.append(icon('check'));
      button.addEventListener('click',()=>{task.done=!task.done;save();renderTasks();toast(task.done?'做得不错，又完成一件小事。':'已恢复为待办任务');});
      const name=document.createElement('span');name.className='task-name'+(task.done?' done':'');name.textContent=task.title;
      const duration=document.createElement('span');duration.className='task-duration';duration.textContent=task.done?'已完成':'待专注';li.append(button,name,duration);$('task-list').append(li);
    }
    if(!state.tasks.length){const li=document.createElement('li');li.className='local-note';li.textContent='写下一件想做的小事，从这里开始。';$('task-list').append(li);}
    const active=!!state.timer;
    document.querySelectorAll('[data-duration]').forEach(b=>{b.setAttribute('aria-pressed',String(+b.dataset.duration===state.duration));b.disabled=active;});
    $('start-focus').replaceChildren(document.createTextNode(active?'回到这次专注':'开始专注'),icon('arrow'));
  }
  function remaining(){if(!state.timer)return state.duration*60000;return state.timer.endAt===null?state.timer.remainingMs:Math.max(0,state.timer.endAt-Date.now());}
  function renderTimer() {
    const ms=remaining(),s=Math.ceil(ms/1000),t=state.timer;
    $('timer').textContent=String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');
    $('focus-task').textContent=t?t.task:taskName();
    const running=!!t&&t.endAt!==null;
    $('focus-mode').textContent=running?'正在专注':t?'已暂停':'准备专注';
    $('focus-dot').classList.toggle('running',running);
    $('timer-caption').textContent=running?'每一分钟，都有它的意义':t?'歇一歇，等你回来':'专注不必着急';
    $('toggle-timer').replaceChildren(icon(running?'pause':'leaf'),Object.assign(document.createElement('span'),{textContent:running?'暂停':t?'继续':'开始计时'}));
    $('end-focus').disabled=!t;
    if(t&&running&&ms===0)finish(true);
  }
  function start() {
    if(!state.timer)state.timer={totalMs:state.duration*60000,remainingMs:state.duration*60000,endAt:Date.now()+state.duration*60000,task:taskName()};
    save();renderTasks();renderTimer();
  }
  function finish(completed=false) {
    const t=state.timer;if(!t)return;
    const seconds=Math.floor((t.totalMs-remaining())/1000);
    state.sessions.unshift({id:Date.now().toString(36),task:t.task,seconds:Math.max(0,seconds),endedAt:Date.now(),completed});
    state.timer=null;save();$('end-confirm').hidden=true;$('focus-controls').hidden=false;renderTasks();renderHistory();renderTimer();location.hash='history';toast(completed?'这段专注完成了，记录已保存。':'实际专注时长已记下。');
  }
  const dayKey = value => {const d=new Date(value);return [d.getFullYear(),d.getMonth(),d.getDate()].join('-');};
  function demoSessions() {
    return [{days:0,minutes:25,task:'读完一章书'},{days:1,minutes:40,task:'写下一个新想法'},{days:2,minutes:15,task:'给今天做个计划'},{days:3,minutes:30,task:'整理手边的工作'},{days:4,minutes:20,task:'认真读一篇文章'},{days:5,minutes:45,task:'完成一段写作'},{days:6,minutes:10,task:'准备新的一天'}].map((s,i)=>{const date=new Date();date.setDate(date.getDate()-s.days);date.setHours(9+i,20,0,0);return {task:s.task,seconds:s.minutes*60,endedAt:date.getTime(),example:true};});
  }
  function renderHistory() {
    const onlyLocal=$('local-only').checked;
    const sessions=onlyLocal?[...state.sessions]:[...state.sessions,...demoSessions()];sessions.sort((a,b)=>b.endedAt-a.endedAt);
    const days=Array.from({length:7},(_,i)=>{const d=new Date();d.setDate(d.getDate()-6+i);const key=dayKey(d);return {d,seconds:sessions.filter(s=>dayKey(s.endedAt)===key).reduce((sum,s)=>sum+s.seconds,0)};});
    const total=days.reduce((sum,d)=>sum+d.seconds,0);$('week-total').textContent=String(Math.floor(total/60));$('chart-source').textContent=onlyLocal?'仅本机记录':'含示例记录';
    const maximum=Math.max(...days.map(d=>d.seconds),60);$('week-bars').replaceChildren();
    for(const item of days){const col=document.createElement('div');col.className='bar-day';const value=document.createElement('span');value.className='bar-value';value.textContent=String(Math.floor(item.seconds/60));const bar=document.createElement('span');bar.className='bar';bar.style.height=(item.seconds/maximum*81+3)+'px';const label=document.createElement('small');label.textContent=item===days[6]?'今天':(item.d.getMonth()+1)+'/'+item.d.getDate();col.append(value,bar,label);$('week-bars').append(col);}
    $('week-bars').setAttribute('aria-label',days.map(d=>(d.d.getMonth()+1)+'月'+d.d.getDate()+'日 '+Math.floor(d.seconds/60)+'分钟').join('；'));
    $('session-list').replaceChildren();
    for(const session of sessions){const li=document.createElement('li');li.className='session-item';const mark=document.createElement('span');mark.className='session-icon';mark.append(icon(session.example?'book':'leaf'));const body=document.createElement('div');body.className='session-body';const name=document.createElement('strong');name.textContent=session.task;const caption=document.createElement('small');caption.textContent=session.seconds<60?'专注不到 1 分钟':'专注 '+Math.floor(session.seconds/60)+' 分钟';const tag=document.createElement('span');tag.className='record-tag';tag.textContent=session.example?'示例':'本机';caption.append(tag);body.append(name,caption);const time=document.createElement('time');time.dateTime=new Date(session.endedAt).toISOString();time.textContent=dayKey(session.endedAt)===dayKey(Date.now())?'今天':new Date(session.endedAt).toLocaleDateString('zh-CN',{month:'numeric',day:'numeric'});li.append(mark,body,time);$('session-list').append(li);}
    $('history-empty').hidden=!!sessions.length;$('records-note').textContent=onlyLocal?'只展示你在当前浏览器产生的实际记录。':'初始记录为示例数据，新增记录来自实际操作。';
  }
  function route(focusHeading=false) {
    const page=['today','focus','history'].includes(location.hash.slice(1))?location.hash.slice(1):'today';
    const screenId={today:'screen-today',focus:'screen-focus',history:'screen-history'}[page];
    for(const section of document.querySelectorAll('.screen'))section.hidden=section.id!==screenId;
    for(const a of document.querySelectorAll('.bottom-nav a')){if(a.hash==='#'+page)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}
    if(page==='focus')renderTimer();if(page==='history')renderHistory();
    document.title='栖刻 · '+{today:'今天',focus:'专注',history:'记录'}[page];
    if(focusHeading){window.scrollTo(0,0);$(page+'-heading').focus({preventScroll:true});}
  }
  document.querySelectorAll('[data-duration]').forEach(b=>b.addEventListener('click',()=>{if(state.timer)return;state.duration=+b.dataset.duration;save();renderTasks();renderTimer();}));
  $('start-focus').addEventListener('click',()=>{start();location.hash='focus';});
  $('toggle-timer').addEventListener('click',()=>{if(!state.timer)start();else if(state.timer.endAt!==null){state.timer.remainingMs=remaining();state.timer.endAt=null;save();renderTimer();}else {state.timer.endAt=Date.now()+state.timer.remainingMs;save();renderTimer();}});
  $('end-focus').addEventListener('click',()=>{$('end-confirm').hidden=false;$('focus-controls').hidden=true;$('cancel-end').focus();});
  $('cancel-end').addEventListener('click',()=>{$('end-confirm').hidden=true;$('focus-controls').hidden=false;$('toggle-timer').focus();});
  $('confirm-end').addEventListener('click',()=>finish());
  $('toggle-task-form').addEventListener('click',()=>{const open=$('task-form').hidden;$('task-form').hidden=!open;$('toggle-task-form').setAttribute('aria-expanded',String(open));if(open)$('task-input').focus();});
  $('task-form').addEventListener('submit',event=>{event.preventDefault();const title=$('task-input').value.trim();if(!title){$('task-error').textContent='先写下一件想做的事。';$('task-input').setAttribute('aria-invalid','true');$('task-input').focus();return;}state.tasks.push({id:Date.now().toString(36),title,done:false});save();renderTasks();$('task-input').value='';$('task-error').textContent='';$('task-input').removeAttribute('aria-invalid');$('task-form').hidden=true;$('toggle-task-form').setAttribute('aria-expanded','false');$('toggle-task-form').focus();toast('小目标已添加。');});
  $('local-only').addEventListener('change',renderHistory);
  $('today-date').textContent=new Date().toLocaleDateString('zh-CN',{month:'long',day:'numeric',weekday:'long'});
  window.addEventListener('hashchange',()=>route(true));
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)renderTimer();});
  renderTasks();renderHistory();renderTimer();route();if(!saveAvailable)save();
  setInterval(()=>{if(state.timer)renderTimer();},500);
})();
