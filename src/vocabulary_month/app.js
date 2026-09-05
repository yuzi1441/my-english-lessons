(() => {
  "use strict";

  const VOCAB_KEY = "ir_vocab_v1";
  // Course-scoped progress key; resolved from month.json meta.course on load.
  const LEGACY_PROGRESS_KEY = "ir_vocab_month_progress_v1";
  let PROGRESS_KEY = "ir:vocab:progress";
  const REVIEW_LIMIT = 24;
  const Review = window.AdaptiveReview;
  const app = document.querySelector("#app");
  const toastEl = document.querySelector("#toast");
  let course = null;
  let courseId = "";
  let selectedDay = 1;
  let selectedMonth = 1;
  let vocab = readJSON(VOCAB_KEY, []).map(normalizeVocab).filter(item => item.word);
  let progress = readJSON(PROGRESS_KEY, { completed: [] });
  let reviewOpen = false;
  let cloudAccount = null;
  let toastTimer = null;
  let activeAudio = null;
  let dictMap = null;

  // load per-course dictionary for tap-any-word lookup
  (async () => {
    try {
      const res = await fetch("../dictionary.json", { credentials: "same-origin" });
      if (res.ok) dictMap = await res.json();
    } catch { /* offline */ }
  })();

  function closeWordCard() { document.getElementById("wordCard")?.remove(); }

  function wordAtPoint(x, y) {
    let el = document.elementFromPoint(x, y);
    while (el && !el.closest?.(".en, .word-term, .word-detail, .review-prompt, .meaning, .example")) {
      el = el.parentElement;
    }
    if (!el) return null;
    let range = null;
    if (document.caretRangeFromPoint) range = document.caretRangeFromPoint(x, y);
    else if (document.caretPositionFromPoint) {
      const pos = document.caretPositionFromPoint(x, y);
      if (pos) { range = document.createRange(); range.setStart(pos.offsetNode, pos.offset); }
    }
    if (!range || !range.startContainer || range.startContainer.nodeType !== Node.TEXT_NODE) return null;
    const text = range.startContainer.textContent;
    const off = range.startOffset;
    let a = off, b = off;
    const isW = c => /[A-Za-z'-]/.test(c);
    while (a > 0 && isW(text[a - 1])) a -= 1;
    while (b < text.length && isW(text[b])) b += 1;
    const word = text.slice(a, b).replace(/^['-]+|['-]+$/g, "").toLowerCase();
    if (!word || word.length < 2) return null;
    const r2 = document.createRange();
    r2.setStart(range.startContainer, a);
    r2.setEnd(range.startContainer, b);
    return { word, rect: r2.getBoundingClientRect() };
  }

  function lookupWord(word) {
    if (!dictMap) return null;
    if (dictMap[word]) return dictMap[word];
    const cands = [];
    if (word.endsWith("s")) cands.push(word.slice(0, -1), word.slice(0, -2));
    if (word.endsWith("es")) cands.push(word.slice(0, -2));
    if (word.endsWith("ed")) cands.push(word.slice(0, -1), word.slice(0, -2));
    if (word.endsWith("ing")) cands.push(word.slice(0, -3), word.slice(0, -3) + "e");
    if (word.endsWith("ly")) cands.push(word.slice(0, -2));
    for (const c of cands) if (dictMap[c]) return dictMap[c];
    return null;
  }

  function showWordCard(word, rect) {
    closeWordCard();
    const hit = lookupWord(word);
    const pop = document.createElement("div");
    pop.id = "wordCard";
    const head = hit
      ? `<b>${word}</b>${hit.p ? `<span class="wc-phon">${hit.p}</span>` : ""}${hit.pos ? `<span class="wc-phon">${hit.pos}</span>` : ""}`
      : `<b>${word}</b>`;
    const synHtml = hit && hit.syn && hit.syn.length ? `<p class="wc-syn">近义词: ${hit.syn.join(", ")}</p>` : "";
    const body = hit
      ? `${hit.t ? `<p class="wc-cn">${hit.t}</p>` : ""}${hit.d ? `<p class="wc-def">${hit.d}</p>` : ""}${synHtml}`
      : '<p class="wc-cn">暂无释义</p>';
    pop.innerHTML = head + body;
    document.body.appendChild(pop);
    const vw = window.innerWidth, vh = window.innerHeight;
    pop.style.top = Math.min(Math.max(rect.top - 8, 60), vh - 150) + "px";
    pop.style.left = Math.min(Math.max(rect.left, 10), vw - 250) + "px";
    setTimeout(() => {
      document.addEventListener("click", closeWordCard, { once: true });
      document.addEventListener("touchstart", closeWordCard, { once: true });
    }, 60);
  }

  document.addEventListener("click", event => {
    if (event.target.closest("#wordCard") || event.target.closest("button") || event.target.closest("a") || event.target.closest("select")) return;
    const hit = wordAtPoint(event.clientX, event.clientY);
    if (hit) { event.stopPropagation(); showWordCard(hit.word, hit.rect); }
  });

  const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[char]));

  function readJSON(key, fallback) {
    try {
      const value = JSON.parse(localStorage.getItem(key) || "null");
      return value ?? fallback;
    } catch { return fallback; }
  }

  function writeJSON(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  function normalizeKey(value) {
    return String(value || "").trim().toLowerCase().replace(/[.!?]+$/, "").replace(/\s+/g, " ");
  }

  function normalizeVocab(item) {
    const now = Date.now();
    return Review.normalize({
      ...item,
      word: String(item?.word || "").trim(),
      createdAt: Number(item?.createdAt) || now,
      updatedAt: Number(item?.updatedAt) || Number(item?.lastReviewed) || now,
    }, now);
  }

  function mergeVocab(...lists) {
    const map = new Map();
    lists.flatMap(list => Array.isArray(list) ? list : []).forEach(raw => {
      const item = normalizeVocab(raw);
      const key = normalizeKey(item.word);
      if (!key) return;
      const previous = map.get(key);
      if (!previous || item.updatedAt >= previous.updatedAt) map.set(key, item);
    });
    return Array.from(map.values()).sort((a, b) => b.updatedAt - a.updatedAt);
  }

  function toast(message) {
    toastEl.textContent = message;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove("show"), 1900);
  }

  function startOfDay(value = Date.now()) {
    const date = new Date(value);
    date.setHours(0, 0, 0, 0);
    return date.getTime();
  }

  function dueItems(source = "all") {
    return vocab
      .filter(item => Number(item.nextReview) <= Date.now() && (source === "all" || Review.sourceKey(item) === source))
      .sort((a, b) => {
        const ratingOrder = { again: 0, hard: 1, good: 2, easy: 3, forgot: 0, fuzzy: 1, remembered: 2 };
        const ratingDiff = (ratingOrder[a.lastRating] ?? 3) - (ratingOrder[b.lastRating] ?? 3);
        return ratingDiff || Number(a.nextReview) - Number(b.nextReview);
      });
  }

  async function api(path, options = {}) {
    const response = await fetch(path, {
      credentials: "same-origin",
      ...options,
      headers: { "content-type": "application/json", ...(options.headers || {}) },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.error || "云端同步失败");
    return body;
  }

  async function loadCloud() {
    try {
      const session = await api("/api/session", { headers: {} });
      cloudAccount = session.authenticated ? session.user : null;
      if (!cloudAccount) return;
      const result = await api("/api/vocab", { headers: {} });
      vocab = mergeVocab(vocab, result.items);
      writeJSON(VOCAB_KEY, vocab);
      render();
      await syncCloud();
    } catch { cloudAccount = null; }
  }

  async function syncCloud() {
    if (!cloudAccount) return;
    try {
      const result = await api("/api/vocab/sync", { method: "POST", body: JSON.stringify({ items: vocab }) });
      vocab = mergeVocab(vocab, result.items);
      writeJSON(VOCAB_KEY, vocab);
    } catch { /* local learning remains usable */ }
  }

  function preferredEnglishVoice() {
    if (!("speechSynthesis" in window)) return null;
    const voices = speechSynthesis.getVoices?.() || [];
    return voices.find(voice => /^en-US\b/i.test(voice.lang || "") && voice.localService === false)
      || voices.find(voice => /^en-US\b/i.test(voice.lang || ""))
      || voices.find(voice => /^en\b/i.test(voice.lang || ""))
      || null;
  }

  function browserSpeak(text) {
    if (!("speechSynthesis" in window)) return toast("音频暂时无法播放");
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 0.92;
    const voice = preferredEnglishVoice();
    if (voice) utterance.voice = voice;
    speechSynthesis.speak(utterance);
  }

  function speak(text, audioPath) {
    if (activeAudio) {
      activeAudio.pause();
      activeAudio = null;
    }
    if ("speechSynthesis" in window) speechSynthesis.cancel();
    if (!audioPath) return browserSpeak(text);
    const audio = new Audio(audioPath);
    activeAudio = audio;
    let fellBack = false;
    const fallback = () => {
      if (fellBack) return;
      fellBack = true;
      activeAudio = null;
      browserSpeak(text);
    };
    audio.onerror = fallback;
    audio.onended = () => { if (activeAudio === audio) activeAudio = null; };
    audio.play().catch(fallback);
  }

  function currentDayFromURL() {
    const day = Number(new URLSearchParams(location.search).get("day"));
    const maxDay = course ? course.meta.days : 1;
    return Number.isInteger(day) && day >= 1 && day <= maxDay ? day : 1;
  }

  function allItems(day) {
    return day.groups.flatMap(group => group.items.map(item => ({ ...item, domain: group.domain, topic: group.topic })));
  }

  function vocabEntryFor(term) {
    return vocab.find(item => normalizeKey(item.word) === normalizeKey(term)) || null;
  }

  function savedAudioPath(path) {
    if (!path) return "";
    if (/^(?:https?:)?\/\//.test(path) || path.startsWith("/")) return path;
    return new URL(String(path).replace(/^\.\//, ""), location.href).href;
  }

  function upsertWord(item, day, now = Date.now()) {
    const previous = vocabEntryFor(item.term);
    const fields = {
      def: item.meaning,
      type: item.domain === "daily" ? "chunk" : "term",
      note: item.note,
      related: [item.collocation],
      examples: Array.from(new Set([item.example, ...(previous?.examples || [])])).slice(0, 5),
      lessons: Array.from(new Set([`词汇强化 Day ${day.day}`, ...(previous?.lessons || [])])).slice(0, 10),
      domain: item.domain,
      course: courseId,
      speech: item.speech,
      audioTerm: savedAudioPath(item.audio_term),
      exampleSpeech: item.example_speech,
      audioExample: savedAudioPath(item.audio_example),
      part: item.part,
      pos: item.pos,
      updatedAt: now,
    };
    if (previous) {
      Object.assign(previous, fields);
      return false;
    }
    vocab.unshift(normalizeVocab({
      word: item.term,
      ...fields,
      reviews: 0,
      stage: 0,
      status: "learning",
      nextReview: now,
      createdAt: now,
    }));
    return true;
  }

  function saveVocab() {
    vocab = mergeVocab(vocab);
    writeJSON(VOCAB_KEY, vocab);
    syncCloud();
  }

  function addWord(item, day) {
    const added = upsertWord(item, day);
    saveVocab();
    render();
    toast(added ? `已将 ${item.term} 加入生词本` : `${item.term} 已在生词本中`);
  }

  // reviews-first (Anki 共识)：积压越多，本次收的新词越少；单词卡添加不受限
  function dueBacklog() {
    return vocab.filter(item => Number(item.nextReview) <= Date.now()).length;
  }

  function addDay(day) {
    const now = Date.now();
    const backlog = dueBacklog();
    const limit = backlog >= 80 ? 8 : backlog >= 40 ? 12 : Infinity;
    const missing = allItems(day).filter(item => !vocabEntryFor(item.term));
    let added = 0;
    missing.slice(0, limit).forEach(item => {
      if (upsertWord(item, day, now)) added += 1;
    });
    saveVocab();
    render();
    if (backlog >= 80) toast(`复习积压 ${backlog} 个，本次只收 ${added} 个新词——建议先清复习`);
    else if (backlog >= 40) toast(`复习积压 ${backlog} 个，本次只收 ${added} 个新词`);
    else if (added) toast(`已加入 ${added} 个新词，今天开始记忆`);
    else toast(missing.length ? "今天的 18 个词已在生词本中" : "今天的 18 个词已在生词本中");
  }

  function rateWord(word, rating) {
    const item = vocab.find(entry => normalizeKey(entry.word) === normalizeKey(word));
    if (!item) return;
    const now = Date.now();
    Object.assign(item, Review.applyRating(item, rating, Review.reviewMode(item), now));
    writeJSON(VOCAB_KEY, vocab);
    syncCloud();
    render();
    const labels = { again: "忘记", hard: "困难", good: "正常", easy: "简单" };
    toast(`${item.word} · ${labels[rating]} · 下次 ${Review.intervalLabel(item.nextReview, now)}`);
  }

  function toggleComplete(dayNumber) {
    const completed = new Set(progress.completed || []);
    if (completed.has(dayNumber)) completed.delete(dayNumber); else completed.add(dayNumber);
    progress.completed = Array.from(completed).sort((a, b) => a - b);
    writeJSON(PROGRESS_KEY, progress);
    if (completed.has(dayNumber)) {
      const dayData = course.days[dayNumber - 1];
      const missing = allItems(dayData).filter(item => !vocabEntryFor(item.term)).length;
      if (missing > 0) toast(`已标记完成 · 本日还有 ${missing} 个词未入生词本`);
    }
    render();
  }

  function selectDay(dayNumber, scroll = true) {
    selectedDay = Math.max(1, Math.min(course ? course.meta.days : 1, dayNumber));
    selectedMonth = Math.ceil(selectedDay / 30);
    const url = new URL(location.href);
    url.searchParams.set("day", selectedDay);
    history.pushState({}, "", url);
    render();
    if (scroll) document.querySelector("#lesson")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function reviewHTML() {
    const due = dueItems(courseId || "all");
    const visible = due.slice(0, REVIEW_LIMIT);
    return `<section class="review-panel">
      <div class="review-head">
        <div><h2>本课程今日到期 · ${due.length} 个</h2><p>先主动回忆再揭晓；FSRS 优先安排遗忘、困难和逾期词，每次最多 24 个。${due.length >= 40 ? '<b style="color:#b3261e">积压较多：建议先清复习，再收新词。</b>' : ''}</p></div>
        <button class="review-toggle" data-toggle-review>${reviewOpen ? "收起复习" : due.length ? `开始复习前 ${visible.length} 个` : "今天已完成"}</button>
      </div>
      <div class="review-list ${reviewOpen ? "" : "hidden"}">
        ${visible.length ? visible.map(reviewCardHTML).join("") : `<div class="empty">今天没有本课程的到期词。学习 Day ${selectedDay} 后，FSRS 会自动安排下一次见面。</div>`}
      </div>
    </section>`;
  }

  function reviewCardHTML(item) {
    const prompt = Review.prompt(item);
    const preview = Review.preview(item);
    const audio = prompt.mode === "audio" ? `<button class="review-audio" data-speak="${esc(item.speech || item.word)}" data-audio="${esc(item.audioTerm || "")}">🔊 播放发音</button>` : `<strong class="review-prompt">${esc(prompt.prompt)}</strong>`;
    const lesson = (item.lessons || []).map(l => /Day\s+(\d+)/.exec(String(l))).find(Boolean);
    const contextLink = lesson ? `<a class="review-context-link" href="../day-${String(Number(lesson[1])).padStart(3, "0")}/index.html">回原文 · Day ${Number(lesson[1])} ↗</a>` : "";
    const leechBadge = Review.lapseCount && Review.lapseCount(item) >= 5 ? '<span class="leech-tag">顽固</span>' : "";
    return `<article class="review-card recall-card" data-review-card="${esc(item.word)}">
      <div class="review-mode">${prompt.label}${leechBadge}${contextLink}</div>
      <p>${esc(prompt.instruction)}</p>
      ${audio}
      <input class="review-input" type="text" autocomplete="off" spellcheck="false" placeholder="先说出来或写下来">
      <button class="review-reveal" data-review-reveal="${esc(item.word)}">揭晓答案</button>
      <div class="review-answer hidden" data-review-answer><b>${esc(prompt.answer)}</b><span>${esc(prompt.definition)}</span></div>
      <div class="rating-actions four-ratings hidden" data-review-ratings>
        <button data-rate-word="${esc(item.word)}" data-rating="again">忘记<small>${preview.again.label}</small></button>
        <button data-rate-word="${esc(item.word)}" data-rating="hard">困难<small>${preview.hard.label}</small></button>
        <button data-rate-word="${esc(item.word)}" data-rating="good">正常<small>${preview.good.label}</small></button>
        <button data-rate-word="${esc(item.word)}" data-rating="easy">简单<small>${preview.easy.label}</small></button>
      </div>
    </article>`;
  }

  function cardHTML(item) {
    const saved = Boolean(vocabEntryFor(item.term));
    return `<article class="word-card">
      <div class="word-top"><div><div class="word-term">${esc(item.term)}</div><span class="part">${esc(item.part)} · ${esc(item.pos)}</span></div></div>
      <div class="word-card-actions">
        <button class="speak term-speak" data-speak="${esc(item.speech)}" data-audio="${esc(item.audio_term)}" aria-label="播放 ${esc(item.term)} 的发音">🔊 播放单词</button>
        <button class="word-add ${saved ? "saved" : ""}" data-add-word="${esc(item.id)}" ${saved ? "aria-pressed=\"true\"" : ""}>${saved ? "✓ 已加入" : "＋ 加入生词本"}</button>
      </div>
      <button class="guess" data-reveal>查看这个词的中文释义</button>
      <div class="word-detail" hidden>
        <div class="meaning">${esc(item.meaning)}</div>
        <p class="explain">${esc(item.explanation)}</p>
        <span class="mini-label">常用搭配</span><p class="example">${esc(item.collocation)}</p>
        <span class="mini-label">英文例句</span><p class="example">${esc(item.example)}</p><button class="speak example-speak" data-speak="${esc(item.example_speech)}" data-audio="${esc(item.audio_example)}" aria-label="播放 ${esc(item.term)} 的例句">🔊 播放例句</button>
        <p class="note">${esc(item.note)}</p>
      </div>
    </article>`;
  }

  function exerciseHTML(exercise, index) {
    return `<article class="exercise"><b>练习 ${index + 1} · ${exercise.type === "choice" ? "识别" : "主动回忆"}</b><p>${esc(exercise.question)}</p>
      ${exercise.choices ? `<div class="choices">${exercise.choices.map((choice, i) => `<span>${String.fromCharCode(65 + i)}. ${esc(choice)}</span>`).join("")}</div>` : ""}
      <details class="answer"><summary>查看答案</summary><div>${esc(exercise.answer)}</div></details>
    </article>`;
  }

  function groupHTML(group) {
    return `<section class="group" data-domain="${group.domain}">
      <div class="group-head"><div class="group-icon">${group.icon}</div><div><p class="eyebrow">${group.title}</p><h3>${esc(group.topic)}</h3><p>${esc(group.intro)}</p></div></div>
      <div class="word-grid">${group.items.map(cardHTML).join("")}</div>
      <div class="exercises">${group.exercises.map(exerciseHTML).join("")}</div>
    </section>`;
  }

  function monthCount() {
    return course ? Math.ceil(course.days.length / 30) : 1;
  }

  function dayGridHTML(completed) {
    const start = (selectedMonth - 1) * 30;
    const end = Math.min(course.days.length, selectedMonth * 30);
    const monthButtons = Array.from({ length: monthCount() }, (_, index) => {
      const month = index + 1;
      return `<button class="month-chip ${month === selectedMonth ? "active" : ""}" data-month="${month}">第 ${month} 月</button>`;
    }).join("");
    const dayButtons = course.days.slice(start, end).map(item =>
      `<button class="day-link ${item.day === selectedDay ? "active" : ""} ${completed.has(item.day) ? "done" : ""}" data-day="${item.day}"><b>${completed.has(item.day) ? "✓ " : ""}Day ${item.day}</b><span>${esc(item.groups[0].topic)}<br>${esc(item.groups[2].topic)}</span></button>`
    ).join("");
    return `<div class="month-chips">${monthButtons}</div><div class="day-grid">${dayButtons}</div>`;
  }

  function render() {
    if (!course) return;
    const day = course.days[selectedDay - 1];
    const totalDays = course.meta.days;
    const completed = new Set(progress.completed || []);
    const due = dueItems();
    const monthDue = dueItems(courseId);
    app.innerHTML = `<section class="hero">
      <p class="eyebrow">${totalDays}-Day Professional Vocabulary</p>
      <h1>${course.meta.title}</h1>
      <p class="hero-copy">${course.meta.subtitle}。口语主课练听说，这里专门扩充词汇和专业表达。先猜、再理解、最后主动说或写一次。</p>
      <div class="hero-stats">
        <div class="hero-stat"><strong>${completed.size}/${totalDays}</strong><span>已完成课程</span></div>
        <div class="hero-stat"><strong>${course.meta.new_terms}</strong><span>已构建新词与表达</span></div>
        <div class="hero-stat"><strong>${vocab.filter(item => item.course === courseId).length}</strong><span>已加入生词本</span></div>
        <div class="hero-stat"><strong>${monthDue.length}/${due.length}</strong><span>本课到期 / 全部到期</span></div>
      </div>
    </section>
    ${reviewHTML()}
    <section class="month-section">
      <div class="section-title"><div><p class="eyebrow">MONTH MAP</p><h2>Day 1–${totalDays} 学习地图</h2></div><p>漏学可以顺延，不受日期限制；按月切换查看。</p></div>
      ${dayGridHTML(completed)}
    </section>
    <section class="lesson" id="lesson">
      <div class="lesson-head"><div><p class="eyebrow">TODAY'S LESSON</p><h2>${esc(day.title)}</h2><p>三个场景 · 18 个新词 · 6 道练习 · ${day.duration}</p></div>
      <div class="lesson-actions"><button class="secondary" data-reveal-all>揭晓全部释义</button><button class="primary" data-add-day>加入今天 18 词</button><button class="primary ${completed.has(day.day) ? "done" : ""}" data-complete>${completed.has(day.day) ? "✓ 今日已完成" : "标记今日完成"}</button></div></div>
      ${day.groups.map(groupHTML).join("")}
      <div class="lesson-nav"><button data-prev ${day.day === 1 ? "disabled" : ""}>← 上一天</button><button data-next ${day.day === totalDays ? "disabled" : ""}>下一天 →</button></div>
    </section>`;
  }

  document.addEventListener("click", event => {
    const monthChip = event.target.closest("[data-month]");
    if (monthChip) {
      selectedMonth = Math.max(1, Math.min(monthCount(), Number(monthChip.dataset.month)));
      return render();
    }
    const dayButton = event.target.closest("[data-day]");
    if (dayButton) return selectDay(Number(dayButton.dataset.day));
    const reveal = event.target.closest("[data-reveal]");
    if (reveal) {
      const detail = reveal.nextElementSibling;
      detail.hidden = !detail.hidden;
      reveal.textContent = detail.hidden ? "查看这个词的中文释义" : "收起这个词的中文释义";
      return;
    }
    const speakButton = event.target.closest("[data-speak]");
    if (speakButton) return speak(speakButton.dataset.speak, speakButton.dataset.audio);
    const addWordButton = event.target.closest("[data-add-word]");
    if (addWordButton) {
      const item = allItems(course.days[selectedDay - 1]).find(entry => entry.id === addWordButton.dataset.addWord);
      if (item) return addWord(item, course.days[selectedDay - 1]);
    }
    const rateButton = event.target.closest("[data-rate-word]");
    if (rateButton) return rateWord(rateButton.dataset.rateWord, rateButton.dataset.rating);
    const reviewReveal = event.target.closest("[data-review-reveal]");
    if (reviewReveal) {
      const card = reviewReveal.closest("[data-review-card]");
      card?.querySelector("[data-review-answer]")?.classList.remove("hidden");
      card?.querySelector("[data-review-ratings]")?.classList.remove("hidden");
      reviewReveal.classList.add("hidden");
      return;
    }
    if (event.target.closest("[data-toggle-review]")) { reviewOpen = !reviewOpen; return render(); }
    if (event.target.closest("[data-reveal-all]")) {
      document.querySelectorAll(".word-detail").forEach(detail => { detail.hidden = false; });
      document.querySelectorAll("[data-reveal]").forEach(button => { button.textContent = "收起这个词的中文释义"; });
      return;
    }
    if (event.target.closest("[data-add-day]")) return addDay(course.days[selectedDay - 1]);
    if (event.target.closest("[data-complete]")) return toggleComplete(selectedDay);
    if (event.target.closest("[data-prev]")) return selectDay(selectedDay - 1);
    if (event.target.closest("[data-next]")) return selectDay(selectedDay + 1);
  });

  window.addEventListener("popstate", () => { selectedDay = currentDayFromURL(); selectedMonth = Math.ceil(selectedDay / 30); render(); });

  function adoptCourse(data) {
    course = data;
    courseId = String(data.meta?.course || "speaking-vocab");
    // Per-course progress key; migrate the single-course legacy key once.
    PROGRESS_KEY = `ir:${courseId}:vocab_progress`;
    const legacy = readJSON(LEGACY_PROGRESS_KEY, null);
    if (legacy && !localStorage.getItem(PROGRESS_KEY)) {
      progress = legacy;
      writeJSON(PROGRESS_KEY, progress);
    } else {
      progress = readJSON(PROGRESS_KEY, { completed: [] });
    }
    selectedDay = currentDayFromURL();
    selectedMonth = Math.ceil(selectedDay / 30);
    render();
    loadCloud();
  }

  fetch("month.json")
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(adoptCourse)
    .catch(error => { app.innerHTML = `<section class="error-card">课程加载失败：${esc(error.message)}</section>`; });

  // ---- selection-based word lookup (划选查词) ----
  let DICT = null;
  (async () => {
    try {
      const res = await fetch("../dictionary.json", { credentials: "same-origin" });
      if (res.ok) DICT = await res.json();
    } catch { /* offline */ }
  })();

  function closeWordCard() { document.getElementById("wordCard")?.remove(); }

  function lookupSel(text) {
    if (!DICT) return null;
    const key = text.toLowerCase().replace(/^['"\s]+|['"\s.]+$/g, "");
    if (!key) return null;
    if (DICT[key]) return { word: key, ...DICT[key] };
    // inflection fallback
    const cands = [];
    if (key.endsWith("s")) cands.push(key.slice(0, -1), key.slice(0, -2));
    if (key.endsWith("es")) cands.push(key.slice(0, -2));
    if (key.endsWith("ed")) cands.push(key.slice(0, -1), key.slice(0, -2));
    if (key.endsWith("ing")) cands.push(key.slice(0, -3), key.slice(0, -3) + "e");
    if (key.endsWith("ly")) cands.push(key.slice(0, -2));
    for (const c of cands) if (DICT[c]) return { word: c, base: c, ...DICT[c] };
    return null;
  }

  function showSelCard(text, rect) {
    closeWordCard();
    const hit = lookupSel(text);
    const pop = document.createElement("div");
    pop.id = "wordCard";
    const word = hit ? hit.word : text;
    const ipa = hit && hit.p ? `<span class="wc-phon">${hit.p}</span>` : "";
    const pos = hit && hit.pos ? `<span class="wc-phon">${hit.pos}</span>` : "";
    const zh = hit && hit.t ? `<p class="wc-cn">${hit.t}</p>` : "";
    const en = hit && hit.d ? `<p class="wc-def">${hit.d}</p>` : "";
    const syn = hit && hit.syn && hit.syn.length ? `<p class="wc-syn">近义词: ${hit.syn.join(", ")}</p>` : "";
    const ant = hit && hit.ant && hit.ant.length ? `<p class="wc-syn">反义词: ${hit.ant.join(", ")}</p>` : "";
    const ex = hit && hit.ex && hit.ex.length ? `<p class="wc-def" style="color:#888;font-style:italic">${hit.ex[0]}</p>` : "";
    const addBtn = `<button class="wc-add" data-word="${word}">＋ 加入生词本</button>`;
    pop.innerHTML = `<b>${word}</b>${ipa}${pos}<div style="margin-top:4px">${zh}${en}${syn}${ant}${ex}</div>${addBtn}`;
    document.body.appendChild(pop);
    // position near selection
    const popEl = document.getElementById("wordCard");
    const pr = popEl.getBoundingClientRect();
    let top = rect.bottom + 8;
    let left = Math.max(10, Math.min(rect.left, window.innerWidth - pr.width - 10));
    if (top + pr.height > window.innerHeight) top = Math.max(10, rect.top - pr.height - 8);
    popEl.style.top = top + "px";
    popEl.style.left = left + "px";
    // add to notebook
    popEl.querySelector(".wc-add").addEventListener("click", ev => {
      ev.stopPropagation();
      if (typeof addVocabWord === "function") {
        addVocabWord(word, { def: hit ? (hit.t || hit.d || "") : "", type: "word" }, "");
      } else if (typeof addWord === "function") {
        // vocab SPA
        toast("已查: " + word);
      }
      closeWordCard();
    });
    // close on outside click (delayed so the mouseup that triggered selection doesn't immediately close)
    setTimeout(() => {
      document.addEventListener("mousedown", closeWordCard, { once: true });
    }, 200);
  }

  document.addEventListener("mouseup", event => {
    if (event.target.closest("#wordCard") || event.target.closest("button") || event.target.closest("a") || event.target.closest("select") || event.target.closest("input")) return;
    setTimeout(() => {
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed) { closeWordCard(); return; }
      const text = sel.toString().trim();
      if (!text || text.length > 60) { closeWordCard(); return; }
      // must contain at least one English letter
      if (!/[A-Za-z]/.test(text)) { closeWordCard(); return; }
      // get selection rect
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      if (rect.width < 2) { closeWordCard(); return; }
      showSelCard(text, rect);
    }, 50);
  });
  document.addEventListener("touchend", event => {
    if (event.target.closest("#wordCard")) return;
    setTimeout(() => {
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed) return;
      const text = sel.toString().trim();
      if (!text || text.length > 60 || !/[A-Za-z]/.test(text)) return;
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      if (rect.width < 2) return;
      showSelCard(text, rect);
    }, 100);
  });

})();
