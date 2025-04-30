import json
import asyncio
from pathlib import Path
import aiofiles


async def write_json(json_path: str, new_data: dict):
    # 确保目录存在
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    # 异步写入
    # 禁止转义
    async with aiofiles.open(json_path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(new_data, indent=4, ensure_ascii=False))


async def read_json(json_path: str):
    if not Path(json_path).exists():
        await write_json(json_path=json_path, new_data={})
    # 异步读取
    async with aiofiles.open(json_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        data = json.loads(content)
        return data


async def add_data(json_path: str, name: str, host: str):
    if name in data:
        return False
    data = await read_json(json_path)
    new_data = {
        name: {
            'name': name,
            'host': host
        }
    }
    data.update(new_data)
    await write_json(json_path, data)
    return True


async def del_data(json_path: str, name: str):
    data = await read_json(json_path)
    if name in data:
        del data[name]
        await write_json(json_path, data)
        return True
    return False
