import { Composition } from "remotion";
import { ApsReport, totalDurationInFrames } from "./aps/ApsReport";
import { fetchApsData } from "./aps/fetchData";
import { SAMPLE_DATA } from "./aps/sample";

const FPS = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Data-driven APS report video. On render/preview it pulls live data
          from the APS backend (falling back to bundled sample data), so the
          video always reflects the latest planning results. */}
      <Composition
        id="ApsReport"
        component={ApsReport}
        durationInFrames={totalDurationInFrames(FPS)}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{ data: SAMPLE_DATA }}
        calculateMetadata={async () => {
          const data = await fetchApsData();
          return {
            props: { data },
            durationInFrames: totalDurationInFrames(FPS),
          };
        }}
      />
    </>
  );
};
