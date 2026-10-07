/* ============================================================
   CRJ Fastigheter AB — Queue System
   ============================================================ */

'use strict';

const PROPERTY_LABELS = {
  'skovdevagen-39': 'Skövdevägen 39, Skultorp'
};

/* ---- Format date in Swedish ---- */
function formatDateSv(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleDateString('sv-SE', { year: 'numeric', month: 'long', day: 'numeric' });
}

/* ---- Validate form fields ---- */
function validateQueueForm(form) {
  let valid = true;

  form.querySelectorAll('[required]').forEach(field => {
    const errEl = field.parentElement.querySelector('.form-error');
    const value = (field.value || '').trim();
    let msg = '';

    if (field.type === 'checkbox') {
      if (!field.checked) msg = 'Du måste godkänna villkoren.';
    } else if (!value) {
      msg = 'Det här fältet är obligatoriskt.';
    } else if (field.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      msg = 'Ange en giltig e-postadress.';
    } else if (field.type === 'tel' && !/^[\d\s+\-().]{6,}$/.test(value)) {
      msg = 'Ange ett giltigt telefonnummer.';
    }

    if (errEl) errEl.textContent = msg;
    if (msg) { valid = false; field.classList.add('error'); }
    else field.classList.remove('error');
  });

  // Consent error
  const consentErr = document.getElementById('consent-error');
  const consent    = document.getElementById('q-consent');
  if (consentErr && consent && !consent.checked) {
    consentErr.textContent = 'Du måste godkänna villkoren för att registrera dig.';
    valid = false;
  } else if (consentErr) {
    consentErr.textContent = '';
  }

  return valid;
}

/* ---- Get queue count for a property ---- */
async function getQueueCount(propertyId) {
  if (!isSupabaseConfigured()) return null;
  try {
    const { count, error } = await supabaseClient
      .from('queue_entries')
      .select('*', { count: 'exact', head: true })
      .eq('property_id', propertyId)
      .in('status', ['pending', 'contacted']);
    if (error) throw error;
    return count;
  } catch { return null; }
}

/* ---- Get current user's entry for a property ---- */
async function getMyQueueEntry(propertyId) {
  if (!isSupabaseConfigured()) return null;
  const user = await getCurrentUser();
  if (!user) return null;

  try {
    const { data, error } = await supabaseClient
      .from('queue_entries')
      .select('*')
      .eq('property_id', propertyId)
      .eq('user_id', user.id)
      .in('status', ['pending', 'contacted'])
      .maybeSingle();
    if (error) throw error;
    return data;
  } catch { return null; }
}

/* ---- Get position in queue ---- */
async function getQueuePosition(propertyId, createdAt) {
  if (!isSupabaseConfigured() || !createdAt) return null;
  try {
    const { count, error } = await supabaseClient
      .from('queue_entries')
      .select('*', { count: 'exact', head: true })
      .eq('property_id', propertyId)
      .in('status', ['pending', 'contacted'])
      .lt('created_at', createdAt);
    if (error) throw error;
    return (count || 0) + 1;
  } catch { return null; }
}

/* ---- Get all my queue entries (across all properties) ---- */
async function getMyAllQueueEntries() {
  if (!isSupabaseConfigured()) return [];
  const user = await getCurrentUser();
  if (!user) return [];

  try {
    const { data, error } = await supabaseClient
      .from('queue_entries')
      .select('*')
      .eq('user_id', user.id)
      .in('status', ['pending', 'contacted'])
      .order('created_at', { ascending: false });
    if (error) throw error;
    return data || [];
  } catch { return []; }
}

/* ---- Submit queue registration ---- */
async function submitQueueForm(propertyId, form) {
  if (!validateQueueForm(form)) return;

  const btn = form.querySelector('[type="submit"]');
  const origHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span>';

  const payload = {
    property_id:    propertyId,
    full_name:      (form.querySelector('[name="full_name"]')?.value || '').trim(),
    email:          (form.querySelector('[name="email"]')?.value || '').trim(),
    phone:          (form.querySelector('[name="phone"]')?.value || '').trim(),
    preferred_size: (form.querySelector('[name="preferred_size"]')?.value || '') || null,
    notes:          (form.querySelector('[name="notes"]')?.value || '').trim() || null,
    status:         'pending'
  };

  // Attach user_id if logged in
  const user = await getCurrentUser();
  if (user) payload.user_id = user.id;

  if (!isSupabaseConfigured()) {
    // Fallback: simulate success
    showQueueSuccess(form, 1, propertyId);
    btn.disabled = false;
    btn.innerHTML = origHtml;
    return;
  }

  try {
    const { data, error } = await supabaseClient
      .from('queue_entries')
      .insert(payload)
      .select()
      .single();

    if (error) {
      if (error.code === '23505') {
        showFormError(form, 'Det finns redan en registrering med den e-postadressen för den här fastigheten.');
      } else {
        showFormError(form, 'Något gick fel. Försök igen eller kontakta oss direkt.');
      }
      btn.disabled = false;
      btn.innerHTML = origHtml;
      return;
    }

    const position = await getQueuePosition(propertyId, data.created_at);
    showQueueSuccess(form, position, propertyId, data);

  } catch {
    showFormError(form, 'Något gick fel. Försök igen eller kontakta oss direkt.');
    btn.disabled = false;
    btn.innerHTML = origHtml;
  }
}

