import asyncio
from mcstatus import JavaServer
import socket
import base64
from pathlib import Path

async def get_server_status(host):
    try:
        # 调用mcstatus获取服务器信息
        server = await JavaServer.async_lookup(host)
        # 使用异步方法查询服务器状态
        status = await server.async_status()

        players_list = []
        latency = int(status.latency)
        plays_max = status.players.max
        plays_online = status.players.online
        server_version = status.version.name

        #保存服务器图标
        if status.icon:
            icon_data = status.icon.split(",")[1]
        else:
            image_path=Path(__file__).resolve().parent.parent/'resource'/'default_icon.png'
            with open(image_path, 'rb') as image_file:
                # 读取图片文件内容
                image_data = image_file.read()
                # 对图片数据进行 Base64 编码
                base64_encoded = base64.b64encode(image_data)
            # 将编码后的字节数据转换为字符串
            icon_data = base64_encoded.decode('utf-8')

        # 查询服务器状态
        if status.players.sample:
            for player in status.players.sample:
                players_list.append(player.name)

        return {
            "players_list": players_list,#玩家昵称列表
            "latency": latency,#延迟
            "plays_max": plays_max,#最大玩家数
            "plays_online": plays_online,#在线玩家数
            "server_version": server_version,#服务器游戏版本
            "icon_base64":icon_data,#服务器图标base64
        }

    except (socket.gaierror, ConnectionRefusedError, asyncio.TimeoutError) as e:
        print(f"查询服务器状态时出错: {e}")
        return None


# 示例调用
if __name__ == "__main__":
    host = "p3.ytonidc.com:36008"  # 替换为实际的服务器地址和端口
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(get_server_status(host))
    if result:
        print(result)
