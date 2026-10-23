# ==========================================
# Multi-stage Dockerfile para Frontend React
# ==========================================

# Estágio de Desenvolvimento (Vite Dev Server)
FROM node:20.18-alpine3.20 AS development

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]

# Estágio de Build para Produção
FROM node:20.18-alpine3.20 AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Estágio de Produção com Nginx Não-Privilegiado
FROM nginxinc/nginx-unprivileged:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
