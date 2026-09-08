import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ApsReportData, ScheduleItem } from "./types";
import { theme, lineColor } from "./theme";
import { AnimatedNumber, KpiCard, RiseIn, SceneHeading } from "./components";

const Bg: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(1200px 600px at 20% 0%, ${theme.bgAlt}, ${theme.bg})`,
      fontFamily: theme.font,
      padding: 90,
    }}
  >
    {children}
  </AbsoluteFill>
);

// ---------- Scene 1: Title ----------
export const TitleScene: React.FC<{ data: ApsReportData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 200 } });
  const scale = interpolate(s, [0, 1], [0.85, 1]);
  const sub = interpolate(frame, [15, 40], [0, 1], { extrapolateRight: "clamp" });
  const date = new Date(data.generatedAt).toLocaleDateString("zh-CN");
  return (
    <Bg>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ transform: `scale(${scale})`, opacity: s, textAlign: "center" }}>
          <div style={{ color: theme.accent, fontSize: 34, fontWeight: 700, letterSpacing: 8 }}>
            APS · 高级计划与排产
          </div>
          <div style={{ color: theme.text, fontSize: 130, fontWeight: 900, marginTop: 12 }}>
            生产计划日报
          </div>
        </div>
        <div style={{ opacity: sub, color: theme.textDim, fontSize: 36, marginTop: 30 }}>
          生成日期 {date} · 数据来源：APS 系统
        </div>
      </AbsoluteFill>
    </Bg>
  );
};

// ---------- Scene 2: Dashboard KPIs ----------
export const KpiScene: React.FC<{ data: ApsReportData }> = ({ data }) => {
  const d = data.dashboard;
  return (
    <Bg>
      <SceneHeading kicker="Dashboard" title="核心指标概览" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 30 }}>
        <KpiCard label="订单总数" delay={0}>
          <AnimatedNumber value={d.total_orders} />
        </KpiCard>
        <KpiCard label="在制订单" delay={6} color={theme.accent2}>
          <AnimatedNumber value={d.open_orders} />
        </KpiCard>
        <KpiCard label="逾期订单" delay={12} color={d.overdue_orders > 0 ? theme.bad : theme.good}>
          <AnimatedNumber value={d.overdue_orders} />
        </KpiCard>
        <KpiCard label="活跃产线" delay={18} color={theme.good}>
          <AnimatedNumber value={d.total_production_lines} />
        </KpiCard>
        <KpiCard label="产能超载周期" delay={24} color={d.overloaded_capacity_periods > 0 ? theme.warn : theme.good}>
          <AnimatedNumber value={d.overloaded_capacity_periods} />
        </KpiCard>
        <KpiCard label="准时交付率" delay={30} color={theme.good}>
          <AnimatedNumber value={d.active_schedule_on_time_rate} decimals={1} suffix="%" />
        </KpiCard>
      </div>
      <RiseIn delay={38} style={{ marginTop: 46, color: theme.textDim, fontSize: 30 }}>
        当前活跃排产方案：
        <span style={{ color: theme.text, fontWeight: 700 }}>
          {d.active_schedule ?? "暂无"}
        </span>
      </RiseIn>
    </Bg>
  );
};

// ---------- Scene 3: Schedule comparison ----------
export const FulfillmentScene: React.FC<{ data: ApsReportData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const rows = data.fulfillment.slice(0, 4);
  const maxRate = 100;
  return (
    <Bg>
      <SceneHeading kicker="Order Fulfillment" title="排产方案对比" />
      <div style={{ display: "flex", flexDirection: "column", gap: 26 }}>
        {rows.map((r, i) => {
          const grow = interpolate(frame - i * 8, [0, 30], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const w = (r.on_time_rate / maxRate) * 100 * grow;
          return (
            <RiseIn key={r.schedule_id} delay={i * 8}>
              <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
                <div style={{ width: 380, color: theme.text, fontSize: 34, fontWeight: 700 }}>
                  {r.schedule_name}
                  <span style={{ color: theme.textDim, fontSize: 24, marginLeft: 12 }}>
                    {r.algorithm}
                  </span>
                </div>
                <div
                  style={{
                    flex: 1,
                    height: 54,
                    background: theme.card,
                    borderRadius: 12,
                    overflow: "hidden",
                    border: `1px solid ${theme.cardBorder}`,
                  }}
                >
                  <div
                    style={{
                      width: `${w}%`,
                      height: "100%",
                      background: `linear-gradient(90deg, ${theme.accent2}, ${theme.accent})`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "flex-end",
                      paddingRight: 16,
                      color: "#0b1220",
                      fontWeight: 800,
                      fontSize: 28,
                    }}
                  >
                    {(r.on_time_rate * grow).toFixed(1)}%
                  </div>
                </div>
                <div style={{ width: 210, color: theme.textDim, fontSize: 26, textAlign: "right" }}>
                  利用率 {r.utilization_rate.toFixed(1)}%
                </div>
              </div>
            </RiseIn>
          );
        })}
      </div>
    </Bg>
  );
};

// ---------- Scene 4: Gantt ----------
function parse(dt: string): number {
  return new Date(dt).getTime();
}

export const GanttScene: React.FC<{ data: ApsReportData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const sched = data.schedule;
  if (!sched || sched.items.length === 0) {
    return (
      <Bg>
        <SceneHeading kicker="Schedule" title="生产甘特图" />
        <div style={{ color: theme.textDim, fontSize: 40 }}>暂无排产明细数据</div>
      </Bg>
    );
  }

  const items = [...sched.items].sort((a, b) => parse(a.start_datetime) - parse(b.start_datetime));
  const t0 = Math.min(...items.map((i) => parse(i.start_datetime)));
  const t1 = Math.max(...items.map((i) => parse(i.end_datetime)));
  const span = Math.max(t1 - t0, 1);

  // Group rows by production line.
  const lines = Array.from(new Set(items.map((i) => i.line_id)));
  const rowH = 70;
  const gap = 18;
  const trackLeft = 360;

  return (
    <Bg>
      <SceneHeading kicker="Schedule" title={`生产甘特图 · ${sched.name}`} />
      <div style={{ display: "flex", flexDirection: "column", gap }}>
        {lines.map((lid, rowIdx) => {
          const lineItems = items.filter((i) => i.line_id === lid);
          const name = lineItems[0]?.line_name ?? `产线 ${lid}`;
          return (
            <div key={lid} style={{ display: "flex", alignItems: "center", height: rowH }}>
              <div style={{ width: trackLeft, color: theme.text, fontSize: 30, fontWeight: 700, paddingRight: 20 }}>
                {name}
              </div>
              <div style={{ position: "relative", flex: 1, height: rowH, background: theme.card, borderRadius: 10, border: `1px solid ${theme.cardBorder}` }}>
                {lineItems.map((it: ScheduleItem, i) => {
                  const left = ((parse(it.start_datetime) - t0) / span) * 100;
                  const width = ((parse(it.end_datetime) - parse(it.start_datetime)) / span) * 100;
                  const appearAt = (rowIdx * lineItems.length + i) * 6;
                  const grow = interpolate(frame - appearAt, [0, 22], [0, 1], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  });
                  const col = lineColor(lid);
                  return (
                    <div
                      key={it.id}
                      title={it.order_no}
                      style={{
                        position: "absolute",
                        left: `${left}%`,
                        top: 8,
                        height: rowH - 16,
                        width: `${width * grow}%`,
                        background: it.is_on_time ? col : theme.bad,
                        borderRadius: 8,
                        display: "flex",
                        alignItems: "center",
                        paddingLeft: 12,
                        color: "#0b1220",
                        fontSize: 20,
                        fontWeight: 800,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        opacity: grow,
                        boxShadow: "0 6px 18px rgba(0,0,0,0.35)",
                      }}
                    >
                      {it.order_no} · {it.planned_quantity}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ display: "flex", gap: 40, marginTop: 44, color: theme.textDim, fontSize: 26 }}>
        <span>制程周期 {sched.makespan_days.toFixed(1)} 天</span>
        <span>准时率 {sched.on_time_rate.toFixed(1)}%</span>
        <span>总成本 ¥{sched.total_cost.toLocaleString()}</span>
        <span style={{ color: theme.bad }}>■ 逾期作业</span>
      </div>
    </Bg>
  );
};

// ---------- Scene 5: Outro ----------
export const OutroScene: React.FC<{ data: ApsReportData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 200 } });
  return (
    <Bg>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center" }}>
        <div style={{ opacity: s, transform: `scale(${interpolate(s, [0, 1], [0.9, 1])})` }}>
          <div style={{ color: theme.text, fontSize: 90, fontWeight: 900 }}>
            数据驱动 · 智能排产
          </div>
          <div style={{ color: theme.textDim, fontSize: 36, marginTop: 24 }}>
            由 APS 系统 + Remotion 自动生成
          </div>
          <div style={{ color: theme.accent, fontSize: 30, marginTop: 40 }}>
            准时交付率 {data.dashboard.active_schedule_on_time_rate.toFixed(1)}% · {data.dashboard.total_production_lines} 条产线协同
          </div>
        </div>
      </AbsoluteFill>
    </Bg>
  );
};
