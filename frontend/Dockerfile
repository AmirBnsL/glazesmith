# GlazeSmith Frontend — Next.js 15 with standalone output
# Multi-stage build: install deps → build → slim runtime image

# ── Stage 1: Install dependencies ──
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ── Stage 2: Build the Next.js app ──
FROM node:22-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY package.json package-lock.json ./
COPY tsconfig.json next.config.ts postcss.config.mjs components.json ./
COPY src ./src
COPY public ./public

# Inject backend URL at build time — rewrites are baked into the Next.js build output.
# Docker: http://backend:8000 (internal network). Local dev: falls back to 127.0.0.1:8000.
ARG NEXT_PUBLIC_API_URL=http://backend:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build with standalone output for minimal production image
RUN npm run build

# ── Stage 3: Production runner ──
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

# Next.js standalone output includes a minimal server + only required node_modules
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# public/ contains 3D models (.glb) and assets (flower.svg) served at runtime
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
