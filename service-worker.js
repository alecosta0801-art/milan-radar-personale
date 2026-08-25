const CACHE='milan-radar-v4.1.0';
const APP_SHELL=[
  './',
  './index.html',
  './manifest.webmanifest',
  './assets/app.css',
  './assets/app.js',
  './assets/icon-180.png',
  './assets/icon-192.png',
  './assets/icon-512.png',
  './config.json',
  './data/catalogo-tv.json',
  './data/calendario.json'
];

self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(APP_SHELL)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));
});

self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET')return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin)return;

  const isData=url.pathname.endsWith('/data/catalogo-tv.json')||url.pathname.endsWith('/data/calendario.json');
  if(isData){
    event.respondWith(fetch(request,{cache:'no-store'}).then(response=>{
      if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(request,copy))}
      return response;
    }).catch(()=>caches.match(request)));
    return;
  }

  if(request.mode==='navigate'){
    event.respondWith(fetch(request).then(response=>{
      if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put('./index.html',copy))}
      return response;
    }).catch(()=>caches.match('./index.html')));
    return;
  }

  event.respondWith(caches.match(request).then(cached=>{
    const update=fetch(request).then(response=>{
      if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(request,copy))}
      return response;
    }).catch(()=>cached);
    return cached||update;
  }));
});
