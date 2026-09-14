#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
draw_by_ratio.py  ——  按“比例坐标”在截图上绘制标记（用于子代理视觉校验）

坐标体系：与 UI 子代理一致，0~1000 表示 0%~100%（1000 = 100%）。

用法示例：
  # 画一个框（比例坐标 left,top,right,bottom），带标签
  python3 draw_by_ratio.py --img in.png --out out.png \
      --rect "120,650,880,780" --label "北语校历"

  # 画一个中心十字 + 圆点（比例 x,y）
  python3 draw_by_ratio.py --img in.png --out out.png \
      --point "500,500" --label "center"

  # 多个标记：多次传 --rect / --point 即可
  python3 draw_by_ratio.py --img in.png --out out.png \
      --rect "120,650,880,780:北语校历" \
      --rect "120,800,880,930:部门黄页"

参数：
  --img    输入图
  --out    输出图（默认 输入名_drawn.png）
  --rect   比例框 "l,t,r,b" 或 "l,t,r,b:标签"，可多次
  --point  比例点 "x,y" 或 "x,y:标签"，可多次
  --color  颜色，默认红 (255,0,0)
  --width  线宽，默认 6
  --scale  比例基准，默认 1000（即 1000=100%）

说明：
  比例值除以 scale 得到 0~1，再乘以图片真实宽高，得到像素坐标。
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFont


def ratio_to_px(v, total, scale):
    return int(round(float(v) / float(scale) * float(total)))


def parse_label(s):
    if ":" in s:
        a, b = s.split(":", 1)
        return a.strip(), b.strip()
    return s.strip(), None


def get_font(size):
    # 尝试常见中文字体，找不到就用默认
    for p in [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/system/fonts/NotoSansCJK-Regular.ttc",
        "/system/fonts/DroidSansFallbackFull.ttf",
    ]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--rect", action="append", default=[])
    ap.add_argument("--point", action="append", default=[])
    ap.add_argument("--color", default="255,0,0")
    ap.add_argument("--width", type=int, default=6)
    ap.add_argument("--scale", type=float, default=1000.0)
    args = ap.parse_args()

    img = Image.open(args.img).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)
    color = tuple(int(x) for x in args.color.split(","))
    font = get_font(max(24, W // 30))

    def draw_label(x, y, text):
        if not text:
            return
        # 给标签加个底，避免看不清
        try:
            tb = draw.textbbox((x, y), text, font=font)
        except Exception:
            tb = (x, y, x + len(text) * 12, y + 30)
        draw.rectangle([tb[0] - 4, tb[1] - 2, tb[2] + 4, tb[3] + 2], fill=(255, 255, 0))
        draw.text((x, y), text, fill=(0, 0, 0), font=font)

    for r in args.rect:
        coord, label = parse_label(r)
        l, t, rr, b = [float(v) for v in coord.split(",")]
        x1 = ratio_to_px(l, W, args.scale)
        y1 = ratio_to_px(t, H, args.scale)
        x2 = ratio_to_px(rr, W, args.scale)
        y2 = ratio_to_px(b, H, args.scale)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=args.width)
        # 中心点
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        cr = args.width * 2
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=color)
        draw_label(x1, max(0, y1 - (font.size + 6) if hasattr(font, "size") else y1 - 36), label)

    for p in args.point:
        coord, label = parse_label(p)
        x, y = [float(v) for v in coord.split(",")]
        px = ratio_to_px(x, W, args.scale)
        py = ratio_to_px(y, H, args.scale)
        r = max(10, args.width * 3)
        draw.line([px - r, py, px + r, py], fill=color, width=args.width)
        draw.line([px, py - r, px, py + r], fill=color, width=args.width)
        draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=color)
        draw_label(px + 12, py + 12, label)

    out = args.out or (os.path.splitext(args.img)[0] + "_drawn.png")
    img.save(out)
    print("saved:", out, "size:", W, "x", H)


if __name__ == "__main__":
    main()
