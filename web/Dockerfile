# Stage 1: Dependencies
FROM node:22-slim AS deps
WORKDIR /app

# Install openssl for Prisma
RUN apt-get update && apt-get install -y --no-install-recommends openssl && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# Stage 2: Builder
FROM node:22-slim AS builder
WORKDIR /app

# Install openssl for Prisma
RUN apt-get update && apt-get install -y --no-install-recommends openssl && rm -rf /var/lib/apt/lists/*

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Generate Prisma artifacts with the version locked in package-lock.json.
# The SQLite schema is prepared at build time so runtime never downloads code.
RUN DATABASE_URL=file:/app/prisma/dev.db ./node_modules/.bin/prisma generate \
    && DATABASE_URL=file:/app/prisma/dev.db ./node_modules/.bin/prisma db push --skip-generate

# Build Next.js
ENV NEXT_TELEMETRY_DISABLED=1

# Accept build arguments for public environment variables
ARG NEXT_PUBLIC_API_URL=http://localhost:9443
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

# Stage 3: Runner
FROM node:22-slim AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3006
ENV HOSTNAME="0.0.0.0"
ENV NEXT_TELEMETRY_DISABLED=1

# Accept build arguments for public environment variables
ARG NEXT_PUBLIC_API_URL=http://localhost:9443
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Install openssl for prisma and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends openssl curl && rm -rf /var/lib/apt/lists/*

# Copy standalone build output
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=builder /app/package.json ./package.json

# Create a non-root user
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs \
    && mkdir -p /app/.npm \
    && chown -R nextjs:nodejs /app
USER nextjs

ENV npm_config_cache=/app/.npm

# Expose port
EXPOSE 3006

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3006/ || exit 1

# Start the standalone server without installing packages at runtime.
CMD ["node", "server.js"]
