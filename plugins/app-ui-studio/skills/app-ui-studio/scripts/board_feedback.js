'use strict';

// The same model is used by the portable page and the Node regression checks.
const BoardFeedback = (() => {
  const clone = value => JSON.parse(JSON.stringify(value));
  const key = source => `${source.candidate_id}/${source.screen_id}`;
  function sourceFor(board, candidateId, screenId) {
    const candidate = board.candidates.find(item => item.id === candidateId);
    const screen = candidate?.screens.find(item => item.id === screenId);
    if (!screen) throw new Error('Unknown screenshot');
    return {candidate_id: candidateId, screen_id: screenId, artifact: screen.artifact,
      sha256: screen.sha256, viewport: clone(screen.viewport)};
  }
  function text(value) {
    if (typeof value !== 'string' || !value.trim() || value.length > 8000) throw new Error('Invalid feedback text');
    return value.trim();
  }
  function point(value) {
    if (!value || !['x', 'y'].every(axis => typeof value[axis] === 'number'
        && Number.isFinite(value[axis]) && value[axis] >= 0 && value[axis] <= 1)) throw new Error('Invalid point');
    return {x: value.x, y: value.y};
  }
  function previewSize(source, available, original) {
    if (![source?.width, source?.height, available?.width, available?.height].every(value => typeof value === 'number' && Number.isFinite(value) && value > 0)) throw new Error('Invalid preview dimensions');
    const scale = original ? 1 : Math.min(1, available.width / source.width, available.height / source.height);
    return {width: source.width * scale, height: source.height * scale};
  }
  function createState(board) {
    return {board_id: board.board_id, selected_candidate: null,
      selected_viewport: board.candidates[0].screens[0].id, notes: [], annotations: [], next_id: 1};
  }
  function readNote(state, source) { return state.notes.find(item => key(item) === key(source))?.text || ''; }
  function writeNote(state, source, value) {
    if (typeof value !== 'string' || value.length > 8000) throw new Error('Invalid feedback text');
    state.notes = state.notes.filter(item => key(item) !== key(source));
    if (value.trim()) state.notes.push({...clone(source), text: value.trim()});
  }
  function addAnnotation(state, source, position, value) {
    if (state.annotations.length >= 1000 || !Number.isSafeInteger(state.next_id)) throw new Error('Annotation limit reached');
    const entry = {...clone(source), id: `note-${state.next_id}`, point: point(position), text: text(value)};
    state.next_id++;
    state.annotations.push(entry);
    return entry;
  }
  function exportFeedback(state) {
    const {board_id, selected_candidate, selected_viewport, notes, annotations} = state;
    return clone({schema_version: 1, board_id, selected_candidate, selected_viewport, notes, annotations});
  }
  function restoreState(board, payload) {
    if (!payload || payload.schema_version !== 1 || payload.board_id !== board.board_id
        || !Array.isArray(payload.notes) || !Array.isArray(payload.annotations)
        || payload.notes.length > 1000 || payload.annotations.length > 1000) throw new Error('Wrong feedback version');
    const state = createState(board);
    if (payload.selected_candidate !== null && !board.candidates.some(item => item.id === payload.selected_candidate)) throw new Error('Unknown selection');
    if (!board.candidates[0].screens.some(item => item.id === payload.selected_viewport)) throw new Error('Unknown viewport');
    state.selected_candidate = payload.selected_candidate;
    state.selected_viewport = payload.selected_viewport;
    const ids = new Set(), notes = new Set();
    function checkedSource(entry) {
      const source = sourceFor(board, entry.candidate_id, entry.screen_id);
      if (source.artifact !== entry.artifact || source.sha256 !== entry.sha256
          || source.viewport.width !== entry.viewport?.width || source.viewport.height !== entry.viewport?.height) throw new Error('Screenshot changed');
      return source;
    }
    for (const entry of payload.notes) {
      const source = checkedSource(entry);
      if (notes.has(key(source))) throw new Error('Duplicate screen note');
      notes.add(key(source)); writeNote(state, source, text(entry.text));
    }
    for (const entry of payload.annotations) {
      const source = checkedSource(entry);
      if (typeof entry.id !== 'string' || !/^note-[1-9][0-9]*$/.test(entry.id) || ids.has(entry.id)
          || !Number.isSafeInteger(Number(entry.id.slice(5))) || Number(entry.id.slice(5)) >= Number.MAX_SAFE_INTEGER) throw new Error('Invalid annotation ID');
      ids.add(entry.id);
      state.annotations.push({...source, id: entry.id, point: point(entry.point), text: text(entry.text)});
      state.next_id = Math.max(state.next_id, Number(entry.id.slice(5)) + 1);
    }
    return state;
  }
  return {createState, sourceFor, readNote, writeNote, addAnnotation, exportFeedback, restoreState, previewSize};
})();
if (typeof module !== 'undefined' && module.exports) module.exports = BoardFeedback;

