import React from "react";
import {Easing, interpolate, useCurrentFrame} from "remotion";

export type PatternTone = "mint" | "orange" | "lavender" | "red";

export type PatternPalette = {
  ink: string;
  surface: string;
  surface2: string;
  text: string;
  muted: string;
  mint: string;
  orange: string;
  lavender: string;
  red: string;
};

export const defaultPatternPalette: PatternPalette = {
  ink: "#070B16",
  surface: "#10182C",
  surface2: "#17233D",
  text: "#F5F8FF",
  muted: "#A7B5D1",
  mint: "#61F4C3",
  orange: "#FFB86B",
  lavender: "#A7A0FF",
  red: "#FF7A95",
};

const easeOut = Easing.bezier(0.16, 1, 0.3, 1);

const enter = (frame: number, start: number, fromY = 26) => ({
  opacity: interpolate(frame, [start, start + 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  }),
  translate: `0px ${interpolate(frame, [start, start + 20], [fromY, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeOut,
  })}px`,
});

const PatternCard: React.FC<React.PropsWithChildren<{
  palette: PatternPalette;
  tone?: PatternTone;
  style?: React.CSSProperties;
}>> = ({children, palette, tone = "mint", style}) => (
  <div style={{
    background: "rgba(18, 29, 52, 0.86)",
    border: `1px solid ${palette[tone]}55`,
    boxShadow: `0 18px 60px ${palette[tone]}18`,
    borderRadius: 30,
    padding: "28px 30px",
    ...style,
  }}>
    {children}
  </div>
);

export const SequentialChips: React.FC<{
  items: string[];
  accent?: PatternTone;
  startAt?: number;
  palette?: PatternPalette;
}> = ({items, accent = "mint", startAt = 0, palette = defaultPatternPalette}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: "flex", gap: 10, flexWrap: "wrap"}}>
      {items.map((item, index) => (
        <div key={item} style={{
          color: palette.text,
          border: `1px solid ${palette[accent]}88`,
          background: `${palette[accent]}18`,
          borderRadius: 14,
          padding: "10px 13px",
          fontSize: 30,
          fontWeight: 800,
          lineHeight: 1.1,
          ...enter(frame, startAt + index * 13, 22),
        }}>
          {item}
        </div>
      ))}
    </div>
  );
};

export const PipelineFlow: React.FC<{
  steps: string[];
  finalTone?: PatternTone;
  palette?: PatternPalette;
}> = ({steps, finalTone = "mint", palette = defaultPatternPalette}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: "flex", alignItems: "center", gap: 16, width: "100%"}}>
      {steps.map((step, index) => (
        <React.Fragment key={step}>
          <PatternCard
            palette={palette}
            tone={index === steps.length - 1 ? finalTone : "lavender"}
            style={{
              padding: "28px 24px",
              flex: 1,
              minHeight: 164,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              textAlign: "center",
              ...enter(frame, index * 12, 0),
              scale: interpolate(frame, [index * 12, index * 12 + 22], [0.86, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: easeOut,
              }),
            }}
          >
            <div style={{color: palette.text, fontSize: 35, fontWeight: 800, lineHeight: 1.3}}>{step}</div>
          </PatternCard>
          {index < steps.length - 1 ? <div style={{
            color: palette.mint,
            fontSize: 40,
            opacity: interpolate(frame, [index * 12 + 16, index * 12 + 30], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}>→</div> : null}
        </React.Fragment>
      ))}
    </div>
  );
};

export type ContrastSide = {
  eyebrow: string;
  title: string;
  detail: string[];
  tone?: PatternTone;
};

