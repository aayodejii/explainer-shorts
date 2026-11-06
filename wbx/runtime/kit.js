// wbx kit: theme-neutral building blocks for an episode.
// The episode says *what* appears and *when*; the theme (series.yaml `style:`) decides how it looks and enters:
//   rough themes (sketch, chalk): outlines draw on, hatch fills scribble in, text writes on
//   clean theme: cards pop, rows slide in, text fades up, highlights wipe
// Everything becomes wb.js data attributes, so render(t) stays a pure function of time.
//
//   const K = wbx.kit();
//   K.scene(0, 5.2);                         // following elements fade out at 5.2
//   K.text(540, 400, 90, 'Hello', 0.3, {anchor:'middle', cls:'title'});
//   K.card(80, 600, 400, 300, 1.0, {tone:'blue', bar:true});
//
// Never put data-pop and data-move on the same element (both set a transform).
(function(){
const NS='http://www.w3.org/2000/svg';
const r2=n=>Math.round(n*100)/100;

// icon outlines, drawn around (0,0) at size 100
const ICONS={
  bookmark:'M-50 -70 L50 -70 L50 70 L0 30 L-50 70 Z',
  plane:'M-65 0 L65 -60 L25 70 L0 18 Z M0 18 L65 -60',
  check:'M-45 0 L-12 35 L50 -40',
  cross:'M-40 -40 L40 40 M40 -40 L-40 40',
  phone:'M-34 -62 L34 -62 L34 62 L-34 62 Z M-10 46 L10 46',
};
const place=(d,x,y,s)=>d.replace(/(-?\d+\.?\d*) (-?\d+\.?\d*)/g,(m,a,b)=>`${r2(x+a*s)} ${r2(y+b*s)}`);

function kit(opts={}){
  const th=Object.assign({},window.WBX_THEME||{},opts);
  const svg=document.getElementById('s'), top=document.getElementById('root');
  if(!svg||!top) throw new Error('kit needs <svg id="s"> containing <g id="root">');
  svg.insertAdjacentHTML('afterbegin',th.background||'');
  if(th.rootFilter) top.setAttribute('filter',`url(#${th.rootFilter})`);
  const rough_=th.kind==='rough', rc=rough_?rough.svg(svg):null;
  let seed=th.seed||7, cur=top;

  const el=(tag,a,parent=cur,txt)=>{const e=document.createElementNS(NS,tag);
    for(const k in a)if(a[k]!=null)e.setAttribute(k,a[k]);if(txt!=null)e.textContent=txt;parent.appendChild(e);return e};
  const ro=x=>Object.assign({seed:seed++,roughness:th.roughness,bowing:1.3,strokeWidth:th.stroke,stroke:th.ink,
                             hachureGap:th.hatchGap,fillWeight:th.fillWeight},x||{});
  const drawAll=(n,t,d)=>{n.querySelectorAll('path').forEach(p=>p.setAttribute('data-draw',`${r2(t)},${d}`));cur.appendChild(n);return n};
  // rough shape: outline draws first, then the fill scribbles in
  const roughShape=(n,t,d=0.5)=>{const kids=[...n.children], out=kids.pop();
    out.setAttribute('data-draw',`${r2(t)},${d}`);
    kids.forEach(k=>{k.setAttribute('data-draw',`${r2(t+d*0.6)},${d*1.6}`);if(th.fillOpacity!=null)k.setAttribute('opacity',th.fillOpacity)});
    cur.appendChild(n);return n};
  const color=tone=>tone?(th[tone]||tone):th.ink;

  const K={
    theme:th, el,
    /** Start a scene: following elements go in a group that fades out at `end` (omit end to keep it). */
    scene(start,end,o={}){cur=el('g',end!=null?{'data-out':`${r2(end)},${o.fade||0.3}`}:{},top);return cur},
    /** Small series title on the hook only. */
    header(txt,end){if(!txt)return;const g=el('g',{'data-out':`${r2(end)},0.3`},top);const keep=cur;cur=g;
      K.text(540,190,44,txt,0,{anchor:'middle',cls:'label',color:th.blue});K.underline(380,700,228,th.ink,0.1);cur=keep;return g},
    text(x,y,size,txt,t,o={}){
      const e=el('text',{x,y,'font-size':size,'text-anchor':o.anchor,class:o.cls,style:o.color?`fill:${color(o.color)}`:null},cur,txt);
      if(rough_)e.setAttribute('data-write',`${r2(t)},${r2(o.dur||Math.min(1.2,0.12+txt.length*0.045))}`);
      else{e.setAttribute('data-fade',`${r2(t)},0.35`);e.setAttribute('data-move',`${r2(t)},0.45,0,26`)}
      return e},
    /** Container. tone: blue/green/red/orange/yellow; bar: accent stripe (clean); hatch: rough fill style. */
    card(x,y,w,h,t,o={}){
      if(rough_)return roughShape(rc.rectangle(x,y,w,h,ro({stroke:o.tone&&o.tone!=='yellow'?color(o.tone):th.ink,
        fill:o.tone?th.fills[o.tone]:undefined,fillStyle:o.hatch||'hachure'})),t);
      const g=el('g',{'data-pop':`${r2(t)},0.4`});
      el('rect',{x,y,width:w,height:h,rx:o.rx??28,fill:(th.tints||{})[o.tone]||'#fff',filter:'url(#sh)'},g);
      if(o.bar)el('rect',{x,y,width:12,height:h,rx:6,fill:color(o.tone)},g);
      return g},
    /** Table/list row. */
    row(x,y,w,h,t,o={}){
      if(rough_)return roughShape(rc.rectangle(x,y,w,h,ro()),t,0.35);
      const g=el('g',{'data-fade':`${r2(t)},0.3`,'data-move':`${r2(t)},0.4,60,0`});
      el('rect',{x,y,width:w,height:h,rx:18,fill:o.zebra?'#F5F6F9':'#fff'},g);return g},
    /** Emphasise a row/box as "the one" (green by default). */
    mark(x,y,w,h,t,o={}){const tone=o.tone||'green';
      if(rough_)return roughShape(rc.rectangle(x,y,w,h,ro({stroke:color(tone),fill:th.fills[tone],fillStyle:'cross-hatch',strokeWidth:th.stroke+1})),t,0.35);
      return el('rect',{x,y,width:w,height:h,rx:18,fill:(th.tints||{})[tone]||'#fff',stroke:color(tone),'stroke-width':5,'data-wipe':`${r2(t)},0.35`})},
    /** Highlighter behind text; pass {before: textElement} so it sits underneath. */
    highlight(x,y,w,h,t,o={}){
      const n=rough_?rc.rectangle(x,y,w,h,ro({stroke:'none',fill:o.color||th.highlight,fillStyle:'solid',roughness:2.2}))
                    :el('rect',{x,y,width:w,height:h,rx:16,fill:o.color||th.highlight});
      n.setAttribute('data-wipe',`${r2(t)},0.4`);cur.insertBefore(n,o.before||null);return n},
    /** Arrow along points [[x,y],...] (rough: curve through them; clean: cubic from 4 points). */
    arrow(pts,t,o={}){const c=color(o.tone||'accent'), d=o.dur||0.6;
      const [x1,y1]=pts[pts.length-2],[x2,y2]=pts[pts.length-1],a=Math.atan2(y2-y1,x2-x1);
      if(rough_){const n=drawAll(rc.curve(pts,ro({stroke:c,strokeWidth:th.stroke+1})),t,d);
        [0.5,-0.5].forEach(s=>drawAll(rc.line(x2,y2,x2-34*Math.cos(a+s),y2-34*Math.sin(a+s),ro({stroke:c,strokeWidth:th.stroke+1})),t+d,0.15));return n}
      const dd=pts.length===4?`M${pts[0]} C ${pts[1]}, ${pts[2]}, ${pts[3]}`:'M'+pts.map(p=>p.join(' ')).join(' L');
      const p=el('path',{d:dd,fill:'none',stroke:c,'stroke-width':9,'stroke-linecap':'round','stroke-linejoin':'round','data-draw':`${r2(t)},${d}`});
      const L=26;el('path',{d:`M${x2+8*Math.cos(a)} ${y2+8*Math.sin(a)} L${x2-L*Math.cos(a+0.5)} ${y2-L*Math.sin(a+0.5)} L${x2-L*Math.cos(a-0.5)} ${y2-L*Math.sin(a-0.5)}Z`,
        fill:c,'data-pop':`${r2(t+d-0.05)},0.25`});return p},
    line(x1,y1,x2,y2,t,o={}){const c=color(o.tone);
      if(rough_)return drawAll(rc.line(x1,y1,x2,y2,ro({stroke:c,strokeWidth:o.width||th.stroke})),t,o.dur||0.35);
      return el('path',{d:`M${x1} ${y1} L${x2} ${y2}`,stroke:c,'stroke-width':o.width||8,'stroke-linecap':'round','data-draw':`${r2(t)},${o.dur||0.35}`})},
    strike(x1,y1,x2,y2,t,o={}){return K.line(x1,y1,x2,y2,t,{tone:o.tone||'red'})},
    underline(x1,x2,y,c,t){
      if(rough_)return drawAll(rc.curve([[x1,y+4],[(x1+x2)/2,y-8],[x2,y+6]],ro({stroke:c||th.accent,strokeWidth:th.stroke+2})),t,0.5);
      return el('rect',{x:x1,y:y-4,width:x2-x1,height:10,rx:5,fill:c||th.accent,'data-wipe':`${r2(t)},0.5`})},
    /** Line icon from the ICONS set, drawn on. size 100 = the reference size. */
    icon(name,x,y,t,o={}){const d=place(ICONS[name],x,y,(o.size||100)/100), c=color(o.tone||'blue');
      if(rough_)return drawAll(rc.path(d,ro({stroke:c,strokeWidth:th.stroke+2})),t,o.dur||0.45);
      return el('path',{d,fill:'none',stroke:c,'stroke-width':9,'stroke-linecap':'round','stroke-linejoin':'round','data-draw':`${r2(t)},${o.dur||0.45}`})},
    magnifier(cx,cy,t,o={}){const c=color(o.tone||'blue');
      if(rough_){drawAll(rc.circle(cx,cy,50,ro({stroke:c})),t,0.3);
        return drawAll(rc.line(cx+18,cy+18,cx+43,cy+43,ro({stroke:c,strokeWidth:th.stroke+2})),t+0.25,0.3)}
      const g=el('g',{'data-pop':`${r2(t)},0.35`});
      el('circle',{cx,cy,r:22,fill:'none',stroke:c,'stroke-width':7},g);
      el('path',{d:`M${cx+16} ${cy+16} L${cx+36} ${cy+36}`,stroke:c,'stroke-width':8,'stroke-linecap':'round'},g);return g},
    /** Database cylinder: centre x, top y, width, height. */
    database(cx,y,w,h,t,o={}){const ry=w*0.16, x0=cx-w/2, x1=cx+w/2, c=color(o.tone||'blue');
      const body=`M${x0} ${y+ry} L${x0} ${y+h-ry} A${w/2} ${ry} 0 0 0 ${x1} ${y+h-ry} L${x1} ${y+ry}`;
      const band=yy=>`M${x0} ${yy} A${w/2} ${ry} 0 0 0 ${x1} ${yy}`;
      if(rough_){roughShape(rc.path(body,ro({stroke:c,fill:th.fills[o.tone||'blue'],fillStyle:'hachure'})),t,0.5);
        drawAll(rc.ellipse(cx,y+ry,w,ry*2,ro({stroke:c})),t+0.2,0.4);
        [0.42,0.7].forEach(f=>drawAll(rc.path(band(y+h*f),ro({stroke:c,strokeWidth:th.stroke-1})),t+0.45,0.35));return}
      const g=el('g',{'data-pop':`${r2(t)},0.4`});
      el('path',{d:body+' Z',fill:'#fff',stroke:c,'stroke-width':5,filter:'url(#sh)'},g);
      [0.3,0.82].forEach(f=>el('path',{d:band(y+h*f),fill:'none',stroke:c,'stroke-width':4,opacity:0.45},g));
      el('ellipse',{cx,cy:y+ry,rx:w/2,ry,fill:(th.tints||{}).blue||'#E8EFFF',stroke:c,'stroke-width':5},g);
      if(o.label)el('text',{x:cx,y:y+h*0.62,'font-size':o.size||44,'text-anchor':'middle',class:'label',style:`fill:${c}`},g,o.label);
      return g},
    /** Pill label centred at (cx, cy). Width is estimated from the text unless o.w is given. */
    chip(cx,cy,txt,t,o={}){const size=o.size||40, w=o.w||Math.round(txt.length*size*(o.cls==='data'?0.62:0.56)+size*1.4), h=size*1.7;
      const c=o.tone?color(o.tone):th.ink;
      if(rough_){roughShape(rc.rectangle(cx-w/2,cy-h/2,w,h,ro({stroke:c})),t,0.35);
        return K.text(cx,cy+size*0.35,size,txt,t+0.2,{anchor:'middle',cls:o.cls,color:o.tone})}
      const g=el('g',{'data-pop':`${r2(t)},0.35`});
      el('rect',{x:cx-w/2,y:cy-h/2,width:w,height:h,rx:h/2,fill:o.fill||(th.tints||{})[o.tone]||'#fff',filter:'url(#sh)'},g);
      el('text',{x:cx,y:cy+size*0.35,'font-size':size,'text-anchor':'middle',class:o.cls,style:`fill:${c}`},g,txt);
      return g},
    /** Number counting from→to over dur seconds. */
    counter(x,y,size,from,to,t,dur,o={}){
      const e=el('text',{x,y,'font-size':size,'text-anchor':o.anchor,class:o.cls,style:o.color?`fill:${color(o.color)}`:null,
        'data-fade':`${r2(t)},0.2`,'data-count':`${r2(t)},${dur},${from},${to}`});return e},
    /** "Save this & share it" end card from t until the end. */
    endCard(t,lines){K.scene(t);
      K.icon('bookmark',260,750,t+0.05);K.text(360,795,120,lines[0],t+0.1,{cls:'title',dur:0.5});
      K.icon('plane',265,960,t+0.65);K.text(360,1005,120,lines[1],t+0.7,{cls:'title',dur:0.5});
      if(lines[2])K.text(540,1160,th.endSmall||62,lines[2],t+1.1,{anchor:'middle',color:'muted',dur:1.0});},
  };
  return K;
}
window.wbx={kit,ICONS};
})();
