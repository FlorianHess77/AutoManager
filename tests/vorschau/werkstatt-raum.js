(()=>{
const css=`
#wsRoom{position:relative;overflow:hidden;background:#120f0c;touch-action:pan-y;--px:0;--py:0;-webkit-tap-highlight-color:transparent}
#wsRoom .wsz{transform-origin:0 0;width:100%;height:100%}
#wsRoom svg{display:block;width:100%;height:100%}
#wsRoom .L0,#wsRoom .L1,#wsRoom .L2,#wsRoom .FX{transition:transform .25s ease-out}
#wsRoom .L0{transform:translate(calc(var(--px)*-3px),calc(var(--py)*-2px))}
#wsRoom .L1{transform:translate(calc(var(--px)*-6px),calc(var(--py)*-4px))}
#wsRoom .L2{transform:translate(calc(var(--px)*-12px),calc(var(--py)*-7px))}
#wsRoom .FX{transform:translate(calc(var(--px)*-4px),calc(var(--py)*-3px))}
#wsRoom .lit{animation:wsOn 1s linear both}
#wsRoom .dark{animation:wsDark 1s linear both;pointer-events:none}
@keyframes wsOn{0%{opacity:0}10%{opacity:.9}16%{opacity:.05}26%{opacity:1}31%{opacity:.3}40%,100%{opacity:1}}
@keyframes wsDark{0%{opacity:.75}10%{opacity:.2}16%{opacity:.7}26%{opacity:.05}31%{opacity:.5}40%,100%{opacity:0}}
#wsRoom .dust{transform-box:fill-box;animation:wsDust var(--d,9s) ease-in-out infinite;animation-delay:var(--dl,0s);opacity:0}
@keyframes wsDust{0%{transform:translate(0,0);opacity:0}20%{opacity:.85}50%{transform:translate(7px,-16px)}80%{opacity:.6}100%{transform:translate(-5px,-30px);opacity:0}}
#wsRoom .cloud{animation:wsCloud 38s linear infinite}
@keyframes wsCloud{from{transform:translateX(-70px)}to{transform:translateX(80px)}}
#wsRoom .star{animation:wsTw 2.4s ease-in-out infinite alternate}
@keyframes wsTw{from{opacity:.25}to{opacity:1}}
#wsRoom .sec{transform-origin:250px 205px;animation:wsSec 60s steps(60) infinite}
@keyframes wsSec{to{transform:rotate(360deg)}}
#wsRoom .note{animation:wsNote 3.2s ease-out infinite;opacity:0;transform-box:fill-box}
@keyframes wsNote{0%{transform:translate(0,0);opacity:0}15%{opacity:1}100%{transform:translate(10px,-26px) rotate(15deg);opacity:0}}
#wsRoom .led{animation:wsLed 1.1s steps(2) infinite}
@keyframes wsLed{50%{opacity:.25}}
#wsRoom .pulse{animation:wsPulse 1.4s ease-in-out infinite}
@keyframes wsPulse{50%{opacity:.35}}
#wsRoom .badge{transform-box:fill-box;transform-origin:center;animation:wsPop .5s 1.1s cubic-bezier(.3,1.8,.5,1) both}
@keyframes wsPop{from{transform:scale(0)}}
#wsRoom [data-ws]{cursor:pointer}
#wsRoom .drawer1{transition:transform .14s ease-out}
#wsRoom.p-tools .drawer1{transform:translateY(7px)}
#wsRoom .wob{transform-box:fill-box;transform-origin:bottom center}
#wsRoom.p-inv .wob{animation:wsWob .3s ease-in-out}
@keyframes wsWob{30%{transform:rotate(-5deg)}70%{transform:rotate(4deg)}}
#wsRoom .paper{transform-box:fill-box;transform-origin:top center;transition:transform .15s}
#wsRoom.p-shop .paper{transform:rotate(-6deg)}
#wsRoom .book{transition:transform .15s;transform-box:fill-box;transform-origin:bottom center}
#wsRoom.p-log .book{transform:translateY(-4px)}
#wsRoom .hint{position:absolute;left:0;right:0;bottom:12px;text-align:center;font:600 12px system-ui;color:#e9e0cf;text-shadow:0 1px 3px #000;animation:wsHint 4s 1.4s both;pointer-events:none}
@keyframes wsHint{0%{opacity:0}10%,80%{opacity:1}100%{opacity:0}}
#wsRoom .fade{position:absolute;inset:0;background:#191612;opacity:0;pointer-events:none}
#view.ws-arrive{animation:wsArr .22s ease-out}
@keyframes wsArr{from{opacity:0;transform:scale(.97)}}
@media (prefers-reduced-motion:reduce){#wsRoom *{animation:none!important;transition:none!important}#wsRoom .dark{opacity:0}#wsRoom .dust,#wsRoom .note{display:none}}`;
const st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
const VP=[195,300],bk=(x,y,k)=>[x+(VP[0]-x)*k,y+(VP[1]-y)*k],P=a=>a.map(p=>p.map(v=>(+v).toFixed(1)).join(',')).join(' ');
const T=(x,y,t,o='')=>`<text x="${x}" y="${y}" font-family="system-ui,sans-serif" ${o}>${t}</text>`;
function svg(hour){
 const nT=S.tools.length,lent=S.tools.filter(t=>t.lentTo).length,nI=S.inventory.length,low=S.inventory.filter(i=>i.minQty!=null&&(i.qty||0)<i.minQty).length,shop=(S.shop||[]).filter(x=>!x.done).length;
 const day=hour>=7&&hour<17,dusk=!day&&hour>=5&&hour<20,night=!day&&!dusk;
 const sky=day?['#6fa8dc','#cfe5f6']:dusk?['#3b3a6b','#f29a4a']:['#070b1e','#18244a'];
 let s=`<svg viewBox="0 0 390 700" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg"><defs>
<linearGradient id="wsFl" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#36312b"/><stop offset="1" stop-color="#5a534b"/></linearGradient>
<linearGradient id="wsSky" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${sky[0]}"/><stop offset="1" stop-color="${sky[1]}"/></linearGradient>
<radialGradient id="wsGlow" cx=".5" cy=".1" r=".8"><stop offset="0" stop-color="#ffe9b8" stop-opacity=".32"/><stop offset=".45" stop-color="#ffd68a" stop-opacity=".08"/><stop offset="1" stop-opacity="0"/></radialGradient>
<radialGradient id="wsVig" cx=".5" cy=".45" r=".78"><stop offset=".55" stop-opacity="0"/><stop offset="1" stop-opacity="${night?.78:day?.5:.65}"/></radialGradient>
<linearGradient id="wsCone" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#fff2cc" stop-opacity=".22"/><stop offset="1" stop-color="#fff2cc" stop-opacity="0"/></linearGradient>
<linearGradient id="wsBeam" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${day?'#fff7d6':'#ffb36b'}" stop-opacity="${day?.2:.12}"/><stop offset="1" stop-color="#fff7d6" stop-opacity="0"/></linearGradient>
<pattern id="wsPeg" width="9" height="9" patternUnits="userSpaceOnUse"><rect width="9" height="9" fill="#8a6a45"/><circle cx="4.5" cy="4.5" r="1.3" fill="#3b2b1a"/></pattern>
<pattern id="wsBrick" width="40" height="20" patternUnits="userSpaceOnUse"><rect width="40" height="20" fill="#3d332a"/><path d="M0 .5h40M0 10.5h40M20 0v10M0 10v10M40 10v10" stroke="#2a221b" stroke-width="1.2"/><rect x="3" y="2" width="14" height="7" fill="#46392e" opacity=".5"/><rect x="24" y="12" width="12" height="7" fill="#33291f" opacity=".6"/></pattern>
<linearGradient id="wsRed" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#d8432f"/><stop offset="1" stop-color="#a5281b"/></linearGradient>
<linearGradient id="wsChr" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#f4f4f4"/><stop offset="1" stop-color="#8a8a8a"/></linearGradient>
<linearGradient id="wsWood" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#c1925b"/><stop offset="1" stop-color="#8a6236"/></linearGradient>
<linearGradient id="wsOrg" x1="0" x2="1"><stop offset="0" stop-color="#f2853a"/><stop offset="1" stop-color="#c0480f"/></linearGradient>
<clipPath id="wsWin"><rect x="238" y="124" width="66" height="52"/></clipPath>
</defs>`;
 // L0: Raum, Fenster, Uhr, Schild, Spinnennetz
 s+=`<g class="L0"><rect x="-40" y="-40" width="470" height="780" fill="#1a1611"/>
<polygon points="-40,-40 430,-40 320,110 70,110" fill="#1c1813"/>
<polygon points="-40,-60 70,110 70,390 -40,470" fill="#2b241d"/><polygon points="430,-60 320,110 320,390 430,470" fill="#2b241d"/>
<rect x="70" y="110" width="250" height="280" fill="url(#wsBrick)"/>
<polygon points="70,390 320,390 440,476 440,760 -50,760 -50,476" fill="url(#wsFl)"/>
<path d="M70 390H320" stroke="#000" stroke-opacity=".5" stroke-width="2"/>
<polygon points="${P([[66,398],[324,398],[331,404],[59,404]])}" fill="#f0b43c" opacity=".75"/>
<ellipse cx="196" cy="668" rx="34" ry="8" fill="#0d0b09" opacity=".55"/><ellipse cx="190" cy="666" rx="12" ry="3" fill="#5a4f7a" opacity=".25"/>
<rect x="234" y="120" width="74" height="60" fill="#5a442b"/><g clip-path="url(#wsWin)"><rect x="238" y="124" width="66" height="52" fill="url(#wsSky)"/>
${day?`<circle cx="292" cy="134" r="7" fill="#fff6c8"/><g class="cloud"><ellipse cx="250" cy="140" rx="14" ry="5" fill="#fff" opacity=".9"/><ellipse cx="258" cy="137" rx="9" ry="5" fill="#fff" opacity=".9"/></g><g class="cloud" style="animation-delay:-19s"><ellipse cx="262" cy="156" rx="11" ry="4" fill="#fff" opacity=".75"/></g>`:''}
${night?`<circle cx="288" cy="136" r="6" fill="#f3efd8"/><circle cx="291" cy="134" r="6" fill="#18244a"/>${[[246,132],[262,142],[276,128],[252,160],[298,158],[270,166]].map(([x,y],i)=>`<circle class="star" style="animation-delay:-${i*.5}s" cx="${x}" cy="${y}" r="1" fill="#fff"/>`).join('')}`:''}
${dusk?`<circle cx="270" cy="170" r="9" fill="#ffcf7a" opacity=".9"/>`:''}
<rect x="238" y="160" width="66" height="16" fill="#1a1611" opacity=".85"/><path d="M238 164h66" stroke="#2b241d"/></g>
<path d="M271 124v52M238 150h66" stroke="#5a442b" stroke-width="3"/>
<circle cx="250" cy="205" r="14" fill="#f3eee2" stroke="#1b160f" stroke-width="2.5"/>${[0,1,2,3,4,5,6,7,8,9,10,11].map(i=>`<path d="M250 193v2.5" stroke="#1b160f" stroke-width="${i%3?1:1.8}" transform="rotate(${i*30} 250 205)"/>`).join('')}
<path id="wsHr" d="M250 205v-7" stroke="#1b160f" stroke-width="2.4" stroke-linecap="round"/><path id="wsMin" d="M250 205v-10" stroke="#1b160f" stroke-width="1.6" stroke-linecap="round"/>
<path class="sec" d="M250 207v-12" stroke="#d5402f" stroke-width=".9"/><circle cx="250" cy="205" r="1.5" fill="#d5402f"/>
<g transform="matrix(1,.68,0,.9,14,176)"><rect width="38" height="56" rx="3" fill="#1d4f9a" stroke="#f0b43c" stroke-width="2"/><circle cx="19" cy="18" r="11" fill="#f0b43c"/>${T(19,22,'ÖL','font-size="10" font-weight="900" text-anchor="middle" fill="#1d4f9a"')}${T(19,42,'MOTOR','font-size="7.5" font-weight="900" text-anchor="middle" fill="#fff"')}${T(19,50,'1958','font-size="5" text-anchor="middle" fill="#f0b43c"')}</g>
<path d="M70 110l26 0M70 110l0 24M70 110l20 16M70 110l11 22M74 112q8 4 12-2M74 118q11 4 16-6M76 124q11 2 14-10" fill="none" stroke="#cfc6b4" stroke-width=".6" opacity=".55"/>
</g>`;
 // L1: Lochwand, Zettel, Werkbank, Radio, Lagerbuch, Reifen
 s+=`<g class="L1"><rect x="84" y="132" width="122" height="104" fill="url(#wsPeg)" stroke="#5a442b" stroke-width="3"/>
<g fill="none" stroke="#dcdcdc" stroke-width="3.2" stroke-linecap="round" opacity=".88"><path d="M98 146v58"/><circle cx="98" cy="212" r="6"/><path d="M118 148l8 52"/><path d="M114 146h10"/><path d="M140 150v38"/><rect x="134" y="188" width="12" height="26" rx="3" fill="#c33" stroke="none"/><path d="M160 146v40m-6-40h12"/><path d="M152 186h16v24h-16z" fill="#c9a227" stroke="none"/></g>
<g id="ws-shop" data-ws="shop"><rect x="166" y="138" width="64" height="92" fill="transparent"/><g class="paper"><rect x="170" y="146" width="56" height="78" rx="3" fill="#7a5530"/><rect x="175" y="156" width="46" height="64" fill="#f3eee2"/>
${T(198,168,'EINKAUF','font-size="7.5" text-anchor="middle" fill="#1b160f" font-weight="800" letter-spacing=".6"')}
${[0,1,2,3].map(k=>`<rect x="180" y="${175+k*10}" width="6" height="6" fill="none" stroke="#555"/><path d="M190 ${178+k*10}h${22-k*3}" stroke="#777" stroke-width="2"/>`).join('')}</g><rect x="186" y="141" width="24" height="10" rx="2" fill="url(#wsChr)"/>
${shop?`<g class="badge"><circle cx="223" cy="150" r="9" fill="#d5402f" stroke="#1b160f" stroke-width="2"/>${T(223,153.5,shop,'font-size="10" text-anchor="middle" fill="#fff" font-weight="800"')}</g>`:''}</g>
<polygon points="${P([[70,330],[210,330],[207,316],[76,316]])}" fill="url(#wsWood)"/><rect x="70" y="330" width="140" height="10" fill="#6d4c28"/>
<rect x="78" y="340" width="7" height="50" fill="#2b251e"/><rect x="198" y="340" width="7" height="50" fill="#2b251e"/>
${[384,371,358].map((y,i)=>`<rect x="138" y="${y-9}" width="60" height="10" fill="#1b1b1b"/><ellipse cx="168" cy="${y+1}" rx="30" ry="6" fill="#141414"/><ellipse cx="168" cy="${y-9}" rx="30" ry="6" fill="#262626"/><ellipse cx="168" cy="${y-9}" rx="15" ry="3" fill="#0a0a0a"/><ellipse cx="168" cy="${y-9}" rx="11" ry="2.2" fill="#8a8a8a" opacity="${i?0:.6}"/>`).join('')}
<rect x="80" y="302" width="22" height="14" fill="#3b5d8a"/><rect x="77" y="298" width="28" height="5" fill="#2c4568"/><rect x="101" y="306" width="13" height="3" fill="#aaa"/>
<rect x="119" y="301" width="27" height="15" rx="2" fill="#6b3b22"/><rect x="122" y="304" width="10" height="9" rx="1" fill="#2a1a10"/>${[0,1,2].map(i=>`<path d="M123 ${306+i*2.5}h8" stroke="#8a6236" stroke-width=".8"/>`).join('')}<circle class="led" cx="140" cy="306" r="1.4" fill="#ff5a3a"/><rect x="135" y="310" width="8" height="2" fill="#c9a227"/><path d="M144 301l6-12" stroke="#999" stroke-width=".8"/>
${[0,1,2].map(i=>`<text class="note" style="animation-delay:${i*1.05}s" x="${130+i*5}" y="298" font-size="8" fill="#f0b43c" font-family="serif">${i%2?'♫':'♪'}</text>`).join('')}
<g id="ws-log" data-ws="log"><rect x="148" y="296" width="44" height="32" fill="transparent"/><g class="book"><polygon points="${P([[152,322],[186,322],[183,310],[156,310]])}" fill="#1e5a3a"/><polygon points="${P([[152,322],[186,322],[186,325],[152,325]])}" fill="#eee"/>${T(169,319,'LAGERBUCH','font-size="5.5" text-anchor="middle" fill="#f0e6c8" font-weight="700"')}</g></g>
</g>`;
 // L2: Regal und Werkzeugwagen
 const sx0=214,sx1=376,sy0=232,sy1=640,k=.2,lv=[318,420,522,624];
 const cont=(x,y,t)=>{const c={can:['#e9b52a','#b98a12'],spray:['#d24b2a','#9c3017'],jar:['#3a72c9','#24508f'],box:['#4a9a52','#2f6f37']}[t];
  if(t==='can')return`<g class="wob"><rect x="${x}" y="${y-30}" width="24" height="30" rx="3" fill="${c[0]}"/><rect x="${x+3}" y="${y-36}" width="7" height="6" fill="${c[1]}"/><rect x="${x+4}" y="${y-20}" width="16" height="8" fill="#f3eee2"/></g>`;
  if(t==='spray')return`<g class="wob"><rect x="${x}" y="${y-32}" width="13" height="32" rx="2" fill="${c[0]}"/><rect x="${x+3}" y="${y-38}" width="7" height="6" fill="#ddd"/></g>`;
  if(t==='jar')return`<g class="wob"><rect x="${x}" y="${y-20}" width="22" height="20" rx="3" fill="${c[0]}"/><rect x="${x-1}" y="${y-24}" width="24" height="5" rx="1" fill="${c[1]}"/></g>`;
  return`<g class="wob"><rect x="${x}" y="${y-24}" width="30" height="24" fill="${c[0]}"/><path d="M${x} ${y-24}l4-5h22l4 5" fill="${c[1]}"/></g>`};
 const rows=[['can','can','spray','jar'],['box','jar','spray','can'],['box','box','jar','spray'],['can','box','jar','jar']];
 s+=`<g class="L2"><ellipse cx="295" cy="650" rx="94" ry="11" fill="#000" opacity=".4"/><ellipse cx="88" cy="642" rx="88" ry="11" fill="#000" opacity=".4"/>
<g id="ws-inv" data-ws="inv"><polygon points="${P([[sx0,sy0],bk(sx0,sy0,k),bk(sx0,sy1,k),[sx0,sy1]])}" fill="#8a3a10"/>
<rect x="${bk(sx0,0,k)[0]}" y="${bk(0,sy0,k)[1]}" width="${bk(sx1,0,k)[0]-bk(sx0,0,k)[0]}" height="${bk(0,sy1,k)[1]-bk(0,sy0,k)[1]}" fill="#1d1914"/>`;
 lv.forEach((y,r)=>{s+=`<polygon points="${P([[sx0,y],[sx1,y],bk(sx1,y,k),bk(sx0,y,k)])}" fill="#4a4036"/>`;let x=sx0+14;for(const t of rows[r]){s+=cont(x,y-3,t);x+=t==='spray'?24:t==='box'?40:34}s+=`<rect x="${sx0}" y="${y}" width="${sx1-sx0}" height="9" fill="url(#wsOrg)"/>`});
 s+=`<rect x="${sx0}" y="${sy0}" width="9" height="${sy1-sy0+8}" fill="url(#wsOrg)"/><rect x="${sx1-9}" y="${sy0}" width="9" height="${sy1-sy0+8}" fill="url(#wsOrg)"/>
${Array.from({length:30},(_,i)=>`<rect x="${sx0+3}" y="${sy0+6+i*14}" width="3" height="6" fill="#0007"/><rect x="${sx1-6}" y="${sy0+6+i*14}" width="3" height="6" fill="#0007"/>`).join('')}
<rect x="${sx0+16}" y="${sy0+12}" width="116" height="22" rx="2" fill="#f0b43c" stroke="#1b160f" stroke-width="1.5"/>${T(sx0+24,sy0+27,'TEILELAGER','font-size="11" fill="#1b160f" font-weight="800" letter-spacing="1"')}${T(sx0+124,sy0+27,nI,'font-size="11" text-anchor="end" fill="#1b160f" font-weight="800"')}
${low?`<circle class="pulse" cx="${sx1-22}" cy="${sy0+23}" r="13" fill="#f0a020" opacity=".3"/><circle cx="${sx1-22}" cy="${sy0+23}" r="7" fill="#f0a020" stroke="#1b160f" stroke-width="1.5"/>${T(sx1-22,sy0+26.5,low,'font-size="9" text-anchor="middle" fill="#1b160f" font-weight="900"')}`:''}</g>`;
 const cx0=12,cx1=162,cy0=402,cy1=628,kk=.2;
 s+=`<g id="ws-tools" data-ws="tools"><polygon points="${P([[cx0,cy0],[cx1,cy0],bk(cx1,cy0,kk),bk(cx0,cy0,kk)])}" fill="#7d1e14"/>
<polygon points="${P([[cx1,cy0],bk(cx1,cy0,kk),bk(cx1,cy1,kk),[cx1,cy1]])}" fill="#6b190f"/>
<rect x="${cx0}" y="${cy0}" width="${cx1-cx0}" height="${cy1-cy0}" rx="3" fill="url(#wsRed)"/>
<rect x="30" y="352" width="100" height="40" rx="3" fill="url(#wsRed)" stroke="#6b190f" stroke-width="1.5"/><rect x="30" y="364" width="100" height="3" fill="#6b190f"/><path d="M60 352v-12h40v12" fill="none" stroke="#222" stroke-width="5" stroke-linejoin="round"/><rect x="74" y="370" width="12" height="7" fill="url(#wsChr)"/>
<rect x="${cx0+6}" y="408" width="${cx1-cx0-12}" height="34" fill="#2a0c08"/>`;
 [[412,30],[446,30],[480,30],[514,38],[556,52]].forEach(([y,h],i)=>{s+=`<g class="${i?'':'drawer1'}"><rect x="${cx0+6}" y="${y}" width="${cx1-cx0-12}" height="${h-4}" rx="2" fill="url(#wsRed)" stroke="#0004"/><rect x="${cx0+40}" y="${y+h-13}" width="${cx1-cx0-80}" height="5" rx="2.5" fill="url(#wsChr)"/>${i?'':`<rect x="${cx0+12}" y="417" width="74" height="14" fill="#f3eee2"/>${T(cx0+49,427.5,'WERKZEUG','font-size="9" text-anchor="middle" fill="#1b160f" font-weight="800" letter-spacing=".8"')}${T(cx0+120,428,nT,'font-size="10" text-anchor="middle" fill="#fff" font-weight="800"')}`}</g>`});
 s+=`${[30,140].map(x=>`<circle cx="${x}" cy="${cy1+8}" r="8" fill="#1a1a1a"/><circle cx="${x}" cy="${cy1+8}" r="3" fill="#777"/>`).join('')}
${lent?`<rect x="${cx0+12}" y="${cy0+186}" width="88" height="16" rx="2" fill="#1b160f"/>${T(cx0+56,cy0+197.5,lent+' verliehen','font-size="9" text-anchor="middle" fill="#f0b43c" font-family="monospace" font-weight="700"')}`:''}
</g></g>`;
 // FX: Licht, Staub, Vignette
 s+=`<g class="FX" pointer-events="none"><polygon points="${day||dusk?'238,176 304,176 360,600 196,600':''}" fill="url(#wsBeam)"/>
<g class="lit"><rect x="146" y="30" width="98" height="5" fill="#555"/><rect x="150" y="35" width="90" height="7" rx="3" fill="#fff6dc"/><polygon points="150,42 240,42 330,640 60,640" fill="url(#wsCone)"/><rect x="-40" y="-40" width="470" height="780" fill="url(#wsGlow)"/></g>
${Array.from({length:18},(_,i)=>{const r=(n)=>((Math.sin(i*12.9898+n*78.233)*43758.5453)%1+1)%1;return`<circle class="dust" style="--d:${7+r(1)*7}s;--dl:-${r(2)*10}s" cx="${110+r(3)*170}" cy="${90+r(4)*420}" r="${.7+r(5)*1.1}" fill="#fff6dc"/>`}).join('')}
</g><rect class="dark" x="-40" y="-40" width="470" height="780" fill="#000"/><rect x="-40" y="-40" width="470" height="780" fill="url(#wsVig)" pointer-events="none"/></svg>`;
 return s}
window.WS={
 render(v,hour=new Date().getHours()){v.innerHTML=`<div id="wsRoom" style="margin:-16px -16px 0;height:calc(100vh - 140px)"><div class="wsz">${svg(hour)}</div><div class="fade"></div><div class="hint">Tippe auf Werkzeugwagen, Regal, Zettel oder Lagerbuch</div></div>`;
  const d=new Date(),m=d.getMinutes(),h=d.getHours()%12;$('#wsHr').setAttribute('transform',`rotate(${h*30+m/2} 250 205)`);$('#wsMin').setAttribute('transform',`rotate(${m*6} 250 205)`);$('#wsRoom .sec').style.animationDelay=`-${d.getSeconds()}s`;
  $('#wsRoom').addEventListener('click',e=>{const g=e.target.closest('[data-ws]');if(g)WS.go(g.dataset.ws)})},
 tilt(x,y){const r=$('#wsRoom');if(r){r.style.setProperty('--px',x);r.style.setProperty('--py',y)}},
 box(t){const r=$('#wsRoom'),g=$('#ws-'+t),a=r.getBoundingClientRect(),b=g.getBoundingClientRect(),W=a.width,H=a.height;const s=Math.min(W/b.width,H/b.height)*.96;
  const cx=b.left-a.left+b.width/2,cy=b.top-a.top+b.height/2;return{s,tx:Math.min(0,Math.max(W-W*s,W/2-cx*s)),ty:Math.min(0,Math.max(H-H*s,H/2-cy*s))}},
 go(t){const r=$('#wsRoom');r.classList.add('p-'+t);setTimeout(()=>{const z=WS.box(t),w=r.querySelector('.wsz');
  w.animate([{transform:'none'},{transform:`translate(${z.tx}px,${z.ty}px) scale(${z.s})`}],{duration:380,easing:'cubic-bezier(.55,0,.25,1)',fill:'forwards'});
  r.querySelector('.fade').animate([{opacity:0},{opacity:0,offset:.6},{opacity:1}],{duration:380,fill:'forwards'}).onfinish=()=>{WS.last=t;const h={tools:'#/tools',inv:'#/inv',shop:'#/shop',log:'#/inv'}[t];if(location.hash===h)render();else location.hash=h;setTimeout(()=>{$('#view').classList.add('ws-arrive');setTimeout(()=>$('#view').classList.remove('ws-arrive'),300)},0)}},160)},
 back(v,hour){WS.render(v,hour);const t=WS.last;if(!t)return;const r=$('#wsRoom'),z=WS.box(t),w=r.querySelector('.wsz');r.querySelector('.dark').style.cssText='animation:none;opacity:0';r.querySelector('.lit').style.animation='none';
  w.animate([{transform:`translate(${z.tx}px,${z.ty}px) scale(${z.s})`},{transform:'none'}],{duration:340,easing:'cubic-bezier(.2,.7,.3,1)'});r.querySelector('.fade').animate([{opacity:1},{opacity:0,offset:.45},{opacity:0}],{duration:340})}
};return 1})()
