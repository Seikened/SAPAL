# Dockerfile (en la RAÍZ del proyecto)
FROM node:20-alpine

WORKDIR /app

# Habilitamos pnpm vía corepack
RUN corepack enable && corepack prepare pnpm@latest --activate

# Instalamos deps usando los manifests de la RAÍZ
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install

# Copiamos el resto del código del frontend que vive en la RAÍZ
COPY . .

# Exponer el puerto de Next (opcional; compose ya mapea)
EXPOSE 3000

# No definimos CMD aquí; lo controla docker-compose con:
# ["pnpm", "dev", "-p", "3000", "-H", "0.0.0.0"]