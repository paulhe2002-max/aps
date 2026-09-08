export const theme = {
  bg: "#0b1220",
  bgAlt: "#111a2e",
  card: "#16223c",
  cardBorder: "#243352",
  text: "#f1f5f9",
  textDim: "#94a3b8",
  accent: "#38bdf8",
  accent2: "#818cf8",
  good: "#34d399",
  warn: "#fbbf24",
  bad: "#f87171",
  font: `"PingFang SC", "Microsoft YaHei", "Noto Sans SC", -apple-system, "Segoe UI", sans-serif`,
};

// Distinct colors for production lines in the Gantt chart.
export const LINE_COLORS = ["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f472b6", "#fb923c"];

export function lineColor(lineId: number): string {
  return LINE_COLORS[(lineId - 1 + LINE_COLORS.length) % LINE_COLORS.length];
}
