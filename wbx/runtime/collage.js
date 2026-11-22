// Collage building blocks for `style: collage` (load after kit.js, before wb.js):
//   const K = wbx.kit(), C = wbx.collage(K);
// Everything is a pure function of t (like the rest of the runtime), so frames render in any order.
//   C.paper(x, y, w, h, t, {rot, fill, tape, ruled, enter:'pop'|'slide', dx, dy, parent})  → group in paper coords
//   C.text(parent, x, y, size, 'txt', t, {anchor, cls:'title'|'hand'|'data'|'stampText', color})
//   C.highlight(parent, x, y, w, h, t)         yellow highlighter swept behind text
//   C.stamp(x, y, 'TEXT', size, rot, t, {parent, color})   distressed rubber stamp that slams in
//   C.string([[x,y],...], t, dur, {parent, pins})          red string drawn through pins
//   C.loop(cx, cy, rx, ry, t, {parent})        hand-drawn loop around something
//   C.mover(keys, show, build)                 keyframed group: keys [[t,x,y,rot?],...], show [t0,t1], build(g)
//   C.camera(keys, {until})                    keys [[t, cx, cy, zoom],...]; identity after `until` (end card)
// Per-frame work goes through the kit (K.onFrame); C.mover/C.onFrame are the kit's K.mover/K.onFrame.
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  window.wbx = window.wbx || {};
  wbx.collage = function (K) {
    const th = K.theme, svg = document.getElementById('s'), root = document.getElementById('root');
    const f2 = n => (+n).toFixed(2);
    // camera wrapper around the kit root; grain + vignette above everything
    const cam = document.createElementNS(NS, 'g'); cam.id = 'cam'; root.parentNode.insertBefore(cam, root); cam.appendChild(root);
    const over = document.createElementNS(NS, 'g'); svg.appendChild(over);
    const el = (tag, a, parent, txt) => { const e = document.createElementNS(NS, tag);
      for (const k in a) if (a[k] != null) e.setAttribute(k, a[k]); if (txt != null) e.textContent = txt; parent.appendChild(e); return e; };
    el('rect', {x: 0, y: 0, width: 1080, height: 1920, filter: 'url(#grain)', opacity: th.grain ?? 0.32}, over);   // static grain: keeps files small
    el('rect', {width: 1080, height: 1920, fill: 'url(#vig)'}, over);
    const cur = () => K.el('g', {});          // current kit scene group (so K.scene fade-outs apply)
    const C = {cam, over};

    C.paper = (x, y, w, h, t, o = {}) => {
      const outer = el('g', {transform: `translate(${x} ${y}) rotate(${o.rot || 0} ${w / 2} ${h / 2})`}, o.parent || cur());
      const anim = el('g', o.enter === 'slide' ? {'data-fade': `${f2(t)},0.25`, 'data-move': `${f2(t)},0.5,${o.dx || 0},${o.dy ?? 80}`}
                                               : {'data-pop': `${f2(t)},0.35`}, outer);
      el('rect', {width: w, height: h, fill: o.fill || th.card, style: 'filter:url(#torn) url(#drop)'}, anim);
      if (o.ruled) el('rect', {x: 10, y: 10, width: w - 20, height: h - 20, fill: 'url(#ruled)'}, anim);
      if (o.tape !== false) el('rect', {x: w / 2 - 70, y: -22, width: 140, height: 44, fill: th.tape, opacity: .8,
        transform: `rotate(${o.tapeRot ?? -3} ${w / 2} 0)`}, anim);
      return el('g', {}, anim);
    };
    C.text = (p, x, y, size, s, t, o = {}) => el('text', {x, y, 'font-size': size, 'text-anchor': o.anchor, class: o.cls,
      style: o.color ? `fill:${th[o.color] || o.color}` : null, 'data-fade': t != null ? `${f2(t)},0.3` : null}, p, s);
    C.highlight = (p, x, y, w, h, t) => { const r = el('rect', {x, y, width: w, height: h, fill: th.yellow, opacity: .85,
      style: 'mix-blend-mode:multiply', 'data-wipe': `${f2(t)},0.4`}, p); p.insertBefore(r, p.firstChild); return r; };
    C.stamp = (x, y, s, size, rot, t, o = {}) => {
      const col = th[o.color] || o.color || th.red;
      const g0 = el('g', {transform: `translate(${x} ${y}) rotate(${rot})`}, o.parent || cur());
      const a = el('g', {'data-pop': `${f2(t)},0.2`, filter: 'url(#stamp)'}, g0);
      const w = s.length * size * 0.66 + size * 0.9;
      el('rect', {x: -w / 2, y: -size * 0.85, width: w, height: size * 1.45, fill: 'none', stroke: col, 'stroke-width': size * 0.09}, a);
      el('text', {y: size * 0.34, 'font-size': size, 'text-anchor': 'middle', class: 'stampText', style: `fill:${col}`}, a, s);
      return g0;
    };
    C.string = (pts, t, dur, o = {}) => {
      const p = o.parent || cur();
      const path = el('path', {d: 'M' + pts.map(q => q.join(' ')).join(' L'), fill: 'none', stroke: th.red, 'stroke-width': 6,
        'stroke-linecap': 'round', 'data-draw': `${f2(t)},${dur}`}, p);
      if (o.pins !== false) pts.forEach(([x, y], i) => { const pg = el('g', {'data-pop': `${f2(t + dur * i / Math.max(1, pts.length - 1))},0.25`}, p);
        el('circle', {cx: x, cy: y, r: 16, fill: th.red}, pg); el('circle', {cx: x - 5, cy: y - 5, r: 5, fill: '#F2A79E'}, pg); });
      return path;
    };
    C.loop = (cx, cy, rx, ry, t, o = {}) => { let d = '';
      for (let a = 0; a <= Math.PI * 2.15; a += 0.12) { const wob = 1 + 0.04 * Math.sin(a * 3);
        d += (d ? ' L' : 'M') + `${f2(cx + Math.cos(a - 2.6) * rx * wob)} ${f2(cy + Math.sin(a - 2.6) * ry * wob)}`; }
      return el('path', {d, fill: 'none', stroke: th.red, 'stroke-width': 7, 'stroke-linecap': 'round', 'data-draw': `${f2(t)},${o.dur || 0.6}`}, o.parent || cur());
    };

    let CAM = null, camUntil = 1e9;
    C.camera = (keys, o = {}) => { CAM = keys; camUntil = o.until ?? 1e9; };
    C.mover = K.mover; C.onFrame = K.onFrame; C.interp = K.interp;
    K.onFrame(t => {
      if (CAM && t < camUntil) { const [cx, cy, z] = K.interp(CAM, t);
        cam.setAttribute('transform', `translate(540 960) scale(${z}) translate(${-cx} ${-cy})`); }
      else cam.removeAttribute('transform');
    });
    return C;
  };
})();
