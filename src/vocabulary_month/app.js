(() => {
  "use strict";

  const VOCAB_KEY = "ir_vocab_v1";
  const PROGRESS_KEY = "ir_vocab_month_progress_v1";
  const REVIEW_LIMIT = 24;
  const Review = window.AdaptiveReview;
  const app = document.querySelector("#app");
  const toastEl = document.querySelector("#toast");
  let course = null;
  let selectedDay = 1;
  let vocab = readJSON(VOCAB_KEY, []).map(normalizeVocab).filter(item => item.word);
  let progress = readJSON(PROGRESS_KEY, { completed: [] });
  let reviewOpen = false;
  let cloudAccount = null;
  let toastTimer = null;
  let activeAudio = null;

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
    return Number.isInteger(day) && day >= 1 && day <= 30 ? day : 1;
  }

  function allItems(day) {
    return day.groups.flatMap(group => group.items.map(item => ({ ...item, domain: group.domain, topic: group.topic })));
  }

  function vocabEntryFor(term) {
    return vocab.find(item => normalizeKey(item.word) === normalizeKey(term)) || null;
  }

  function savedAudioPath(path) {
    if (!path) return "";
    if (/^(?:https?:)?\//.test(path)) return path;
    return `/vocabulary-month/${String(path).replace(/^\.\//, "")}`;
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
      course: "vocabulary-month",
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

  function addDay(day) {
    const now = Date.now();
    let added = 0;
    allItems(day).forEach(item => {
      if (upsertWord(item, day, now)) added += 1;
    });
    saveVocab();
    render();
    toast(added ? `已加入 ${added} 个新词，今天开始记忆` : "今天的 18 个词已在生词本中");
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
    render();
  }

  function selectDay(dayNumber, scroll = true) {
    selectedDay = Math.max(1, Math.min(30, dayNumber));
    const url = new URL(location.href);
    url.searchParams.set("day", selectedDay);
    history.pushState({}, "", url);
    render();
    if (scroll) document.querySelector("#lesson")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function reviewHTML() {
    const due = dueItems("vocabulary-month");
    const visible = due.slice(0, REVIEW_LIMIT);
    return `<section class="review-panel">
      <div class="review-head">
        <div><h2>本课程今日到期 · ${due.length} 个</h2><p>先主动回忆再揭晓；FSRS 优先安排遗忘、困难和逾期词，每次最多 24 个。</p></div>
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
    return `<article class="review-card recall-card" data-review-card="${esc(item.word)}">
      <div class="review-mode">${prompt.label}</div>
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

  function render() {
    if (!course) return;
    const day = course.days[selectedDay - 1];
    const completed = new Set(progress.completed || []);
    const due = dueItems();
    const monthDue = dueItems("vocabulary-month");
    app.innerHTML = `<section class="hero">
      <p class="eyebrow">30-Day Professional Vocabulary</p>
      <h1>${course.meta.title}</h1>
      <p class="hero-copy">${course.meta.subtitle}。口语主课练听说，这里专门扩充词汇和专业表达。先猜、再理解、最后主动说或写一次。</p>
      <div class="hero-stats">
        <div class="hero-stat"><strong>${completed.size}/30</strong><span>已完成课程</span></div>
        <div class="hero-stat"><strong>${course.meta.new_terms}</strong><span>整月新词与表达</span></div>
        <div class="hero-stat"><strong>${vocab.filter(item => item.course === "vocabulary-month").length}</strong><span>已加入生词本</span></div>
        <div class="hero-stat"><strong>${monthDue.length}/${due.length}</strong><span>本课到期 / 全部到期</span></div>
      </div>
    </section>
    ${reviewHTML()}
    <section class="month-section">
      <div class="section-title"><div><p class="eyebrow">MONTH MAP</p><h2>Day 1–30 学习地图</h2></div><p>漏学可以顺延，不受日期限制。</p></div>
      <div class="day-grid">${course.days.map(item => `<button class="day-link ${item.day === selectedDay ? "active" : ""} ${completed.has(item.day) ? "done" : ""}" data-day="${item.day}"><b>${completed.has(item.day) ? "✓ " : ""}Day ${item.day}</b><span>${esc(item.groups[0].topic)}<br>${esc(item.groups[2].topic)}</span></button>`).join("")}</div>
    </section>
    <section class="lesson" id="lesson">
      <div class="lesson-head"><div><p class="eyebrow">TODAY'S LESSON</p><h2>${esc(day.title)}</h2><p>三个场景 · 18 个新词 · 6 道练习 · ${day.duration}</p></div>
      <div class="lesson-actions"><button class="secondary" data-reveal-all>揭晓全部释义</button><button class="primary" data-add-day>加入今天 18 词</button><button class="primary ${completed.has(day.day) ? "done" : ""}" data-complete>${completed.has(day.day) ? "✓ 今日已完成" : "标记今日完成"}</button></div></div>
      ${day.groups.map(groupHTML).join("")}
      <div class="lesson-nav"><button data-prev ${day.day === 1 ? "disabled" : ""}>← 上一天</button><button data-next ${day.day === 30 ? "disabled" : ""}>下一天 →</button></div>
    </section>`;
  }

  document.addEventListener("click", event => {
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

  window.addEventListener("popstate", () => { selectedDay = currentDayFromURL(); render(); });

  fetch("month.json")
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(data => {
      course = data;
      selectedDay = currentDayFromURL();
      render();
      loadCloud();
    })
    .catch(error => { app.innerHTML = `<section class="error-card">课程加载失败：${esc(error.message)}</section>`; });
})();
