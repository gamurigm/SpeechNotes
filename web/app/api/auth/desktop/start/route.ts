import { NextResponse } from "next/server";
import { registerDesktopAuthRequest } from "@/lib/desktop-auth-handoff";

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }

  const callbackUrl =
    typeof body === "object" && body !== null && "callbackUrl" in body
      ? body.callbackUrl
      : null;
  if (typeof callbackUrl !== "string") {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }

  try {
    return NextResponse.json(registerDesktopAuthRequest(callbackUrl));
  } catch (error) {
    const status =
      error instanceof Error && error.message === "Too many pending desktop sign-ins"
        ? 429
        : 400;
    return NextResponse.json({ error: "Unable to start desktop sign-in" }, { status });
  }
}
