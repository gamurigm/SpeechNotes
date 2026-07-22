import { Prisma } from "@prisma/client";
import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { hashPassword } from "@/lib/password";

export const runtime = "nodejs";

const USERNAME_PATTERN = /^[a-z0-9._-]{3,32}$/;
const NAME_PATTERN = /^[\p{L}\p{M}][\p{L}\p{M} .'-]{1,79}$/u;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_EMAIL_LENGTH = 254;
const MIN_PASSWORD_LENGTH = 8;
const MAX_PASSWORD_LENGTH = 128;
const PASSWORD_PATTERN = /^(?=.*[A-Za-z])(?=.*\d).+$/;
const MAX_REQUEST_BYTES = 4096;
const RATE_LIMIT_WINDOW_MS = 60_000;
const MAX_REGISTER_ATTEMPTS = 10;

type RateLimitEntry = {
  count: number;
  resetAt: number;
};

const globalForRegister = globalThis as typeof globalThis & {
  registerAttempts?: Map<string, RateLimitEntry>;
};

const registerAttempts =
  globalForRegister.registerAttempts ?? new Map<string, RateLimitEntry>();

globalForRegister.registerAttempts = registerAttempts;

function normalizeUsername(value: unknown): string {
  return typeof value === "string" ? value.trim().toLowerCase() : "";
}

function normalizeName(value: unknown): string {
  return typeof value === "string" ? value.trim().replace(/\s+/g, " ") : "";
}

function normalizeEmail(value: unknown): string {
  return typeof value === "string" ? value.trim().toLowerCase() : "";
}

function readStringField(body: unknown, field: string): string {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return "";
  }

  const value = (body as Record<string, unknown>)[field];
  return typeof value === "string" ? value : "";
}

function isAllowedOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) {
    return true;
  }

  const allowedOrigins = new Set([new URL(request.url).origin]);
  if (process.env.NEXTAUTH_URL) {
    try {
      allowedOrigins.add(new URL(process.env.NEXTAUTH_URL).origin);
    } catch {
      console.warn("Ignoring invalid NEXTAUTH_URL for register origin check.");
    }
  }

  return allowedOrigins.has(origin);
}

function getRateLimitKey(request: Request): string {
  return (
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    request.headers.get("x-real-ip") ||
    "local"
  );
}

function isRateLimited(request: Request): boolean {
  const now = Date.now();
  const key = getRateLimitKey(request);
  const current = registerAttempts.get(key);

  if (!current || current.resetAt <= now) {
    registerAttempts.set(key, {
      count: 1,
      resetAt: now + RATE_LIMIT_WINDOW_MS,
    });
    return false;
  }

  current.count += 1;
  return current.count > MAX_REGISTER_ATTEMPTS;
}

function isBodyTooLarge(request: Request): boolean {
  const contentLength = request.headers.get("content-length");
  if (!contentLength) {
    return false;
  }

  const bytes = Number(contentLength);
  return Number.isFinite(bytes) && bytes > MAX_REQUEST_BYTES;
}

export async function POST(request: Request) {
  if (!isAllowedOrigin(request)) {
    return NextResponse.json({ error: "Origen no permitido." }, { status: 403 });
  }

  if (isRateLimited(request)) {
    return NextResponse.json(
      { error: "Demasiados intentos de registro. Intenta mas tarde." },
      { status: 429 },
    );
  }

  if (!request.headers.get("content-type")?.includes("application/json")) {
    return NextResponse.json(
      { error: "La solicitud debe ser JSON." },
      { status: 415 },
    );
  }

  if (isBodyTooLarge(request)) {
    return NextResponse.json(
      { error: "La solicitud es demasiado grande." },
      { status: 413 },
    );
  }

  const body = await request.json().catch(() => null);
  const name = normalizeName(readStringField(body, "name"));
  const username = normalizeUsername(readStringField(body, "username"));
  const email = normalizeEmail(readStringField(body, "email"));
  const password = readStringField(body, "password");

  if (!NAME_PATTERN.test(name)) {
    return NextResponse.json(
      {
        error:
          "El nombre debe tener entre 2 y 80 caracteres y solo puede incluir letras, espacios, punto, apostrofe o guion.",
      },
      { status: 400 },
    );
  }

  if (!USERNAME_PATTERN.test(username)) {
    return NextResponse.json(
      {
        error:
          "El usuario debe tener entre 3 y 32 caracteres: letras, numeros, punto, guion o guion bajo.",
      },
      { status: 400 },
    );
  }

  if (email.length > MAX_EMAIL_LENGTH || !EMAIL_PATTERN.test(email)) {
    return NextResponse.json(
      { error: "Ingresa un correo electronico valido." },
      { status: 400 },
    );
  }

  if (
    password.length < MIN_PASSWORD_LENGTH ||
    password.length > MAX_PASSWORD_LENGTH ||
    !PASSWORD_PATTERN.test(password)
  ) {
    return NextResponse.json(
      {
        error:
          "La contrasena debe tener 8 a 128 caracteres e incluir letras y numeros.",
      },
      { status: 400 },
    );
  }

  if (password.toLowerCase() === username) {
    return NextResponse.json(
      { error: "La contrasena no puede ser igual al usuario." },
      { status: 400 },
    );
  }

  const existingUser = await prisma.user.findFirst({
    where: {
      OR: [{ username }, { email }],
    },
    select: { id: true },
  });

  if (existingUser) {
    return NextResponse.json(
      { error: "El usuario o correo electronico ya esta registrado." },
      { status: 409 },
    );
  }

  try {
    await prisma.user.create({
      data: {
        username,
        email,
        name,
        password: await hashPassword(password),
      },
      select: { id: true },
    });

    return NextResponse.json({ ok: true }, { status: 201 });
  } catch (error) {
    if (
      error instanceof Prisma.PrismaClientKnownRequestError &&
      error.code === "P2002"
    ) {
      return NextResponse.json(
        { error: "El usuario o correo electronico ya esta registrado." },
        { status: 409 },
      );
    }

    console.error("Register user failed:", error);
    return NextResponse.json(
      { error: "No se pudo registrar el usuario." },
      { status: 500 },
    );
  }
}
