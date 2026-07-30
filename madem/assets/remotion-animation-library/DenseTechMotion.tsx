import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  ProductIcon,
  ProductIconId,
} from "../product-icons/v2/ProductIcon";

export const denseTechColors = {
  bg: "#06090D",
  bg2: "#0B1118",
  grid: "#25313B",
  white: "#F7FAFC",
  muted: "#9BA8B4",
  green: "#39FF91",
  green2: "#15D979",
  yellow: "#FFD938",
  blue: "#2B7FFF",
  cyan: "#42D9FF",
  purple: "#9B6BFF",
  pink: "#FF4FD8",
  red: "#FF5D67",
  panel: "#101923",
  panel2: "#16222E",
  border: "#314251",
} as const;

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};
const ease = Easing.bezier(0.16, 1, 0.3, 1);
const progress = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [0, 1], {...clamp, easing: ease});

export const TechGridBackground: React.FC<{
  accent?: string;
  spacing?: number;
}> = ({accent = denseTechColors.green, spacing = 56}) => {
  const {width, height} = useVideoConfig();
  const columns = Math.ceil(width / spacing) + 1;
  const rows = Math.ceil(height / spacing) + 1;
  return (
    <>
      <AbsoluteFill style={{background: denseTechColors.bg}} />
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{position: "absolute", inset: 0}}
      >
        {Array.from({length: columns}, (_, index) => (
          <line
            key={`column-${index}`}
            x1={index * spacing}
            x2={index * spacing}
            y1={0}
            y2={height}
            stroke={index % 4 === 0 ? "#364653" : denseTechColors.grid}
            strokeWidth={index % 4 === 0 ? 1.5 : 1}
            opacity={index % 4 === 0 ? 0.5 : 0.3}
          />
        ))}
        {Array.from({length: rows}, (_, index) => (
          <line
            key={`row-${index}`}
            x1={0}
            x2={width}
            y1={index * spacing}
            y2={index * spacing}
            stroke={index % 4 === 0 ? "#364653" : denseTechColors.grid}
            strokeWidth={index % 4 === 0 ? 1.5 : 1}
            opacity={index % 4 === 0 ? 0.5 : 0.3}
          />
        ))}
        <circle
          cx={width / 2}
          cy={height * 0.4}
          r={Math.min(width, height) * 0.42}
          fill={accent}
          opacity={0.018}
        />
      </svg>
    </>
  );
};

export const TechGridSceneShell: React.FC<
  React.PropsWithChildren<{accent?: string; fadeFrames?: number}>
> = ({accent, fadeFrames = 10, children}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const opacity = interpolate(
    frame,
    [0, fadeFrames, Math.max(fadeFrames + 1, durationInFrames - fadeFrames), durationInFrames],
    [0, 1, 1, 0],
    clamp,
  );
  return (
    <AbsoluteFill style={{opacity}}>
      <TechGridBackground accent={accent} />
      {children}
    </AbsoluteFill>
  );
};

export const NeonTag: React.FC<
  React.PropsWithChildren<{color?: string; style?: React.CSSProperties}>
> = ({children, color = denseTechColors.green, style}) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "12px 19px",
      borderRadius: 8,
      background: color,
      color: "#07110C",
      fontSize: 32,
      fontWeight: 1000,
      lineHeight: 1,
      boxShadow: `0 0 22px ${color}55`,
      ...style,
    }}
  >
    {children}
  </div>
);

export const AppWindowFrame: React.FC<
  React.PropsWithChildren<{
    title: string;
    accent?: string;
    style?: React.CSSProperties;
  }>
