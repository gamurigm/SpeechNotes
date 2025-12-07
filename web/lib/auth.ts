import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";
import { getConfig } from "@/config/ConfigManager";

// Obtener instancia única de configuración
const config = getConfig();
const authConfig = config.getNextAuthConfig();

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        // Demo: hardcoded user for testing
        // In production, query your database here
        const demoUser = {
          id: "1",
          email: "demo@example.com",
          password: "demo123",
          name: "Demo User",
        };

        if (
          credentials.email === demoUser.email &&
          credentials.password === demoUser.password
        ) {
          return {
            id: demoUser.id,
            email: demoUser.email,
            name: demoUser.name,
          };
        }

        return null;
      },
    }),
  ],
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/login",
  },
  secret: authConfig.secret || process.env.NEXTAUTH_SECRET,
};
