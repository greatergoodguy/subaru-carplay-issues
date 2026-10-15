// Directory filtering + "show more". Every complaint is already in the HTML (for
// search engines and no-JS readers); this script only hides/shows and paginates.
(function () {
  var list = document.getElementById('complaints');
  if (!list) return;
  var PAGE = 20;
  var items = Array.prototype.slice.call(list.querySelectorAll('article.c'));
  var q = document.getElementById('q');
  var model = document.getElementById('f-model');
  var year = document.getElementById('f-year');
  var safety = document.getElementById('f-safety');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip[data-tag]'));
  var count = document.getElementById('count');
  var empty = document.getElementById('empty');
  var moreBtn = document.getElementById('more');
  var clearBtn = document.getElementById('clear');
  var directory = document.getElementById('directory');
  var activeTags = [];
  var limit = PAGE;

  function setPressed() {
    chips.forEach(function (c) {
      c.setAttribute('aria-pressed', activeTags.indexOf(c.dataset.tag) > -1 ? 'true' : 'false');
    });
  }

  function readUrl() {
    var p = new URLSearchParams(location.search);
    if (q) q.value = p.get('q') || '';
    if (model) model.value = p.get('model') || '';
    if (year) year.value = p.get('year') || '';
    if (safety) safety.checked = p.get('safety') === '1';
    activeTags = (p.get('symptom') || '').split(',').filter(Boolean);
    setPressed();
  }

  function writeUrl() {
    var p = new URLSearchParams();
    if (q && q.value.trim()) p.set('q', q.value.trim());
    if (model && model.value) p.set('model', model.value);
    if (year && year.value) p.set('year', year.value);
    if (safety && safety.checked) p.set('safety', '1');
    if (activeTags.length) p.set('symptom', activeTags.join(','));
    var s = p.toString();
    history.replaceState(null, '', (s ? '?' + s : location.pathname) + location.hash);
    if (clearBtn) clearBtn.hidden = !s;
  }

  function matches(el, text) {
    if (model && model.value && el.dataset.model !== model.value) return false;
    if (year && year.value && el.dataset.year !== year.value) return false;
    if (safety && safety.checked && el.dataset.safety !== '1') return false;
    if (activeTags.length) {
      var t = el.dataset.tags.split('|');
      if (!activeTags.some(function (a) { return t.indexOf(a) > -1; })) return false;
    }
    return !text || el.textContent.toLowerCase().indexOf(text) > -1;
  }

  function apply(resetLimit) {
    if (resetLimit) limit = PAGE;
    var text = q ? q.value.trim().toLowerCase() : '';
    var shown = 0;
    items.forEach(function (el) {
      var ok = matches(el, text);
      el.hidden = !ok;
      if (ok) shown++;
      el.classList.toggle('more', ok && shown > limit);
    });
    if (count) count.textContent = shown === items.length ? items.length + ' complaints' : shown + ' of ' + items.length + ' complaints';
    if (empty) empty.hidden = shown !== 0;
    if (moreBtn) {
      moreBtn.hidden = shown <= limit;
      moreBtn.textContent = 'Show ' + Math.min(PAGE, shown - limit) + ' more (' + (shown - limit) + ' remaining)';
    }
    writeUrl();
  }

  function toggleTag(tag, on) {
    var i = activeTags.indexOf(tag);
    if (on === undefined) on = i === -1;
    if (on && i === -1) activeTags.push(tag);
    if (!on && i > -1) activeTags.splice(i, 1);
    setPressed();
    apply(true);
  }

  chips.forEach(function (c) {
    c.addEventListener('click', function () { toggleTag(c.dataset.tag); });
  });
  [model, year, safety].forEach(function (el) { if (el) el.addEventListener('change', function () { apply(true); }); });
  if (q) q.addEventListener('input', function () { apply(true); });
  if (moreBtn) moreBtn.addEventListener('click', function () { limit += PAGE; apply(false); });
  if (clearBtn) clearBtn.addEventListener('click', function () {
    if (q) q.value = ''; if (model) model.value = ''; if (year) year.value = ''; if (safety) safety.checked = false;
    activeTags = []; setPressed(); apply(true);
  });

  // Chart bars: show only that symptom, then jump to the list.
  Array.prototype.slice.call(document.querySelectorAll('[data-show-tag]')).forEach(function (b) {
    b.addEventListener('click', function () {
      activeTags = [b.dataset.showTag]; setPressed(); apply(true);
      directory.scrollIntoView({ behavior: 'smooth' });
    });
  });

  // Hero search: filter in place instead of reloading.
  var hero = document.getElementById('hero-search');
  if (hero) hero.addEventListener('submit', function (ev) {
    ev.preventDefault();
    if (q) q.value = hero.querySelector('input').value;
    apply(true);
    directory.scrollIntoView({ behavior: 'smooth' });
  });

  readUrl();
  apply(true);
})();
