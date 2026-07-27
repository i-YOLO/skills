import React, {useCallback, useEffect, useState} from "react";
import {
  AbsoluteFill,
  cancelRender,
  continueRender,
  delayRender,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type CaptionCue = {
  text: string;
  startMs: number;
  endMs: number;
};

export type CaptionOverlayProps = {
  captionSrc: string;
  bottomMargin?: number;
  horizontalMargin?: number;
  maxWidth?: number;
  fontSize?: number;
};

/** Copy into the target Remotion project after build_captions.py emits captions.json. */
export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({
  captionSrc,
  bottomMargin = 86,
  horizontalMargin = 140,
  maxWidth = 1540,
  fontSize = 49,
}) => {
  const [captions, setCaptions] = useState<CaptionCue[] | null>(null);
  const [handle] = useState(() => delayRender("Load caption cues"));
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const scale = height / 1080;

  const loadCaptions = useCallback(async () => {
    try {
      const response = await fetch(staticFile(captionSrc));
      if (!response.ok) {
        throw new Error(`Caption JSON returned ${response.status}`);
      }
      setCaptions((await response.json()) as CaptionCue[]);
      continueRender(handle);
    } catch (error) {
      cancelRender(error);
    }
  }, [captionSrc, handle]);

  useEffect(() => {
    void loadCaptions();
  }, [loadCaptions]);

  const currentMs = (frame / fps) * 1000;
  const active = captions?.find((caption) => currentMs >= caption.startMs && currentMs < caption.endMs);
  if (!active) {
    return null;
  }

  return (
    <AbsoluteFill
      style={{
        zIndex: 20,
        pointerEvents: "none",
        justifyContent: "flex-end",
        alignItems: "center",
        padding: `0 ${horizontalMargin * scale}px ${bottomMargin * scale}px`,
      }}
    >
      <div
        style={{
          maxWidth: maxWidth * scale,
          color: "#FFFFFF",
          fontFamily: '"PingFang SC", "Noto Sans CJK SC", Arial, sans-serif',
          fontSize: fontSize * scale,
          fontWeight: 700,
          lineHeight: 1.34,
          letterSpacing: 0.4 * scale,
          textAlign: "center",
          whiteSpace: "pre-line",
          WebkitTextStroke: `${10 * scale}px #000000`,
          paintOrder: "stroke fill",
        }}
      >
        {active.text}
      </div>
    </AbsoluteFill>
  );
};
