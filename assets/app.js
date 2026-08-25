(()=>{'use strict';
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const KEYS={catalog:'mr4.catalog',calendar:'mr4.calendar',remote:'mr4.remote',personal:'mr4.personal',round:'mr4.round',country:'mr4.country',focus:'mr4.focus',install:'mr4.install-dismissed'};
const state={config:{catalogUrl:'data/catalogo-tv.json',calendarUrl:'data/calendario.json'},calendar:null,catalog:null,personal:safe(localStorage.getItem(KEYS.personal),[]),coverage:'ALL',world:'ALL',expanded:new Set(),tab:'focus',focusEvent:null,server:false};
const names=typeof Intl.DisplayNames==='function'?new Intl.DisplayNames(['it'],{type:'region'}):null;
function safe(value,fallback){try{return value?JSON.parse(value):fallback}catch{return fallback}}
function esc(value){return String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]))}
function countryName(code){try{return names?.of(code)||code}catch{return code}}
function flag(code){return /^[A-Z]{2}$/.test(code)?String.fromCodePoint(...[...code].map(ch=>127397+ch.charCodeAt())):'🌍'}
function timeout(ms){const c=new AbortController();setTimeout(()=>c.abort(),ms);return c.signal}
function dateTime(value){try{return new Intl.DateTimeFormat('it-IT',{dateStyle:'short',timeStyle:'short'}).format(new Date(value))}catch{return '—'}}
function day(value){return new Intl.DateTimeFormat('it-IT',{weekday:'short',day:'numeric',month:'short'}).format(new Date(value))}
function hour(value){return new Intl.DateTimeFormat('it-IT',{hour:'2-digit',minute:'2-digit'}).format(new Date(value))}
function eventLabel(event){return `G${event.round} · ${event.home.name} – ${event.away.name} · ${day(event.date)}`}
function allAssignments(){return [...(state.catalog?.assignments||[]),...state.personal]}
function eventAssignments(event,code='ALL'){return allAssignments().filter(x=>String(x.eventId)===String(event.id)&&(code==='ALL'||(x.territories||[]).includes(code)))}
function relevantOpportunities(code){return code==='ALL'?[]:(state.catalog?.opportunities||[]).filter(x=>(x.territories||[]).includes(code))}
function relevantReviews(code){return [...(state.catalog?.reviews||[]),...(state.catalog?.automaticReviewQueue||[])].filter(x=>(x.territories||[]).includes(code))}
function setConnection(ok,text){$('#connection').classList.toggle('offline',!ok);$('#connection span').textContent=text}
function notice(text=''){const box=$('#app-notice');box.textContent=text;box.classList.toggle('hidden',!text)}
function idleRefreshLabel(){return state.server?'<span>↻</span> Aggiorna e verifica':'<span>↻</span> Sincronizza dati'}
function updateInstallHint(){const ua=navigator.userAgent,ios=/iPad|iPhone|iPod/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1),safari=/Safari/i.test(ua)&&!/CriOS|FxiOS|EdgiOS|OPiOS/i.test(ua),standalone=matchMedia('(display-mode: standalone)').matches||navigator.standalone===true,eligible=ios&&safari&&!standalone&&location.protocol==='https:'&&!localStorage.getItem(KEYS.install);$('#ios-install')?.classList.toggle('hidden',!eligible)}
async function registerPWA(){if(!('serviceWorker'in navigator)||location.protocol!=='https:')return;try{await navigator.serviceWorker.register('./service-worker.js',{scope:'./'})}catch(error){console.warn('Service worker non registrato',error)}}
async function fetchJSON(url){const response=await fetch(url,{cache:'no-store',signal:timeout(25000),headers:{Accept:'application/json'}});if(!response.ok)throw Error(`HTTP ${response.status}`);return response.json()}
function validateData(calendar,catalog){if(!calendar||!Array.isArray(calendar.events)||calendar.events.length<300)throw Error('Calendario incompleto');if(!catalog||catalog.schemaVersion!==3||!Array.isArray(catalog.assignments)||catalog.coverage?.territoriesCompared!==249)throw Error('Catalogo TV non valido');if(!catalog.milanRadar||catalog.milanRadar.broadcasters?.length!==6||catalog.milanRadar.fixtures?.length!==38)throw Error('Milan Radar incompleto');}
function deriveCalendarUrl(catalogUrl){try{const u=new URL(catalogUrl,location.href);u.pathname=u.pathname.replace(/catalogo-tv\.json$/,'calendario.json');return u.href}catch{return state.config.calendarUrl}}
async function detectServer(){if(location.protocol==='https:')return false;try{const health=await fetchJSON('/api/health');return health?.python===true}catch{return false}}
async function readConfig(){try{state.config={...state.config,...await fetchJSON('config.json')}}catch{}state.server=await detectServer()}
async function loadData({refresh=false}={}){
  const button=$('#refresh-button');button.disabled=true;button.classList.add('loading');button.innerHTML=state.server?'<span>↻</span> Controllo fonti…':'<span>↻</span> Sincronizzazione…';notice('');
  let report=null;
  try{
    if(refresh&&state.server){
      const response=await fetch('/api/refresh',{method:'POST',cache:'no-store',signal:timeout(150000)});
      report=await response.json();if(!response.ok||!report.ok)throw Error(report.error||'Controllo Python non riuscito');
    }
    const custom=localStorage.getItem(KEYS.remote)?.trim();
    const catalogUrl=custom||state.config.catalogUrl;
    const calendarUrl=custom?deriveCalendarUrl(custom):state.config.calendarUrl;
    let catalog,calendar;
    try{[catalog,calendar]=await Promise.all([fetchJSON(catalogUrl),fetchJSON(calendarUrl)]);validateData(calendar,catalog)}catch(primaryError){
      if(custom){[catalog,calendar]=await Promise.all([fetchJSON(state.config.catalogUrl),fetchJSON(state.config.calendarUrl)]);validateData(calendar,catalog);notice(`Catalogo remoto non raggiungibile (${primaryError.message}). Uso la copia locale valida.`)}else throw primaryError;
    }
    state.catalog=catalog;state.calendar=calendar;
    localStorage.setItem(KEYS.catalog,JSON.stringify(catalog));localStorage.setItem(KEYS.calendar,JSON.stringify(calendar));
    setConnection(true,state.server?'Python attivo':'Online · dati sincronizzati');
    if(refresh&&!noticeText())notice(report?`Controlli Python completati. Catalogo rigenerato ${dateTime(catalog.generatedAt)}.`:`Sincronizzazione completata. Il catalogo disponibile è stato generato ${dateTime(catalog.generatedAt)}; GitHub esegue i controlli automatici ogni sei ore.`);
  }catch(error){
    const catalog=safe(localStorage.getItem(KEYS.catalog),null),calendar=safe(localStorage.getItem(KEYS.calendar),null);
    try{validateData(calendar,catalog);state.catalog=catalog;state.calendar=calendar;setConnection(false,'Cache locale');notice(`Rete non disponibile: uso l’ultima copia valida. ${error.message}`)}catch{setConnection(false,'Errore dati');notice(`Impossibile caricare i dati: ${error.message}`)}
  }finally{
    button.disabled=false;button.classList.remove('loading');button.innerHTML=idleRefreshLabel();
    if(state.calendar&&state.catalog){fillFilters();renderAll()}
  }
}
function noticeText(){return $('#app-notice').classList.contains('hidden')?'':$('#app-notice').textContent}
function currentRound(){return $('#round-filter')?.value||'ALL'}
function currentCountry(){return $('#country-filter')?.value||'ALL'}
function scopeEvents(){const round=currentRound();return (state.calendar?.events||[]).filter(e=>round==='ALL'||String(e.round)===round)}
function chooseDefaultRound(){
  const saved=localStorage.getItem(KEYS.round);if(saved==='ALL'||(+saved>=1&&+saved<=38))return saved;
  const now=Date.now(),events=state.calendar?.events||[];
  const next=events.find(e=>e.status==='LIVE'||(e.status!=='FINISHED'&&new Date(e.date).getTime()>now-4*3600000));return String(next?.round||1)
}
function chooseFocusEvent(){
  const fixtures=state.catalog?.milanRadar?.fixtures||[],saved=localStorage.getItem(KEYS.focus);if(saved&&fixtures.some(x=>String(x.eventId)===saved))return saved;
  const now=Date.now();const next=fixtures.find(x=>x.status==='LIVE'||(x.status!=='FINISHED'&&new Date(x.date).getTime()>now-4*3600000));return String(next?.eventId||fixtures[0]?.eventId||'')
}
function fillFocusEvents(){
  const select=$('#focus-event'),fixtures=state.catalog?.milanRadar?.fixtures||[];if(!select)return;
  const value=select.dataset.ready?select.value:(state.focusEvent||chooseFocusEvent());select.innerHTML=fixtures.map(x=>`<option value="${esc(x.eventId)}">G${x.round} · ${esc(x.home)} – ${esc(x.away)} · ${day(x.date)}</option>`).join('');select.value=fixtures.some(x=>String(x.eventId)===String(value))?String(value):String(fixtures[0]?.eventId||'');select.dataset.ready='1';state.focusEvent=select.value;
}
function fillFilters(){
  const round=$('#round-filter'),country=$('#country-filter');const roundValue=round.dataset.ready?round.value:chooseDefaultRound();
  round.innerHTML='<option value="ALL">Intera stagione</option>'+Array.from({length:38},(_,i)=>`<option value="${i+1}">Giornata ${i+1}</option>`).join('');round.value=roundValue;round.dataset.ready='1';
  const codes=(state.catalog.countryIndex||[]).map(x=>x.code);const countryValue=country.dataset.ready?country.value:(localStorage.getItem(KEYS.country)||'ALL');
  country.innerHTML='<option value="ALL">Tutto il mondo</option>'+codes.map(code=>`<option value="${code}">${flag(code)} ${esc(countryName(code))}</option>`).join('');country.value=codes.includes(countryValue)?countryValue:'ALL';country.dataset.ready='1';
  fillFocusEvents();fillPersonalEvents();
}
function score(event){if(event.status==='FINISHED'||event.status==='LIVE')return `${event.homeScore??'–'} · ${event.awayScore??'–'}`;return hour(event.date)}
function statusSub(event){if(event.status==='LIVE')return 'In diretta';if(event.status==='FINISHED')return 'Finale';if(event.status==='POSTPONED')return 'Rinviata';return 'Ora italiana'}
function crest(team){return `<span class="crest" style="--team:${esc(team.color)};--alt:${esc(team.alternateColor)}"><b>${esc((team.short||team.name).slice(0,1))}</b></span>`}
function accessText(item){const a=item.access||{};return typeof a==='string'?a:[a.platform,a.registration,a.tvLicense].filter(Boolean).join(' · ')}
function confidence(item){const v=item.verification?.confidence||'PERSONAL';return v==='HIGH'?'Alta':v==='MEDIUM'?'Media':v==='PERSONAL'?'Personale':v}
function assignmentHTML(item){
  const territories=(item.territories||[]).map(c=>`${flag(c)} ${esc(countryName(c))}`).join(', '),personal=item.sourceId==='personal';
  return `<article class="assignment"><span class="channel-mark">${esc((item.broadcaster||'TV').replace(/[^a-z0-9]/gi,'').slice(0,2).toUpperCase())}</span><div><strong>${esc(item.broadcaster)}</strong><div class="meta-row"><span>${territories}</span><span class="mini free">Gratis</span><span class="mini ${personal?'personal':''}">${personal?'Archivio personale':'Attendibilità '+esc(confidence(item))}</span><span class="mini">${esc(item.freshness||'CURRENT')}</span></div><small>${esc(item.note||item.verification?.evidence||'Conferma puntuale.') }<br><b>Accesso:</b> ${esc(accessText(item))} · <b>Restrizione:</b> ${esc(item.restriction)} · <b>Verifica:</b> ${esc(dateTime(item.verification?.checkedAt))}</small></div><div class="link-row"><a href="${esc(item.sourceUrl)}" target="_blank" rel="noopener noreferrer">Fonte ↗</a>${item.rightsUrl&&item.rightsUrl!==item.sourceUrl?`<a href="${esc(item.rightsUrl)}" target="_blank" rel="noopener noreferrer">Diritti ↗</a>`:''}<a href="${esc(item.watchUrl)}" target="_blank" rel="noopener noreferrer">Sito ↗</a></div></article>`
}
function pendingHTML(item){return `<div class="pending-row"><div><b>${(item.territories||[]).map(flag).join(' ')} ${esc(item.broadcaster)} · selezione non attribuita</b><span>${esc(item.amount)}. ${esc(item.note)}</span></div><a href="${esc(item.sourceUrl)}" target="_blank" rel="noopener noreferrer">Fonte ↗</a></div>`}
function matchHTML(event){
  const code=currentCountry(),exact=eventAssignments(event,code),pending=relevantOpportunities(code),open=state.expanded.has(event.id),confirmed=exact.length>0;
  const status=confirmed?`<span class="status-pill yes">${exact.length} confermat${exact.length===1?'a':'e'}</span>`:pending.length?'<span class="status-pill wait">Selezione in attesa</span>':'<span class="status-pill">Nessuna conferma</span>';
  return `<article class="match-card ${confirmed?'confirmed':''} ${event.status==='LIVE'?'live':''} ${open?'open':''}" data-event="${esc(event.id)}"><div class="match-top"><span>${day(event.date)} · Giornata ${event.round}</span><b class="${event.status==='LIVE'?'live-text':''}">${event.status==='LIVE'?'● LIVE':esc(event.statusText||'Serie A')}</b></div><div class="match-main"><div class="team home"><span>${esc(event.home.name)}</span>${crest(event.home)}</div><div class="score"><strong>${score(event)}</strong><span>${statusSub(event)}</span></div><div class="team">${crest(event.away)}<span>${esc(event.away.name)}</span></div></div><button class="match-toggle" data-toggle="${esc(event.id)}"><span class="toggle-state">${status}${pending.length&&!confirmed?`<span>${pending.length} programma${pending.length===1?'':'i'} selettivo${pending.length===1?'':'i'}</span>`:''}</span><span class="chevron">⌄</span></button><div class="match-details"><div class="detail-heading"><h3>Dirette gratuite per questa gara</h3><span>ID ${esc(event.id)}</span></div>${exact.length?`<div class="assignment-list">${exact.map(assignmentHTML).join('')}</div>`:'<div class="empty-confirmation"><b>Nessuna diretta gratuita confermata per questa partita nel territorio selezionato.</b><br>Il risultato descrive le fonti monitorate, non dimostra l’assenza assoluta di altre trasmissioni.</div>'}${pending.length?`<div class="pending-block"><h4>Programmi selettivi da verificare</h4>${pending.map(pendingHTML).join('')}</div>`:''}<div class="territory-note"><b>Vincolo territoriale.</b> I link non modificano la tua posizione. L’accesso è consentito soltanto dove diritti e condizioni lo prevedono.</div></div></article>`
}
function filteredEvents(){const team=$('#team-filter').value.trim().toLocaleLowerCase('it'),code=currentCountry();return scopeEvents().filter(event=>{const exact=eventAssignments(event,code).length>0;if(state.coverage==='CONFIRMED'&&!exact)return false;if(state.coverage==='NONE'&&exact)return false;return !team||`${event.home.name} ${event.away.name}`.toLocaleLowerCase('it').includes(team)})}
function renderMatches(){
  const list=filteredEvents(),round=currentRound(),code=currentCountry();$('#matches-title').textContent=round==='ALL'?'Intera stagione':`Giornata ${round}`;
  $('#matches-summary').textContent=`${list.length} partite mostrate · ${code==='ALL'?'tutti i territori':countryName(code)}`;
  $('#match-list').innerHTML=list.length?list.map(matchHTML).join(''):'<div class="empty-state"><div><strong>Nessuna partita corrispondente</strong><p>Modifica squadra, Paese, giornata o filtro copertura.</p></div></div>';
}
function countryStatus(code){const events=scopeEvents(),ids=new Set(events.map(e=>String(e.id))),exact=allAssignments().filter(x=>(x.territories||[]).includes(code)&&ids.has(String(x.eventId))).length;if(exact)return{state:'EXACT',note:`${exact} conferm${exact===1?'a':'e'} puntuale${exact===1?'':'i'} nel periodo.`};const pending=relevantOpportunities(code);if(pending.length)return{state:'PENDING',note:pending.map(x=>`${x.broadcaster}: ${x.amount}`).join(' · ')};const review=relevantReviews(code);if(review.length)return{state:'REVIEW',note:review.map(x=>x.broadcaster).filter(Boolean).join(' · ')+' — prova puntuale insufficiente.'};return{state:'NONE',note:'Nessuna opzione provata nelle fonti monitorate.'}}
function renderWorld(){
  const q=$('#world-search').value.trim().toLocaleLowerCase('it'),labels={EXACT:'Conferma puntuale',PENDING:'Selezione in attesa',REVIEW:'Da verificare',NONE:'Nessuna conferma'},counts={EXACT:0,PENDING:0,REVIEW:0,NONE:0};
  let rows=(state.catalog?.countryIndex||[]).map(({code})=>({code,name:countryName(code),...countryStatus(code)}));rows.forEach(x=>counts[x.state]++);
  $('#world-exact').textContent=counts.EXACT;$('#world-pending').textContent=counts.PENDING;$('#world-review').textContent=counts.REVIEW;$('#world-none').textContent=counts.NONE;$('#world-all').textContent=rows.length;$('#world-scope').textContent=currentRound()==='ALL'?'Ambito: intera stagione':`Ambito: giornata ${currentRound()}`;
  rows=rows.filter(x=>(state.world==='ALL'||x.state===state.world)&&(!q||`${x.name} ${x.code}`.toLocaleLowerCase('it').includes(q))).sort((a,b)=>a.name.localeCompare(b.name,'it'));
  $('#country-grid').innerHTML=rows.map(x=>`<article class="country-row"><div class="country-name"><span class="flag">${flag(x.code)}</span>${esc(x.name)} <small>${x.code}</small></div><span class="audit-pill ${x.state.toLowerCase()}">${labels[x.state]}</span><div class="country-note">${esc(x.note)}</div></article>`).join('')||'<div class="empty-state"><div><strong>Nessun Paese trovato</strong></div></div>';
}
function renderSources(){
  const sources=state.catalog?.sources||[],counts={ok:0,limited:0,error:0,changed:0};sources.forEach(x=>{if(['OK','CHANGED'].includes(x.status))counts.ok++;if(['LIMITED','BLOCKED'].includes(x.status))counts.limited++;if(x.status==='ERROR')counts.error++;if(x.contentChanged)counts.changed++});
  $('#source-summary').innerHTML=`<div><strong>${sources.length}</strong><span>Registrate</span></div><div><strong>${counts.ok}</strong><span>Raggiungibili</span></div><div><strong>${counts.limited+counts.error}</strong><span>Limitate o in errore</span></div><div><strong>${counts.changed}</strong><span>Modificate</span></div>`;
  $('#source-list').innerHTML=sources.length?sources.map(x=>`<article class="source-card ${x.priorityMilan?'priority':''}"><i class="source-dot ${esc(String(x.status).toLowerCase())}"></i><div><h3>${esc(x.name)}</h3><span class="source-meta">${(x.territories||[]).map(c=>flag(c)+' '+c).join(' · ')} · ${x.official?'Fonte ufficiale':'Fonte secondaria'}</span></div><div class="source-note">${esc(x.note||x.error||'Fonte registrata.')}${x.error?` · Errore: ${esc(x.error)}`:''}</div><div class="source-side"><b>${esc(x.status||'NON CONTROLLATA')}</b><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">Apri fonte ↗</a></div></article>`).join(''):'<div class="empty-state"><div><strong>Controllo fonti non disponibile</strong><p>Sincronizza il catalogo oppure avvia un controllo da GitHub Actions.</p></div></div>';
  $('#review-count').textContent=(state.catalog?.automaticReviewQueue||[]).length+(state.catalog?.reviews||[]).length;
}
function radarStateClass(value){if(value==='CONFIRMED_FREE')return'confirmed-free';if(value==='CONFIRMED_NOT_FREE')return'confirmed-not-free';if(value==='PROBABLE_NOT_FREE')return'probable';if(value==='POSSIBLE_NOT_CONFIRMED')return'possible';if(['HIGHLIGHTS_ONLY','TEXT_SCORE_ONLY'].includes(value))return'media';return'none'}
function radarRow(profile,eventId){const radar=state.catalog.milanRadar,observation=(radar.observations||[]).find(x=>String(x.eventId)===String(eventId)&&x.broadcasterId===profile.id),candidates=(state.catalog.automaticReviewQueue||[]).filter(x=>String(x.eventId)===String(eventId)&&(profile.sourceIds||[]).includes(x.sourceId));return{profile,observation,candidates,state:observation?.state||(candidates.length?'POSSIBLE_NOT_CONFIRMED':profile.baselineState),label:observation?.label||(candidates.length?'Nuovo segnale da verificare':profile.baselineLabel)}}
function sourceHealth(profile){const rows=(state.catalog.sources||[]).filter(x=>(profile.sourceIds||[]).includes(x.id)),ok=rows.filter(x=>['OK','CHANGED'].includes(x.status)).length;return rows.length?`${ok}/${rows.length} fonti raggiungibili`:'Controllo tecnico non eseguito'}
function broadcasterHTML(row){
  const p=row.profile,o=row.observation,candidates=row.candidates||[],cls=radarStateClass(row.state),territory=`${flag(p.territory)} ${countryName(p.territory)}`;
  const exact=o?`${o.channel||'Canale da verificare'} · ${o.localDateTime||'data del calendario'}`:candidates.length?`${candidates.length} rilevazione automatica non ancora approvata.`:'Nessuna assegnazione ufficiale puntuale conservata per questa gara.';
  const evidence=o?.evidence||(candidates.length?`${candidates[0].reason} Segnali: ${(candidates[0].mediaSignals||[]).join(', ')||'nessun tipo di contenuto determinato'}.`:`${p.fullMatchRights} ${p.warning}`);
  return `<article class="broadcaster-card state-${cls}"><div class="broadcaster-head"><span class="broadcaster-logo">${esc(p.name.replace(/[^a-z0-9]/gi,'').slice(0,3).toUpperCase())}</span><div><h3>${esc(p.name)}</h3><small>${territory} · ${esc(p.language)}</small></div><span class="verdict">${esc(row.label)}</span></div><div class="broadcaster-body"><div class="fact-row"><b>Partita</b><span>${esc(exact)}</span></div><div class="fact-row"><b>Diretta integrale</b><span>${esc(p.fullMatchRights)}</span></div><div class="fact-row"><b>Gratis?</b><span>${esc(p.freeStatus)}</span></div><div class="fact-row"><b>Accesso</b><span>${esc(p.access)}</span></div><div class="fact-row"><b>Registrazione</b><span>${esc(p.registration)}</span></div><div class="fact-row"><b>Controlli</b><span>${esc(sourceHealth(p))}</span></div><div class="evidence-box"><b>${o?'Prova relativa a questa partita':candidates.length?'Segnale automatico, non conferma':'Perché non è confermata'}</b>${esc(evidence)}${o?.checkedAt?`<br>Controllata: ${esc(dateTime(o.checkedAt))}`:''}</div></div><div class="broadcaster-links"><a href="${esc(o?.sourceUrl||candidates[0]?.sourceUrl||p.watchUrl)}" target="_blank" rel="noopener noreferrer">${o?'Fonte puntuale':candidates.length?'Fonte del segnale':'Fonte / piattaforma'} ↗</a>${o?.secondaryUrl?`<a href="${esc(o.secondaryUrl)}" target="_blank" rel="noopener noreferrer">Seconda prova ↗</a>`:''}${o&&o.sourceUrl!==p.watchUrl?`<a href="${esc(p.watchUrl)}" target="_blank" rel="noopener noreferrer">Piattaforma ↗</a>`:''}</div></article>`
}
function renderFocus(){
  const radar=state.catalog?.milanRadar;if(!radar)return;const eventId=$('#focus-event')?.value||state.focusEvent||chooseFocusEvent(),event=(state.calendar.events||[]).find(x=>String(x.id)===String(eventId)),fixture=(radar.fixtures||[]).find(x=>String(x.eventId)===String(eventId));if(!event||!fixture)return;
  state.focusEvent=String(eventId);const rows=(radar.broadcasters||[]).map(p=>radarRow(p,eventId)),free=rows.filter(x=>x.state==='CONFIRMED_FREE').length,confirmed=rows.filter(x=>['CONFIRMED_FREE','CONFIRMED_NOT_FREE'].includes(x.state)).length,possible=rows.filter(x=>['PROBABLE_NOT_FREE','POSSIBLE_NOT_CONFIRMED'].includes(x.state)).length,other=rows.length-confirmed-possible;
  $('#focus-summary').innerHTML=`<div class="focus-match"><span class="eyebrow">GIORNATA ${fixture.round} · ${esc(event.statusText||'SERIE A')}</span><h3>${esc(fixture.home)} – ${esc(fixture.away)}</h3><p>${esc(day(fixture.date))} · ${hour(fixture.date)} ora italiana · ID ${esc(eventId)}</p></div><div class="focus-stat"><strong>${free}</strong><span>dirette gratis confermate</span></div><div class="focus-stat"><strong>${confirmed}</strong><span>live esatti, anche non gratis</span></div><div class="focus-stat"><strong>${possible} / ${other}</strong><span>possibili / non provate</span></div>`;
  $('#broadcaster-grid').innerHTML=rows.map(broadcasterHTML).join('');
  const obsByEvent=new Map();for(const o of radar.observations||[]){const values=obsByEvent.get(String(o.eventId))||[];values.push(o);obsByEvent.set(String(o.eventId),values)}
  $('#milan-fixtures').innerHTML=(radar.fixtures||[]).map(x=>{const obs=obsByEvent.get(String(x.eventId))||[],freeCount=obs.filter(o=>o.countsAsFreeFullMatch).length,exactCount=obs.filter(o=>['CONFIRMED_FREE','CONFIRMED_NOT_FREE'].includes(o.state)).length,candidateCount=(state.catalog.automaticReviewQueue||[]).filter(c=>String(c.eventId)===String(x.eventId)).length,label=freeCount?`${freeCount} gratis confermata`:exactCount?`${exactCount} live non gratis`:obs.length?`${obs.length} verifiche puntuali`:candidateCount?`${candidateCount} segnali da revisionare`:'In attesa di annunci';return`<button class="milan-fixture ${String(x.eventId)===String(eventId)?'active':''} ${obs.length||candidateCount?'has-proof':''}" data-focus-event="${esc(x.eventId)}"><strong>G${x.round} · ${esc(x.home)} – ${esc(x.away)}</strong><span>${day(x.date)} · ${hour(x.date)}</span><span class="fixture-state">${esc(label)}</span></button>`}).join('')
}
function renderMetrics(){
  const radar=state.catalog.milanRadar,c=state.catalog.coverage,free=(radar.observations||[]).filter(x=>x.countsAsFreeFullMatch).length;
  $('#metric-matches').textContent=radar.fixtures.length;$('#metric-countries').textContent=c.territoriesCompared;$('#metric-confirmed').textContent=free;$('#metric-sources').textContent=c.sourcesRegistered;
  $('#catalog-state').textContent=state.server?'Python collegato':'Aggiornamento online';$('#catalog-detail').textContent=`Ultimo controllo TV: ${dateTime(state.catalog.generatedAt)} · Calendario: ${dateTime(state.calendar.updatedAt)}`;$('#footer-update').textContent=`Catalogo generato ${dateTime(state.catalog.generatedAt)}`;$('#personal-count').textContent=state.personal.length;
}
function renderAll(){renderFocus();renderMetrics();renderMatches();renderWorld();renderSources()}
function showTab(name){state.tab=name;$$('.nav-button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));$$('.tab-panel').forEach(p=>p.classList.toggle('active',p.id===`tab-${name}`));if(name==='focus')renderFocus();if(name==='world')renderWorld();if(name==='sources')renderSources();scrollTo({top:0,behavior:'smooth'})}
function openModal(id){$(id).classList.remove('hidden')}
function closeModal(element){element.closest('.modal-back')?.classList.add('hidden')}
function fillPersonalEvents(){const select=$('#personal-event');if(!state.calendar)return;select.innerHTML=state.calendar.events.map(e=>`<option value="${esc(e.id)}">${esc(eventLabel(e))}</option>`).join('')}
function savePersonal(){localStorage.setItem(KEYS.personal,JSON.stringify(state.personal));renderAll()}
function personalFromForm(form){const f=new FormData(form),code=String(f.get('code')).trim().toUpperCase(),codes=(state.catalog.countryIndex||[]).map(x=>x.code);if(!codes.includes(code))throw Error('Codice Paese ISO non valido');const id=`personal-${Date.now()}`;return{id,eventId:String(f.get('eventId')),territories:[code],broadcaster:String(f.get('broadcaster')),watchUrl:String(f.get('watchUrl')),sourceUrl:String(f.get('sourceUrl')),sourceId:'personal',access:{cost:'FREE',platform:String(f.get('access'))},restriction:String(f.get('restriction')),verification:{status:'CONFIRMED',method:'PERSONAL_EDITORIAL',checkedAt:String(f.get('checkedAt'))+'T12:00:00Z',confidence:'PERSONAL',evidence:'Verifica inserita nell’archivio locale.'},freshness:'PERSONAL',note:'Conferma puntuale dell’archivio personale; non pubblicata nel catalogo remoto.'}}
function download(name,value){const blob=new Blob([JSON.stringify(value,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
$('#match-list').addEventListener('click',event=>{const button=event.target.closest('[data-toggle]');if(!button)return;const id=button.dataset.toggle;state.expanded.has(id)?state.expanded.delete(id):state.expanded.add(id);renderMatches()});
$('#focus-event').addEventListener('change',()=>{state.focusEvent=$('#focus-event').value;localStorage.setItem(KEYS.focus,state.focusEvent);renderFocus()});
$('#milan-fixtures').addEventListener('click',event=>{const button=event.target.closest('[data-focus-event]');if(!button)return;state.focusEvent=button.dataset.focusEvent;$('#focus-event').value=state.focusEvent;localStorage.setItem(KEYS.focus,state.focusEvent);renderFocus();$('#focus-summary').scrollIntoView({behavior:'smooth',block:'center'})});
$$('[data-tab]').forEach(button=>button.addEventListener('click',()=>showTab(button.dataset.tab)));$$('[data-go]').forEach(button=>button.addEventListener('click',()=>showTab(button.dataset.go)));
$('#round-filter').addEventListener('change',()=>{localStorage.setItem(KEYS.round,currentRound());renderAll()});$('#country-filter').addEventListener('change',()=>{localStorage.setItem(KEYS.country,currentCountry());renderAll()});$('#team-filter').addEventListener('input',renderMatches);
$$('[data-coverage]').forEach(button=>button.addEventListener('click',()=>{state.coverage=button.dataset.coverage;$$('[data-coverage]').forEach(x=>x.classList.toggle('active',x===button));renderMatches()}));
$$('[data-world]').forEach(button=>button.addEventListener('click',()=>{state.world=button.dataset.world;$$('[data-world]').forEach(x=>x.classList.toggle('active',x===button));renderWorld()}));$('#world-search').addEventListener('input',renderWorld);
$('#refresh-button').addEventListener('click',()=>loadData({refresh:true}));$('#settings-button').addEventListener('click',()=>{$('#remote-url').value=localStorage.getItem(KEYS.remote)||'';openModal('#settings-modal')});
$$('[data-close]').forEach(button=>button.addEventListener('click',()=>closeModal(button)));$$('.modal-back').forEach(back=>back.addEventListener('mousedown',event=>{if(event.target===back)back.classList.add('hidden')}));
$('#save-settings').addEventListener('click',()=>{const value=$('#remote-url').value.trim();if(value&&!/^https?:\/\//i.test(value)){alert('Inserisci un URL http/https completo oppure lascia vuoto.');return}value?localStorage.setItem(KEYS.remote,value):localStorage.removeItem(KEYS.remote);alert(`Impostazione salvata. Premi ${state.server?'Aggiorna e verifica':'Sincronizza dati'}.`);$('#settings-modal').classList.add('hidden')});
$('#test-remote').addEventListener('click',async()=>{const value=$('#remote-url').value.trim();if(!value){alert('Il campo è vuoto: verrà usato il catalogo incluso.');return}try{const data=await fetchJSON(value);if(data.schemaVersion!==3||data.coverage?.territoriesCompared!==249||data.milanRadar?.fixtures?.length!==38||data.milanRadar?.broadcasters?.length!==6)throw Error('formato inatteso');alert(`Catalogo Milan Radar valido: ${data.milanRadar.observations.length} verifiche puntuali.`)}catch(error){alert('URL non utilizzabile: '+error.message)}});
$('#add-personal').addEventListener('click',()=>{$('#settings-modal').classList.add('hidden');$('#personal-form').reset();$('#personal-form').elements.checkedAt.value=new Date().toISOString().slice(0,10);openModal('#personal-modal')});
$('#personal-form').addEventListener('submit',event=>{event.preventDefault();try{state.personal.push(personalFromForm(event.currentTarget));savePersonal();$('#personal-modal').classList.add('hidden');alert('Conferma personale salvata soltanto per la partita scelta.')}catch(error){alert(error.message)}});
$('#export-personal').addEventListener('click',()=>download('MilanRadar-archivio-personale.json',{schemaVersion:1,exportedAt:new Date().toISOString(),assignments:state.personal}));
$('#import-personal').addEventListener('change',async event=>{try{const data=JSON.parse(await event.target.files[0].text()),items=Array.isArray(data)?data:data.assignments;if(!Array.isArray(items))throw Error('Formato non valido');const valid=items.filter(x=>x&&x.eventId&&x.broadcaster&&x.watchUrl&&x.sourceUrl&&Array.isArray(x.territories)).map(x=>({...x,sourceId:'personal'}));const map=new Map([...state.personal,...valid].map(x=>[x.id||`${x.eventId}|${x.broadcaster}|${x.territories[0]}`,x]));state.personal=[...map.values()];savePersonal();alert(`${valid.length} elementi importati.`)}catch(error){alert('Importazione non riuscita: '+error.message)}finally{event.target.value=''}});
$('#dismiss-install').addEventListener('click',()=>{localStorage.setItem(KEYS.install,'1');$('#ios-install').classList.add('hidden')});
$('#clear-local').addEventListener('click',()=>{if(confirm('Cancellare cache, impostazioni e archivio personale?')){Object.values(KEYS).forEach(key=>localStorage.removeItem(key));location.reload()}});
(async()=>{registerPWA();updateInstallHint();await readConfig();$('#refresh-button').innerHTML=idleRefreshLabel();await loadData()})();
})();
