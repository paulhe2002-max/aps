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
        calculateMetadata={async ({ props }) => {
          // When the caller supplies data via input props (e.g. the backend
          // "one-click" endpoint sets REMOTION_APS_SKIP_FETCH=1 and passes
          // --props), use it as-is. Otherwise pull live data from the backend.
          // Note: Remotion only exposes env vars prefixed with REMOTION_ to the
          // bundle, so the flag must carry that prefix.
          const skipFetch =
            typeof process !== "undefined" &&
            process.env?.REMOTION_APS_SKIP_FETCH === "1";
          const data = skipFetch ? props.data : await fetchApsData();
          return {
            props: { data },
            durationInFrames: totalDurationInFrames(FPS),
          };
        }}
      />
    </>
  );
};
