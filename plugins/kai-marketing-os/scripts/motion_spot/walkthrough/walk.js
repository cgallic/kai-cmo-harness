// Frame-deterministic walkthrough engine: every style is a pure function of t (window.seek(t)).
// Driven by window.SPEC, written by walkthrough.py from a JSON spec: real screenshots (already privacy-blurred)
// with a camera path, spotlights, callout pills and caption plates; a title card and an end card.
const S = window.SPEC, W = S.W, H = S.H;
const P = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
const eo = x => x >= 1 ? 1 : 1 - Math.pow(2, -10 * x);
const eio = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const L = (a, b, k) => a + (b - a) * k;
const stage = document.getElementById('stage');
const $ = (tag, cls, par, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; (par || stage).appendChild(e); return e; };
document.documentElement.style.setProperty('--W', W + 'px'); document.documentElement.style.setProperty('--H', H + 'px');
for (const k in (S.css || {})) document.documentElement.style.setProperty(k, S.css[k]);

// masked words; a run wrapped in *...* is the accent colour
function words(par, text) {
  const parts = text.split(' '), out = []; let on = false;
  parts.forEach((w, i) => {
    if (w.startsWith('*')) on = true;
    const m = $('span', 'm', par); const s = $('span', 'w' + (on ? ' acc' : ''), m, w.replace(/\*/g, ''));
    if (w.endsWith('*')) on = false;
    out.push(s); if (i < parts.length - 1) par.appendChild(document.createTextNode(' '));
  });
  return out;
}
function wordAnim(ws, t, a, b, step = 0.07, dur = 0.55) {
  ws.forEach((w, i) => {
    const kin = eo(P(t, a + i * step, a + i * step + dur)), kout = eio(P(t, b - 0.38 + i * 0.03, b + i * 0.03));
    const y = 110 * (1 - kin) - 110 * kout;
    w.style.transform = `translateY(${y}%)`; w.style.visibility = Math.abs(y) >= 100 ? 'hidden' : 'visible';
  });
}

// ---------- build ----------
$('div', 'bg');
const shotEls = S.shots.map(sh => {
  const wrap = $('div', 'shot'); const img = $('img', 'shotimg', wrap); img.src = 'assets/' + sh.img + '.png';
  img.style.width = sh.iw + 'px'; img.style.height = sh.ih + 'px';
  const spots = (sh.spots || []).map(sp => ({ sp, el: $('div', 'spot', wrap) }));
  const calls = (sh.calls || []).map(c => {
    const g = $('div', 'call', wrap); const line = $('div', 'cline', g); const dot = $('div', 'cdot', g);
    const pill = $('div', 'cpill', g); const inner = $('div', 'cin', pill); const ws = words(inner, c.text);
    return { c, g, line, dot, pill, ws };
  });
  return { sh, wrap, img, spots, calls };
});
const capBox = $('div', 'cap');
const capEls = S.caps.map(c => {
  const g = $('div', 'capg', capBox); const plate = $('div', 'plate', g);
  const hw = c.h.split('|').map(line => words($('div', 'ch', g), line)).flat(); let sw = [];
  if (c.s) { const s = $('div', 'cs', g); sw = words(s, c.s); }
  return { c, g, plate, hw, sw };
});
const wipe = $('div', 'wipe');
const title = $('div', 'title'); const tlogo = $('img', 'tlogo', title);
if (S.title.logo) tlogo.src = S.title.logo; else tlogo.style.display = 'none';
const tk = $('div', 'tk', title); const tkw = words(tk, S.title.kicker || '');
const tt = $('div', 'tt', title);
const ttw = S.title.text.split('|').map(line => words($('div', 'ttl', tt), line)).flat();
const end = $('div', 'end'); const elock = $('img', 'elock', end);
if (S.end.logo) elock.src = S.end.logo; else elock.style.display = 'none';
const et = $('div', 'et', end); const etw = words(et, S.end.text);

function cam(sh, t) {
  const k = sh.cam; if (t <= k[0][0]) return k[0].slice(1);
  for (let i = 0; i < k.length - 1; i++) if (t <= k[i + 1][0]) {
    const e = eio(P(t, k[i][0], k[i + 1][0])); return [1, 2, 3].map(j => L(k[i][j], k[i + 1][j], e));
  }
  return k[k.length - 1].slice(1);
}