> = ({title, accent = denseTechColors.green, style, children}) => (
  <div
    style={{
      borderRadius: 28,
      overflow: "hidden",
      border: `2px solid ${denseTechColors.border}`,
      background: denseTechColors.panel,
      boxShadow: "0 30px 70px #00000088",
      ...style,
    }}
  >
    <div
      style={{
        height: 64,
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "0 22px",
        borderBottom: `1px solid ${denseTechColors.border}`,
        background: "#0C131B",
      }}
    >
      {[denseTechColors.red, denseTechColors.yellow, denseTechColors.green2].map(
        (color) => (
          <div
            key={color}
            style={{width: 14, height: 14, borderRadius: 99, background: color}}
          />
        ),
      )}
      <div
        style={{
          marginLeft: 10,
          color: denseTechColors.muted,
          fontSize: 22,
          fontWeight: 850,
        }}
      >
        {title}
      </div>
      <div
        style={{
          marginLeft: "auto",
          width: 54,
          height: 8,
          borderRadius: 99,
          background: accent,
          opacity: 0.8,
        }}
      />
    </div>
    {children}
  </div>
);

export const FolderCollector: React.FC<{
  open?: number;
  width?: number;
  style?: React.CSSProperties;
}> = ({open = 1, width = 330, style}) => {
  const scale = width / 330;
  return (
    <div
      style={{
        width,
        height: 218 * scale,
        position: "relative",
        ...style,
      }}
    >
      <div
        style={{
          position: "absolute",
          left: 20 * scale,
          top: 20 * scale,
          width: 150 * scale,
          height: 58 * scale,
          borderRadius: `${24 * scale}px ${24 * scale}px 0 0`,
          background: "#4A96FF",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 58 * scale,
          bottom: 0,
          borderRadius: 30 * scale,
          background: denseTechColors.blue,
          border: `${3 * scale}px solid #76B4FF`,
          boxShadow: "0 24px 48px #001A46AA",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 14 * scale,
          right: 14 * scale,
          top: 46 * scale,
          height: 90 * scale,
          borderRadius: `${26 * scale}px ${26 * scale}px ${12 * scale}px ${12 * scale}px`,
          background: "#73B2FF",
          transformOrigin: "50% 100%",
          transform: `perspective(${500 * scale}px) rotateX(${-54 * open}deg)`,
          border: `${3 * scale}px solid #A8D0FF`,
        }}
      />
    </div>
  );
};

export const IconSwarmCollector: React.FC<{
  iconIds: ProductIconId[];
  startFrame?: number;
  durationFrames?: number;
  staggerFrames?: number;
  width?: number;
  height?: number;
  target?: {x: number; y: number};
  iconSize?: number;
  renderTarget?: (open: number) => React.ReactNode;
}> = ({
  iconIds,
  startFrame = 0,
  durationFrames = 92,
  staggerFrames = 6,
  width = 1040,
  height = 1300,
  target = {x: 520, y: 1010},
  iconSize = 104,
  renderTarget,
}) => {
  const frame = useCurrentFrame();
  const columns = Math.max(3, Math.ceil(Math.sqrt(iconIds.length)));
  const rows = Math.ceil(iconIds.length / columns);
  const open = interpolate(
    frame,
    [startFrame, startFrame + 35],
    [0.1, 1],
    clamp,
  );
  return (
    <div style={{position: "relative", width, height}}>
      {iconIds.map((assetId, index) => {
        const column = index % columns;
        const row = Math.floor(index / columns);
        const initialX =
          70 + column * ((width - 140 - iconSize) / Math.max(1, columns - 1));
        const initialY =
          height * 0.25 +
          row * ((height * 0.35) / Math.max(1, rows - 1));
        const amount = progress(
          frame,
          startFrame + index * staggerFrames,
          startFrame + durationFrames + index * staggerFrames,
        );
        const curve =
          Math.sin(amount * Math.PI) * (index % 2 === 0 ? width * 0.09 : -width * 0.09);
        const x = initialX * (1 - amount) + target.x * amount + curve;
        const y =
          initialY * (1 - amount) +
          target.y * amount -
          Math.sin(amount * Math.PI) * height * 0.09;
        return (
          <ProductIcon
            key={`${assetId}-${index}`}
            assetId={assetId}
            size={iconSize}
            style={{
              position: "absolute",
              left: x,
              top: y,
              opacity: interpolate(amount, [0, 0.88, 1], [1, 1, 0], clamp),
              transform: `rotate(${amount * (index % 2 === 0 ? 160 : -160)}deg) scale(${1 - amount * 0.68})`,
              zIndex: 3,
            }}
          />
        );
      })}
      <div
        style={{
          position: "absolute",
          left: target.x - 165,
          top: target.y - 20,
          zIndex: 2,
        }}
      >
        {renderTarget ? renderTarget(open) : <FolderCollector open={open} />}
      </div>
    </div>
  );
};

