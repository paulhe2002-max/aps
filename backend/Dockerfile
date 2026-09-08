# 直接用本地已有的 aps_claude-backend（内含 Python 环境，基于 Debian）
# 注意：构建上下文为仓库根目录（见 docker-compose.yml: context: .），
# 以便把 remotion/ 视频工程一并打进后端镜像用于「一键生成视频报告」。
FROM aps_claude-backend:latest

# ---------------------------------------------------------------------------
# 1) Node.js —— Remotion 渲染需要（从官方 node 镜像拷贝，避免额外安装源）
# ---------------------------------------------------------------------------
COPY --from=node:22-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:22-bookworm-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && node --version && npm --version

# ---------------------------------------------------------------------------
# 2) Chrome Headless Shell 运行所需的系统库 + 中文字体（否则中文显示为方块）
#    如基础镜像非 Debian/apt 体系，请改用对应包管理器安装等价依赖。
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates fonts-liberation fonts-noto-cjk \
      libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
      libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
      libgbm1 libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0 \
      libx11-6 libxcb1 libxext6 libxi6 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# 3) Python 依赖
# ---------------------------------------------------------------------------
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    -r requirements.txt

# ---------------------------------------------------------------------------
# 4) Remotion 工程：安装依赖并预置 Chrome Headless Shell（构建期下载进镜像，
#    运行期即可离线渲染）。REMOTION_DIR 指向该目录供后端调用。
# ---------------------------------------------------------------------------
WORKDIR /remotion
COPY remotion/package.json remotion/package-lock.json ./
RUN npm ci
COPY remotion/ ./
RUN npx remotion browser ensure
ENV REMOTION_DIR=/remotion

# ---------------------------------------------------------------------------
# 5) 后端源码
# ---------------------------------------------------------------------------
WORKDIR /app
COPY backend/ .
RUN chmod +x start.sh

CMD ["/bin/sh", "start.sh"]
