import os
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from .get_server_info import get_server_status


@register("astrbot_mcgetter", "QiChen", "查询mc服务器信息和玩家列表,用html渲染为图片", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 把信息渲染成图片
    @filter.command("html")
    async def custom_t2i_tmpl(self, event: AstrMessageEvent, host: str):
        try:
            # 获取当前脚本所在的目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # 构建 html_style.txt 的绝对路径
            file_path = os.path.join(script_dir, 'html_style.txt')
            with open(file_path, 'r', encoding="utf-8") as file:
                TMPL = file.read()
        except FileNotFoundError:
            logger.error(f"无法读取 {file_path}，请检查文件是否存在。")
            return
        except PermissionError:
            logger.error(f"没有权限读取 {file_path}，请检查文件权限。")
            return
        except Exception as e:
            logger.error(f"读取文件时发生未知错误: {e}")
            return

        info = await get_server_status(host)
        info['server_name'] = '原神'
        url = await self.html_render(TMPL, info)  # 第二个参数是 Jinja2 的渲染数据
        yield event.image_result(url)