export type MicroMotionKind =
  | "growth-bars"
  | "flow-path"
  | "particle-gather"
  | "typewriter"
  | "ring-progress"
  | "check-complete";

export const MicroMotion: React.FC<{
  kind: MicroMotionKind;
  color?: string;
  label?: string;
}> = ({kind, color = denseTechColors.green, label = "AI 动效正在生成"}) => {
  const frame = useCurrentFrame();
  const cycle = frame % 150;
  if (kind === "growth-bars") {
    return (
      <div
        style={{
          position: "absolute",
          left: 26,
          right: 26,
          top: 50,
          bottom: 30,
          display: "flex",
          alignItems: "flex-end",
          gap: 12,
        }}
      >
        {[0.42, 0.68, 0.52, 0.84, 1].map((height, index) => (
          <div
            key={height}
            style={{
              flex: 1,
              height: `${height * progress(cycle, 8 + index * 8, 30 + index * 8) * 100}%`,
              minHeight: 4,
              borderRadius: "9px 9px 3px 3px",
              background: color,
            }}
          />
        ))}
      </div>
    );
  }
  if (kind === "flow-path") {
    const amount = progress(cycle, 8, 62);
    return (
      <svg width="100%" height="100%" viewBox="0 0 440 220">
        <path
          d="M60 145 C145 40 250 190 376 70"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          pathLength="1"
          strokeDasharray="1"
          strokeDashoffset={1 - amount}
        />
        {[
          [60, 145],
          [205, 108],
          [376, 70],
        ].map(([x, y], index) => (
          <circle
            key={`${x}-${y}`}
            cx={x}
            cy={y}
            r={18 * progress(cycle, 18 + index * 16, 34 + index * 16)}
            fill={color}
            stroke="#FFFFFF"
            strokeWidth="4"
          />
        ))}
      </svg>
    );
  }
  if (kind === "particle-gather") {
    return (
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "48%",
          width: 150,
          height: 150,
          transform: `translate(-50%, -50%) rotate(${frame * 2.4}deg)`,
          borderRadius: 999,
          border: `3px solid ${color}66`,
        }}
      >
        {[0, 120, 240].map((angle, index) => (
          <div
            key={angle}
            style={{
              position: "absolute",
              left: 66,
              top: -10,
              width: 22 + index * 4,
              height: 22 + index * 4,
              borderRadius: 99,
              background: color,
              transformOrigin: `10px ${85 + index * 12}px`,
              transform: `rotate(${angle}deg)`,
              boxShadow: `0 0 18px ${color}`,
            }}
          />
        ))}
        <div
          style={{
            position: "absolute",
            inset: 43,
            borderRadius: 99,
            background: color,
            transform: `scale(${0.78 + Math.sin(frame / 10) * 0.12})`,
          }}
        />
      </div>
    );
  }
  if (kind === "typewriter") {
    const visible = Math.floor(
      interpolate(cycle, [8, 88], [0, label.length], clamp),
    );
    return (
      <div
        style={{
          position: "absolute",
          left: 28,
          right: 28,
          top: 68,
          padding: "22px 20px",
          borderRadius: 16,
          border: `2px solid ${color}`,
          color: denseTechColors.white,
          fontSize: 27,
          fontWeight: 900,
          fontFamily: "Menlo, monospace",
        }}
      >
        {label.slice(0, visible)}
        <span style={{color, opacity: Math.floor(frame / 12) % 2 ? 1 : 0}}>
          ▌
        </span>
      </div>
    );
  }
  if (kind === "ring-progress") {
    const amount = interpolate(cycle, [8, 96], [0.06, 0.86], clamp);
    return (
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "48%",
          width: 158,
          height: 158,
          transform: "translate(-50%, -50%)",
        }}
      >
        <svg width="158" height="158" style={{transform: "rotate(-90deg)"}}>
          <circle
            cx="79"
            cy="79"
            r="61"
            fill="none"
            stroke="#293947"
            strokeWidth="18"
          />
          <circle
            cx="79"
            cy="79"
            r="61"
            fill="none"
            stroke={color}
            strokeWidth="18"
            strokeLinecap="round"
            pathLength="1"
            strokeDasharray="1"
            strokeDashoffset={1 - amount}
          />
        </svg>
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "grid",
            placeItems: "center",
            color: denseTechColors.white,
            fontSize: 30,
            fontWeight: 1000,
          }}
        >
          {Math.round(amount * 100)}%
        </div>
      </div>
    );
  }
  const amount = progress(cycle, 28, 72);
  return (
    <div style={{position: "absolute", inset: 0}}>
      {Array.from({length: 10}, (_, index) => {
        const angle = (index / 10) * Math.PI * 2;
        const radius = (1 - amount) * 94;
        return (
          <div
            key={index}
            style={{
              position: "absolute",
              left: 210 + Math.cos(angle) * radius,
              top: 92 + Math.sin(angle) * radius,
              width: 14,
              height: 14,
              borderRadius: index % 2 ? 99 : 3,
              background: color,
              opacity: 1 - amount * 0.45,
              transform: `rotate(${frame * 3 + index * 24}deg)`,
            }}
          />
        );
      })}
      <div
        style={{
          position: "absolute",
          left: 176,
          top: 55,
          width: 92,
          height: 92,
          borderRadius: 99,
          display: "grid",
          placeItems: "center",
          background: color,
          color: "#07110C",
          fontSize: 54,
          fontWeight: 1000,
          transform: `scale(${amount})`,
        }}
      >
        ✓
      </div>
    </div>
  );
};

