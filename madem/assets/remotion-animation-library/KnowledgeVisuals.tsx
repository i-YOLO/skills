import React from "react";
import {Easing, Img, interpolate, staticFile, useCurrentFrame} from "remotion";
import type {PatternPalette, PatternTone} from "./PatternLibrary";

const ease = Easing.bezier(0.16, 1, 0.3, 1);

export const warmKnowledgePalette: PatternPalette = {
  ink: "#12315B",
  surface: "#FFFCF7",
  surface2: "#F4EFE6",
  text: "#12315B",
  muted: "#64748B",
  mint: "#2F9E76",
  orange: "#FF6B1A",
  lavender: "#2563EB",
  red: "#D95D5D",
};

const reveal = (frame: number, start: number, duration = 20, distance = 24) => ({
  opacity: interpolate(frame, [start, start + duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  }),
  transform: `translateY(${interpolate(frame, [start, start + duration], [distance, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  })}px)`,
});

export type KnowledgeLayer = {
  index: string;
  name: string;
  detail: string;
  tone: PatternTone;
};

export const FiveLayerStack: React.FC<{
  layers: KnowledgeLayer[];
  startAt?: number;
  starts?: number[];
  stagger?: number;
  revealDuration?: number;
  compact?: boolean;
  palette?: PatternPalette;
}> = ({
  layers,
  startAt = 0,
  starts,
  stagger = 22,
  revealDuration = 20,
  compact = false,
  palette = warmKnowledgePalette,
}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: "grid", gap: compact ? 10 : 12, width: "100%"}}>
      {layers.map((layer, index) => {
        const start = starts?.[index] ?? startAt + index * stagger;
        const color = palette[layer.tone];
        return (
          <div
            key={`${layer.index}-${layer.name}`}
            style={{
              height: compact ? 76 : 92,
              borderRadius: 22,
              border: `2px solid ${color}55`,
              background: `${color}0D`,
              display: "grid",
              gridTemplateColumns: compact ? "92px 150px 1fr" : "108px 180px 1fr",
              alignItems: "center",
              padding: compact ? "0 22px" : "0 28px",
              opacity: interpolate(frame, [start, start + revealDuration], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: ease,
              }),
              transform: `translateX(${interpolate(
                frame,
                [start, start + revealDuration + 4],
                [46, 0],
                {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease},
              )}px)`,
            }}
          >
            <div style={{fontSize: compact ? 23 : 26, fontWeight: 900, color}}>{layer.index}</div>
            <div style={{fontSize: compact ? 32 : 38, fontWeight: 900, color}}>{layer.name}</div>
            <div style={{fontSize: compact ? 24 : 29, fontWeight: 750, color: palette.ink, opacity: 0.78}}>
              {layer.detail}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export type BrandIconItem = {
  src: string;
  label: string;
  start?: number;
};

export const BrandIconRow: React.FC<{
  items: BrandIconItem[];
  startAt?: number;
  stagger?: number;
  iconBoxSize?: number;
  iconSize?: number;
}> = ({items, startAt = 0, stagger = 12, iconBoxSize = 106, iconSize = 100}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: "flex", alignItems: "center", gap: 20}}>
      {items.map((item, index) => (
        <div
          key={item.label}
          aria-label={item.label}
          style={{
            width: iconBoxSize,
            height: iconBoxSize,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            ...reveal(frame, item.start ?? startAt + index * stagger, 18, 16),
          }}
        >
          <Img
            src={staticFile(item.src)}
            style={{width: iconSize, height: iconSize, objectFit: "contain"}}
          />
        </div>
      ))}
    </div>
  );
};

