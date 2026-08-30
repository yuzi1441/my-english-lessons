(() => {
  "use strict";

  if (!window.FSRS) throw new Error("FSRS scheduler is not available");

  const DAY = 24 * 60 * 60 * 1000;
  const VERSION = 2;
  const TARGET_RETENTION = 0.9;
  const { Rating, State, createEmptyCard, fsrs, generatorParameters } = window.FSRS;
  const scheduler = fsrs(generatorParameters({
    request_retention: TARGET_RETENTION,
    maximum_interval: 3650,
    enable_fuzz: true,
    enable_short_term: true,
    learning_steps: ["1m", "10m"],
    relearning_steps: ["10m"],
  }));
  const ratingMap = { again: Rating.Again, hard: Rating.Hard, good: Rating.Good, easy: Rating.Easy };
  const legacyRatingMap = { forgot: "again", fuzzy: "hard", remembered: "good" };
  const legacyStability = [0.2, 1, 3, 7, 14, 30];

  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const timestamp = value => {
    const time = value instanceof Date ? value.getTime() : Number(value);
    return Number.isFinite(time) ? time : null;
  };

  function serializeCard(card) {
    return {
      due: timestamp(card.due),
      stability: Number(card.stability) || 0,
      difficulty: Number(card.difficulty) || 0,
      elapsed_days: Number(card.elapsed_days) || 0,
      scheduled_days: Number(card.scheduled_days) || 0,
      learning_steps: Number(card.learning_steps) || 0,
      reps: Number(card.reps) || 0,
      lapses: Number(card.lapses) || 0,
      state: Number(card.state) || State.New,
      last_review: timestamp(card.last_review),
    };
  }

  function cardInput(raw) {
    return {
      due: Number(raw?.due) || Date.now(),
      stability: Number(raw?.stability) || 0,
      difficulty: Number(raw?.difficulty) || 0,
      elapsed_days: Number(raw?.elapsed_days) || 0,
      scheduled_days: Number(raw?.scheduled_days) || 0,
      learning_steps: Number(raw?.learning_steps) || 0,
      reps: Number(raw?.reps) || 0,
      lapses: Number(raw?.lapses) || 0,
      state: Number.isFinite(Number(raw?.state)) ? Number(raw.state) : State.New,
      last_review: Number(raw?.last_review) || null,
    };
  }

  function migrateCard(item, at = Date.now()) {
    if (item?.fsrsCard?.due) return serializeCard(cardInput(item.fsrsCard));
    const reviews = Math.max(0, Number(item?.reviews) || 0);
    if (!reviews) return serializeCard(createEmptyCard(Number(item?.createdAt) || at));
    const stage = clamp(Number(item?.stage) || Math.min(reviews, 5), 0, 5);
    const stability = legacyStability[stage] || Math.max(1, Number(item?.intervalDays) || 1);
    return serializeCard({
      due: new Date(Number(item?.nextReview) || at),
      stability,
      difficulty: clamp(Number(item?.difficulty) || (item?.lastRating === "forgot" ? 7 : item?.lastRating === "fuzzy" ? 6 : 5), 1, 10),
      elapsed_days: 0,
      scheduled_days: Math.round(stability),
      learning_steps: 0,
      reps: reviews,
      lapses: Number(item?.lapses) || 0,
      state: State.Review,
      last_review: new Date(Number(item?.lastReviewed) || Number(item?.updatedAt) || at),
    });
  }

  function normalize(item, at = Date.now()) {
    const fsrsCard = migrateCard(item, at);
    const reviews = Math.max(Number(item?.reviews) || 0, fsrsCard.reps || 0);
    const history = Array.isArray(item?.reviewHistory) ? item.reviewHistory.map(Number).filter(Number.isFinite) : [];
    const reviewLog = Array.isArray(item?.reviewLog) ? item.reviewLog.filter(entry => Number(entry?.at)) : [];
    return {
      ...item,
      reviews,
      stage: Number(item?.stage) || 0,
      nextReview: fsrsCard.due || Number(item?.nextReview) || at,
      reviewHistory: history,
      reviewLog,
      fsrsCard,
      schedulerVersion: VERSION,
      difficulty: Number(fsrsCard.difficulty || item?.difficulty || 0),
      stability: Number(fsrsCard.stability || item?.stability || 0),
      lapses: Number(fsrsCard.lapses || item?.lapses || 0),
      status: fsrsCard.state === State.Review && fsrsCard.stability >= 21 ? "known" : "learning",
    };
  }

  function intervalLabel(due, at = Date.now()) {
    const ms = Math.max(0, Number(due) - Number(at));
    const minutes = Math.max(1, Math.round(ms / 60000));
    if (minutes < 60) return `${minutes}分钟`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours}小时`;
    const days = Math.round(hours / 24);
    if (days < 30) return `${days}天`;
    const months = Math.round(days / 30);
    if (months < 12) return `${months}个月`;
    return `${Math.round(days / 365)}年`;
  }

  function preview(item, at = Date.now()) {
    const normalized = normalize(item, at);
    const outcomes = scheduler.repeat(cardInput(normalized.fsrsCard), new Date(at));
    return Object.fromEntries(Object.entries(ratingMap).map(([key, rating]) => [key, {
      due: timestamp(outcomes[rating].card.due),
      label: intervalLabel(outcomes[rating].card.due, at),
    }]));
  }

  function retrievability(item, at = Date.now()) {
    const normalized = normalize(item, at);
    if (normalized.fsrsCard.state === State.New) return 0;
    return scheduler.get_retrievability(cardInput(normalized.fsrsCard), new Date(at), false);
  }

  function applyRating(item, rawRating, mode, at = Date.now()) {
    const rating = legacyRatingMap[rawRating] || rawRating;
    if (!ratingMap[rating]) throw new Error(`Unsupported review rating: ${rawRating}`);
    const normalized = normalize(item, at);
    const beforeR = retrievability(normalized, at);
    const result = scheduler.next(cardInput(normalized.fsrsCard), new Date(at), ratingMap[rating]);
    const fsrsCard = serializeCard(result.card);
    const next = {
      ...normalized,
      fsrsCard,
      nextReview: fsrsCard.due,
      lastReviewed: at,
      lastRating: rating,
      reviews: fsrsCard.reps,
      lapses: fsrsCard.lapses,
      difficulty: fsrsCard.difficulty,
      stability: fsrsCard.stability,
      status: fsrsCard.state === State.Review && fsrsCard.stability >= 21 ? "known" : "learning",
      updatedAt: at,
    };
    next.reviewHistory = [...normalized.reviewHistory, at].slice(-500);
    next.reviewLog = [...normalized.reviewLog, {
      at,
      rating,
      mode,
      retrievability: Number(beforeR.toFixed(4)),
      stability: Number(fsrsCard.stability.toFixed(4)),
      difficulty: Number(fsrsCard.difficulty.toFixed(4)),
      due: fsrsCard.due,
    }].slice(-500);
    return next;
  }

  // Legacy stamps (pre multi-course) all belong to the main course.
  const LEGACY_COURSE_ALIASES = {
    "vocabulary-month": "speaking-vocab",
    "speaking-course": "speaking-vocab",
    "30 天词汇课": "speaking-vocab"
  };

  function sourceKey(item) {
    if (item?.course) {
      const course = String(item.course);
      return LEGACY_COURSE_ALIASES[course] || course;
    }
    if ((item?.lessons || []).some(value => String(value).includes("词汇强化"))) return "speaking-vocab";
    if ((item?.lessons || []).length) return "speaking-vocab";
    return "other";
  }

  function reviewedToday(item, at = Date.now()) {
    const date = new Date(at);
    const start = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
    const end = start + DAY;
    const times = (item?.reviewLog || []).map(entry => Number(entry?.at)).filter(Number.isFinite);
    if (!times.length) times.push(...(item?.reviewHistory || []).map(Number).filter(Number.isFinite));
    return times.some(time => time >= start && time < end);
  }

  function reviewMode(item) {
    const modes = ["en-zh", "zh-en", "audio", "cloze"];
    return modes[(Number(item?.reviews) || 0) % modes.length];
  }

  function clozeSentence(item) {
    const example = (item?.examples || []).find(Boolean) || "";
    if (!example) return "";
    const escaped = String(item.word || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const result = example.replace(new RegExp(escaped, "ig"), "_____");
    return result === example ? "" : result;
  }

  function prompt(item) {
    let mode = reviewMode(item);
    const cloze = clozeSentence(item);
    if (mode === "audio" && !(item?.audioTerm || item?.speech || item?.word)) mode = "zh-en";
    if (mode === "cloze" && !cloze) mode = "zh-en";
    const prompts = {
      "en-zh": { label: "英 → 中", prompt: item.word, instruction: "先回忆中文意思，再揭晓答案" },
      "zh-en": { label: "中 → 英", prompt: item.def || "待补充释义", instruction: "请说出或写出英文" },
      audio: { label: "听音辨词", prompt: "先听发音，不看拼写回忆单词", instruction: "听完后写出英文" },
      cloze: { label: "语境填空", prompt: cloze, instruction: "根据句子补全英文" },
    };
    return { mode, ...prompts[mode], answer: item.word, definition: item.def || "待补充释义" };
  }

  window.AdaptiveReview = {
    VERSION,
    TARGET_RETENTION,
    Rating,
    State,
    normalize,
    applyRating,
    preview,
    retrievability,
    sourceKey,
    reviewedToday,
    reviewMode,
    prompt,
    intervalLabel,
  };
})();
