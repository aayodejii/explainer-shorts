// Shared whiteboard animation runtime: every element is a pure function of t,
// so frames can be rendered in any order.
const clamp=x=>Math.max(0,Math.min(1,x));
const ease=x=>1-Math.pow(1-x,3);
const back=x=>{const c=1.7;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
const arg=(el,k)=>el.dataset[k].split(',').map(Number);
const els=k=>document.querySelectorAll('[data-'+k+']');
window.WORDS=window.WORDS||[];
// caption chunks: up to 4 words / ~20 chars, breaking after punctuation
function chunks(){const out=[];let cur=[],len=0;
  for(const w of WORDS){
    if(cur.length&&len+w.w.length>20){out.push(cur);cur=[];len=0}
    cur.push(w);len+=w.w.length+1;
    if(cur.length==4||/[.?!,]$/.test(w.w)){out.push(cur);cur=[];len=0}}
  if(cur.length)out.push(cur);return out;}
let CH=null;
window.render=function(t){
  for(const el of els('draw')){
    if(el._L==null){el._L=el.getTotalLength();el.style.strokeDasharray=el._L}
    const[s,d]=arg(el,'draw');const p=ease(clamp((t-s)/d));
    el.style.strokeDashoffset=el._L*(1-p);el.style.visibility=p>0?'visible':'hidden';}
  for(const el of els('fade')){const[s,d]=arg(el,'fade');el.style.opacity=clamp((t-s)/d);}
  for(const el of els('write')){const[s,d]=arg(el,'write');const p=clamp((t-s)/d);
    el.style.clipPath=`inset(-20% ${(1-p)*100}% -20% -5%)`;}
  for(const el of els('wipe')){const[s,d]=arg(el,'wipe');const p=ease(clamp((t-s)/d));
    el.style.clipPath=`inset(0 ${(1-p)*100}% 0 0)`;}
  for(const el of els('pop')){const[s,d]=arg(el,'pop');const p=clamp((t-s)/d);
    el.style.opacity=p>0?Math.min(1,p*3):0;el.style.transform=`scale(${p>0?0.5+0.5*back(p):0.5})`;}
  // fade-out multiplies whatever pop/fade-in set this frame, so an element can have both
  for(const el of els('out')){const[s,d]=arg(el,'out');
    const base=el.hasAttribute('data-pop')||el.hasAttribute('data-fade')?parseFloat(el.style.opacity):1;
    el.style.opacity=base*(1-clamp((t-s)/d));}
  // slide in: data-move="start,dur,dx,dy" starts offset by (dx,dy) and eases to its place
  for(const el of els('move')){const[s,d,dx,dy]=arg(el,'move');const p=1-ease(clamp((t-s)/d));
    el.setAttribute('transform',`translate(${dx*p} ${dy*p})`);}
  // count up: data-count="start,dur,from,to"
  for(const el of els('count')){const[s,d,a,b]=arg(el,'count');
    el.textContent=Math.round(a+(b-a)*ease(clamp((t-s)/d))).toLocaleString('en-GB');}
  if(window.extra)window.extra(t);
  // hand-drawn "boil": new noise seed ~8 times a second
  const turb=document.getElementById('turb'); if(turb)turb.setAttribute('seed',1+Math.floor(t*8)%4);
  const cap=document.getElementById('cap'); if(!cap)return;
  CH=CH||chunks();let html='';
  for(let i=0;i<CH.length;i++){const ch=CH[i],next=CH[i+1],end=next?next[0].s:1e9;
    if(t>=ch[0].s&&t<end){let cur=0;ch.forEach((w,j)=>{if(t>=w.s)cur=j});
      html=ch.map((w,j)=>`<span class="${j==cur?'on':''}">${w.w}</span>`).join(' ');break;}}
  cap.innerHTML=html;
};
