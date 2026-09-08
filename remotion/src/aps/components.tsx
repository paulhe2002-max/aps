import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "./theme";

// Count-up number that eases to its target value.
export const AnimatedNumber: React.FC<{
  value: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  delay?: number;
  duration?: number;
}> = ({ value, decimals = 0, suffix = "", prefix = "", delay = 0, duration = 40 }) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame - delay, [0, duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const eased = 1 - Math.pow(1 - t, 3);
  const shown = (value * eased).toFixed(decimals);
  return (
    <span>
      {prefix}
      {shown}
      {suffix}
    </span>
  );
};

// Card that springs up into place with a stagger delay.
export const RiseIn: React.FC<{
  delay?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ delay = 0, children, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  const y = interpolate(s, [0, 1], [40, 0]);
  return (
    <div style={{ ...style, opacity: s, transform: `translateY(${y}px)` }}>
      {children}
    </div>
  );
};

export const KpiCard: React.FC<{
  label: string;
  children: React.ReactNode;
  color?: string;
  delay?: number;
}> = ({ label, children, color = theme.accent, delay = 0 }) => {
  return (
    <RiseIn
      delay={delay}
      style={{
        background: theme.card,
        border: `1px solid ${theme.cardBorder}`,
        borderRadius: 20,
        padding: "28px 32px",
        display: "flex",
        flexDirection: "column",
        gap: 10,
        minWidth: 260,
        boxShadow: "0 12px 40px rgba(0,0,0,0.35)",
      }}
    >
      <div style={{ color: theme.textDim, fontSize: 26, fontWeight: 600 }}>
        {label}
      </div>
      <div style={{ color, fontSize: 68, fontWeight: 800, lineHeight: 1 }}>
        {children}
      </div>
    </RiseIn>
  );
};

export const SceneHeading: React.FC<{ kicker: string; title: string }> = ({
  kicker,
  title,
}) => {
  const frame = useCurrentFrame();
  const op = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const x = interpolate(frame, [0, 20], [-30, 0], { extrapolateRight: "clamp" });
  return (
    <div style={{ opacity: op, transform: `translateX(${x}px)`, marginBottom: 44 }}>
      <div
        style={{
          color: theme.accent,
          fontSize: 26,
          fontWeight: 700,
          letterSpacing: 4,
          textTransform: "uppercase",
        }}
      >
        {kicker}
      </div>
      <div style={{ color: theme.text, fontSize: 60, fontWeight: 800, marginTop: 6 }}>
        {title}
      </div>
    </div>
  );
};
