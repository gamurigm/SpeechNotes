import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";

export async function proxy(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const { pathname } = req.nextUrl;

  // 1. Permitir siempre rutas de autenticación y estáticos
  if (
    pathname.startsWith("/api/auth") ||
    pathname.startsWith("/_next") ||
    pathname === "/favicon.ico"
  ) {
    return NextResponse.next();
  }

  // 2. Si el usuario va al login y ya tiene sesión, mandar al dashboard
  if (pathname === "/login") {
    if (token) {
      return NextResponse.redirect(new URL("/dashboard", req.url));
    }
    return NextResponse.next();
  }

  // 3. Si NO tiene token y trata de entrar a cualquier otra ruta, redirigir a login
  if (!token) {
    const url = new URL("/login", req.url);
    url.searchParams.set("callbackUrl", encodeURI(req.url));
    return NextResponse.redirect(url);
  }

  // 4. Si tiene token, dejar pasar
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api/auth (API routes for auth)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api/auth|_next/static|_next/image|favicon.ico).*)",
  ],
};
