import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { completeDesktopAuthRequest } from "@/lib/desktop-auth-handoff";

export async function GET(request: NextRequest) {
  const session = await getServerSession(authOptions);
  const state = request.nextUrl.searchParams.get("state");
  const userId = (session?.user as { id?: string } | undefined)?.id;
  if (!state || !userId) {
    return NextResponse.redirect(new URL("/login?error=DesktopAuth", request.url));
  }

  const handoff = completeDesktopAuthRequest(state, userId);
  if (!handoff) {
    return NextResponse.redirect(
      new URL("/login?error=DesktopAuthExpired", request.url),
    );
  }

  const callback = new URL(handoff.callbackUrl);
  callback.searchParams.set("code", handoff.code);
  callback.searchParams.set("state", state);
  return NextResponse.redirect(callback);
}
