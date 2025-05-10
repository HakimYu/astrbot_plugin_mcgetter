import asyncio
import aiohttp
from mcstatus import JavaServer
import socket
import base64
from pathlib import Path
import re
from typing import Optional, Dict, List, Any, Union
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 常量配置
CSU_HOST: str = 'csu-mc.org'
CSU_PLAYERS_URL: str = 'https://map.magicalsheep.cn/tiles/players.json'
DEFAULT_ICON_PATH: Path = Path(__file__).resolve().parent.parent / 'resource' / 'default_icon.png'

async def get_server_status(host: str) -> Optional[Dict[str, Any]]:
    """
    异步获取Minecraft服务器状态信息

    Args:
        host: 服务器主机名或IP地址

    Returns:
        Optional[Dict[str, Any]]: 包含以下键的字典：
            - players_list: List[str] - 在线玩家列表
            - latency: int - 服务器延迟（毫秒）
            - plays_max: int - 最大玩家数
            - plays_online: int - 当前在线玩家数
            - server_version: str - 服务器版本
            - icon_base64: str - 服务器图标的base64编码
        如果获取失败则返回None
    """
    try:
        server = await JavaServer.async_lookup(host)
        status = await server.async_status(timeout=10)  # 添加10秒超时
        
        # 获取玩家列表
        players_list = []
        if status.players.sample:
            players_list = [player.name for player in status.players.sample]
        
        # 特殊处理CSU服务器
        if host == CSU_HOST:
            try:
                players_list = await fetch_players_names(CSU_PLAYERS_URL)
            except Exception as e:
                logger.warning(f"获取CSU玩家列表失败，使用默认玩家列表: {e}")

        # 获取服务器图标
        icon_data = await get_server_icon(status.icon)

        # 按字母排序玩家列表
        players_list.sort()

        return {
            "players_list": players_list,
            "latency": int(status.latency),
            "plays_max": status.players.max,
            "plays_online": status.players.online,
            "server_version": status.version.name,
            "icon_base64": icon_data,
        }

    except (socket.gaierror, ConnectionRefusedError) as e:
        logger.error(f"连接服务器失败: {e}")
        return None
    except asyncio.TimeoutError:
        logger.error(f"获取服务器状态超时")
        return None
    except Exception as e:
        logger.error(f"获取服务器状态时发生未知错误: {e}")
        return None

async def get_server_icon(icon_data: Optional[str]) -> str:
    """
    获取服务器图标的base64编码

    Args:
        icon_data: Optional[str] - 服务器图标的base64字符串，如果为None则使用默认图标

    Returns:
        str: 图标的base64编码字符串，如果获取失败则返回空字符串
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
        url: str - 数据接口URL

    Returns:
        List[str]: 过滤后的玩家名称列表，如果获取失败则返回空列表

    Raises:
        ValueError: 当请求失败时抛出
    """
    try:
        timeout = aiohttp.ClientTimeout(total=10)  # 10秒超时
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"请求失败，状态码: {response.status}")

                data = await response.json()
                names = [player["name"] for player in data.get("players", [])]
                return [name for name in names if not re.match(r'^bot_', name)]
    except aiohttp.ClientError as e:
        logger.error(f"HTTP请求失败: {e}")
        return []
    except ValueError as e:
        logger.error(f"数据解析失败: {e}")
        return []
    except Exception as e:
        logger.error(f"获取玩家列表时发生未知错误: {e}")
        return []

async def main() -> None:
    """
    主函数，用于测试服务器状态获取
    
    测试CSU服务器的状态信息获取功能
    """
    host = CSU_HOST
    result = await get_server_status(host)
    if result:
        logger.info(f"服务器状态: {result}")
    else:
        logger.error("未获取到服务器状态信息")

if __name__ == "__main__":
    asyncio.run(main())