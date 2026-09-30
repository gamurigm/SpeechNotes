import { createHash, randomBytes } from "node:crypto";
import { prisma } from "@/lib/prisma";

const REQUEST_TTL_MS = 3 * 60 * 1000;
const CODE_TTL_MS = 2 * 60 * 1000;
const MAX_HANDOFFS = 32;

type Handoff = {
  callbackUrl: string;
  expiresAt: number;
  codeHash?: string;
  userId?: string;
};

type HandoffGlobal = typeof globalThis & {
  __speechNotesDesktopAuthHandoffs?: Map<string, Handoff>;
};

const globalWithHandoffs = globalThis as HandoffGlobal;
const handoffs =
  globalWithHandoffs.__speechNotesDesktopAuthHandoffs ??
  (globalWithHandoffs.__speechNotesDesktopAuthHandoffs = new Map());

function hash(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}

function pruneExpired(now = Date.now()): void {
  for (const [stateHash, handoff] of handoffs) {
    if (handoff.expiresAt <= now) handoffs.delete(stateHash);
  }
}

function validateCallbackUrl(value: string): string {
  if (value.length > 512) throw new Error("Invalid desktop callback URL");

  let callback: URL;
  try {
    callback = new URL(value);
  } catch {
    throw new Error("Invalid desktop callback URL");
  }

  const port = Number(callback.port);
  if (
    callback.protocol !== "http:" ||
    callback.hostname !== "127.0.0.1" ||
    !callback.port ||
    !Number.isInteger(port) ||
    port < 1 ||
    port > 65535 ||
    callback.pathname !== "/callback" ||
    callback.username ||
    callback.password ||
    callback.search ||
    callback.hash
  ) {
    throw new Error("Invalid desktop callback URL");
  }

  return callback.toString();
}

export function registerDesktopAuthRequest(
  callbackUrl: string,
): { state: string } {
  const callback = validateCallbackUrl(callbackUrl);
  const now = Date.now();
  pruneExpired(now);
  if (handoffs.size >= MAX_HANDOFFS) {
    throw new Error("Too many pending desktop sign-ins");
  }

  const state = randomBytes(32).toString("base64url");
  handoffs.set(hash(state), {
    callbackUrl: callback,
    expiresAt: now + REQUEST_TTL_MS,
  });
  return { state };
}

export function completeDesktopAuthRequest(
  state: string,
  userId: string,
): { callbackUrl: string; code: string } | null {
  if (!state || !userId) return null;
  const stateHash = hash(state);
  const handoff = handoffs.get(stateHash);
  const now = Date.now();
  if (!handoff || handoff.expiresAt <= now || handoff.codeHash) {
    if (handoff?.expiresAt && handoff.expiresAt <= now) {
      handoffs.delete(stateHash);
    }
    return null;
  }

  const code = randomBytes(32).toString("base64url");
  handoff.codeHash = hash(code);
  handoff.userId = userId;
  handoff.expiresAt = now + CODE_TTL_MS;
  return { callbackUrl: handoff.callbackUrl, code };
}

export async function consumeDesktopAuthCode(
  code: string,
  state: string,
): Promise<{ id: string; email: string | null; name: string | null } | null> {
  if (!code || !state) return null;
  const stateHash = hash(state);
  const handoff = handoffs.get(stateHash);
  if (
    !handoff ||
    handoff.expiresAt <= Date.now() ||
    !handoff.codeHash ||
    handoff.codeHash !== hash(code) ||
    !handoff.userId
  ) {
    return null;
  }

  handoffs.delete(stateHash);
  return prisma.user.findUnique({
    where: { id: handoff.userId },
    select: { id: true, email: true, name: true },
  });
}
