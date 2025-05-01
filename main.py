from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from pathlib import Path
import astrbot.core.message.components as Comp
from .script.get_server_info import get_server_status
from .script.get_img import generate_server_info_image
from .script.json_operate import *
from astrbot.api.star import StarTools


@register("astrbot_mcgetter", "QiChen", "查询mc服务器信息和玩家列表,渲染为图片", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("MyPlugin 初始化完成")

    @filter.command("mchelp")
    async def get_help(self,event:AstrMessageEvent):
        help_info="""
/mchelp 
--查看帮助

/mc   
--查询保存的服务器

/mcadd 服务器名称 服务器地址 
--添加要查询的服务器

/mcdel 服务器名称 
--删除服务器
"""
        yield event.plain_result(f"{help_info}")

    # 查询信息
    @filter.command("mc")
    async def mcgetter(self, event: AstrMessageEvent):
        logger.info("开始执行 mc 命令")
        try:
            # 通过配置读取
            # 按群号读取
            group_id = event.get_group_id()
            logger.info(f"获取到的群号: {group_id}")
            json_path = await self.get_json_path(group_id)
            logger.info(f"JSON 文件路径: {json_path}")
            json_data = await read_json(json_path)
            logger.info(f"读取到的 JSON 数据: {json_data}")
            message_chain = []
            for name in json_data:
                try:
                    logger.info(f"当前处理的服务器名称: {name}")
                    mcinfo_img = await self.get_img(json_data[name]['name'], json_data[name]['host'])
                    if mcinfo_img:
                        message_chain.append(Comp.Image.fromBase64(mcinfo_img))
                        logger.info(f"成功添加图片到消息链，服务器名称: {name}")
                except Exception as e:
                    logger.error(f"处理服务器 {name} 时出错: {e}")
            if message_chain:
                logger.info("消息链中有图片，返回消息结果")
                yield event.chain_result(message_chain)
            else:
                logger.info("消息链中没有图片，不返回结果")
        except Exception as e:
            logger.error(f"执行 mc 命令时出错: {e}")

    # 添加服务器
    @filter.command("mcadd")
    async def mcadd(self, event: AstrMessageEvent, name: str, host: str):
        logger.info("开始执行 mcadd 命令")
        try:
            group_id = event.get_group_id()
            logger.info(f"获取到的群号: {group_id}")
            json_path = await self.get_json_path(group_id)
            logger.info(f"JSON 文件路径: {json_path}")
            if await add_data(json_path, name, host):
                logger.info(f"成功添加服务器 {name} 到 {json_path}")
                yield event.plain_result(f"成功添加服务器 {name}")
            else:
                logger.info(f'无法添加{name},请检查是否已存在')
                yield event.plain_result(f'无法添加{name},请检查是否已存在')
        except Exception as e:
            logger.error(f"执行 mcadd 命令时出错: {e}")

    # 删除服务器
    @filter.command("mcdel")
    async def mcdel(self, event: AstrMessageEvent, name: str):
        logger.info("开始执行 mcdel 命令")
        try:
            group_id = event.get_group_id()
            logger.info(f"获取到的群号: {group_id}")
            json_path = await self.get_json_path(group_id)
            logger.info(f"JSON 文件路径: {json_path}")
            if await del_data(json_path, name):
                logger.info(f"成功从 {json_path} 删除服务器 {name}")
                yield event.plain_result(f"成功删除服务器 {name}") 
            else:
                logger.info(f'无法删除{name},请检查是否存在')
                yield event.plain_result(f'无法删除{name},请检查是否存在')      
        except Exception as e:
            logger.error(f"执行 mcdel 命令时出错: {e}")

    async def get_img(self, server_name: str, host: str):
        logger.info(f"开始获取服务器 {server_name} 的图片，主机地址: {host}")
        try:
            info = await get_server_status(host)
            logger.info(f"获取到的服务器信息: {info}")
            info['server_name'] = server_name
            # 使用 pillow 绘制
            mcinfo_img = await generate_server_info_image(
                players_list=info['players_list'],
                latency=info['latency'],
                server_name=info['server_name'],
                plays_max=info['plays_max'],
                plays_online=info['plays_online'],
                server_version=info['server_version'],
                icon_base64=info['icon_base64']
            )
            logger.info(f"成功生成服务器 {server_name} 的图片")
            return mcinfo_img
        except Exception as e:
            logger.error(f"获取服务器 {server_name} 的图片时出错: {e}")
            return None

    # 获取 json 配置文件路径
    async def get_json_path(self, group_id: str):
        logger.info(f"开始获取群号 {group_id} 的 JSON 文件路径")
        data_path = StarTools.get_data_dir("astrbot_mcgetter")
        json_path=data_path/f'{group_id}.json'
        json_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"群号 {group_id} 的 JSON 文件路径: {json_path}")
        return json_path