if (typeof document !== 'undefined') (() => {
  const data = JSON.parse(document.getElementById('board-data').textContent);
  const $ = id => document.getElementById(id);
  const api = BoardFeedback, storageKey = `app-ui-studio:board-feedback:1:${data.board_id}`;
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  let state = api.createState(data), draftStatus = '草稿保存在本标签页；关闭前请导出', reviewSource = null, returnFocus = null, originalSize = false, imageReady = false;
  function animateFeedback(element, frames, duration = 160) {
    if (motion.matches || !element.animate) return;
    element.getAnimations().forEach(animation => animation.cancel());
    element.animate(frames, {duration, easing: 'cubic-bezier(.2,.7,.2,1)'});
  }
  try {
    const saved = sessionStorage.getItem(storageKey);
    if (saved) {state = api.restoreState(data, JSON.parse(saved)); draftStatus = '已恢复本标签页草稿；关闭前请导出';}
  } catch {draftStatus = '标签页草稿不可用；可导出反馈文件保留意见';}
  function persist() {
    try {sessionStorage.setItem(storageKey, JSON.stringify(api.exportFeedback(state))); draftStatus = '已保存本标签页草稿；关闭前请导出';}
    catch {draftStatus = '标签页保存不可用；请导出反馈文件保留意见';}
    $('draft-status').textContent = draftStatus;
  }
  function label(source) {
    const item = data.candidates.find(item => item.id === source.candidate_id);
    return `${item.label}（${source.candidate_id}） · ${source.screen_id} · ${source.viewport.width} × ${source.viewport.height}`;
  }
  function updateSummary() {
    const chosen = data.candidates.find(item => item.id === state.selected_candidate);
    const lines = [`${data.title}`, `对比页：${data.board_id}`, chosen ? `选择方案：${chosen.label}（${chosen.id}）` : '推荐方案：尚未选择'];
    for (const item of state.notes) lines.push(`\n整图意见 · ${label(item)}\n截图：${item.artifact}\nSHA-256：${item.sha256}\n${item.text}`);
    for (const item of state.annotations) lines.push(`\n${item.id} · ${label(item)}\n截图：${item.artifact}\nSHA-256：${item.sha256}\n位置：x=${(item.point.x * 100).toFixed(1)}%，y=${(item.point.y * 100).toFixed(1)}%\n${item.text}`);
    lines.push('\n意见尚未应用到项目；截图与意见不构成质量认证。');
    $('summary').value = lines.join('\n');
    $('feedback-count').textContent = `${state.notes.length} 条整图意见 · ${state.annotations.length} 条位置批注`;
  }
  function syncNotes() {
    const chosen = data.candidates.find(item => item.id === state.selected_candidate);
    $('notes').disabled = !chosen;
    $('notes-label').textContent = chosen ? `${chosen.label} · ${state.selected_viewport} 的整图意见` : '选择候选后填写整图意见';
    $('notes').value = chosen ? api.readNote(state, api.sourceFor(data, chosen.id, state.selected_viewport)) : '';
    updateSummary();
  }
  function renderCards() {
    const grid = $('grid'); grid.replaceChildren();
    for (const item of data.candidates) {
      const screen = item.screens.find(screen => screen.id === state.selected_viewport);
      const card = document.createElement('article'); card.className = 'card' + (item.id === state.selected_candidate ? ' chosen' : ''); card.dataset.id = item.id;
      const title = document.createElement('h2'); title.textContent = item.label;
      const heading = document.createElement('div'); heading.className = 'candidate-heading';
      const index = document.createElement('span'); index.className = 'candidate-index'; index.textContent = item.id.toUpperCase(); heading.append(title, index);
      const note = document.createElement('p'); note.className = 'card-note'; note.textContent = item.note || '';
      const preview = document.createElement('button'); preview.type = 'button'; preview.className = 'preview'; preview.setAttribute('aria-label', `查看并批注 ${item.label}`);
      const img = document.createElement('img'); img.src = screen.artifact; img.alt = `${item.label}，${state.selected_viewport}截图`; preview.append(img);
      const imageError = document.createElement('p'); imageError.className = 'image-error'; imageError.hidden = true; imageError.setAttribute('role', 'status'); imageError.textContent = '截图未能载入，请检查证据文件。';
      img.onerror = () => {imageError.hidden = false; preview.disabled = true; review.disabled = true;};
      preview.onclick = () => openDetail(item.id, preview);
      const actions = document.createElement('div'); actions.className = 'actions';
      const choose = document.createElement('button'); choose.type = 'button'; choose.className = 'choose';
      choose.textContent = item.id === state.selected_candidate ? '已选择' : '选择此方案'; choose.setAttribute('aria-pressed', String(item.id === state.selected_candidate));
      choose.onclick = () => {
        state.selected_candidate = item.id;
        for (const current of grid.children) {
          const active = current.dataset.id === item.id; current.classList.toggle('chosen', active);
          const button = current.querySelector('.choose'); button.textContent = active ? '已选择' : '选择此方案'; button.setAttribute('aria-pressed', String(active));
        }
        persist(); syncNotes(); $('status').textContent = `已选择 ${item.label}；尚未应用到项目`; animateFeedback(choose, [{opacity: .55}, {opacity: 1}]);
      };
      const review = document.createElement('button'); review.type = 'button'; review.className = 'secondary review'; review.textContent = '查看与批注'; review.setAttribute('aria-label', `批注 ${item.label}`); review.onclick = () => openDetail(item.id, review);
      actions.append(choose, review);
      if (item.url) {const link = document.createElement('a'); link.href = item.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = '打开实际页面'; actions.append(link);}
      const count = document.createElement('p'); count.className = 'screen-meta';
      count.textContent = `${screen.viewport.width} × ${screen.viewport.height} · ${state.annotations.filter(entry => entry.candidate_id === item.id && entry.screen_id === screen.id).length} 条位置批注`;
      card.append(heading, note, preview, imageError, actions, count); grid.append(card);
    }
    syncNotes();
  }
  function openDetail(candidateId, trigger) {
    reviewSource = api.sourceFor(data, candidateId, state.selected_viewport); returnFocus = trigger.classList.contains('preview') ? '.preview' : '.review';
    originalSize = false; imageReady = false; $('save-annotation').disabled = true;
    const source = reviewSource, image = $('full-image');
    const ready = () => {
      if (reviewSource !== source) return;
      imageReady = image.naturalWidth === source.viewport.width && image.naturalHeight === source.viewport.height;
      $('save-annotation').disabled = !imageReady;
      $('image-status').textContent = imageReady ? '位置以原图百分比保存，切换缩放不会改变。' : '截图未能正确加载，请核对证据文件后重试。';
    };
    image.onload = ready; image.onerror = () => {if (reviewSource === source) {imageReady = false; $('save-annotation').disabled = true; $('image-status').textContent = '截图未能载入，请检查证据文件。';}};
    image.src = reviewSource.artifact; image.alt = label(reviewSource);
    $('detail-label').textContent = label(reviewSource);
    $('source-id').textContent = `${reviewSource.artifact} · SHA-256 ${reviewSource.sha256.slice(0, 12)}…${reviewSource.sha256.slice(-8)}`;
    $('source-id').title = reviewSource.sha256;
    $('x').value = '50'; $('y').value = '50'; $('annotation-text').value = ''; $('annotation-status').textContent = '点击截图定位，或输入横纵百分比。';
    renderAnnotations(); $('detail').showModal(); layoutPreview();
    if (image.complete && image.naturalWidth) ready();
    animateFeedback($('detail'), [{opacity: .4, transform: 'translateY(8px) scale(.99)'}, {opacity: 1, transform: 'translateY(0) scale(1)'}]);
  }
  function layoutPreview() {
    if (!reviewSource || !$('detail').open) return;
    const pane = $('image-pane');
    const mobile = matchMedia('(max-width: 800px)').matches;
    pane.classList.toggle('original-size', originalSize);
    const size = api.previewSize(reviewSource.viewport, {width: Math.max(1, pane.clientWidth - 32), height: mobile ? reviewSource.viewport.height : Math.max(1, pane.clientHeight - 32)}, originalSize);
    $('image-stage').style.width = `${size.width}px`; $('image-stage').style.height = `${size.height}px`;
    $('preview-mode').textContent = originalSize ? '原始尺寸 · 100%' : `${mobile ? '适合宽度' : '适合窗口'} · ${Math.round(size.width / reviewSource.viewport.width * 100)}%`;
    $('zoom').textContent = originalSize ? (mobile ? '适合宽度' : '适合窗口') : '原始尺寸'; $('zoom').setAttribute('aria-pressed', String(originalSize));
  }
  function currentEntries() {return state.annotations.filter(item => item.candidate_id === reviewSource.candidate_id && item.screen_id === reviewSource.screen_id);}
  function markPosition() {
    $('cursor').style.left = `${$('x').value}%`; $('cursor').style.top = `${$('y').value}%`;
  }
  function renderAnnotations(newId) {
    $('pins').replaceChildren(); $('annotation-list').replaceChildren();
    for (const item of currentEntries()) {
      const pin = document.createElement('span'); pin.className = 'pin'; pin.style.left = `${item.point.x * 100}%`; pin.style.top = `${item.point.y * 100}%`; pin.textContent = item.id.slice(5); pin.title = item.text; $('pins').append(pin);
      if (item.id === newId) animateFeedback(pin, [{opacity: .2, transform: 'translate(-50%,-50%) scale(.7)'}, {opacity: 1, transform: 'translate(-50%,-50%) scale(1)'}]);
      const row = document.createElement('li'), description = document.createElement('p'), remove = document.createElement('button');
      description.textContent = `${item.id} · ${Math.round(item.point.x * 100)}%, ${Math.round(item.point.y * 100)}%\n${item.text}`;
      remove.type = 'button'; remove.className = 'secondary'; remove.textContent = '移除'; remove.setAttribute('aria-label', `移除 ${item.id}`);
      remove.onclick = () => {state.annotations = state.annotations.filter(entry => entry.id !== item.id); persist(); renderAnnotations(); updateSummary(); $('annotation-text').focus();};
      row.append(description, remove); $('annotation-list').append(row);
    }
    $('annotation-empty').hidden = currentEntries().length > 0; markPosition();
  }
  $('title').textContent = data.title;
  $('context').textContent = Object.entries(data.context).map(([name, value]) => `${name}: ${typeof value === 'string' ? value : JSON.stringify(value)}`).join(' · ');
  for (const screen of data.candidates[0].screens) {const option = document.createElement('option'); option.value = screen.id; option.textContent = `${screen.id} · ${screen.viewport.width} × ${screen.viewport.height}`; $('viewport').append(option);}
  $('viewport').value = state.selected_viewport;
  $('viewport').onchange = () => {state.selected_viewport = $('viewport').value; persist(); renderCards();};
  $('notes').oninput = () => {api.writeNote(state, api.sourceFor(data, state.selected_candidate, state.selected_viewport), $('notes').value); persist(); updateSummary();};
  $('full-image').onclick = event => {
    const box = event.currentTarget.getBoundingClientRect();
    $('x').value = (Math.min(1, Math.max(0, (event.clientX - box.left) / box.width)) * 100).toFixed(1);
    $('y').value = (Math.min(1, Math.max(0, (event.clientY - box.top) / box.height)) * 100).toFixed(1);
    markPosition(); $('annotation-text').focus();
  };
  $('x').oninput = markPosition; $('y').oninput = markPosition;
  $('annotation-form').onsubmit = event => {
    event.preventDefault();
    if (!imageReady) {$('annotation-status').textContent = '请等待截图正确加载后再定位批注。'; return;}
    let entry;
    try {entry = api.addAnnotation(state, reviewSource, {x: Number($('x').value) / 100, y: Number($('y').value) / 100}, $('annotation-text').value);}
    catch {$('annotation-status').textContent = '请填写有效位置（0–100）和批注意见。'; return;}
    persist(); renderAnnotations(entry.id); updateSummary(); $('annotation-text').value = ''; $('annotation-status').textContent = '批注已绑定此截图；尚未应用到项目'; $('annotation-text').focus();
  };
  $('close').onclick = () => $('detail').close();
  $('detail').addEventListener('close', () => {const id = reviewSource.candidate_id; reviewSource = null; renderCards(); $('grid').querySelector(`[data-id="${id}"] ${returnFocus}`)?.focus();});
  $('zoom').onclick = () => {originalSize = !originalSize; layoutPreview();};
  window.addEventListener('resize', layoutPreview, {passive: true});
  window.addEventListener('pagehide', () => {window.removeEventListener('resize', layoutPreview); $('detail').getAnimations().forEach(animation => animation.cancel());});
  window.addEventListener('pageshow', () => {window.addEventListener('resize', layoutPreview, {passive: true}); layoutPreview();});
  $('copy').onclick = async () => {
    if (!state.selected_candidate && !state.notes.length && !state.annotations.length) {$('status').textContent = '请先选择候选或留下意见'; return;}
    try {await navigator.clipboard.writeText($('summary').value); $('status').textContent = '已复制含截图身份的意见；尚未应用到项目';}
    catch {$('summary').closest('details').open = true; $('summary').focus(); $('summary').select(); $('status').textContent = '自动复制不可用，请复制已选中的意见';}
  };
  $('download').onclick = () => {
    const blob = new Blob([JSON.stringify(api.exportFeedback(state), null, 2) + '\n'], {type: 'application/json'});
    const url = URL.createObjectURL(blob), link = document.createElement('a'); link.href = url; link.download = `board-feedback-${data.board_id.slice(0, 12)}.json`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000); $('status').textContent = '已准备本地反馈文件；尚未应用到项目';
  };
  $('draft-status').textContent = draftStatus; renderCards();
  if (state.selected_candidate) $('status').textContent = '已恢复候选选择；尚未应用到项目';
})();
