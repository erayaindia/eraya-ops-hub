// Support Tickets JavaScript
// Handles all functionality for the support tickets page

import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";

// ====== CONFIGURATION ======
// These values are now passed from the server for security
const SUPABASE_URL = window.SUPABASE_URL; // From server config
const SUPABASE_ANON_KEY = window.SUPABASE_KEY; // From server config
const TABLE_NAME = "support_tickets"; // exact table name
// ========================

// Check if Supabase credentials are available
if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error('Supabase credentials not available');
  // supabase will be undefined, which is handled by our error checking
}

const supabase = SUPABASE_URL && SUPABASE_ANON_KEY ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY) : null;

// Display columns: label -> key mapping
const DISPLAY_COLS = [
  { key: 'ticket_id',    label: 'Ticket' },
  { key: 'full_name',    label: 'Name' },
  { key: 'email',        label: 'Email' },
  { key: 'phone',        label: 'Phone' },
  { key: 'contact_channel', label: 'Channel' },
  { key: 'order_id',     label: 'Order ID' },
  { key: 'issue_type',   label: 'Issue' },
  { key: 'summary',      label: 'Summary' },
  { key: 'status',       label: 'Status' },
  { key: 'priority',     label: 'Priority' },
  { key: 'created_at',   label: 'Created' },
  { key: 'updated_at',   label: 'Updated' },
];

const SEARCH_COLS = ['ticket_id','full_name','email','phone','order_id','summary','description'];

// State
let page = 1;
let pageSize = 25;
let sortBy = 'created_at';
let sortAsc = false;
let lastCount = 0;
let cache = []; // last fetched rows
let visible = new Set(DISPLAY_COLS.map(c=>c.key));
let chips = {}; // active quick filters

// Refs
const $ = (id) => document.getElementById(id);

// Check if all required elements exist
const requiredElements = ['body', 'headRow', 'search', 'status', 'issue_type', 'priority', 'pageSize', 'prev', 'next', 'pageInfo', 'count', 'meta', 'metaBar', 'refresh', 'errorBox', 'columnBtn', 'columnMenu', 'themeToggle'];
const missingElements = requiredElements.filter(id => !document.getElementById(id));
if (missingElements.length > 0) {
  console.error('Missing required elements:', missingElements);
}

const $tbody=$("body"), $headRow=$("headRow"), $search=$("search"), $status=$("status"), $issue=$("issue_type"), $prio=$("priority"), $pageSizeSel=$("pageSize"), $prev=$("prev"), $next=$("next"), $pageInfo=$("pageInfo"), $count=$("count"), $meta=$("meta"), $metaBar=$("metaBar"), $refresh=$("refresh"), $err=$("errorBox"), $columnBtn=$("columnBtn"), $columnMenu=$("columnMenu"), $themeToggle=$("themeToggle");

// Sheet refs
const $sheetRoot=$("sheetRoot"), $sheet=$("sheet"), $sheetOverlay=$("sheetOverlay"), $close=$("closeSheet"), $copyId=$("copyId"), $mailto=$("mailto"), $tel=$("tel");

// Utilities
const fmtDate = (v)=> v ? new Date(v).toLocaleString() : '';
const esc = (s)=>{ const d=document.createElement('div'); d.innerText=String(s??''); return d.innerHTML; };
const pill = (text, type)=>{
  if (type === 'status') {
    const status = String(text||'').toLowerCase();
    const statusClass = status === 'new' ? 'status-pill new' : 
                       status === 'open' ? 'status-pill open' : 
                       status === 'closed' ? 'status-pill closed' : 
                       status === 'waiting' ? 'status-pill waiting' : 
                       'status-pill new';
    return `<span class="${statusClass}">${esc(text||'—')}</span>`;
  } else if (type === 'priority') {
    const priority = String(text||'').toLowerCase();
    const priorityClass = priority === 'high' ? 'priority-pill high' : 
                         priority === 'normal' ? 'priority-pill normal' : 
                         priority === 'low' ? 'priority-pill low' : 
                         'priority-pill normal';
    return `<span class="${priorityClass}">${esc(text||'—')}</span>`;
  }
  return `<span class="px-2 py-1 rounded-lg text-xs bg-slate-100 text-slate-700">${esc(text||'—')}</span>`;
};

function showError(msg){ $err.classList.remove('hidden'); $err.textContent = typeof msg==='string'? msg : (msg?.message || JSON.stringify(msg)); }
function clearError(){ $err.classList.add('hidden'); $err.textContent=''; }

