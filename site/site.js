'use strict';
const StudioStory = (() => {
  function phaseAt(steps, viewportHeight) {
    if (!Array.isArray(steps) || !steps.length || !Number.isFinite(viewportHeight) || viewportHeight <= 0) throw new Error('Invalid story geometry');
    const cursor = viewportHeight * .48;
    let index = 0;
    steps.forEach((step, i) => {if (!Number.isFinite(step.top) || !Number.isFinite(step.bottom)) throw new Error('Invalid step'); if (step.top <= cursor) index = i;});
    const range = steps[steps.length - 1].bottom - steps[0].top;
    return {index, progress: range <= 0 ? 0 : Math.max(0, Math.min(1, (cursor - steps[0].top) / range))};
  }
  return {phaseAt};
})();
if (typeof module !== 'undefined' && module.exports) module.exports = StudioStory;
if (typeof document !== 'undefined') (() => {
  const workflow = document.getElementById('workflow'), steps = [...document.querySelectorAll('[data-story-step]')];
  const stage = document.querySelector('.story-stage'), visual = document.getElementById('story-visual');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)'), wide = matchMedia('(min-width: 900px)');
  const reading = document.getElementById('story-static');
  const labels = ['任务与锁定项', '代表页与实际状态', '定位意见与回改交接'];
  let active = -1, frame = 0, enhanced = false, observer, staticReading = false;
  steps.forEach((step, index) => {const panel = step.querySelector('.static-panel').cloneNode(true); panel.classList.remove('static-panel'); panel.classList.add('story-frame'); panel.hidden = index !== 0; visual.append(panel);});
  const panels = [...visual.children], buttons = [...stage.querySelectorAll('button')];
  function select(index) {
    if (active === index) return;
    active = index; panels.forEach((panel, i) => {panel.hidden = i !== index;});
    buttons.forEach((button, i) => {if (i === index) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current');});
    document.getElementById('story-caption').textContent = labels[index];
    if (!reduce.matches && panels[index].animate) {panels[index].getAnimations().forEach(animation => animation.cancel()); panels[index].animate([{opacity:.3,transform:'translateY(8px)'},{opacity:1,transform:'translateY(0)'}],{duration:180,easing:'ease-out'});}
  }
  function update() {
    frame = 0;
    if (!enhanced || document.hidden) return;
    const current = StudioStory.phaseAt(steps.map(step => {const r = step.getBoundingClientRect(); return {top:r.top,bottom:r.bottom};}), innerHeight);
    select(current.index); document.getElementById('story-progress').style.transform = `scaleX(${current.progress})`;
  }
  function queue() {if (!frame && enhanced && !document.hidden) frame = requestAnimationFrame(update);}
  function layout() {
    enhanced = wide.matches && !reduce.matches && !staticReading;
    workflow.classList.toggle('story-enhanced', enhanced); stage.hidden = !enhanced;
    reading.hidden = !wide.matches; reading.disabled = reduce.matches; reading.setAttribute('aria-pressed', String(staticReading || reduce.matches)); reading.textContent = reduce.matches ? '系统已减少动态效果' : staticReading ? '滚动演示' : '静态阅读';
    if (frame) cancelAnimationFrame(frame); frame = 0;
    if (enhanced) update(); else cancelAnimations();
  }
  function cancelAnimations() {document.querySelectorAll('[data-reveal],.story-frame').forEach(element => element.getAnimations().forEach(animation => animation.cancel()));}
  function visibility() {if (document.hidden) {if (frame) cancelAnimationFrame(frame); frame = 0; cancelAnimations();} else queue();}
  function start() {
    stop();
    window.addEventListener('scroll', queue, {passive:true}); window.addEventListener('resize', layout, {passive:true}); document.addEventListener('visibilitychange', visibility);
    reduce.addEventListener('change', layout); wide.addEventListener('change', layout); layout();
    if ('IntersectionObserver' in window && !reduce.matches) {
      observer = new IntersectionObserver(entries => {entries.forEach(entry => {if (entry.isIntersecting) {if (!reduce.matches && !staticReading && !document.hidden && entry.target.animate) entry.target.animate([{opacity:.4,transform:'translateY(12px)'},{opacity:1,transform:'translateY(0)'}],{duration:420,easing:'ease-out'}); observer.unobserve(entry.target);}});},{threshold:.12});
      document.querySelectorAll('[data-reveal]').forEach(element => observer.observe(element));
    }
  }
  function stop() {
    if (frame) cancelAnimationFrame(frame); frame = 0; observer?.disconnect(); observer = undefined; cancelAnimations();
    window.removeEventListener('scroll', queue); window.removeEventListener('resize', layout); document.removeEventListener('visibilitychange', visibility); reduce.removeEventListener('change', layout); wide.removeEventListener('change', layout);
  }
  buttons.forEach(button => {button.onclick = () => document.getElementById(button.dataset.stepTarget).scrollIntoView({behavior:reduce.matches?'auto':'smooth',block:'start'});});
  reading.onclick = () => {staticReading = !staticReading; layout();};
  window.addEventListener('pagehide', stop); window.addEventListener('pageshow', start);
  start();
})();
