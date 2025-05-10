import json
import asyncio
from pathlib import Path
import aiofiles
from typing import Dict, Any, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def write_json(json_path: str, new_data: Dict[str, Any]) -> None:
    """
    异步写入JSON数据到文件

    Args:
        json_path: JSON文件路径
        new_data: 要写入的数据字典

    Raises:
        IOError: 当文件写入失败时抛出
    """
    try:
        # 确保目录存在
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 异步写入，禁止转义
        async with aiofiles.open(json_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(new_data, indent=4, ensure_ascii=False))
        logger.info(f"成功写入JSON文件: {json_path}")
    except Exception as e:
        logger.error(f"写入JSON文件失败: {e}")
        raise IOError(f"写入JSON文件失败: {e}")

async def read_json(json_path: str) -> Dict[str, Any]:
    """
    异步读取JSON文件内容

    Args:
        json_path: JSON文件路径

    Returns:
        解析后的JSON数据字典

    Raises:
        IOError: 当文件读取失败时抛出
        json.JSONDecodeError: 当JSON解析失败时抛出
    """
    try:
        if not Path(json_path).exists():
            logger.info(f"JSON文件不存在，创建新文件: {json_path}")
            await write_json(json_path=json_path, new_data={})
            return {}

        async with aiofiles.open(json_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            logger.info(f"读取到的JSON内容: {content}")
            data = json.loads(content)
            logger.info(f"成功读取JSON文件: {json_path}, 数据: {data}")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}, 文件内容: {content if 'content' in locals() else '无法读取'}")
        raise json.JSONDecodeError(f"JSON解析失败: {e}", e.doc, e.pos)
    except Exception as e:
        logger.error(f"读取JSON文件失败: {e}, 文件路径: {json_path}")
        raise IOError(f"读取JSON文件失败: {e}")

async def add_data(json_path: str, name: str, host: str) -> bool:
    """
    向JSON文件添加新的服务器数据

    Args:
        json_path: JSON文件路径
        name: 服务器名称
        host: 服务器主机地址

    Returns:
        bool: 添加是否成功
    """
    try:
        data = await read_json(json_path)
        if name in data:
            logger.warning(f"服务器名称已存在: {name}")
            return False

        new_data = {
            name: {
                'name': name,
                'host': host
            }
        }
        data.update(new_data)
        await write_json(json_path, data)
        logger.info(f"成功添加服务器数据: {name}")
        return True
    except Exception as e:
        logger.error(f"添加服务器数据失败: {e}")
        return False

async def del_data(json_path: str, name: str) -> bool:
    """
    从JSON文件中删除服务器数据

    Args:
        json_path: JSON文件路径
        name: 要删除的服务器名称

    Returns:
        bool: 删除是否成功
    """
    try:
        data = await read_json(json_path)
        if name not in data:
            logger.warning(f"服务器名称不存在: {name}")
            return False

        del data[name]
        await write_json(json_path, data)
        logger.info(f"成功删除服务器数据: {name}")
        return True
    except Exception as e:
        logger.error(f"删除服务器数据失败: {e}")
        return False
