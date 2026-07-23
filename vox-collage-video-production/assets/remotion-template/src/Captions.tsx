import type {Caption} from "@remotion/captions";
import React from "react";
import {Easing, Sequence, interpolate, useCurrentFrame} from "remotion";

type SafeCaptionArea = {x: number; y: number; width: number; height: number};

export const CaptionLayer: React.FC<{captions: Caption[]; fps: number; area: SafeCaptionArea}> = ({captions, fps, area}) => (
  <>
    {captions.map((caption, index) => {
      const from = Math.round((caption.startMs / 1000) * fps);
      const durationInFrames = Math.max(1, Math.ceil(((caption.endMs - caption.startMs) / 1000) * fps));
      return (
        <Sequence key={`${caption.startMs}-${index}`} from={from} durationInFrames={durationInFrames} layout="none">
          <CaptionCard text={caption.text} area={area} />
        </Sequence>
      );
    })}
  </>
);

const CaptionCard: React.FC<{text: string; area: SafeCaptionArea}> = ({text, area}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 5, 10], [0, 1, 1], {extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1)});
  const translateY = interpolate(frame, [0, 8], [Math.max(14, area.height * 0.14), 0], {extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1)});
  return (
    <div style={{position: "absolute", left: area.x, top: area.y, width: area.width, height: area.height, display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, opacity, transform: `translateY(${translateY}px)`, pointerEvents: "none"}}>
      <div style={{maxWidth: "94%", padding: "0.32em 0.72em 0.38em", background: "rgba(13,45,86,0.94)", color: "#FFF7E6", borderLeft: "0.18em solid #C83D2E", boxShadow: "0.18em 0.18em 0 rgba(13,45,86,0.22)", fontFamily: '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif', fontSize: Math.max(26, area.height * 0.26), fontWeight: 800, lineHeight: 1.28, textAlign: "center", whiteSpace: "pre-wrap"}}>
        {text}
      </div>
    </div>
  );
};
