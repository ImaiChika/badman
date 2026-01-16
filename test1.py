import json
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerEmpty
import asyncio
import socks  # 如果使用代理

# 替换为您的 API ID 和 API Hash
api_id = ''
api_hash = ''

# 指定频道用户名或 ID
channel_username = '@tddbda'
# '@XiaoHaiGe_SGK'
# 输出文件
output_file = 'channel_tddbda.json'  # 修改文件名以反映内容变化

# 每次请求的消息数量
limit_per_request = 100

# 总消息数量限制（0 表示无限制；这里基于总消息计数，但只保存有文本的消息）
total_limit = 1000000

# 代理配置（可选；如果不需要，注释掉下一行并移除 proxy=proxy）
proxy = (socks.SOCKS5, '127.0.0.1', 7890, True)

async def main():
    # 创建 Telegram 客户端（如果使用代理，添加 proxy=proxy）
    client = TelegramClient('session_name', api_id, api_hash, proxy=proxy)
    await client.start()

    # 授权部分
    try:
        if not await client.is_user_authorized():
            phone = input('Enter your phone number (e.g., +1234567890): ')
            await client.send_code_request(phone)
            code = input('Enter the code you received: ')
            await client.sign_in(phone, code)
    except SessionPasswordNeededError:
        password = input('Two-step verification is enabled. Enter your password: ')
        await client.sign_in(password=password)

    # 获取频道实体
    channel = await client.get_entity(channel_username)

    # 准备存储数据（现在只保存文本列表）
    texts_data = []  # 改为列表，只存文本字符串
    offset_id = 0
    total_fetched = 0

    while True:
        try:
            history = await client(GetHistoryRequest(
                peer=channel,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit_per_request,
                max_id=0,
                min_id=0,
                hash=0
            ))
        except Exception as e:
            print(f"Error: {e}. Retrying in 10 seconds...")
            await asyncio.sleep(10)
            continue

        if not history.messages:
            break

        for message in history.messages:
            if total_limit > 0 and total_fetched >= total_limit:
                break

            # 只提取文本（如果无文本，保存空字符串；如果想过滤空消息，添加 if message.message:）
            text = message.message if message.message else ''
            texts_data.append(text)  # 直接添加字符串到列表

            total_fetched += 1

        offset_id = history.messages[-1].id

        print(f'Fetched {total_fetched} messages so far...')

        if total_limit > 0 and total_fetched >= total_limit:
            break

    # 保存为 JSON（现在是一个字符串数组：["text1", "text2", ...]）
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(texts_data, f, ensure_ascii=False, indent=4)

    print(f'Data saved to {output_file}. Total texts: {len(texts_data)}')

# 运行异步主函数
asyncio.run(main())
