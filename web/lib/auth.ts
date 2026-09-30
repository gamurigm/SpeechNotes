import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";
import { PrismaAdapter } from "@next-auth/prisma-adapter";
import { prisma } from "@/lib/prisma";
import { getConfig } from "@/config/ConfigManager";
import { hashPassword, verifyPassword } from "@/lib/password";
import { consumeDesktopAuthCode } from "@/lib/desktop-auth-handoff";

// Obtener instancia única de configuración
const config = getConfig();
const authConfig = config.getNextAuthConfig();

// Demo user fallback (used when no DB user exists yet)
const DEMO_USER = {
  id: "demo-user",
  username: "demo",
  email: "demo@speechnotes.app",
  password: "demo123",
  name: "Demo User",
};
const MAX_LOGIN_LENGTH = 254;
const MAX_PASSWORD_LENGTH = 128;
const SESSION_MAX_AGE_SECONDS = 30 * 24 * 60 * 60;

export const authOptions: NextAuthOptions = {
  // PrismaAdapter persists OAuth accounts, users and sessions in dev.db
  adapter: PrismaAdapter(prisma),

  providers: [
    // Google OAuth — set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
      ? [
          GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
            authorization: { params: { prompt: "select_account" } },
          }),
        ]
      : []),

    CredentialsProvider({
      id: "desktop-google",
      name: "Desktop Google",
      credentials: {
        code: { label: "Code", type: "text" },
        state: { label: "State", type: "text" },
      },
      async authorize(credentials) {
        const code = typeof credentials?.code === "string" ? credentials.code : "";
        const state = typeof credentials?.state === "string" ? credentials.state : "";
        if (code.length > 128 || state.length > 128) return null;
        return consumeDesktopAuthCode(code, state);
      },
    }),

    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        const login = (credentials?.username || credentials?.email || "")
          .trim()
          .toLowerCase();
        const password =
          typeof credentials?.password === "string" ? credentials.password : "";

        if (
          !login ||
          !password ||
          login.length > MAX_LOGIN_LENGTH ||
          password.length > MAX_PASSWORD_LENGTH
        ) {
          return null;
        }

        // 1. Look up user in the database first
        const dbUser = await prisma.user.findFirst({
          where: {
            OR: [{ username: login }, { email: login }],
          },
        });

        if (dbUser?.password) {
          const passwordResult = await verifyPassword(password, dbUser.password);
          if (!passwordResult.isValid) {
            return null;
          }

          if (passwordResult.needsRehash) {
            await prisma.user.update({
              where: { id: dbUser.id },
              data: { password: await hashPassword(password) },
            });
          }

          return { id: dbUser.id, email: dbUser.email!, name: dbUser.name };
        }

        // 2. Fallback: demo user (auto-creates it in DB on first login)
        if (
          (login === DEMO_USER.username || login === DEMO_USER.email) &&
          password === DEMO_USER.password
        ) {
          // Ensure demo user exists in DB for session linkage
          const existingDemo = await prisma.user.findFirst({
            where: {
              OR: [{ username: DEMO_USER.username }, { email: DEMO_USER.email }],
            },
          });

          const user = existingDemo
            ? await prisma.user.update({
                where: { id: existingDemo.id },
                data: {
                  username: DEMO_USER.username,
                  email: DEMO_USER.email,
                  name: DEMO_USER.name,
                  password: await hashPassword(DEMO_USER.password),
                },
              })
            : await prisma.user.create({
                data: {
                  id: DEMO_USER.id,
                  username: DEMO_USER.username,
                  email: DEMO_USER.email,
                  name: DEMO_USER.name,
                  password: await hashPassword(DEMO_USER.password),
                },
              });

          return { id: user.id, email: user.email!, name: user.name };
        }

        return null;
      },
    }),
  ],

  session: {
    // "jwt" strategy: session token is a signed JWT stored in a cookie.
    // Works reliably in Electron (no SameSite / DB-cookie issues).
    // The PrismaAdapter still handles user + account rows for Google OAuth.
    strategy: "jwt",
    maxAge: SESSION_MAX_AGE_SECONDS, // 30 days
  },

  pages: {
    signIn: "/login",
  },

  callbacks: {
    // Persist user id into the JWT payload on first sign-in
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },

    // Expose user id inside the session object on the client
    async session({ session, token }) {
      if (session.user && token) {
        (session.user as { id?: string }).id = (token.id ?? token.sub) as string;
      }
      return session;
    },
  },

  secret: authConfig.secret || process.env.NEXTAUTH_SECRET,
};
