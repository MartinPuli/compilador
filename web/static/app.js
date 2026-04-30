// MORSE.LAB — client app
(function () {
  'use strict';

  // ---------- helpers ----------

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  async function api(path, body, opts = {}) {
    const init = {
      method: opts.method || (body ? 'POST' : 'GET'),
      headers: opts.formData ? undefined : { 'Content-Type': 'application/json' },
      body: opts.formData ? body : (body ? JSON.stringify(body) : undefined),
    };
    const res = await fetch(path, init);
    const text = await res.text();
    try { return { ok: res.ok, data: JSON.parse(text) }; }
    catch { return { ok: res.ok, data: { error: text } }; }
  }

  function setStatus(state) {
    const dot = $('#status-dot');
    if (dot) dot.dataset.state = state;
  }

  // ---------- nav between views ----------

  $$('.nav-item').forEach((btn) => {
    btn.addEventListener('click', () => {
      $$('.nav-item').forEach((b) => b.classList.toggle('is-active', b === btn));
      const target = btn.dataset.view;
      $$('.view').forEach((v) => v.classList.toggle('is-active', v.dataset.view === target));
    });
  });

  // ---------- decorative right-rail morse stream ----------

  (function rightRail() {
    const stream = $('#morse-stream');
    if (!stream) return;
    const seed = '· — · · — — · · · — · — · — · · · — · · · · — · — · — — — · · — · · ·';
    let buf = '';
    for (let i = 0; i < 80; i++) buf += seed + '   ';
    stream.textContent = buf;
  })();

  // ---------- editor wiring ----------

  const sourceEl = $('#source');
  const outputBody = $('#output-body');
  const outputLabel = $('#output-label');

  async function loadExamples() {
    const { ok, data } = await api('/api/examples');
    if (!ok || !Array.isArray(data)) return;
    const sel = $('#example-select');
    data.forEach((name) => {
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = name;
      sel.appendChild(opt);
    });
  }

  $('#example-select').addEventListener('change', async (e) => {
    const name = e.target.value;
    if (!name) return;
    const { ok, data } = await api(`/api/example/${encodeURIComponent(name)}`);
    if (ok && data.source != null) sourceEl.value = data.source;
    e.target.value = '';
  });

  $$('[data-action]').forEach((btn) => {
    btn.addEventListener('click', () => onAction(btn.dataset.action));
  });

  async function onAction(action) {
    if (action === 'run' || action === 'tokens' || action === 'ast') {
      setStatus('busy');
      const path = action === 'run' ? '/api/run' : action === 'tokens' ? '/api/tokens' : '/api/ast';
      const { data } = await api(path, { source: sourceEl.value });
      outputLabel.textContent = action === 'run' ? 'OUTPUT' : action === 'tokens' ? 'TOKENS' : 'AST';
      renderOutput(action, data);
      setStatus(data.error ? 'error' : 'ok');
    } else if (action === 'decode') {
      decodeAudio();
    } else if (action === 'send-to-editor') {
      sendDecodedToEditor();
    } else if (action === 'run-symtab') {
      runSymtab();
    }
  }

  function renderOutput(action, data) {
    outputBody.innerHTML = '';
    if (data.error) {
      const div = document.createElement('div');
      div.className = 'output-error';
      div.innerHTML = `<b>ERROR ${data.error.phase || ''}</b>${escapeHtml(data.error.message || '')}`;
      outputBody.appendChild(div);
    }
    if (action === 'tokens' && data.tokens) {
      data.tokens.forEach((t) => {
        const row = document.createElement('div');
        row.className = 'token-row';
        row.innerHTML = `
          <span class="tok-line">${t.line}</span>
          <span class="tok-type">${t.type}</span>
          <span class="tok-lex">${escapeHtml(t.lexeme)}</span>`;
        outputBody.appendChild(row);
      });
    } else if (action === 'ast' && data.ast) {
      const pre = document.createElement('pre');
      pre.className = 'ast-pre';
      pre.textContent = renderAstTree(data.ast);
      outputBody.appendChild(pre);
    } else if (action === 'run') {
      if (data.output && data.output.length) {
        data.output.forEach((line, i) => {
          const div = document.createElement('div');
          div.className = 'output-line';
          div.textContent = line;
          div.style.animation = `fade-in 260ms ease both`;
          div.style.animationDelay = `${i * 60}ms`;
          outputBody.appendChild(div);
        });
      } else if (!data.error) {
        outputBody.innerHTML = '<p class="placeholder">(sin salida)</p>';
      }
      if (data.final_symbol_table && Object.keys(data.final_symbol_table).length) {
        renderSymbolTable(data.final_symbol_table);
      }
    }
  }

  function renderSymbolTable(table) {
    const wrap = document.createElement('div');
    wrap.className = 'output-symbols';
    const h = document.createElement('p');
    h.className = 'output-symbols-h';
    h.textContent = 'TABLA DE SÍMBOLOS — final';
    wrap.appendChild(h);
    Object.entries(table).forEach(([name, info]) => {
      const row = document.createElement('div');
      row.className = 'symbol-row';
      row.innerHTML = `
        <span class="sym-name">${escapeHtml(name)}</span>
        <span class="sym-tipo">${escapeHtml(info.tipo)}</span>
        <span class="sym-val">${escapeHtml(String(info.valor))}</span>`;
      wrap.appendChild(row);
    });
    outputBody.appendChild(wrap);
  }

  function renderAstTree(node, depth = 0) {
    const pad = '  '.repeat(depth);
    if (node === null || node === undefined) return pad + '·';
    if (Array.isArray(node)) return node.map((n) => renderAstTree(n, depth)).join('\n');
    if (typeof node !== 'object') return pad + String(node);
    const head = `${pad}${node.node || ''}`;
    const meta = [];
    Object.entries(node).forEach(([k, v]) => {
      if (k === 'node' || v === null || v === undefined) return;
      if (typeof v === 'object') return;
      meta.push(`${k}=${JSON.stringify(v)}`);
    });
    let out = head + (meta.length ? ` (${meta.join(', ')})` : '');
    Object.entries(node).forEach(([k, v]) => {
      if (k === 'node') return;
      if (typeof v === 'object' && v !== null) {
        out += `\n${pad}  ${k}:`;
        out += '\n' + renderAstTree(v, depth + 2);
      }
    });
    return out;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    })[c]);
  }

  // ---------- audio ----------

  const audioFile = $('#audio-file');
  const audioName = $('#audio-name');
  const sendBtn = $('[data-action="send-to-editor"]');
  let lastDecoded = null;

  audioFile.addEventListener('change', () => {
    audioName.textContent = audioFile.files[0] ? audioFile.files[0].name : '';
  });

  async function decodeAudio() {
    if (!audioFile.files[0]) {
      audioName.textContent = '⚠ seleccioná un .wav';
      return;
    }
    const fd = new FormData();
    fd.append('audio', audioFile.files[0]);
    const wpm = $('#wpm').value;
    if (wpm) fd.append('wpm', wpm);
    const { ok, data } = await api('/api/decode-audio', fd, { formData: true });
    if (!ok) {
      $('#morse-out').textContent = data.error || 'error';
      return;
    }
    lastDecoded = data;
    $('#m-wpm').textContent = data.detected_wpm;
    $('#m-dot').textContent = data.dot_length_ms;
    $('#morse-out').textContent = data.morse;
    sendBtn.disabled = false;
    drawEnvelope(data.envelope, data.threshold);
  }

  function sendDecodedToEditor() {
    if (!lastDecoded) return;
    sourceEl.value = lastDecoded.morse;
    $$('.nav-item').forEach((b) => b.classList.toggle('is-active', b.dataset.view === 'editor'));
    $$('.view').forEach((v) => v.classList.toggle('is-active', v.dataset.view === 'editor'));
  }

  function drawEnvelope(env, threshold) {
    const cv = $('#env-chart');
    if (!cv || !env || !env.length) return;
    const ctx = cv.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const cssW = cv.clientWidth || 600;
    const cssH = 80;
    cv.width = cssW * dpr;
    cv.height = cssH * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, cssW, cssH);

    const max = Math.max(...env, threshold) || 1;
    // baseline grid
    ctx.strokeStyle = 'rgba(255, 149, 0, 0.08)';
    ctx.lineWidth = 1;
    for (let x = 0; x < cssW; x += 30) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, cssH); ctx.stroke();
    }

    // threshold line
    const ty = cssH - (threshold / max) * cssH;
    ctx.strokeStyle = 'rgba(109, 192, 255, 0.5)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(0, ty); ctx.lineTo(cssW, ty); ctx.stroke();
    ctx.setLineDash([]);

    // envelope
    ctx.beginPath();
    env.forEach((v, i) => {
      const x = (i / env.length) * cssW;
      const y = cssH - (v / max) * cssH;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = '#ff9500';
    ctx.lineWidth = 1.4;
    ctx.shadowColor = 'rgba(255, 149, 0, 0.6)';
    ctx.shadowBlur = 6;
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  // ---------- TP inspector ----------

  $$('.tp-step').forEach((b) => {
    b.addEventListener('click', () => {
      const tp = b.dataset.tp;
      $$('.tp-step').forEach((s) => s.classList.toggle('is-active', s === b));
      $$('.tp-panel').forEach((p) => p.classList.toggle('is-active', p.dataset.tp === tp));
    });
  });

  // live lex trace
  const lexInput = $('#lex-trace-input');
  const lexOut = $('#lex-trace-out');
  if (lexInput) {
    const update = async () => {
      const { data } = await api('/api/tokens', { source: lexInput.value });
      lexOut.innerHTML = '';
      if (data.error) {
        lexOut.innerHTML = `<div class="output-error"><b>${data.error.phase}</b>${escapeHtml(data.error.message)}</div>`;
        return;
      }
      (data.tokens || []).forEach((t) => {
        const row = document.createElement('div');
        row.className = 'token-row';
        row.innerHTML = `
          <span class="tok-line">${t.line}</span>
          <span class="tok-type">${t.type}</span>
          <span class="tok-lex">${escapeHtml(t.lexeme)}</span>`;
        lexOut.appendChild(row);
      });
    };
    lexInput.addEventListener('input', debounce(update, 280));
    update();
  }

  // live AST
  const astInput = $('#ast-input');
  const astOut = $('#ast-out');
  if (astInput) {
    const update = async () => {
      const { data } = await api('/api/ast', { source: astInput.value });
      if (data.error) {
        astOut.textContent = `${data.error.phase}: ${data.error.message}`;
        return;
      }
      astOut.textContent = data.ast ? renderAstTree(data.ast) : '—';
    };
    astInput.addEventListener('input', debounce(update, 280));
    update();
  }

  // step-by-step symbol table
  async function runSymtab() {
    const out = $('#symtab-out');
    out.innerHTML = '';
    const { data } = await api('/api/run', { source: $('#symtab-source').value });
    if (data.error) {
      out.innerHTML = `<div class="output-error"><b>${data.error.phase}</b>${escapeHtml(data.error.message)}</div>`;
      return;
    }
    (data.symbol_table_snapshots || []).forEach((s, i) => {
      const card = document.createElement('div');
      card.className = 'snap';
      const h = document.createElement('p');
      h.className = 'snap-h';
      h.innerHTML = `STEP ${String(i + 1).padStart(2, '0')} — <em>${escapeHtml(s.stmt)}</em>`;
      card.appendChild(h);
      Object.entries(s.table).forEach(([name, info]) => {
        const row = document.createElement('div');
        row.className = 'symbol-row';
        row.innerHTML = `
          <span class="sym-name">${escapeHtml(name)}</span>
          <span class="sym-tipo">${escapeHtml(info.tipo)}</span>
          <span class="sym-val">${escapeHtml(String(info.valor))}</span>`;
        card.appendChild(row);
      });
      out.appendChild(card);
    });
  }

  // error gallery
  async function loadErrorGallery() {
    const gallery = $('#error-gallery');
    if (!gallery) return;
    const { data: names } = await api('/api/examples');
    const errFiles = (names || []).filter((n) => n.startsWith('error_'));
    for (const name of errFiles) {
      const { data: ex } = await api(`/api/example/${encodeURIComponent(name)}`);
      const { data: result } = await api('/api/run', { source: ex.source });
      const card = document.createElement('div');
      card.className = 'err-card';
      card.innerHTML = `
        <div class="pane-bar"><span class="pane-label">${escapeHtml(name)}</span></div>
        <pre class="err-source">${escapeHtml(ex.source)}</pre>
        <div class="err-msg">${result.error ? escapeHtml(result.error.message) : '(sin error — revisar)'}</div>`;
      gallery.appendChild(card);
    }
  }

  // ---------- ayuda tables ----------

  async function loadAyuda() {
    const { ok, data } = await api('/api/reference');
    if (!ok) return;
    const lt = $('#letters-table');
    const dg = $('#digits-table');
    const kw = $('#kw-table');
    data.letters.forEach((r) => {
      const c = document.createElement('div');
      c.className = 'cell';
      c.innerHTML = `<span class="ch">${r.char}</span><span class="mz">${r.morse}</span>`;
      lt.appendChild(c);
    });
    data.digits.forEach((r) => {
      const c = document.createElement('div');
      c.className = 'cell';
      c.innerHTML = `<span class="ch">${r.char}</span><span class="mz">${r.morse}</span>`;
      dg.appendChild(c);
    });
    data.keywords.forEach((r) => {
      const c = document.createElement('div');
      c.className = 'cell kw-cell';
      c.innerHTML = `<span class="ch">${r.text}</span><span class="mz">${r.morse}</span>`;
      kw.appendChild(c);
    });
  }

  // ---------- utils ----------

  function debounce(fn, ms) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }

  // ---------- keyboard shortcuts ----------

  document.addEventListener('keydown', (e) => {
    const editorActive = $$('.nav-item.is-active')[0]?.dataset.view === 'editor';
    if (!editorActive) return;
    if (!(e.ctrlKey || e.metaKey)) return;

    if (e.key === 'Enter') {
      e.preventDefault();
      onAction('run');
    } else if (e.key.toLowerCase() === 't') {
      e.preventDefault();
      onAction('tokens');
    } else if (e.key.toLowerCase() === 'r') {
      e.preventDefault();
      onAction('ast');
    }
  });

  // ---------- boot ----------

  loadExamples();
  loadAyuda();
  loadErrorGallery();
})();
