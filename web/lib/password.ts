import { randomBytes, scrypt as scryptCallback, timingSafeEqual } from "crypto";
import { promisify } from "util";

const scrypt = promisify(scryptCallback);
const HASH_PREFIX = "scrypt";
const KEY_LENGTH = 64;

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16).toString("hex");
  const derivedKey = (await scrypt(password, salt, KEY_LENGTH)) as Buffer;

  return `${HASH_PREFIX}:${salt}:${derivedKey.toString("hex")}`;
}

export async function verifyPassword(
  password: string,
  storedPassword: string,
): Promise<{ isValid: boolean; needsRehash: boolean }> {
  if (!storedPassword.startsWith(`${HASH_PREFIX}:`)) {
    const isValid = password === storedPassword;
    return { isValid, needsRehash: isValid };
  }

  const [, salt, storedKeyHex] = storedPassword.split(":");
  if (!salt || !storedKeyHex) {
    return { isValid: false, needsRehash: false };
  }

  const storedKey = Buffer.from(storedKeyHex, "hex");
  const derivedKey = (await scrypt(password, salt, storedKey.length)) as Buffer;

  if (storedKey.length !== derivedKey.length) {
    return { isValid: false, needsRehash: false };
  }

  return {
    isValid: timingSafeEqual(storedKey, derivedKey),
    needsRehash: false,
  };
}
