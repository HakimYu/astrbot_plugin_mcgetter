import os
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.core.message.components as Comp
from .get_server_info import get_server_status
from .get_img import generate_server_info_image


@register("astrbot_mcgetter", "QiChen", "查询mc服务器信息和玩家列表,渲染为图片", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 把信息渲染成图片
    @filter.command("mc")
    async def custom_t2i_tmpl(self, event: AstrMessageEvent, host: str):
        
        info = await get_server_status(host)
        info['server_name'] = '原神'
        #使用pillow绘制
        mcinfo_img = await generate_server_info_image(
            players_list=info['players_list'],
            latency=info['latency'],
            server_name=info['server_name'],
            plays_max=info['plays_max'],
            plays_online=info['plays_online'],
            server_version=info['server_version'],
            icon_base64=info['icon_base64']
        )
        if mcinfo_img:
            yield event.chain_result([Comp.Image.fromBase64(mcinfo_img)])
