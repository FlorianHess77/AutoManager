// Offline-Cache für Garage & Wartungsmanager
// Bei jedem Release CACHE hochzählen – und APP_VER in index.html auf denselben Wert setzen.
const CACHE='garage-v47';
const OCR='garage-ocr';
const FILES=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES.map(f=>new Request(f,{cache:'reload'})))).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==CACHE&&x!==OCR).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
// Die Seite fragt nach der Version, um „Neue Version – neu laden“ anzuzeigen
self.addEventListener('message',e=>{if(e.data==='version'&&e.source)e.source.postMessage({version:CACHE})});
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=new URL(e.request.url);
  // Texterkennung (einmal geladen, danach offline aus dem Cache)
  if(url.hostname==='cdn.jsdelivr.net'){
    e.respondWith(caches.open(OCR).then(c=>c.match(e.request).then(hit=>hit||fetch(e.request).then(r=>{if(r.ok)c.put(e.request,r.clone());return r}))));
    return;
  }
  if(url.origin!==location.origin)return;
  // Netz zuerst, am Server nachfragen statt den Browser-Cache zu nehmen (damit Updates sofort ankommen);
  // offline aus dem Cache
  const net=e.request.mode==='navigate'?fetch(url.href,{cache:'no-cache',credentials:'same-origin'}):fetch(e.request,{cache:'no-cache'});
  e.respondWith(net.then(r=>{if(r.ok){const c=r.clone();caches.open(CACHE).then(x=>x.put(e.request,c))}return r})
    .catch(()=>caches.match(e.request,{ignoreSearch:true}).then(r=>r||caches.match('./index.html'))));
});