// Build headers with sort + column visibility
function buildHeaders(){
  $headRow.innerHTML='';
  DISPLAY_COLS.forEach(col => {
    if(!visible.has(col.key)) return;
    const th = document.createElement('th');
    th.className = 'text-left font-semibold text-white/90 sticky top-0 px-5 py-4 border-b border-white/20 whitespace-nowrap';
    th.innerHTML = `<button class="inline-flex items-center gap-2 hover:text-white transition-colors group">${col.label}<span class="text-[11px] text-white/50 group-hover:text-white/70">${sortBy===col.key?(sortAsc?'▲':'▼'):''}</span></button>`;
    th.querySelector('button').addEventListener('click',()=>{ if(sortBy===col.key) sortAsc=!sortAsc; else { sortBy=col.key; sortAsc=true; } load(); });
    $headRow.appendChild(th);
  });
}

// Column menu
function buildColumnMenu(){
  $columnMenu.innerHTML = DISPLAY_COLS.map(c=>{
    const id = `col_${c.key}`;
    return `<label class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/10 text-white"><input type="checkbox" id="${id}" ${visible.has(c.key)?'checked':''}/> <span>${c.label}</span></label>`;
  }).join('');
  DISPLAY_COLS.forEach(c=>{
    const id = `col_${c.key}`;
    const el = document.getElementById(id);
    if(!el) return;
    el.addEventListener('change',()=>{ el.checked ? visible.add(c.key) : visible.delete(c.key); buildHeaders(); renderRows(cache); });
  });
}

// Populate filter options
async function loadFilterOptions(){
  try{
    // Check if Supabase is available
    if (!supabase) {
      console.warn('Supabase not available, using demo data');
      return;
    }
    
    const { data: statuses } = await supabase.from(TABLE_NAME).select('status').not('status','is',null);
    const { data: issues } = await supabase.from(TABLE_NAME).select('issue_type').not('issue_type','is',null);
    const sVals = [...new Set((statuses??[]).map(r=>r.status).filter(Boolean))].sort();
    const iVals = [...new Set((issues??[]).map(r=>r.issue_type).filter(Boolean))].sort();
    $status.innerHTML = `<option value="">All Status</option>${sVals.map(v=>`<option>${esc(v)}</option>`).join('')}`;
    $issue.innerHTML = `<option value="">All Issue Types</option>${iVals.map(v=>`<option>${esc(v)}</option>`).join('')}`;
  }catch(e){ 
    console.warn('Filter load error:', e);
    showError(`Filter load error: ${e.message||e}`); 
  }
}

// Query builder (uses * to avoid column drift)
function baseQuery(){
  // Check if Supabase is available
  if (!supabase) {
    console.warn('Supabase not available, returning empty result');
    return Promise.resolve({ data: [], error: null, count: 0 });
  }
  
  let q = supabase.from(TABLE_NAME).select('*', { count: 'exact' });
  const s = $search.value.trim();
  if(s){ const parts = SEARCH_COLS.map(c=>`${c}.ilike.%${s}%`).join(','); q=q.or(parts); }
  if($status.value) q=q.eq('status',$status.value);
  if($issue.value) q=q.eq('issue_type',$issue.value);
  if($prio.value) q=q.eq('priority',$prio.value);
  if(chips['status']) q=q.eq('status', chips['status']);
  if(chips['priority']) q=q.eq('priority', chips['priority']);
  if(chips['channel']) q=q.eq('contact_channel', chips['channel']);
  q = q.order(sortBy,{ ascending: sortAsc, nullsFirst: false });
  const from=(page-1)*pageSize, to=from+pageSize-1; return q.range(from,to);
}

// Enhanced loading skeleton
function skeleton(){
  const cols = [...visible].length || 6;
  const rows = 8;
  const tr = (i)=>`<tr>${Array.from({length:cols}).map(()=>`<td class='px-5 py-4'><div class='h-4 rounded skeleton'></div></td>`).join('')}</tr>`;
  $tbody.innerHTML = Array.from({length:rows}).map((_,i)=>tr(i)).join('');
}

async function load(){
  try{
    clearError();
    pageSize = parseInt($pageSizeSel.value||'25',10);
    skeleton();
    const { data, error, count } = await baseQuery();
    if(error) throw error;
    cache = data || [];
    renderRows(cache);
    lastCount = count ?? 0;
    $("pageInfo").textContent = `Page ${page} • Showing ${cache.length} of ${count ?? 0}`;
    $("count").textContent = `${count ?? 0} tickets`;
    $("meta").textContent = `Sorted by ${sortBy} ${sortAsc? '↑':'↓'} • ${pageSize}/page`;
    $("metaBar").innerHTML = `<span class="enhanced-meta">🕐 ${new Date().toLocaleTimeString()} • Refreshed</span>`;
    $("prev").disabled = page<=1; $("next").disabled = (page*pageSize) >= (count ?? 0);
  }catch(e){ showError(e); $tbody.innerHTML = `<tr><td class="px-3 py-6 text-center text-red-400">${esc(e.message||e)}</td></tr>`; }
}

