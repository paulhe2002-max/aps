# 阶段1: 构建
FROM registry.cn-hangzhou.aliyuncs.com/library/node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./

# 换 npm 为阿里云镜像
RUN npm ci --registry=https://registry.npmmirror.com

COPY . .
RUN npm run build

# 阶段2: 部署
FROM registry.cn-hangzhou.aliyuncs.com/library/nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 7000
