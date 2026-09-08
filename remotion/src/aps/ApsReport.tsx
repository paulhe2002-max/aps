import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { ApsReportData } from "./types";
import { SAMPLE_DATA } from "./sample";
import {
  TitleScene,
  KpiScene,
  FulfillmentScene,
  GanttScene,
  OutroScene,
} from "./scenes";

export type ApsReportProps = {
  data: ApsReportData;
};

// Scene durations in seconds. Gantt gets a little extra room per line.
export const SCENE_SECONDS = {
  title: 3,
  kpi: 5,
  fulfillment: 4.5,
  gantt: 6,
  outro: 3.5,
};

export function totalDurationInFrames(fps: number): number {
  const total =
    SCENE_SECONDS.title +
    SCENE_SECONDS.kpi +
    SCENE_SECONDS.fulfillment +
    SCENE_SECONDS.gantt +
    SCENE_SECONDS.outro;
  return Math.round(total * fps);
}

export const ApsReport: React.FC<ApsReportProps> = ({ data }) => {
  const { fps } = useVideoConfig();
  const d = data ?? SAMPLE_DATA;
  const f = (s: number) => Math.round(s * fps);

  let cursor = 0;
  const seq = (secs: number) => {
    const from = cursor;
    cursor += f(secs);
    return { from, durationInFrames: f(secs) };
  };

  const title = seq(SCENE_SECONDS.title);
  const kpi = seq(SCENE_SECONDS.kpi);
  const ful = seq(SCENE_SECONDS.fulfillment);
  const gantt = seq(SCENE_SECONDS.gantt);
  const outro = seq(SCENE_SECONDS.outro);

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b1220" }}>
      <Sequence {...title}>
        <TitleScene data={d} />
      </Sequence>
      <Sequence {...kpi}>
        <KpiScene data={d} />
      </Sequence>
      <Sequence {...ful}>
        <FulfillmentScene data={d} />
      </Sequence>
      <Sequence {...gantt}>
        <GanttScene data={d} />
      </Sequence>
      <Sequence {...outro}>
        <OutroScene data={d} />
      </Sequence>
    </AbsoluteFill>
  );
};