function renderRows(rows){
  if(!rows.length){ 
    $tbody.innerHTML = `<tr><td colspan="${DISPLAY_COLS.length}" class="enhanced-empty"><div class='enhanced-empty-icon'>🗂️</div><div class='enhanced-empty-text'>No tickets found</div><div class='enhanced-empty-subtext'>Try adjusting your search or filters</div></td></tr>`; 
    return; 
  }
  const activeCols = DISPLAY_COLS.filter(c=>visible.has(c.key));
  const tr = (r, i)=>{
    const t = (k)=>{
      let v = r[k];
      if(k.endsWith('_at')) return esc(fmtDate(v));
      if(k==='status') return pill(v,'status');
      if(k==='priority') return pill(v,'priority');
      if(v===true||v===false) return `<span class="text-xs px-2 py-1 rounded-lg ${v?'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30':'bg-slate-500/20 text-slate-400 border border-slate-500/30'}">${v?'Yes':'No'}</span>`;
      if(v==null||v==='') return '<span class="text-white/40">—</span>';
      return esc(v);
    };
    return `<tr data-idx="${i}" class="even:bg-white/5 hover:bg-white/10 cursor-pointer border-b border-white/10 transition-all duration-200">
      ${activeCols.map(c=>`<td class="px-5 py-4 align-top text-white/90 ${['summary'].includes(c.key)?'max-w-[400px] break-words':''}">${t(c.key)}</td>`).join('')}
    </tr>`;
  };
  $tbody.innerHTML = rows.map(tr).join('');
  [...$tbody.querySelectorAll('tr[data-idx]')].forEach(row=>{ row.addEventListener('click',()=>openSheet(cache[Number(row.dataset.idx)])); });
}

// ====== Sheet (details) ======
function openSheet(row){
  if(!row) return;
  $("sheetTitle").textContent = row.ticket_id || '(no ticket id)';
  $("sheetSub").textContent = `${row.issue_type||'—'} • ${row.status||'—'} • ${row.priority||'—'}`;
  $("d_status").innerHTML = pill(row.status,'status');
  $("d_priority").innerHTML = pill(row.priority,'priority');
  $("d_channel").textContent = row.contact_channel || '—';
  $("d_issue").textContent = row.issue_type || '—';
  $("d_name").textContent = row.full_name || '—';
  $("d_contact").innerHTML = [row.email, row.phone].filter(Boolean).map(esc).join(' • ') || '—';
  $("d_summary").textContent = row.summary || '—';
  $("d_description").textContent = row.description || '—';
  $("d_order").textContent = row.order_id || '—';
  $("d_tz").textContent = row.timezone || '—';
  $("d_created").textContent = fmtDate(row.created_at);
  $("d_updated").textContent = fmtDate(row.updated_at);
  $("d_json").textContent = JSON.stringify(row, null, 2);

  $copyId.onclick = ()=>{ navigator.clipboard.writeText(row.ticket_id||'').then(()=>toast('Ticket ID copied')); };
  $mailto.href = row.email ? `mailto:${encodeURIComponent(row.email)}?subject=${encodeURIComponent(row.ticket_id||'Ticket')}` : '#';
  $mailto.classList.toggle('pointer-events-none', !row.email);
  $mailto.classList.toggle('opacity-50', !row.email);
  $tel.href = row.phone ? `tel:${row.phone}` : '#';
  $tel.classList.toggle('pointer-events-none', !row.phone);
  $tel.classList.toggle('opacity-50', !row.phone);

  $sheetRoot.classList.remove('hidden');
  requestAnimationFrame(()=>{ $("sheetOverlay").classList.remove('opacity-0'); $sheet.classList.remove('sheet-enter'); $sheet.classList.add('sheet-enter-active'); });
}

function closeSheet(){ $("sheetOverlay").classList.add('opacity-0'); $sheet.classList.remove('sheet-enter-active'); $sheet.classList.add('sheet-exit-active'); setTimeout(()=>{ $sheetRoot.classList.add('hidden'); $sheet.classList.remove('sheet-exit-active'); $sheet.classList.add('sheet-enter'); }, 220); }
function toast(msg){ const t=document.createElement('div'); t.className='fixed bottom-5 left-1/2 -translate-x-1/2 z-[60] bg-slate-900 dark:bg-black text-white text-sm px-3 py-2 rounded-lg shadow'; t.textContent=msg; document.body.appendChild(t); setTimeout(()=>t.remove(),1200); }