export const ContrastCards: React.FC<{
  left: ContrastSide;
  right: ContrastSide;
  palette?: PatternPalette;
}> = ({left, right, palette = defaultPatternPalette}) => {
  const frame = useCurrentFrame();
  const sides = [left, right];
  return (
    <div style={{display: "grid", gridTemplateColumns: "1fr 1fr", gap: 26, width: "100%", maxWidth: 1500, margin: 0}}>
      {sides.map((side, index) => {
        const tone = side.tone ?? (index === 0 ? "red" : "mint");
        return (
          <PatternCard key={side.eyebrow} palette={palette} tone={tone} style={{
            minHeight: 250,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            opacity: interpolate(frame, [10 + index * 12, 32 + index * 14], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: easeOut,
            }),
            translate: `${interpolate(frame, [10 + index * 12, 32 + index * 14], [index === 0 ? -60 : 60, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: easeOut,
            })}px 0px`,
          }}>
            <div style={{color: palette[tone], fontSize: 30, fontWeight: 900, letterSpacing: 2}}>{side.eyebrow}</div>
            <div style={{color: palette.text, fontSize: 48, fontWeight: 800, lineHeight: 1.25}}>{side.title}</div>
            <div style={{color: palette.muted, fontSize: 29, lineHeight: 1.38}}>{side.detail.join("\n")}</div>
            <div style={{height: 10, borderRadius: 8, background: palette[tone], width: `${interpolate(frame, [20 + index * 16, 100 + index * 16], [20, 100], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })}%`}} />
          </PatternCard>
        );
      })}
    </div>
  );
};

export const CycleFlow: React.FC<{
  steps: string[];
  activeIndex?: number;
  palette?: PatternPalette;
}> = ({steps, activeIndex = 0, palette = defaultPatternPalette}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: "flex", alignItems: "center", justifyContent: "flex-start", gap: 24, width: "100%", maxWidth: 1260, margin: 0}}>
      {steps.map((step, index) => (
        <React.Fragment key={step}>
          <div style={{
            width: 168,
            height: 168,
            borderRadius: 999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: palette.ink,
            background: index === activeIndex ? palette.mint : palette.text,
            fontSize: 35,
            fontWeight: 900,
            boxShadow: index === activeIndex ? `0 0 36px ${palette.mint}55` : undefined,
            ...enter(frame, index * 13, 0),
            scale: interpolate(frame, [index * 13, index * 13 + 22], [0.7, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: easeOut,
            }),
          }}>{step}</div>
          {index < steps.length - 1 ? <div style={{
            color: palette.mint,
            fontSize: 40,
            opacity: interpolate(frame, [index * 13 + 18, index * 13 + 32], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}>→</div> : null}
        </React.Fragment>
      ))}
    </div>
  );
};

export type LayerColumn = {
  label: string;
  tags: string[];
  tone: PatternTone;
};