function showFormError(form, message) {
  let errEl = form.querySelector('.form-submit-error');
  if (!errEl) {
    errEl = document.createElement('p');
    errEl.className = 'form-submit-error';
    errEl.style.cssText = 'color:var(--error);font-size:0.85rem;margin-top:12px;';
    form.appendChild(errEl);
  }
  errEl.textContent = message;
}

function showQueueSuccess(form, position, propertyId, data) {
  const formState = document.getElementById('modal-form-state');
  const successState = document.getElementById('modal-success-state');
  const posEl = document.getElementById('success-position');

  if (formState) formState.style.display = 'none';
  if (successState) successState.style.display = 'block';
  if (posEl && position) posEl.textContent = `Plats ${position}`;

  // Update the queue display on page
  setTimeout(() => initPropertyQueue(propertyId), 500);
}

/* ---- Init queue UI on property page ---- */
async function initPropertyQueue(propertyId) {
  const stateLoading   = document.getElementById('state-loading');
  const stateInQueue   = document.getElementById('state-in-queue');
  const stateNotInQueue = document.getElementById('state-not-in-queue');
  const countDisplay   = document.getElementById('queue-count-display');

  if (!stateLoading && !stateInQueue && !stateNotInQueue) return;

  // Show loading
  if (stateLoading)    stateLoading.style.display    = 'flex';
  if (stateInQueue)    stateInQueue.style.display     = 'none';
  if (stateNotInQueue) stateNotInQueue.style.display  = 'none';

  // Fetch count
  const count = await getQueueCount(propertyId);
  if (countDisplay) countDisplay.textContent = count !== null ? count : '—';

  // Check if user is in queue
  const myEntry = await getMyQueueEntry(propertyId);

  if (stateLoading) stateLoading.style.display = 'none';

  if (myEntry) {
    const position = await getQueuePosition(propertyId, myEntry.created_at);

    const posEl   = document.getElementById('my-position-number');
    const dateEl  = document.getElementById('my-queue-date');
    const beforeEl = document.getElementById('my-queue-persons-before');

    if (posEl)   posEl.textContent  = position || '—';
    if (dateEl)  dateEl.textContent = `Registrerad ${formatDateSv(myEntry.created_at)}`;
    if (beforeEl && position && position > 1) {
      beforeEl.textContent = `${position - 1} ${position - 1 === 1 ? 'person' : 'personer'} står före dig.`;
    } else if (beforeEl && position === 1) {
      beforeEl.textContent = 'Du är först i kön.';
    }

    if (stateInQueue) stateInQueue.style.display = 'block';
  } else {
    if (stateNotInQueue) stateNotInQueue.style.display = 'block';
  }
}

/* ---- Init "Mina köer" page ---- */
async function initMyQueues() {
  const container = document.getElementById('my-queues-container');
  const loading   = document.getElementById('my-queues-loading');
  const empty     = document.getElementById('my-queues-empty');
  const noAuth    = document.getElementById('my-queues-noauth');

  if (!container) return;

  const user = await getCurrentUser();

  if (!user) {
    if (loading)  loading.style.display  = 'none';
    if (noAuth)   noAuth.style.display   = 'block';
    return;
  }

  const entries = await getMyAllQueueEntries();

  if (loading) loading.style.display = 'none';

  if (!entries.length) {
    if (empty) empty.style.display = 'block';
    return;
  }

  const list = document.createElement('div');
  list.className = 'my-queues-list';

  for (const entry of entries) {
    const position = await getQueuePosition(entry.property_id, entry.created_at);
    const label    = PROPERTY_LABELS[entry.property_id] || entry.property_id;

    const item = document.createElement('div');
    item.className = 'my-queue-item';
    item.innerHTML = `
      <div>
        <div class="my-queue-item__title">${label}</div>
        <div class="my-queue-item__meta">
          Plats ${position || '—'} · Registrerad ${formatDateSv(entry.created_at)}
        </div>
      </div>
      <div>
        <a href="lagenheter.html#ko-sektion" class="btn btn--outline-navy btn--sm">Visa kö</a>
      </div>
    `;
    list.appendChild(item);
  }

  container.appendChild(list);
}