export const MockChatWindow: React.FC<{
  startAt?: number;
  title?: string;
  userMessage?: string;
  assistantMessage?: string;
  inputPlaceholder?: string;
  sidebarItems?: string[];
  width?: number;
  height?: number;
  palette?: PatternPalette;
}> = ({
  startAt = 0,
  title = "AI 助手",
  userMessage = "帮我整理会议重点",
  assistantMessage = "好的，正在生成回答……",
  inputPlaceholder = "输入你的问题",
  sidebarItems = ["最近对话", "资料库", "设置"],
  width = 520,
  height = 420,
  palette = warmKnowledgePalette,
}) => {
  const frame = useCurrentFrame();
  const userOpacity = interpolate(frame, [startAt + 28, startAt + 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const assistantOpacity = interpolate(frame, [startAt + 62, startAt + 90], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        width,
        height,
        overflow: "hidden",
        display: "grid",
        gridTemplateRows: "58px 1fr",
        borderRadius: 28,
        border: `2px solid ${palette.lavender}38`,
        background: palette.surface,
        boxShadow: `0 18px 54px ${palette.ink}12`,
        ...reveal(frame, startAt, 28),
      }}
    >
      <div style={{borderBottom: `1px solid #D8CEBE`, display: "flex", alignItems: "center", padding: "0 18px", gap: 9}}>
        {[palette.red, palette.orange, palette.mint].map((color) => (
          <div key={color} style={{width: 10, height: 10, borderRadius: 99, background: color}} />
        ))}
        <div style={{marginLeft: 10, fontSize: 20, fontWeight: 850, color: palette.ink}}>{title}</div>
      </div>
      <div style={{display: "grid", gridTemplateColumns: "122px 1fr", minHeight: 0}}>
        <div style={{borderRight: "1px solid #D8CEBE", background: palette.surface2, padding: "18px 12px", display: "grid", alignContent: "start", gap: 14}}>
          <div style={{borderRadius: 10, background: `${palette.lavender}14`, color: palette.lavender, padding: "10px 9px", fontSize: 16, fontWeight: 850}}>
            ＋ 新对话
          </div>
          {sidebarItems.map((item) => (
            <div key={item} style={{fontSize: 15, fontWeight: 700, color: palette.muted, paddingLeft: 8}}>{item}</div>
          ))}
        </div>
        <div style={{position: "relative", padding: "22px 18px 72px", background: "#FFFFFF"}}>
          <div style={{marginLeft: 62, padding: "12px 14px", borderRadius: "16px 16px 4px 16px", background: `${palette.lavender}12`, fontSize: 17, fontWeight: 750, opacity: userOpacity}}>
            {userMessage}
          </div>
          <div style={{marginTop: 16, marginRight: 42, padding: "13px 14px", borderRadius: "16px 16px 16px 4px", border: "1px solid #D8CEBE", fontSize: 16, fontWeight: 700, color: palette.muted, opacity: assistantOpacity}}>
            {assistantMessage}
          </div>
          <div style={{position: "absolute", left: 16, right: 16, bottom: 15, height: 44, border: "1px solid #D8CEBE", borderRadius: 14, display: "flex", alignItems: "center", padding: "0 12px", color: palette.muted, fontSize: 15}}>
            {inputPlaceholder}
            <div style={{marginLeft: "auto", width: 28, height: 28, borderRadius: 99, background: palette.ink, color: palette.surface, display: "flex", alignItems: "center", justifyContent: "center"}}>↑</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export type AgentLoopNode = {
  label: string;
  x: number;
  y: number;
  tone: PatternTone;
  start: number;
};

export const AgentDecisionLoop: React.FC<{
  nodes: AgentLoopNode[];
  startToDecisionProgress: number;
  questionLoopProgress: number;
  decisionToContinueProgress: number;
  continueToCompleteProgress: number;
  shortageLabel?: string;
  returnLabel?: string;
  palette?: PatternPalette;
}> = ({
  nodes,
  startToDecisionProgress,
  questionLoopProgress,
  decisionToContinueProgress,
  continueToCompleteProgress,
  shortageLabel = "资料不足",
  returnLabel = "补充后回到判断",
  palette = warmKnowledgePalette,
}) => {
  const frame = useCurrentFrame();
  const orangeMarker = "knowledge-agent-arrow-orange";
  const greenMarker = "knowledge-agent-arrow-green";
  const paths = [
    {d: "M24 90 L279 90", tone: "orange" as const, progress: startToDecisionProgress, marker: orangeMarker},
    {d: "M279 90 C320 34 382 5 454 5 C560 5 570 138 452 138 C360 138 306 122 279 90", tone: "orange" as const, progress: questionLoopProgress, marker: orangeMarker},
    {d: "M279 90 L674 90", tone: "orange" as const, progress: decisionToContinueProgress, marker: orangeMarker},
    {d: "M674 90 L924 90", tone: "mint" as const, progress: continueToCompleteProgress, marker: greenMarker},
  ];
  return (
    <div style={{position: "relative", width: 1080, height: 230}}>
      <svg width="1080" height="200" style={{position: "absolute", inset: 0, overflow: "visible"}}>
        <defs>
          <marker id={orangeMarker} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill={palette.orange} />
          </marker>
          <marker id={greenMarker} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill={palette.mint} />
          </marker>
        </defs>
        {paths.map((path) => (
          <path
            key={path.d}
            d={path.d}
            fill="none"
            stroke={palette[path.tone]}
            strokeWidth="6"
            strokeLinecap="round"
            strokeLinejoin="round"
            pathLength="1"
            strokeDasharray="1"
            strokeDashoffset={1 - path.progress}
            markerEnd={path.progress > 0.02 ? `url(#${path.marker})` : undefined}
          />
        ))}
        <text x="320" y="-12" fill={palette.orange} fontSize="22" fontWeight="850" opacity={questionLoopProgress > 0.05 ? 1 : 0}>{shortageLabel}</text>
        <text x="385" y="174" fill={palette.orange} fontSize="22" fontWeight="850" opacity={questionLoopProgress > 0.9 ? 1 : 0}>{returnLabel}</text>
      </svg>
      {nodes.map((node) => (
        <div
          key={node.label}
          style={{
            position: "absolute",
            left: node.x,
            top: 66 + node.y,
            width: 48,
            height: 48,
            borderRadius: 99,
            background: palette[node.tone],
            border: "8px solid #FAF8F3",
            opacity: interpolate(frame, [node.start, node.start + 20], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          <div style={{position: "absolute", top: node.y < 0 ? -44 : 58, left: -42, width: 130, textAlign: "center", fontSize: 24, fontWeight: 850, color: node.label === "追问" ? palette.orange : palette.muted}}>
            {node.label}
          </div>
        </div>
      ))}
    </div>
  );
};

export type PermissionGate = {
  title: string;
  detail: string;
  tone: PatternTone;
  start: number;
};

export const PermissionGateCards: React.FC<{
  gates: PermissionGate[];
  palette?: PatternPalette;
}> = ({gates, palette = warmKnowledgePalette}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: "grid", gridTemplateColumns: `repeat(${gates.length}, minmax(0, 1fr))`, alignItems: "center", gap: 30, width: "100%"}}>
      {gates.map((gate, index) => (
        <div key={gate.title} style={{minHeight: 320, padding: 36, display: "flex", flexDirection: "column", justifyContent: "space-between", borderRadius: 28, border: `2px solid ${palette[gate.tone]}38`, background: palette.surface, boxShadow: `0 18px 54px ${palette.ink}12`, ...reveal(frame, gate.start, 30)}}>
          <div style={{width: 70, height: 70, borderRadius: 20, display: "flex", alignItems: "center", justifyContent: "center", color: palette.surface, background: palette[gate.tone], fontSize: 34, fontWeight: 900}}>{index + 1}</div>
          <div style={{fontSize: 42, fontWeight: 900, color: palette[gate.tone]}}>{gate.title}</div>
          <div style={{fontSize: 28, fontWeight: 750, color: palette.muted}}>{gate.detail}</div>
        </div>
      ))}
    </div>
  );
};

export const InterfaceToSystemReveal: React.FC<{
  chatStart?: number;
  arrowStart?: number;
  layerStarts?: number[];
  layers: KnowledgeLayer[];
  palette?: PatternPalette;
}> = ({
  chatStart = 0,
  arrowStart = 60,
  layerStarts,
  layers,
  palette = warmKnowledgePalette,
}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: "grid", gridTemplateColumns: "520px 90px 1fr", alignItems: "center", gap: 28, width: "100%"}}>
      <MockChatWindow startAt={chatStart} width={520} height={420} palette={palette} />
      <div style={{fontSize: 64, fontWeight: 900, color: palette.orange, ...reveal(frame, arrowStart, 18, 0)}}>→</div>
      <FiveLayerStack layers={layers} starts={layerStarts} startAt={arrowStart + 20} compact palette={palette} />
    </div>
  );
};
