(() => {
  const KEY = "ir_vocab_v1";
  const DAY = 24 * 60 * 60 * 1000;
  const REVIEW_LIMIT = 24;
  const Review = window.AdaptiveReview;
  const $ = (sel) => document.querySelector(sel);
  const esc = (text) => String(text || "").replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[ch]));
  const now = () => Date.now();
  let view = "due";
  let sourceFilter = "all";
  let account = null;
  let authMode = "login";
  let syncPromise = Promise.resolve();
  let activeAudio = null;
  const revealedReviews = new Set();

  function read() {
    try {
      const raw = JSON.parse(localStorage.getItem(KEY) || "[]");
      return Array.isArray(raw) ? raw.map(normalize).filter(item => item.word) : [];
    } catch {
      return [];
    }
  }

  function save(items) {
    localStorage.setItem(KEY, JSON.stringify(items));
  }

  let entries = read();
  save(entries);

  function startOfDay(value = now()) {
    const date = new Date(value);
    date.setHours(0, 0, 0, 0);
    return date.getTime();
  }

  function dateKey(value) {
    const date = new Date(value);
    return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
  }

  function normalize(item) {
    return Review.normalize({
      ...item,
      word: String(item?.word || "").trim(),
      createdAt: Number(item?.createdAt) || now(),
      updatedAt: Number(item?.updatedAt) || Number(item?.lastReviewed) || Number(item?.createdAt) || now(),
    });
  }

  async function api(path, options = {}) {
    const response = await fetch(path, {
      credentials: "same-origin",
      ...options,
      headers: { "content-type": "application/json", ...(options.headers || {}) }
    });
    let body = {};
    try { body = await response.json(); } catch { /* non-JSON error */ }
    if (!response.ok) throw new Error(body.error || "云端同步失败");
    return body;
  }

  function mergeItems(...lists) {
    const merged = new Map();
    for (const list of lists) {
      for (const raw of Array.isArray(list) ? list : []) {
        const item = normalize(raw);
        const key = item.word.toLowerCase();
        const previous = merged.get(key);
        if (!previous || Number(item.updatedAt) >= Number(previous.updatedAt)) merged.set(key, item);
      }
    }
    return Array.from(merged.values()).sort((a, b) => Number(b.updatedAt || 0) - Number(a.updatedAt || 0));
  }

  function updateAccountUI() {
    const state = $("#accountState");
    const open = $("#accountOpen");
    const logout = $("#accountLogout");
    if (!state || !open || !logout) return;
    if (account) {
      state.textContent = `已同步 · ${account.username}`;
      state.classList.add("connected");
      open.textContent = "账号设置";
      logout.classList.remove("hidden");
    } else {
      state.textContent = "本设备保存";
      state.classList.remove("connected");
      open.textContent = "登录同步";
      logout.classList.add("hidden");
    }
  }

  function openAuth(mode = "login") {
    authMode = mode;
    $("#authTitle").textContent = mode === "login" ? "登录你的生词本" : "注册同步账号";
    $("#authSubmit").textContent = mode === "login" ? "登录并同步" : "注册并同步";
    $("#authSwitch").textContent = mode === "login" ? "还没有账号？注册一个" : "已有账号？返回登录";
    $("#authError").textContent = "";
    $("#authBackdrop").classList.remove("hidden");
    $("#authUsername").focus();
  }

  function closeAuth() {
    $("#authBackdrop")?.classList.add("hidden");
  }

  async function syncCloud(showToast = false) {
    if (!account) return;
    syncPromise = syncPromise.then(async () => {
      const result = await api("/api/vocab/sync", { method: "POST", body: JSON.stringify({ items: entries }) });
      entries = mergeItems(entries, result.items);
      save(entries);
      render();
      if (showToast) toast("已同步到云端");
    }).catch(error => {
      if (showToast) toast(error.message || "云端同步失败");
    });
    return syncPromise;
  }

  async function loadCloud() {
    try {
      const session = await api("/api/session", { headers: {} });
      account = session.authenticated ? session.user : null;
      updateAccountUI();
      if (!account) return;
      const result = await api("/api/vocab", { headers: {} });
      entries = mergeItems(entries, result.items);
      save(entries);
      render();
      await syncCloud();
    } catch {
      account = null;
      updateAccountUI();
    }
  }

  async function submitAuth(event) {
    event.preventDefault();
    const errorEl = $("#authError");
    const submit = $("#authSubmit");
    const username = $("#authUsername").value.trim();
    const password = $("#authPassword").value;
    errorEl.textContent = "";
    submit.disabled = true;
    submit.textContent = authMode === "login" ? "正在登录…" : "正在注册…";
    try {
      const endpoint = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
      const result = await api(endpoint, { method: "POST", body: JSON.stringify({ username, password }) });
      account = result.user;
      updateAccountUI();
      await syncCloud();
      closeAuth();
      $("#authPassword").value = "";
      toast(`已登录 ${account.username}，生词已同步`);
    } catch (err) {
      errorEl.textContent = err.message || "登录失败，请稍后重试";
    } finally {
      submit.disabled = false;
      submit.textContent = authMode === "login" ? "登录并同步" : "注册并同步";
    }
  }

  function isDue(item) {
    return Number(item.nextReview) <= now();
  }

  function sameDay(a, b) {
    return dateKey(a) === dateKey(b);
  }

  function timeLabel(ts) {
    if (!ts) return "待安排";
    const remaining = Number(ts) - now();
    if (remaining > 0 && remaining < DAY) return `${Review.intervalLabel(ts)}后复习`;
    const diff = Math.round((startOfDay(ts) - startOfDay()) / DAY);
    if (diff < 0) return `已逾期 ${Math.abs(diff)} 天`;
    if (diff === 0) return "今天复习";
    if (diff === 1) return "明天复习";
    if (diff <= 7) return `${diff} 天后复习`;
    return new Intl.DateTimeFormat("zh-CN", { month: "numeric", day: "numeric" }).format(new Date(ts)) + " 复习";
  }

  function toast(message) {
    const el = $("#vocabToast");
    if (!el) return;
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove("show"), 1800);
  }

  function browserSpeak(text) {
    if (!("speechSynthesis" in window)) return toast("音频暂时无法播放");
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 0.92;
    const voices = speechSynthesis.getVoices?.() || [];
    utterance.voice = voices.find(voice => /^en-US\b/i.test(voice.lang || ""))
      || voices.find(voice => /^en\b/i.test(voice.lang || ""))
      || null;
    speechSynthesis.speak(utterance);
  }

  function speak(text, audioPath) {
    if (activeAudio) activeAudio.pause();
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

  function stats() {
    const due = entries.filter(isDue);
    const learning = entries.filter(item => item.status !== "known");
    const known = entries.filter(item => item.status === "known");
    const doneItems = entries.filter(item => Review.reviewedToday(item));
    const done = doneItems.length;
    return { due, learning, known, done, doneItems };
  }

  const COURSE_LABELS = {
    "speaking-vocab": "词汇口语课",
    "vocabulary-month": "词汇口语课",
    "speaking-course": "口语主课",
    other: "其他来源"
  };
  const sourceLabel = key => COURSE_LABELS[key] || key;

  function sourceCounts() {
    const counts = {};
    entries.forEach(item => {
      const key = Review.sourceKey(item);
      counts[key] = (counts[key] || 0) + 1;
    });
    return counts;
  }

  function refreshSourceFilter() {
    const select = $("#vocabSource");
    if (!select) return;
    const current = sourceFilter;
    const counts = sourceCounts();
    select.innerHTML = `<option value="all">全部来源</option>` + Object.keys(counts).sort().map(key =>
      `<option value="${esc(key)}">${esc(sourceLabel(key))}</option>`
    ).join("");
    select.value = counts[current] || current === "all" ? current : "all";
    if (select.value !== current) sourceFilter = select.value;
  }

  function renderStats() {
    const { due, learning, known, done, doneItems } = stats();
    const dailyTotal = Math.max(new Set([...due, ...doneItems].map(item => String(item.word).toLowerCase())).size, 1);
    const progressLabel = due.length ? `${done} / ${dailyTotal}` : `${done}`;
    $("#statTotal").textContent = entries.length;
    $("#statDone").textContent = done;
    $("#statLearning").textContent = learning.length;
    $("#statKnown").textContent = known.length;
    $("#heroProgressNumber").textContent = progressLabel;
    $("#heroProgressLabel").textContent = due.length ? "今日进度" : "今日完成";
    $("#heroProgressCaption").textContent = due.length
      ? `还剩 ${due.length} 个到期词`
      : done ? "今天的到期词已完成" : "暂时没有到期词";
    $("#heroTitle").textContent = due.length
      ? `今天有 ${due.length} 个词，值得再见一面。`
      : done ? "今天的复习已经完成。" : "今天没有到期词，轻松一点。";
    $("#heroMessage").textContent = due.length
      ? "先不要看答案：尝试说出或写出答案，揭晓后再按真实难度评分。"
      : done ? "下一次到期时，它们会自动回到这里。" : "你可以去任意一课，把不熟的词加入生词本。";
    $("#tabDue").textContent = due.length;
    $("#tabAll").textContent = entries.length;
    $("#tabLearning").textContent = learning.length;
    $("#tabKnown").textContent = known.length;
    const counts = sourceCounts();
    refreshSourceFilter();
    $("#vocabSourceSummary").innerHTML = Object.keys(counts).sort().map(key =>
      `<span>${esc(sourceLabel(key))} <b>${counts[key]}</b></span>`
    ).join("") + ["computer", "daily", "github"].filter(domain => entries.some(item => item.domain === domain)).map(domain =>
      `<span>${{ computer: "计算机", daily: "日常交流", github: "GitHub" }[domain]} <b>${entries.filter(item => item.domain === domain).length}</b></span>`
    ).join("");
  }

  function progressHTML(item) {
    const r = item.reviews ? Math.round(Review.retrievability(item) * 100) : 0;
    return `<div class="vocab-progress adaptive-progress"><span>记忆稳定性 <b>${Number(item.stability || 0).toFixed(1)}天</b></span><span>难度 <b>${Number(item.difficulty || 0).toFixed(1)}/10</b></span><span>当前可回忆率 <b>${r}%</b></span></div>`;
  }

  function ratingButtons(item, mode) {
    const preview = Review.preview(item);
    return `<div class="adaptive-ratings hidden" data-review-ratings>
      <p>根据刚才真实回忆的难度选择：</p>
      <div class="vocab-rating-actions four-ratings">
        <button class="rating-again" data-vocab-review="${esc(item.word)}" data-vocab-rating="again" data-review-mode="${mode}">忘记 <small>${preview.again.label}</small></button>
        <button class="rating-hard" data-vocab-review="${esc(item.word)}" data-vocab-rating="hard" data-review-mode="${mode}">困难 <small>${preview.hard.label}</small></button>
        <button class="rating-good" data-vocab-review="${esc(item.word)}" data-vocab-rating="good" data-review-mode="${mode}">正常 <small>${preview.good.label}</small></button>
        <button class="rating-easy" data-vocab-review="${esc(item.word)}" data-vocab-rating="easy" data-review-mode="${mode}">简单 <small>${preview.easy.label}</small></button>
      </div>
    </div>`;
  }

  function reviewItemHTML(item) {
    const prompt = Review.prompt(item);
    const source = sourceLabel(Review.sourceKey(item));
    const audio = prompt.mode === "audio" ? `<button class="review-audio" data-vocab-speak="${esc(item.speech || item.word)}" data-vocab-audio="${esc(item.audioTerm || "")}">🔊 播放发音</button>` : "";
    return `<article class="vocab-item recall-card is-due" data-review-card="${esc(item.word)}">
      <div class="recall-card-head"><span class="recall-mode">${prompt.label}</span><span class="recall-source">${source}</span><span class="vocab-due due">${timeLabel(item.nextReview)}</span></div>
      <p class="recall-instruction">${prompt.instruction}</p>
      ${audio || `<div class="recall-prompt">${esc(prompt.prompt)}</div>`}
      <label class="recall-input"><span>我的答案（可选）</span><input type="text" autocomplete="off" spellcheck="false" placeholder="先说出来或写下来，再揭晓"></label>
      <button class="reveal-review" data-review-reveal="${esc(item.word)}">揭晓答案</button>
      <div class="recall-answer hidden" data-review-answer>
        <div><span>英文</span><strong>${esc(prompt.answer)}</strong> <button class="vocab-speak" data-vocab-speak="${esc(item.speech || item.word)}" data-vocab-audio="${esc(item.audioTerm || "")}">🔊 发音</button></div>
        <div><span>释义</span><p>${esc(prompt.definition)}</p></div>
        ${(item.examples || []).find(Boolean) ? `<div><span>语境</span><p>${esc((item.examples || []).find(Boolean))}</p></div>` : ""}
      </div>
      ${ratingButtons(item, prompt.mode)}
      ${progressHTML(item)}
    </article>`;
  }

  function itemHTML(item) {
    const due = isDue(item);
    const type = item.type === "term" ? "术语" : item.type === "chunk" ? "词块" : "生词";
    const examples = (item.examples || []).filter(Boolean).slice(0, 2);
    const lessons = (item.lessons || []).filter(Boolean).join(" · ") || "课程词汇";
    const knownLabel = item.status === "known" ? "巩固中" : "学习中";
    return `<article class="vocab-item${item.status === "known" ? " known" : ""}${due ? " is-due" : ""}">
      <div class="vocab-item-head">
        <div>
          <div class="vocab-title-row"><span class="vocab-word">${esc(item.word)}</span><button class="vocab-speak" data-vocab-speak="${esc(item.speech || item.word)}" data-vocab-audio="${esc(item.audioTerm || "")}" aria-label="播放 ${esc(item.word)} 的发音">🔊 发音</button><span class="pop-type ${esc(item.type || "word")}">${type}</span></div>
          ${item.ipa ? `<div class="vocab-ipa">${esc(item.ipa)}</div>` : ""}
        </div>
        <div class="vocab-card-state"><span class="vocab-due ${due ? "due" : ""}">${timeLabel(item.nextReview)}</span><small>${knownLabel}</small></div>
      </div>
      <div class="vocab-def">${esc(item.def || "待补充")}</div>
      ${progressHTML(item)}
      <div class="vocab-actions">
        <details class="vocab-details"><summary>查看笔记</summary><div class="vocab-details-body">
          ${item.note ? `<div class="vocab-note"><span class="pop-label">学习提示</span>${esc(item.note)}</div>` : ""}
          ${examples.map(example => `<div class="vocab-example"><span class="pop-label">本课语境</span>${esc(example)}</div>`).join("")}
          ${item.related?.length ? `<div class="vocab-related"><span class="pop-label">相关搭配</span>${item.related.map(esc).join(" · ")}</div>` : ""}
          <div class="vocab-meta"><span>来自 ${esc(lessons)}</span><span>累计复习 ${item.reviews} 次</span>${item.lastReviewed ? `<span>上次 ${new Intl.DateTimeFormat("zh-CN", { month: "numeric", day: "numeric" }).format(new Date(item.lastReviewed))}</span>` : ""}</div>
          <button class="vocab-remove" data-vocab-remove="${esc(item.word)}">从生词本移除</button>
        </div></details>
      </div>
    </article>`;
  }

  function getVisible() {
    const query = ($("#vocabSearch")?.value || "").trim().toLowerCase();
    const sort = $("#vocabSort")?.value || "due";
    let visible = entries.filter(item => {
      const haystack = [item.word, item.def, item.note, item.lessons?.join(" "), item.examples?.join(" "), item.related?.join(" ")].join(" ").toLowerCase();
      if (query && !haystack.includes(query)) return false;
      if (sourceFilter !== "all" && Review.sourceKey(item) !== sourceFilter) return false;
      if (view === "due") return isDue(item);
      if (view === "learning") return item.status !== "known";
      if (view === "known") return item.status === "known";
      return true;
    });
    visible.sort((a, b) => {
      if (sort === "alpha") return a.word.localeCompare(b.word);
      if (sort === "recent") return (b.createdAt || 0) - (a.createdAt || 0);
      return Number(a.nextReview || 0) - Number(b.nextReview || 0);
    });
    return view === "due" ? visible.slice(0, REVIEW_LIMIT) : visible;
  }

  function render() {
    renderStats();
    document.querySelectorAll("[data-vocab-view]").forEach(tab => {
      const active = tab.dataset.vocabView === view;
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-selected", String(active));
    });
    const visible = getVisible();
    const list = $("#vocabList");
    const headings = { due: "今天复习什么？", all: "全部生词", learning: "正在学习", known: "进入巩固" };
    $("#vocabSectionTitle").textContent = headings[view] || "我的生词";
    $("#vocabSummary").textContent = view === "due"
      ? `${visible.length} 个当前筛选词到期 · 全部来源共 ${stats().due.length} 个 · 每次最多 ${REVIEW_LIMIT} 个`
      : `显示 ${visible.length} / ${entries.length} 个词 · 复习次数只在完成复习后增加`;
    if (!visible.length) {
      const empty = view === "due" ? (entries.length ? "今天没有到期词。可以先回顾“全部生词”，或者等下一次提醒。" : "还没有生词。打开任意一课，点击单词注释里的“加入生词本”。") : "没有符合当前筛选条件的词。";
      list.innerHTML = `<div class="vocab-empty"><div class="vocab-empty-icon">◌</div><strong>${empty}</strong><span>${view === "due" && entries.length ? "间隔复习的关键是按时回来，不需要一次背完。" : ""}</span></div>`;
      return;
    }
    list.innerHTML = `<div class="vocab-list">${visible.map(item => view === "due" ? reviewItemHTML(item) : itemHTML(item)).join("")}</div>`;
  }

  document.addEventListener("click", event => {
    const tab = event.target.closest?.("[data-vocab-view]");
    if (tab) {
      view = tab.dataset.vocabView;
      render();
      return;
    }
    const target = event.target.closest?.("button");
    if (!target) return;
    if (target.dataset.vocabSpeak) {
      speak(target.dataset.vocabSpeak, target.dataset.vocabAudio);
      return;
    }
    if (target.dataset.reviewReveal) {
      const card = target.closest("[data-review-card]");
      card?.querySelector("[data-review-answer]")?.classList.remove("hidden");
      card?.querySelector("[data-review-ratings]")?.classList.remove("hidden");
      target.classList.add("hidden");
      revealedReviews.add(String(target.dataset.reviewReveal).toLowerCase());
      return;
    }
    const word = target.dataset.vocabReview || target.dataset.vocabRemove;
    if (!word) return;
    const item = entries.find(entry => String(entry.word).toLowerCase() === word.toLowerCase());
    if (!item) return;
    if (target.dataset.vocabReview) {
      const timestamp = now();
      const rating = target.dataset.vocabRating || "good";
      const updated = Review.applyRating(item, rating, target.dataset.reviewMode || Review.reviewMode(item), timestamp);
      Object.assign(item, updated);
      save(entries);
      const ratingLabel = { again: "忘记", hard: "困难", good: "正常", easy: "简单" }[rating];
      toast(`${item.word} · ${ratingLabel} · 下一次：${timeLabel(item.nextReview)}`);
      syncCloud();
    } else {
      entries = entries.filter(entry => entry !== item);
      save(entries);
      toast(`已移除 ${item.word}`);
      if (account) {
        api(`/api/vocab?word=${encodeURIComponent(item.word)}`, { method: "DELETE" }).catch(() => toast("本地已移除，云端删除稍后重试"));
      }
    }
    render();
  });

  $("#vocabSearch").addEventListener("input", render);
  $("#vocabSort").addEventListener("change", render);
  $("#vocabSource").addEventListener("change", event => { sourceFilter = event.target.value; render(); });
  $("#accountOpen").addEventListener("click", () => openAuth(account ? "login" : "login"));
  $("#accountLogout").addEventListener("click", async () => {
    try { await api("/api/auth/logout", { method: "POST", body: "{}" }); } catch { /* local mode remains usable */ }
    account = null;
    updateAccountUI();
    toast("已退出云端同步，本设备数据仍保留");
  });
  $("#authClose").addEventListener("click", closeAuth);
  $("#authBackdrop").addEventListener("click", event => { if (event.target.id === "authBackdrop") closeAuth(); });
  $("#authSwitch").addEventListener("click", () => openAuth(authMode === "login" ? "register" : "login"));
  $("#authForm").addEventListener("submit", submitAuth);
  document.addEventListener("keydown", event => { if (event.key === "Escape") closeAuth(); });
  updateAccountUI();
  render();
  loadCloud();
})();