// Enhanced Chips
function handleChip(el){
  const [k,v] = (el.dataset.chip||'').split(':');
  if(!k||!v) return; chips[k]=v; page=1; load();
  document.querySelectorAll('.enhanced-chip').forEach(c=>c.classList.remove('active'));
  el.classList.add('active');
}

// Theme toggle
$themeToggle.addEventListener('click',()=>{ const r=document.documentElement; r.classList.toggle('dark'); localStorage.setItem('eraya-theme', r.classList.contains('dark')? 'dark':'light'); });
(function initTheme(){ const pref=localStorage.getItem('eraya-theme'); if(pref==='dark' || (!pref && window.matchMedia('(prefers-color-scheme: dark)').matches)) document.documentElement.classList.add('dark'); })();

// Events
$("search").addEventListener('input', debounce(()=>{ page=1; load(); }, 250));
$("status").addEventListener('change', ()=>{ page=1; load(); });
$("issue_type").addEventListener('change', ()=>{ page=1; load(); });
$("priority").addEventListener('change', ()=>{ page=1; load(); });
$("pageSize").addEventListener('change', ()=>{ page=1; load(); });
$("prev").addEventListener('click', ()=>{ if(page>1){ page--; load(); }});
$("next").addEventListener('click', ()=>{ if((page*pageSize)<lastCount){ page++; load(); }});
$("refresh").addEventListener('click', ()=> load());

document.querySelectorAll('[data-chip]').forEach(btn=>btn.addEventListener('click',()=>handleChip(btn)));
$("clearChips").addEventListener('click',()=>{ chips={}; page=1; load(); document.querySelectorAll('.enhanced-chip').forEach(c=>c.classList.remove('active')); });

// Column menu toggle
$columnBtn.addEventListener('click',()=>{ $columnMenu.classList.toggle('hidden'); if(!$columnMenu.classList.contains('hidden')) buildColumnMenu(); });
document.addEventListener('click',(e)=>{ if(!$columnMenu.contains(e.target) && !$columnBtn.contains(e.target)) $columnMenu.classList.add('hidden'); });

// Sheet events
$("sheetOverlay").addEventListener('click', closeSheet);
$("closeSheet").addEventListener('click', closeSheet);
document.addEventListener('keydown', (e)=>{ if(e.key==='Escape' && !$sheetRoot.classList.contains('hidden')) closeSheet(); });

function debounce(fn,ms){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a),ms); } }

// Demo data for when Supabase is not available
const DEMO_DATA = [
  {
    ticket_id: "TK1001",
    full_name: "Aarav Sharma",
    email: "aarav@example.com",
    phone: "+91-98765-43210",
    contact_channel: "Instagram DM",
    order_id: "ORD-2024-001",
    issue_type: "Order Status",
    summary: "Where is my order?",
    description: "I placed an order 3 days ago but haven't received any updates.",
    status: "Open",
    priority: "High",
    created_at: "2024-01-15T10:30:00Z",
    updated_at: "2024-01-15T10:30:00Z"
  },
  {
    ticket_id: "TK1002",
    full_name: "Priya Verma",
    email: "priya@example.com",
    phone: "+91-87654-32109",
    contact_channel: "WhatsApp",
    order_id: "ORD-2024-002",
    issue_type: "Customization",
    summary: "Change back engraving text",
    description: "I want to change the engraving text on my order.",
    status: "Waiting on Customer",
    priority: "Normal",
    created_at: "2024-01-14T15:45:00Z",
    updated_at: "2024-01-15T09:20:00Z"
  }
];

// init
(async function init(){
  try {
    buildHeaders();
    await loadFilterOptions();
    await load();
  } catch (error) {
    console.error('Initialization error:', error);
    showError('Failed to initialize: ' + error.message);
    
    // Show demo data if Supabase is not available
    if (!supabase) {
      console.log('Showing demo data');
      cache = DEMO_DATA;
      renderRows(DEMO_DATA);
      $("pageInfo").textContent = `Page 1 • Showing ${DEMO_DATA.length} of ${DEMO_DATA.length}`;
      $("count").textContent = `${DEMO_DATA.length} tickets`;
      $("meta").textContent = `Demo data • ${pageSize}/page`;
    }
  }
})();
