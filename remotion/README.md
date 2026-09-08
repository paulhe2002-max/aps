# APS Remotion 视频工程

本目录是一个独立的 [Remotion](https://www.remotion.dev/) 工程，用于以 React 代码的方式编程生成视频。

> 说明：Remotion 基于 React，无法直接在本项目的 Vue 前端（`frontend/`）中运行，
> 因此单独放在 `remotion/` 目录，拥有自己的 `package.json` 与依赖，互不影响。

## 安装

```bash
cd remotion
npm install
```

## 常用命令

```bash
# 启动 Remotion Studio（浏览器可视化预览/编辑）
npm run dev

# 渲染视频到 out/ 目录
npm run render HelloWorld out/video.mp4

# 升级 Remotion 全套依赖
npm run upgrade
```

## 目录结构

- `src/index.ts` — 入口，注册根组件
- `src/Root.tsx` — 定义所有 Composition（视频）
- `src/HelloWorld.tsx` — 示例视频组件
- `remotion.config.ts` — 渲染配置

## 系统依赖

渲染时 Remotion 依赖 FFmpeg（新版本已内置），若系统缺少 Chrome/Chromium，
首次渲染会自动从 `remotion.media` 下载 Chrome Headless Shell。

> 注意：在受限网络（如 CI / 沙箱）中首次渲染可能因无法访问 `remotion.media`
> 而失败（HTTP 403）。此时可将该域名加入网络出口白名单，或用环境变量
> `REMOTION_CHROME_EXECUTABLE` 指向系统已安装的 Chrome/Chromium。
> 注意：这只影响“渲染”，`npm install` 与 `npm run dev`（Studio 预览）不受影响。
