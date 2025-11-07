FROM node:20-alpine

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

# Manifiestos del FRONTEND (contexto = ./frontend)
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install

# Código del FRONTEND
COPY . .

EXPOSE 3000
# El CMD lo define docker-compose (pnpm dev -p 3000 -H 0.0.0.0)