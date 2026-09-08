# APS Remotion 视频工程

本目录是一个独立的 [Remotion](https://www.remotion.dev/) 工程，能够**读取 APS 系统的实时数据（生产计划 / 看板 / 甘特图）自动生成视频报告**。

> 说明：Remotion 基于 React，无法直接在本项目的 Vue 前端（`frontend/`）中运行，
> 因此单独放在 `remotion/` 目录，拥有自己的 `package.json` 与依赖，互不影响。

## 视频内容（`ApsReport` composition，约 22 秒 / 1080p）

依次包含 5 个场景，全部由数据驱动：

1. **标题页** — APS 生产计划日报 + 生成日期
2. **核心指标概览** — 来自 `GET /api/reports/dashboard`（订单数、逾期、产线、准时率等，带数字滚动动画）
3. **排产方案对比** — 来自 `GET /api/reports/order-fulfillment`（各方案准时率条形对比）
4. **生产甘特图** — 来自 `GET /api/scheduling/schedules/{id}`（按产线分行、逾期作业红色高亮）
5. **结尾页** — 汇总数据

## 安装

```bash
cd remotion
npm install
```

## 数据来源与两种渲染方式

### 方式 A：渲染时实时拉取（推荐，需能访问后端）

`Root.tsx` 中的 `calculateMetadata` 会在预览/渲染时自动登录 APS 后端并拉取数据，
失败时（后端未启动 / 网络受限）自动回退到内置示例数据 `src/aps/sample.ts`，
保证视频始终可渲染。

```bash
# 可视化预览（Remotion Studio）
npm run dev

# 直接渲染视频到 out/aps-report.mp4
npm run render
```

可通过环境变量指定后端地址与账户：

```bash
APS_API_BASE=http://localhost:9000/api APS_USER=admin APS_PASSWORD=admin123 npm run render
```

### 方式 B：先抓数据再离线渲染（适合 CI / 受限网络）

```bash
npm run fetch-data     # 抓取后端数据 -> out/aps-data.json
npm run render:file    # 用该 JSON 作为 props 离线渲染
```

### 方式 C：后端「一键生成」接口（推荐给最终用户）

报表页的「一键生成视频报告」按钮，后端提供两套接口：

**同步接口**（简单，会阻塞到渲染完成）
- `GET /api/export/video-report` → 直接返回 MP4

**异步接口（推荐，前端按钮实际使用）** —— 渲染较慢，避免长时间阻塞请求：
- `POST /api/export/video-report/jobs` → 立即返回 `{job_id, status}`
- `GET  /api/export/video-report/jobs/{job_id}` → 轮询状态 `pending|running|done|error`
- `GET  /api/export/video-report/jobs/{job_id}/download` → 渲染完成后下载 MP4

以上接口都直接从数据库组装数据，写入临时 `--props` 文件后调用本工程渲染。

- 该接口通过 `REMOTION_APS_SKIP_FETCH=1` 让 composition **直接使用后端传入的数据**，
  不再回调 API（无需二次登录）。
- 服务器需安装 Node.js，并在 `remotion/` 执行过 `npm install`。
- 相关环境变量（后端读取）：
  - `REMOTION_DIR`：Remotion 工程目录（默认自动定位到仓库内 `remotion/`）
  - `REMOTION_BROWSER_EXECUTABLE`：Chrome Headless Shell 路径（受限网络下必填）
  - `REMOTION_RENDER_TIMEOUT`：渲染超时秒数（默认 600）

> Remotion 只会把以 `REMOTION_` 开头的环境变量注入到 bundle 中，因此上面这些
> 传给 composition 的变量都带 `REMOTION_` 前缀。

## 目录结构

```
src/
  index.ts              入口，注册根组件
  Root.tsx              定义 ApsReport composition（含实时取数）
  aps/
    types.ts            APS 数据类型（对应后端 JSON）
    fetchData.ts        登录并拉取 dashboard / fulfillment / schedule
    sample.ts           离线回退示例数据（对应 seed_demo.py）
    theme.ts            配色 / 字体
    components.tsx       通用动画组件（数字滚动、卡片等）
    scenes.tsx          5 个场景组件
    ApsReport.tsx        场景编排与时长计算
fetch-aps-data.mjs      离线取数脚本
remotion.config.ts      渲染配置
```

## 系统依赖

渲染时 Remotion 依赖 FFmpeg（新版本已内置），若系统缺少 Chrome/Chromium，
首次渲染会自动从 `remotion.media` 下载 Chrome Headless Shell。

> 注意：在受限网络（如 CI / 沙箱）中首次渲染可能因无法访问 `remotion.media`
> 而失败（HTTP 403）。此时可将该域名加入网络出口白名单，或用参数
> `--browser-executable=/path/to/headless_shell` 指向已安装的 Chrome Headless Shell。
> 例如本仓库开发环境：
> `npm run render -- --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`
> 注意：这只影响“渲染”，`npm install` 与 Studio 预览取数逻辑不受影响。
