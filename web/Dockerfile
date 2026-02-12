# Stage 1: Dependencies
FROM node:20-slim AS deps
WORKDIR /app

# Install openssl for Prisma
RUN apt-get update && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Stage 2: Builder
FROM node:20-slim AS builder
WORKDIR /app

# Install openssl for Prisma
RUN apt-get update && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

RUN npm install -g pnpm

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Generate Prisma client
RUN npx prisma generate

# Build Next.js
# Disable type checking during build for speed
ENV NEXT_TELEMETRY_DISABLED=1

# Accept build arguments for public environment variables
ARG NEXT_PUBLIC_API_URL=http://localhost:8001
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN pnpm build

# Stage 3: Runner
FROM node:20-slim AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3006
ENV NEXT_TELEMETRY_DISABLED=1

# Accept build arguments for public environment variables
ARG NEXT_PUBLIC_API_URL=http://localhost:8001
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Install openssl for prisma
RUN apt-get update && apt-get install -y openssl curl && rm -rf /var/lib/apt/lists/*

# Copy built assets
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
# We don't need to copy node_modules if we use standalone output, 
# but usually standalone requires copying static and public.
# However, prisma client might strictly need .prisma/client if not bundled.
# Standalone mode traces dependencies.
# If standalone is not enabled in next.config.ts, we need node_modules.
# Current next.config.ts doesn't show output: 'standalone'.
# So we need to copy node_modules or enable standalone.
# I will assume standard build for now and copy node_modules as before, but filtered.
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/prisma ./prisma

# Create a non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3006

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3006/api/health || curl -f http://localhost:3006 || exit 1

# Run prisma migration and start
CMD npx prisma db push && npm start
