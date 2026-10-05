import {address, ApiError, decode58, Env, jsonBody, requiredDB, timestamp} from "./runtime";
const COOKIE = "quant_wallet_session";
const hash = async (s: string) => Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)))).map(x => x.toString(16).padStart(2, "0")).join("");
const random = () => Array.from(crypto.getRandomValues(new Uint8Array(32))).map(x => x.toString(16).padStart(2, "0")).join("");
export function originFor(request: Request, env: Env): string {
  const origin = new URL(env.APP_ORIGIN || request.url).origin;
  const supplied = request.headers.get("Origin");
  if (supplied !== origin) throw new ApiError(403, "This request must come from the research terminal's own origin.");
  return origin;
}
function sessionToken(request: Request) {return request.headers.get("Cookie")?.split(";").map(x => x.trim()).find(x => x.startsWith(COOKIE + "="))?.slice(COOKIE.length + 1) || "";}
function cookie(token: string, request: Request, maxAge = 86400) {return `${COOKIE}=${token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${maxAge}${new URL(request.url).protocol === "https:" ? "; Secure" : ""}`;}
export async function session(request: Request, env: Env) {
  const token = sessionToken(request); if (!/^[a-f0-9]{64}$/.test(token)) return null;
  return requiredDB(env).prepare("SELECT wallet, expires_at FROM wallet_sessions WHERE token_hash = ? AND expires_at > ?").bind(await hash(token), timestamp()).first<{wallet: string; expires_at: number}>();
}
export async function requireWallet(request: Request, env: Env, wallet?: string) {
  const s = await session(request, env); if (!s || (wallet && s.wallet !== wallet)) throw new ApiError(401, "Sign a login message in Phantom to save this wallet's observations."); return s;
}
export async function authRoute(request: Request, env: Env, path: string): Promise<Response> {
  const db = requiredDB(env);
  if (path === "/api/auth/session" && request.method === "GET") return Response.json({session: await session(request, env)});
  const origin = originFor(request, env);
  if (path === "/api/auth/nonce" && request.method === "POST") {
    const body = await jsonBody(request), wallet = address(String(body.wallet || "")), now = timestamp();
    const count = await db.prepare("SELECT COUNT(*) AS n FROM wallet_nonces WHERE wallet = ? AND issued_at > ?").bind(wallet, now - 60).first<{n: number}>();
    if ((count?.n || 0) >= 5) throw new ApiError(429, "Too many login requests. Wait a minute and retry.");
    const nonce = random(), id = crypto.randomUUID(), issued = new Date(now * 1000).toISOString(), expiry = new Date((now + 300) * 1000).toISOString();
    const message = `${new URL(origin).host} wants you to sign in with your Solana account:\n${wallet}\n\nSign in to Solana Quant Research Lab. This message authorizes a session only.\n\nURI: ${origin}\nVersion: 1\nChain ID: solana:mainnet\nNonce: ${nonce}\nIssued At: ${issued}\nExpiration Time: ${expiry}`;
    await db.batch([
      db.prepare("DELETE FROM wallet_nonces WHERE expires_at < ?").bind(now - 3600),
      db.prepare("DELETE FROM wallet_sessions WHERE expires_at < ?").bind(now),
      db.prepare("INSERT INTO wallet_nonces (id, wallet, nonce, message, origin, issued_at, expires_at, consumed) VALUES (?, ?, ?, ?, ?, ?, ?, 0)").bind(id, wallet, nonce, message, origin, now, now + 300)
    ]);
    return Response.json({id, wallet, message, expires_at: now + 300});
  }
  if (path === "/api/auth/verify" && request.method === "POST") {
    const body = await jsonBody(request), wallet = address(String(body.wallet || ""));
    const challenge = await db.prepare("SELECT * FROM wallet_nonces WHERE id = ? AND wallet = ? AND origin = ? AND consumed = 0 AND expires_at > ?").bind(String(body.id || ""), wallet, origin, timestamp()).first<{id: string; message: string}>();
    if (!challenge) throw new ApiError(401, "Login challenge expired or already used. Request a new message.");
    let valid = false;
    try {
      const encoded = String(body.signature || ""); if (!/^[A-Za-z0-9+/]{86}==$/.test(encoded)) throw new Error();
      const sig = Uint8Array.from(atob(encoded), c => c.charCodeAt(0));
      const key = await crypto.subtle.importKey("raw", Uint8Array.from(decode58(wallet)).buffer, {name: "Ed25519"}, false, ["verify"]);
      valid = await crypto.subtle.verify("Ed25519", key, sig, new TextEncoder().encode(challenge.message));
    } catch {valid = false;}
    // Invalid attempts also consume the nonce; valid requests use an atomic compare-and-set.
    const used = await db.prepare("UPDATE wallet_nonces SET consumed = 1 WHERE id = ? AND consumed = 0 AND expires_at > ?").bind(challenge.id, timestamp()).run();
    if (!valid || used.meta.changes !== 1) throw new ApiError(401, "Message signature could not be verified. Request a new login message.");
    const token = random(), expires = timestamp() + 86400;
    await db.prepare("INSERT INTO wallet_sessions (token_hash, wallet, expires_at) VALUES (?, ?, ?)").bind(await hash(token), wallet, expires).run();
    return Response.json({wallet, expires_at: expires}, {headers: {"Set-Cookie": cookie(token, request)}});
  }
  if (path === "/api/auth/logout" && request.method === "POST") {
    await db.prepare("DELETE FROM wallet_sessions WHERE token_hash = ?").bind(await hash(sessionToken(request))).run();
    return Response.json({ok: true}, {headers: {"Set-Cookie": cookie("", request, 0)}});
  }
  throw new ApiError(404, "Authentication route not found.");
}
