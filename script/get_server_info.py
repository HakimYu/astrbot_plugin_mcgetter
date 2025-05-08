import asyncio
import aiohttp
from mcstatus import JavaServer
import socket
import base64
from pathlib import Path
import re
from typing import Optional, Dict, List, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 常量配置
CSU_HOST = 'csu-mc.org'
CSU_PLAYERS_URL = 'https://map.magicalsheep.cn/tiles/players.json'
DEFAULT_ICON_PATH = Path(__file__).resolve().parent.parent / 'resource' / 'default_icon.png'

async def get_server_status(host: str) -> Optional[Dict[str, Any]]:
    """
    异步获取Minecraft服务器状态信息

    Args:
        host: 服务器主机名或IP地址

    Returns:
        包含服务器信息的字典，如果获取失败则返回None
    """
    try:
        server = await JavaServer.async_lookup(host)
        status = await server.async_status()
        
        # 获取玩家列表
        players_list = []
        if status.players.sample:
            players_list = [player.name for player in status.players.sample]
        
        # 特殊处理CSU服务器
        if host == CSU_HOST:
            players_list = await fetch_players_names(CSU_PLAYERS_URL)

        # 获取服务器图标
        icon_data = await get_server_icon(status.icon)

        return {
            "players_list": players_list,
            "latency": int(status.latency),
            "plays_max": status.players.max,
            "plays_online": status.players.online,
            "server_version": status.version.name,
            "icon_base64": icon_data,
        }

    except (socket.gaierror, ConnectionRefusedError, asyncio.TimeoutError) as e:
        logger.error(f"查询服务器状态时出错: {e}")
        return None
    except Exception as e:
        logger.error(f"发生未知错误: {e}")
        return None

async def get_server_icon(icon_data: Optional[str]) -> str:
    """
    获取服务器图标的base64编码

    Args:
        icon_data: 服务器图标的base64字符串

    Returns:
        图标的base64编码字符串
    """
    if icon_data:
        return icon_data.split(",")[1]
    
    try:
        with open(DEFAULT_ICON_PATH, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"读取默认图标失败: {e}")
        return ""

async def fetch_players_names(url: str) -> List[str]:
    """
    异步获取并解析玩家名称列表，过滤掉bot玩家

    Args:
        url: 数据接口URL

    Returns:
        过滤后的玩家名称列表

    Raises:
        ValueError: 当请求失败时抛出
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"请求失败，状态码: {response.status}")

                data = await response.json()
                names = [player["name"] for player in data.get("players", [])]
                return [name for name in names if not re.match(r'^bot_', name)]
    except Exception as e:
        logger.error(f"获取玩家列表失败: {e}")
        return []

async def main() -> None:
    """主函数，用于测试服务器状态获取"""
    host = CSU_HOST
    result = await get_server_status(host)
    if result:
        logger.info(f"服务器状态: {result}")
    else:
        logger.error("未获取到服务器状态信息")

if __name__ == "__main__":
    asyncio.run(main())