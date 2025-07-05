from PIL import Image, ImageDraw, ImageFont
import asyncio
import io
from pathlib import Path
import base64
from typing import Optional


async def load_font(font_size):
    # 尝试多路径加载
    font_paths = [
        Path(__file__).resolve().parent.parent/'resource'/'msyh.ttf',
        'msyh.ttf',  # 当前目录
        '/usr/share/fonts/zh_CN/msyh.ttf',  # Linux常见路径
        'C:/Windows/Fonts/msyh.ttc',  # Windows路径
        '/System/Library/Fonts/Supplemental/Songti.ttc'  # macOS路径
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, font_size)
        except OSError:
            continue

    # 全部失败时使用默认字体（添加中文支持）
    try:
        # 尝试加载PIL的默认中文字体
        return ImageFont.load_default().font_variant(size=font_size)
    except:
        return ImageFont.load_default()

# 在代码中替换字体加载部分
title_font = load_font(30)
text_font = load_font(20)
small_font = load_font(18)


async def fetch_icon(icon_base64: Optional[str] = None) -> Optional[Image.Image]:
    """处理Base64编码的服务器图标"""
    if not icon_base64:
        return None

    try:
        # 去除可能的Base64前缀
        if "," in icon_base64:
            icon_base64 = icon_base64.split(",", 1)[1]
        icon_data = base64.b64decode(icon_base64)
        return Image.open(io.BytesIO(icon_data)).convert("RGBA")
    except Exception as e:
        print(f"Base64图标解码失败: {str(e)}")
        return None


async def generate_server_info_image(
    players_list: list,
    latency: int,
    server_name: str,
    plays_max: int,
    plays_online: int,
    server_version: str,
    icon_base64: Optional[str] = None
) -> str:
    """生成服务器信息图片并返回base64编码"""

    # 异步获取图标
    server_icon = await fetch_icon(icon_base64)

    # 配置参数 - 使用更现代的配色方案
    BG_COLOR = (24, 25, 29)  # 深色背景
    CARD_BG = (32, 34, 37)   # 卡片背景色
    TEXT_COLOR = (255, 255, 255)  # 主文本色
    SECONDARY_TEXT = (185, 187, 190)  # 次要文本色
    ACCENT_COLOR = (88, 101, 242)  # Discord风格的强调色
    SUCCESS_COLOR = (87, 242, 135)  # 在线状态色
    WARNING_COLOR = (255, 163, 72)  # 警告色
    ERROR_COLOR = (237, 66, 69)     # 错误色

    try:
        title_font = await load_font(32)
        subtitle_font = await load_font(24)
        text_font = await load_font(20)
        small_font = await load_font(16)
    except IOError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # 计算布局参数
    PADDING = 30
    icon_size = 80 if server_icon else 0
    base_y = PADDING
    text_x = PADDING + icon_size + 20

    # 计算玩家列表所需的高度
    player_line_height = 35
    players_per_line = 3
    player_lines = (len(players_list) + players_per_line -
                    1) // players_per_line if players_list else 1

    # 基础高度 + 玩家列表高度 + 额外边距
    img_height = 250 + (player_lines * player_line_height) + PADDING
    img_width = 700  # 增加宽度以适应内容

    # 创建主画布（使用RGBA模式）
    img = Image.new("RGBA", (img_width, img_height), color=BG_COLOR + (255,))
    draw = ImageDraw.Draw(img)

    # 绘制背景卡片
    draw.rounded_rectangle(
        [PADDING//2, PADDING//2, img_width-PADDING//2, img_height-PADDING//2],
        radius=15,
        fill=CARD_BG + (255,)
    )

    # 绘制服务器图标
    if server_icon:
        try:
            if server_icon.mode != 'RGBA':
                server_icon = server_icon.convert('RGBA')

            icon_mask = Image.new("L", (icon_size, icon_size), 0)
            mask_draw = ImageDraw.Draw(icon_mask)
            mask_draw.rounded_rectangle(
                (0, 0, icon_size, icon_size), radius=15, fill=255)

            server_icon = server_icon.resize(
                (icon_size, icon_size), Image.Resampling.LANCZOS)
            img.paste(server_icon, (PADDING, base_y), mask=icon_mask)
        except Exception as e:
            print(f"处理服务器图标时出错: {e}")

    # 服务器名称
    draw.text((text_x, base_y), server_name,
              font=title_font, fill=TEXT_COLOR + (255,))
    base_y += 50

    # 版本信息和延迟
    version_text = f"版本: {server_version}"
    draw.text((text_x, base_y), version_text,
              font=subtitle_font, fill=SECONDARY_TEXT + (255,))

    # 延迟指示器
    latency_color = SUCCESS_COLOR if latency < 100 else WARNING_COLOR if latency < 200 else ERROR_COLOR
    latency_text = f"{latency}ms"
    latency_w = draw.textlength(latency_text, font=subtitle_font)
    ping_x = img_width - PADDING - latency_w - 40

    # 绘制延迟背景和文字
    draw.rounded_rectangle(
        [ping_x-10, base_y, ping_x+latency_w+10, base_y+30],
        radius=8,
        fill=latency_color + (50,)  # 半透明背景
    )
    draw.text((ping_x, base_y), latency_text,
              font=subtitle_font, fill=TEXT_COLOR + (255,))

    base_y += 60

    # 玩家统计
    player_stat_bg = (44, 47, 51)
    stat_width = (img_width - PADDING * 3) // 2

    # 在线玩家统计框
    draw.rounded_rectangle(
        [text_x, base_y, text_x+stat_width, base_y+60],
        radius=10,
        fill=player_stat_bg + (255,)
    )
    draw.text((text_x+20, base_y+10), "在线玩家",
              font=small_font, fill=SECONDARY_TEXT + (255,))
    draw.text((text_x+20, base_y+30),
              f"{plays_online}/{plays_max}", font=text_font, fill=TEXT_COLOR + (255,))

    base_y += 80

    # 玩家列表标题
    if players_list:
        draw.text((text_x, base_y), "在线玩家列表",
                  font=subtitle_font, fill=ACCENT_COLOR + (255,))
        base_y += 40

        # 玩家列表（每行3个玩家）
        chunks = [players_list[i:i+players_per_line]
                  for i in range(0, len(players_list), players_per_line)]
        max_width = (img_width - text_x - PADDING * 2) // players_per_line

        for chunk in chunks:
            x = text_x + 20
            for player in chunk:
                # 计算玩家名称宽度并确保不超过最大宽度
                name_width = min(draw.textlength(
                    player, font=small_font), max_width - 20)

                # 绘制玩家名称背景
                draw.rounded_rectangle(
                    [x-5, base_y-2, x+name_width+5, base_y+20],
                    radius=5,
                    fill=player_stat_bg + (255,)
                )

                # 如果名字太长，添加省略号
                display_name = player
                if draw.textlength(player, font=small_font) > max_width - 20:
                    while draw.textlength(display_name + "...", font=small_font) > max_width - 20:
                        display_name = display_name[:-1]
                    display_name += "..."

                draw.text((x, base_y), display_name,
                          font=small_font, fill=TEXT_COLOR + (255,))
                x += min(name_width + 40, max_width)
            base_y += player_line_height
    else:
        draw.text((text_x+20, base_y), "暂无玩家在线",
                  font=text_font, fill=SECONDARY_TEXT + (255,))

    # 在保存之前转换为RGB模式
    img = img.convert('RGB')

    # 转换为base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return img_base64
