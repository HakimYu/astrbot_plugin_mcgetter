from typing import List, Optional
from pathlib import Path
import astrbot.core.message.components as Comp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.api import logger
from .script.get_server_info import get_server_status
from .script.get_img import generate_server_info_image
from .script.json_operate import read_json, add_data, del_data
import asyncio
import re

# 常量定义
HELP_INFO = """
/mchelp
--查看帮助

/mc
--查询保存的服务器

/mcadd 服务器名称 服务器地址 [force]
--添加要查询的服务器
--force: 可选参数，设为True时跳过预查询检查强制添加

/mcget 服务器名称
--获取指定服务器的地址信息

/mcdel 服务器名称
--删除服务器
"""


@register("mcgetter", "QiChen/HakimYu", "查询mc服务器信息和玩家列表,渲染为图片", "1.2.0")
class MyPlugin(Star):
    """Minecraft服务器信息查询插件"""

    def __init__(self, context: Context):
        """
        初始化插件

        Args:
            context: 插件上下文
        """
        super().__init__(context)
        logger.info("MyPlugin 初始化完成")

    @filter.command("mchelp")
    async def get_help(self, event: AstrMessageEvent):
        """
        显示帮助信息

        Args:
            event: 消息事件

        Returns:
            包含帮助信息的消息结果
        """
        yield event.plain_result(HELP_INFO)

    @filter.command("mc")
    async def mcgetter(self, event: AstrMessageEvent):
        """
        查询所有保存的服务器信息

        Args:
            event: 消息事件

        Returns:
            包含服务器信息图片的消息结果，如果出错则返回None
        """
        logger.info("开始执行 mc 命令")
        try:
            group_id = event.get_group_id()
            logger.info(f"获取到群组ID: {group_id}")

            json_path = await self.get_json_path(group_id)
            logger.info(f"JSON文件路径: {json_path}")

            json_data = await read_json(json_path)
            logger.info(f"读取到的JSON数据: {json_data}")

            if not json_data:
                logger.warning("JSON数据为空")
                yield event.plain_result("请先使用 /mcadd 添加服务器")
                return

            message_chain: List[Comp.Image] = []
            for name, server_info in json_data.items():
                try:
                    logger.info(f"正在处理服务器: {name}, 信息: {server_info}")
                    mcinfo_img = await self.get_img(server_info['name'], server_info['host'])
                    if mcinfo_img:
                        message_chain.append(Comp.Image.fromBase64(mcinfo_img))
                        logger.info(f"成功添加图片到消息链，服务器名称: {name}")
                    else:
                        logger.warning(f"获取服务器 {name} 的图片失败")
                except Exception as e:
                    logger.error(f"处理服务器 {name} 时出错: {e}")
                    continue

            if message_chain:
                logger.info(f"成功生成消息链，包含 {len(message_chain)} 张图片")
                yield event.chain_result(message_chain)
            else:
                logger.warning("没有可用的服务器信息")
                yield event.plain_result("没有可用的服务器信息，请检查服务器是否在线")

        except Exception as e:
            logger.error(f"执行 mc 命令时出错: {e}")
            yield event.plain_result("查询服务器信息时发生错误")

    @filter.command("mcadd")
    async def mcadd(self, event: AstrMessageEvent, name: str, host: str, force: bool = False):
        """
        添加新的服务器

        Args:
            event: 消息事件
            name: 服务器名称
            host: 服务器地址
            force: 是否强制添加（跳过预查询检查）

        Returns:
            操作结果消息
        """
        logger.info(f"开始执行 mcadd 命令: {name} -> {host}, force: {force}")

        try:
            # 检查host合法性
            if not re.match(r'^[a-zA-Z0-9.,:]+$', host):
                yield event.plain_result("服务器地址格式不正确，只能包含字母、数字和符号.,:")
                return
            elif await get_server_status(host) is None and not force:
                yield event.plain_result("预查询失败，请检查服务器是否在线或地址是否正确，或在完整的/mcadd命令后加上True 强制添加")
                return

            group_id = event.get_group_id()
            json_path = await self.get_json_path(group_id)

            # 检查当前地址是否已存在
            try:
                json_data = await read_json(json_path)
                if json_data:
                    for existing_name, server_info in json_data.items():
                        if server_info['host'] == host:
                            yield event.plain_result(f"已存在相同地址的服务器 {existing_name}")
                            return
            except Exception as e:
                logger.error(f"检查服务器地址时出错: {e}")
                yield event.plain_result("检查服务器地址时发生错误")
                return

            if await add_data(json_path, name, host):
                yield event.plain_result(f"成功添加服务器 {name}")
            else:
                yield event.plain_result(f"无法添加 {name}，请检查是否已存在")

        except Exception as e:
            logger.error(f"执行 mcadd 命令时出错: {e}")
            yield event.plain_result("添加服务器时发生错误")

    @filter.command("mcdel")
    async def mcdel(self, event: AstrMessageEvent, name: str):
        """
        删除指定的服务器

        Args:
            event: 消息事件
            name: 要删除的服务器名称

        Returns:
            操作结果消息
        """
        logger.info(f"开始执行 mcdel 命令: {name}")
        try:
            group_id = event.get_group_id()
            json_path = await self.get_json_path(group_id)

            if await del_data(json_path, name):
                yield event.plain_result(f"成功删除服务器 {name}")
            else:
                yield event.plain_result(f"无法删除 {name}，请检查是否存在")

        except Exception as e:
            logger.error(f"执行 mcdel 命令时出错: {e}")
            yield event.plain_result("删除服务器时发生错误")

    @filter.command("mcget")
    async def mcget(self, event: AstrMessageEvent, name: str):
        """
        获取指定服务器的信息
        """
        group_id = event.get_group_id()
        json_path = await self.get_json_path(group_id)
        json_data = await read_json(json_path)
        if not json_data:
            yield event.plain_result("没有可用的服务器信息")
            return
        if name not in json_data:
            yield event.plain_result(f"没有找到服务器 {name}")
            return
        server_info = json_data[name]
        yield event.plain_result(f"{server_info['name']} 的地址是:")
        yield event.plain_result(f"{server_info['host']}")

    async def get_img(self, server_name: str, host: str) -> Optional[str]:
        """
        获取服务器信息图片

        Args:
            server_name: 服务器名称
            host: 服务器地址

        Returns:
            图片的base64编码字符串，如果获取失败则返回None
        """
        logger.info(f"开始获取服务器 {server_name} 的图片，主机地址: {host}")
        try:
            info = await get_server_status(host)
            if not info:
                logger.error(f"无法获取服务器 {server_name} 的状态信息")
                return None

            info['server_name'] = server_name
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

    async def get_json_path(self, group_id: str) -> Path:
        """
        获取群组的JSON配置文件路径

        Args:
            group_id: 群组ID

        Returns:
            JSON文件的Path对象
        """
        data_path = StarTools.get_data_dir("astrbot_mcgetter")
        json_path = data_path / f'{group_id}.json'
        json_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"群号 {group_id} 的 JSON 文件路径: {json_path}")
        return json_path
