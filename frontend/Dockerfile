# 阶段1: 用本地已有的 node:22-alpine 构建
FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --registry=https://registry.npmmirror.com
COPY . .
RUN npm run build

# 阶段2: 用本地已有的 forecast_claude-frontend（内含 nginx）运行
FROM forecast_claude-frontend:latest

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 7000