window.seek = async function (t) {
  const T1 = S.title.t1;
  title.style.display = t < T1 + 0.05 ? 'flex' : 'none';
  wordAnim(tkw, t, 0.15, T1 - 0.1); wordAnim(ttw, t, 0.35, T1);
  const lk = eo(P(t, 0.0, 0.8)), lo = eio(P(t, T1 - 0.45, T1));
  tlogo.style.transform = `translateY(${(1 - lk) * 40 - lo * 60}px)`; tlogo.style.opacity = Math.min(lk, 1 - lo);

  shotEls.forEach(({ sh, wrap, img, spots, calls }) => {
    const on = t >= sh.t0 && t < sh.t1; wrap.style.display = on ? 'block' : 'none'; if (!on) return;
    const [cx, cy, z] = cam(sh, t); const [ax, ay] = sh.anchor || S.anchor;
    const dy = sh.rise ? (1 - eo(P(t, sh.t0, sh.t0 + 1.1))) * H * 0.8 : 0;
    const ox = ax - cx * z, oy = ay - cy * z + dy;
    img.style.transform = `translate(${ox}px,${oy}px) scale(${z})`;
    const X = x => ox + x * z, Y = y => oy + y * z;
    spots.forEach(({ sp, el }) => {
      const a = eo(P(t, sp.t0, sp.t0 + 0.5)) * (1 - eio(P(t, sp.t1 - 0.4, sp.t1)));
      el.style.display = a > 0.001 ? 'block' : 'none'; const pad = 8;
      el.style.left = X(sp.box[0]) - pad + 'px'; el.style.top = Y(sp.box[1]) - pad + 'px';
      el.style.width = (sp.box[2] - sp.box[0]) * z + 2 * pad + 'px'; el.style.height = (sp.box[3] - sp.box[1]) * z + 2 * pad + 'px';
      el.style.opacity = a;
    });
    calls.forEach(({ c, g, line, dot, pill, ws }) => {
      const a0 = c.t0, a1 = c.t1; const vis = t >= a0 && t < a1; g.style.display = vis ? 'block' : 'none'; if (!vis) return;
      const px = X(c.at[0]), py = Y(c.at[1]); const qx = px + c.dx, qy = py + c.dy;
      const kd = eo(P(t, a0, a0 + 0.35)), kl = eo(P(t, a0 + 0.1, a0 + 0.55)), kp = eo(P(t, a0 + 0.3, a0 + 0.8));
      const ko = eio(P(t, a1 - 0.35, a1));
      dot.style.transform = `translate(${px}px,${py}px) translate(-50%,-50%) scale(${kd * (1 - ko)})`;
      const len = Math.hypot(c.dx, c.dy), ang = Math.atan2(c.dy, c.dx);
      line.style.width = len + 'px'; line.style.transform = `translate(${px}px,${py}px) rotate(${ang}rad) scaleX(${kl * (1 - ko)})`;
      const pw = pill.offsetWidth, ph = pill.offsetHeight;
      let lx, ly;
      if (c.dx === 0) { lx = qx - pw / 2; ly = c.dy < 0 ? qy - ph : qy; }
      else { lx = c.dx < 0 ? qx - pw : qx; ly = qy - ph / 2; }
      pill.style.transform = `translate(${lx}px,${ly}px)`;
      pill.style.clipPath = `inset(0 ${(1 - kp) * 100}% 0 0 round 999px)`;
      pill.style.opacity = 1 - ko;
      wordAnim(ws, t, a0 + 0.35, a1, 0.05, 0.5);
    });
  });

  capEls.forEach(({ c, g, plate, hw, sw }) => {
    const vis = t >= c.t0 && t < c.t1 + 0.1; g.style.display = vis ? 'block' : 'none'; if (!vis) return;
    const kp = eo(P(t, c.t0, c.t0 + 0.6)), ko = eio(P(t, c.t1 - 0.3, c.t1 + 0.1));
    plate.style.clipPath = `inset(0 ${(1 - kp) * 100}% 0 ${ko * 100}% round 28px)`;
    wordAnim(hw, t, c.t0 + 0.15, c.t1); wordAnim(sw, t, c.t0 + 0.35, c.t1);
  });

  const e0 = S.end.t0, kw = eio(P(t, e0 - 0.5, e0));
  wipe.style.display = t >= e0 - 0.5 && t < e0 + 0.05 ? 'block' : 'none'; wipe.style.clipPath = `inset(${(1 - kw) * 100}% 0 0 0)`;
  end.style.display = t >= e0 ? 'flex' : 'none';
  const kl2 = eo(P(t, e0, e0 + 0.9)); elock.style.transform = `translateY(${(1 - kl2) * 30}px) scale(${L(0.96, 1, kl2)})`; elock.style.opacity = kl2;
  wordAnim(etw, t, e0 + 0.35, 1e9);

  await Promise.all(shotEls.filter(s => s.wrap.style.display === 'block').map(s => s.img.decode().catch(() => 0)));
};
window.ready = (async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode().catch(() => 0))); await seek(0); return true; })();
