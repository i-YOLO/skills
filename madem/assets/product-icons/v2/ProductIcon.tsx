import React from "react";
import {Img, staticFile} from "remotion";

export const productIconPaths = {
  chatgpt: "png/chatgpt.png",
  claude: "source/claude.svg",
  gemini: "png/gemini.png",
  manus: "png/manus.png",
  perplexity: "source/perplexity.svg",
  coze: "png/coze.png",
  grok: "png/grok.png",
  deepseek: "source/deepseek.svg",
  yuanbao: "png/yuanbao.png",
  kimi: "png/kimi.png",
} as const;

export type ProductIconId = keyof typeof productIconPaths;

export type ProductIconProps = {
  assetId: ProductIconId;
  size?: number;
  basePath?: string;
  shadow?: boolean;
  style?: React.CSSProperties;
};

/** Copy this component and the selected icon files below public/assets/product-icons/v2. */
export const ProductIcon: React.FC<ProductIconProps> = ({
  assetId,
  size = 86,
  basePath = "assets/product-icons/v2",
  shadow = true,
  style,
}) => (
  <div
    data-product-icon={assetId}
    style={{
      width: size,
      height: size,
      display: "grid",
      placeItems: "center",
      background: "transparent",
      filter: shadow
        ? "drop-shadow(0 12px 12px #000C) drop-shadow(0 0 8px #FFFFFF22)"
        : undefined,
      ...style,
    }}
  >
    <Img
      src={staticFile(`${basePath}/${productIconPaths[assetId]}`)}
      alt={assetId}
      style={{width: "100%", height: "100%", objectFit: "contain"}}
    />
  </div>
);
