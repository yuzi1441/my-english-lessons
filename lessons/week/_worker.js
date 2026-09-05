const SESSION_COOKIE = "ir_session";
const SESSION_DAYS = 30;
const PASSWORD_ITERATIONS = 100000;
const encoder = new TextEncoder();

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extraHeaders }
  });
}

function error(message, status = 400) {
  return json({ error: message }, status);
}

function bytesToBase64Url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function base64UrlToBytes(value) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - normalized.length % 4) % 4);
  const binary = atob(padded);
  return Uint8Array.from(binary, char => char.charCodeAt(0));
}

async function sha256(value) {
  return bytesToBase64Url(new Uint8Array(await crypto.subtle.digest("SHA-256", encoder.encode(value))));
}

async function hashPassword(password, salt) {
  const key = await crypto.subtle.importKey("raw", encoder.encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", salt: base64UrlToBytes(salt), iterations: PASSWORD_ITERATIONS, hash: "SHA-256" }, key, 256);
  return bytesToBase64Url(new Uint8Array(bits));
}

function safeEqual(a, b) {
  if (a.length !== b.length) return false;
  let different = 0;
  for (let i = 0; i < a.length; i += 1) different |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return different === 0;
}

function cookieValue(request, name) {
  const header = request.headers.get("cookie") || "";
  const item = header.split(";").map(part => part.trim()).find(part => part.startsWith(`${name}=`));
  return item ? decodeURIComponent(item.slice(name.length + 1)) : "";
}

function sessionCookie(token, maxAge = SESSION_DAYS * 24 * 60 * 60) {
  return `${SESSION_COOKIE}=${encodeURIComponent(token)}; Path=/; Max-Age=${maxAge}; HttpOnly; Secure; SameSite=Lax`;
}

async function createSession(env, userId) {
  const token = bytesToBase64Url(crypto.getRandomValues(new Uint8Array(32)));
  const createdAt = Date.now();
  const expiresAt = createdAt + SESSION_DAYS * 24 * 60 * 60 * 1000;
  await env.DB.prepare("INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)")
    .bind(await sha256(token), userId, createdAt, expiresAt).run();
  return { token, expiresAt };
}

async function currentUser(request, env) {
  const token = cookieValue(request, SESSION_COOKIE);
  if (!token) return null;
  const row = await env.DB.prepare(
    "SELECT users.id, users.username, sessions.token_hash, sessions.expires_at FROM sessions JOIN users ON users.id = sessions.user_id WHERE sessions.token_hash = ? LIMIT 1"
  ).bind(await sha256(token)).first();
  if (!row || Number(row.expires_at) <= Date.now()) {
    if (row) await env.DB.prepare("DELETE FROM sessions WHERE token_hash = ?").bind(row.token_hash).run();
    return null;
  }
  return { id: row.id, username: row.username, tokenHash: row.token_hash };
}

async function requestJSON(request, maxBytes = 700000) {
  const contentLength = Number(request.headers.get("content-length") || 0);
  if (contentLength > maxBytes) throw new Error("请求内容过大");
  const text = await request.text();
  if (text.length > maxBytes) throw new Error("请求内容过大");
  try { return JSON.parse(text || "{}"); } catch { throw new Error("请求格式不正确"); }
}

function normalizeUserName(value) {
  return String(value || "").trim();
}

function validUserName(username) {
  return /^[a-zA-Z0-9_\u4e00-\u9fff-]{2,32}$/.test(username);
}

function normalizeItems(items) {
  if (!Array.isArray(items)) return [];
  return items.slice(0, 1000).map(item => {
    const word = String(item?.word || "").trim();
    if (!word) return null;
    const updatedAt = Number(item.updatedAt) || Number(item.lastSeen) || Number(item.createdAt) || Date.now();
    return { ...item, word, updatedAt, wordKey: word.toLowerCase() };
  }).filter(Boolean);
}

async function allVocabulary(env, userId) {
  const result = await env.DB.prepare("SELECT payload FROM vocabulary WHERE user_id = ? ORDER BY updated_at DESC")
    .bind(userId).all();
  return (result.results || []).map(row => {
    try { return JSON.parse(row.payload); } catch { return null; }
  }).filter(Boolean);
}

async function syncVocabulary(request, env, user) {
  const body = await requestJSON(request);
  const items = normalizeItems(body.items);
  for (const item of items) {
    const existing = await env.DB.prepare("SELECT payload, updated_at FROM vocabulary WHERE user_id = ? AND word_key = ?")
      .bind(user.id, item.wordKey).first();
    const incomingUpdated = Number(item.updatedAt) || Date.now();
    if (!existing || incomingUpdated >= Number(existing.updated_at)) {
      const payload = { ...item };
      delete payload.wordKey;
      await env.DB.prepare(
        "INSERT INTO vocabulary (user_id, word_key, payload, updated_at) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, word_key) DO UPDATE SET payload = excluded.payload, updated_at = excluded.updated_at"
      ).bind(user.id, item.wordKey, JSON.stringify(payload), incomingUpdated).run();
    }
  }
  return json({ ok: true, user: { username: user.username }, items: await allVocabulary(env, user.id) });
}

async function authRegister(request, env) {
  const body = await requestJSON(request, 20000);
  const username = normalizeUserName(body.username);
  const password = String(body.password || "");
  if (!validUserName(username)) return error("用户名需为 2–32 位中文、字母、数字、下划线或短横线");
  if (password.length < 8 || password.length > 128) return error("密码需为 8–128 位");
  const salt = bytesToBase64Url(crypto.getRandomValues(new Uint8Array(16)));
  const userId = crypto.randomUUID();
  try {
    await env.DB.prepare("INSERT INTO users (id, username, password_hash, password_salt, created_at) VALUES (?, ?, ?, ?, ?)")
      .bind(userId, username, await hashPassword(password, salt), salt, Date.now()).run();
  } catch (err) {
    if (String(err).toLowerCase().includes("unique")) return error("这个用户名已经注册了", 409);
    throw err;
  }
  const session = await createSession(env, userId);
  return json({ ok: true, user: { username } }, 201, { "set-cookie": sessionCookie(session.token) });
}

async function authLogin(request, env) {
  const body = await requestJSON(request, 20000);
  const username = normalizeUserName(body.username);
  const password = String(body.password || "");
  const user = await env.DB.prepare("SELECT id, username, password_hash, password_salt FROM users WHERE username = ? COLLATE NOCASE LIMIT 1")
    .bind(username).first();
  if (!user || !safeEqual(await hashPassword(password, user.password_salt), user.password_hash)) return error("用户名或密码不正确", 401);
  const session = await createSession(env, user.id);
  return json({ ok: true, user: { username: user.username } }, 200, { "set-cookie": sessionCookie(session.token) });
}

async function api(request, env) {
  if (!env.DB) return error("云端同步服务尚未连接", 503);
  const url = new URL(request.url);
  const path = url.pathname;
  if (request.method === "POST" && path === "/api/auth/register") return authRegister(request, env);
  if (request.method === "POST" && path === "/api/auth/login") return authLogin(request, env);
  if (path === "/api/auth/logout" && (request.method === "POST" || request.method === "GET")) {
    const token = cookieValue(request, SESSION_COOKIE);
    if (token) await env.DB.prepare("DELETE FROM sessions WHERE token_hash = ?").bind(await sha256(token)).run();
    return json({ ok: true }, 200, { "set-cookie": sessionCookie("", 0) });
  }
  const user = await currentUser(request, env);
  if (path === "/api/session" && request.method === "GET") return json({ authenticated: !!user, user: user ? { username: user.username } : null });
  if (!user) return error("请先登录同步账号", 401);
  if (path === "/api/vocab" && request.method === "GET") return json({ ok: true, user: { username: user.username }, items: await allVocabulary(env, user.id) });
  if (path === "/api/vocab" && request.method === "DELETE") {
    const word = String(url.searchParams.get("word") || "").trim().toLowerCase();
    if (!word) return error("缺少要移除的单词");
    await env.DB.prepare("DELETE FROM vocabulary WHERE user_id = ? AND word_key = ?").bind(user.id, word).run();
    return json({ ok: true, items: await allVocabulary(env, user.id) });
  }
  if (path === "/api/vocab/sync" && request.method === "POST") return syncVocabulary(request, env, user);
  return error("找不到这个同步接口", 404);
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) {
      try { return await api(request, env); } catch (err) {
        console.error("sync_api_error", err instanceof Error ? err.stack : String(err));
        return error("服务暂时不可用，请稍后重试", 500);
      }
    }
    return env.ASSETS.fetch(request);
  }
};
