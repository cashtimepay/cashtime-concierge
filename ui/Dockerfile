# Multi-stage build for the Brand UI (Next.js standalone output).
FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

FROM node:22-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# The concierge API URL is baked at build time (NEXT_PUBLIC_*).
ARG NEXT_PUBLIC_CONCIERGE_API
ENV NEXT_PUBLIC_CONCIERGE_API=$NEXT_PUBLIC_CONCIERGE_API
RUN npm run build

FROM node:22-slim AS run
WORKDIR /app
ENV NODE_ENV=production \
    PORT=3000
RUN useradd --uid 1001 --create-home nextjs
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