const motionKinds: MicroMotionKind[] = [
  "growth-bars",
  "flow-path",
  "particle-gather",
  "typewriter",
  "ring-progress",
  "check-complete",
];
const defaultMotionLabels = [
  "数据增长",
  "流程连线",
  "粒子聚合",
  "动态文字",
  "环形进度",
  "检查完成",
];

export const MotionGallery: React.FC<{
  labels?: string[];
  starts?: number[];
  columns?: number;
}> = ({
  labels = defaultMotionLabels,
  starts = [0, 8, 16, 24, 32, 40],
  columns = 2,
}) => {
  const frame = useCurrentFrame();
  const colors = [
    denseTechColors.blue,
    denseTechColors.purple,
    denseTechColors.green2,
    denseTechColors.pink,
    denseTechColors.yellow,
    denseTechColors.cyan,
  ];
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap: 18,
      }}
    >
      {motionKinds.map((kind, index) => {
        const amount = progress(frame, starts[index] ?? 0, (starts[index] ?? 0) + 20);
        const color = colors[index];
        return (
          <div
            key={kind}
            style={{
              height: 250,
              borderRadius: 24,
              background: "#0C151E",
              border: `2px solid ${color}`,
              overflow: "hidden",
              opacity: amount,
              transform: `translateY(${(1 - amount) * 48}px) scale(${0.9 + amount * 0.1})`,
              position: "relative",
              boxShadow: `0 18px 42px #0008, 0 0 22px ${color}18`,
            }}
          >
            <MicroMotion kind={kind} color={color} />
            <div
              style={{
                position: "absolute",
                left: 20,
                bottom: 16,
                padding: "7px 11px",
                borderRadius: 8,
                background: color,
                color: index === 4 ? "#111820" : denseTechColors.white,
                fontSize: 20,
                fontWeight: 1000,
              }}
            >
              {labels[index] ?? defaultMotionLabels[index]}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export type InspectionStep = {
  label: string;
  startFrame: number;
};

export const QualityInspectionLoop: React.FC<{
  steps: InspectionStep[];
  failFrame: number;
  fixFrame: number;
  passFrame: number;
  height?: number;
}> = ({steps, failFrame, fixFrame, passFrame, height = 690}) => {
  const frame = useCurrentFrame();
  const failed = frame >= failFrame && frame < fixFrame;
  const fixed = frame >= passFrame;
  const accent = failed ? denseTechColors.red : denseTechColors.green;
  return (
    <div
      style={{
        height,
        display: "grid",
        gridTemplateColumns: "1.08fr 0.92fr",
        borderRadius: 24,
        overflow: "hidden",
        border: `2px solid ${accent}`,
        background: denseTechColors.panel,
      }}
    >
      <div
        style={{
          position: "relative",
          borderRight: `1px solid ${denseTechColors.border}`,
          overflow: "hidden",
        }}
      >
        <TechGridBackground accent={accent} />
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            height: height * 0.46,
            top: interpolate(frame % 100, [0, 99], [-height * 0.5, height], clamp),
            background: `linear-gradient(180deg, transparent, ${accent}66, transparent)`,
          }}
        />
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "grid",
            placeItems: "center",
            color: accent,
            fontSize: 34,
            fontWeight: 1000,
          }}
        >
          {failed ? "发现遮挡" : fixed ? "重新渲染通过" : "正在检查"}
        </div>
      </div>
      <div style={{padding: 24, display: "grid", alignContent: "start", gap: 15}}>
        {steps.map((step, index) => {
          const amount = progress(frame, step.startFrame, step.startFrame + 18);
          const state =
            failed && index === Math.max(0, steps.length - 2) ? "fail" : "pass";
          const color =
            state === "fail" ? denseTechColors.red : denseTechColors.green;
          return (
            <div
              key={step.label}
              style={{
                minHeight: 86,
                borderRadius: 20,
                border: `2px solid ${color}`,
                background: `${color}12`,
                display: "flex",
                alignItems: "center",
                padding: "0 24px",
                gap: 18,
                color: denseTechColors.white,
                fontSize: 27,
                fontWeight: 900,
                opacity: amount,
                transform: `translateX(${(1 - amount) * 60}px)`,
              }}
            >
              <div
                style={{
                  width: 42,
                  height: 42,
                  borderRadius: 99,
                  background: color,
                  color: "#07110C",
                  display: "grid",
                  placeItems: "center",
                }}
              >
                {state === "fail" ? "!" : "✓"}
              </div>
              {step.label}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const MotionGatherTransition: React.FC<{
  startFrame: number;
  endFrame: number;
  target: {x: number; y: number};
  positions?: Array<{x: number; y: number}>;
}> = ({
  startFrame,
  endFrame,
  target,
  positions = [
    {x: 130, y: 520},
    {x: 380, y: 420},
    {x: 720, y: 520},
    {x: 150, y: 900},
    {x: 735, y: 900},
    {x: 430, y: 1080},
  ],
}) => {
  const frame = useCurrentFrame();
  const amount = progress(frame, startFrame, endFrame);
  const colors = [
    denseTechColors.blue,
    denseTechColors.purple,
    denseTechColors.green,
    denseTechColors.pink,
    denseTechColors.yellow,
    denseTechColors.cyan,
  ];
  return (
    <>
      {positions.map((position, index) => (
        <div
          key={`${position.x}-${position.y}`}
          style={{
            position: "absolute",
            left: position.x * (1 - amount) + target.x * amount,
            top: position.y * (1 - amount) + target.y * amount,
            width: 104,
            height: 104,
            borderRadius: index % 2 ? 99 : 20,
            border: `7px solid ${colors[index % colors.length]}`,
            opacity: 1 - amount,
            transform: `rotate(${frame * (index % 2 ? -1.6 : 1.6)}deg) scale(${1 - amount * 0.68})`,
          }}
        />
      ))}
    </>
  );
};
