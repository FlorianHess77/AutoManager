// Offline-Cache für Garage & Wartungsmanager
const CACHE='garage-v43';
const OCR='garage-ocr';
const FILES=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==CACHE&&x!==OCR).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=new URL(e.request.url);
  // Texterkennung (einmal geladen, danach offline aus dem Cache)
  if(url.hostname==='cdn.jsdelivr.net'){
    e.respondWith(caches.open(OCR).then(c=>c.match(e.request).then(hit=>hit||fetch(e.request).then(r=>{if(r.ok)c.put(e.request,r.clone());return r}))));
    return;
  }
  // Netz zuerst (damit Updates ankommen), offline aus dem Cache
  e.respondWith(fetch(e.request).then(r=>{if(r.ok&&url.origin===location.origin){const c=r.clone();caches.open(CACHE).then(x=>x.put(e.request,c))}return r})
    .catch(()=>caches.match(e.request,{ignoreSearch:true}).then(r=>r||caches.match('./index.html'))));
});
