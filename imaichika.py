import json
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerEmpty
import asyncio
import socks  # 新增导入

# 替换为您的 API ID 和 API Hash
api_id = ''
api_hash = ''

# 指定频道用户名或 ID
channel_username = '@XiaoHaiGe_SGK'

# 输出文件
output_file = 'channel_data.json'

# 每次请求的消息数量
limit_per_request = 100

# 总消息数量限制（0 表示无限制）
total_limit = 10000

# 新增: 代理配置（例如 SOCKS5 代理；替换为您的代理 host/port/user/pass）
proxy = (socks.SOCKS5, '127.0.0.1', 7890, True) # 如果无认证: (socks.SOCKS5, 'host', port)

async def main():
    # 创建 Telegram 客户端，并添加代理
    client = TelegramClient('session_name', api_id, api_hash, proxy=proxy)
    await client.start()

    # 授权部分（同原脚本）
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

    # 准备存储数据
    messages_data = []
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
        except Exception as e:  # 新增: 捕获异常并重试
            print(f"Error: {e}. Retrying in 10 seconds...")
            await asyncio.sleep(10)  # 等待 10 秒后重试
            continue

        if not history.messages:
            break

        for message in history.messages:
            if total_limit > 0 and total_fetched >= total_limit:
                break

            data = {
                'id': message.id,
                'date': str(message.date),
                'sender_id': message.sender_id,
                'text': message.message if message.message else '',
                'reply_to': message.reply_to_msg_id if message.reply_to else None,
            }
            messages_data.append(data)
            total_fetched += 1

        offset_id = history.messages[-1].id

        print(f'Fetched {total_fetched} messages so far...')

        if total_limit > 0 and total_fetched >= total_limit:
            break

    # 保存为 JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(messages_data, f, ensure_ascii=False, indent=4)

    print(f'Data saved to {output_file}. Total messages: {len(messages_data)}')

# 运行异步主函数
asyncio.run(main())
