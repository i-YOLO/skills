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
  minimumFontSize?: number;
};

/** Copy into the target Remotion project after build_captions.py emits captions.json. */
export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({
  captionSrc,
  bottomMargin = 86,
  horizontalMargin,
  maxWidth,
  fontSize = 49,
  minimumFontSize = 36,
}) => {
  const [captions, setCaptions] = useState<CaptionCue[] | null>(null);
  const [handle] = useState(() => delayRender("Load caption cues"));
  const frame = useCurrentFrame();
  const {fps, height, width} = useVideoConfig();
  const portrait = height > width;
  const scale = height / (portrait ? 1920 : 1080);
  const resolvedHorizontalMargin = horizontalMargin ?? (portrait ? 70 : 140);
  const resolvedMaxWidth = maxWidth ?? (portrait ? 940 : 1540);

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
  const normalizedText = active.text.replace(/\s+/g, " ").trim();
  const textUnits = Array.from(normalizedText).reduce((total, character) => {
    if (character === " ") {
      return total + 0.35;
    }
    return total + ((character.codePointAt(0) ?? 256) <= 255 ? 0.58 : 1);
  }, 0);
  const widthBudget = (resolvedMaxWidth - 40) * scale;
  const resolvedFontSize = Math.min(
    fontSize * scale,
    Math.max(minimumFontSize * scale, widthBudget / Math.max(1, textUnits)),
  );

  return (
    <AbsoluteFill
      style={{
        zIndex: 20,
        pointerEvents: "none",
        justifyContent: "flex-end",
        alignItems: "center",
        padding: `0 ${resolvedHorizontalMargin * scale}px ${bottomMargin * scale}px`,
      }}
    >
      <div
        style={{
          width: resolvedMaxWidth * scale,
          color: "#FFFFFF",
          fontFamily: '"PingFang SC", "Noto Sans CJK SC", Arial, sans-serif',
          fontSize: resolvedFontSize,
          fontWeight: 700,
          lineHeight: 1.28,
          letterSpacing: 0,
          textAlign: "center",
          whiteSpace: "nowrap",
          WebkitTextStroke: `${10 * scale}px #000000`,
          paintOrder: "stroke fill",
        }}
      >
        {normalizedText}
      </div>
    </AbsoluteFill>
  );
};