export const LayerCards: React.FC<{
  columns: LayerColumn[];
  palette?: PatternPalette;
}> = ({columns, palette = defaultPatternPalette}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: "grid", gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr))`, gap: 22, width: "100%", maxWidth: 1500, margin: 0}}>
      {columns.map((column, index) => (
        <PatternCard key={column.label} palette={palette} tone={column.tone} style={{
          minHeight: 248,
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          ...enter(frame, index * 14, 60),
        }}>
          <div style={{color: palette[column.tone], fontSize: 30, fontWeight: 900, letterSpacing: 2}}>{column.label}</div>
          <SequentialChips items={column.tags} accent={column.tone} startAt={index * 14 + 20} palette={palette} />
        </PatternCard>
      ))}
    </div>
  );
};

export const TimelineAnchor: React.FC<{
  steps: string[];
  activeIndex?: number;
  palette?: PatternPalette;
}> = ({steps, activeIndex = 1, palette = defaultPatternPalette}) => {
  const frame = useCurrentFrame();
  const positions = steps.map((_, index) => 18 + index * (60 / Math.max(1, steps.length - 1)));
  return (
    <div style={{display: "flex", flexDirection: "column", gap: 32, width: "100%", maxWidth: 1480, margin: 0}}>
      <div style={{height: 12, borderRadius: 12, background: "rgba(255,255,255,0.16)", position: "relative"}}>
        <div style={{height: "100%", borderRadius: 12, background: palette.mint, width: `${interpolate(frame, [0, 100], [0, 100], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: easeOut,
        })}%`}} />
        {positions.map((position, index) => <div key={position} style={{
          position: "absolute",
          left: `${position}%`,
          top: -26,
          width: 64,
          height: 64,
          borderRadius: 64,
          background: index === activeIndex ? palette.orange : palette.mint,
          border: `8px solid ${palette.ink}`,
          opacity: interpolate(frame, [22 + index * 17, 38 + index * 17], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }} />)}
      </div>
      <div style={{display: "grid", gridTemplateColumns: `repeat(${steps.length}, 1fr)`, gap: 18}}>
        {steps.map((step, index) => <PatternCard key={step} palette={palette} tone={index === activeIndex ? "orange" : "mint"} style={{
          minHeight: 104,
          padding: "22px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          ...enter(frame, 18 + index * 16, 24),
        }}><div style={{color: palette.text, fontSize: 31, fontWeight: 800, lineHeight: 1.35}}>{step}</div></PatternCard>)}
      </div>
    </div>
  );
};

export const CompoundingFlywheel: React.FC<{
  stages: string[];
  centerTitle?: string;
  centerCaption?: string;
  palette?: PatternPalette;
}> = ({stages, centerTitle = "SKILL", centerCaption = "复利", palette = defaultPatternPalette}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [22, 182], [0, 0.94], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut});
  const positions = [
    {top: 0, left: "50%", translate: "-50% 0"},
    {top: "50%", right: 0, translate: "0 -50%"},
    {bottom: 0, left: "50%", translate: "-50% 0"},
    {top: "50%", left: 0, translate: "0 -50%"},
  ];
  return (
    <div style={{height: 340, width: 340, position: "relative", display: "flex", alignItems: "center", justifyContent: "center"}}>
      <svg width="260" height="260" viewBox="0 0 240 240" style={{position: "absolute", rotate: `${interpolate(frame, [0, 420], [-16, 34], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: easeOut,
      })}deg`}}>
        <circle cx="120" cy="120" r="100" fill="none" stroke="rgba(213,229,255,0.14)" strokeWidth="15" />
        <circle cx="120" cy="120" r="100" fill="none" stroke={palette.mint} strokeWidth="15" strokeLinecap="round" strokeDasharray="628" strokeDashoffset={628 * (1 - progress)} />
        <circle cx="120" cy="120" r="76" fill="none" stroke={palette.lavender} strokeWidth="6" strokeLinecap="round" strokeDasharray="12 18" opacity={interpolate(frame, [120, 166], [0, 0.82], {extrapolateLeft: "clamp", extrapolateRight: "clamp"})} />
      </svg>
      <div style={{width: 142, height: 142, borderRadius: 999, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: palette.surface2, border: `2px solid ${palette.mint}`, boxShadow: `0 0 42px ${palette.mint}33`, zIndex: 1, ...enter(frame, 34, 0), scale: interpolate(frame, [34, 62], [0.72, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut})}}>
        <div style={{color: palette.mint, fontSize: 25, fontWeight: 900, letterSpacing: 1}}>{centerTitle}</div>
        <div style={{color: palette.text, fontSize: 34, fontWeight: 900}}>{centerCaption}</div>
      </div>
      {stages.slice(0, 4).map((stage, index) => <div key={stage} style={{position: "absolute", width: 90, height: 56, borderRadius: 99, display: "flex", alignItems: "center", justifyContent: "center", color: palette.ink, background: index === 2 ? palette.orange : palette.mint, fontSize: 25, fontWeight: 900, ...positions[index], translate: positions[index].translate, opacity: interpolate(frame, [48 + index * 22, 66 + index * 22], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut}), scale: interpolate(frame, [48 + index * 22, 66 + index * 22], [0.72, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut})}}>{stage}</div>)}
    </div>
  );
};
