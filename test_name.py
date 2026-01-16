import json
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
import asyncio
import socks

# ==================== 配置区 ====================
api_id = '32805884'
api_hash = '0573c570f9296be684a0ebd0c80dedcf'

channel_username = '@LMYYDS8'          # 要爬的频道
output_file = 'nchannel_LMYYDS8.json'   # 保存文件

total_limit = 1000000                 # 最大消息数，0=无限制
limit_per_request = 100

# 代理（Clash/V2Ray/Shadowsocks 默认端口 7890 无密码的正确写法）
proxy = (socks.SOCKS5, '127.0.0.1', 7890, True)
# ================================================

async def main():
    # 如果你不需要代理，把 proxy=proxy 删掉即可
    client = TelegramClient('session_name', api_id, api_hash, proxy=proxy)
    await client.start()

    # 登录（已经登录过以后就不会再问）
    if not await client.is_user_authorized():
        phone = input('Enter your phone number: ')
        await client.send_code_request(phone)
        code = input('Enter code: ')
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input('2FA password: ')
            await client.sign_in(password=password)

    channel = await client.get_entity(channel_username)

    messages_data = []  # 改为存储字典列表，便于大模型学习（如对话数据集）
    user_cache = {}     # 缓存用户ID到用户名的映射，避免重复查询
    offset_id = 0
    total_fetched = 0

    print("开始爬取，按 Ctrl+C 可随时中断并保存已获取的数据...\n")

    try:
        while True:
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

            if not history.messages:
                print("已到达频道最旧消息，爬取完成。")
                break

            for message in history.messages:
                if total_limit > 0 and total_fetched >= total_limit:
                    print("已达到设定的 total_limit，停止爬取。")
                    break

                # 获取用户名（使用缓存优化）
                username = "unknown"
                if message.sender_id:
                    if message.sender_id not in user_cache:
                        try:
                            user = await client.get_entity(message.sender_id)
                            user_cache[message.sender_id] = user.username if user.username else f"user_{message.sender_id}"
                        except Exception as e:
                            print(f"获取用户 {message.sender_id} 失败: {e}")
                            user_cache[message.sender_id] = "unknown"
                    username = user_cache[message.sender_id]
                else:
                    username = channel_username.strip('@')  # 如果无发送者，用频道名

                text = message.message if message.message else ''

                # 保存为字典格式
                messages_data.append({
                    "username": username,
                    "text": text
                })
                total_fetched += 1

                # 实时显示进度
                if total_fetched % 500 == 0:
                    print(f'已爬取 {total_fetched} 条...')

            offset_id = history.messages[-1].id

            if total_limit > 0 and total_fetched >= total_limit:
                break

            # 防 FloodWait（可根据需要调整）
            await asyncio.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断！正在保存已爬取的数据...")
    except Exception as e:
        print(f"\n发生错误: {e}")
    finally:
        # 无论正常结束还是 Ctrl+C，这里都会执行保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(messages_data, f, ensure_ascii=False, indent=4)
        print(f"保存完成！共 {len(messages_data)} 条消息 → {output_file}")

asyncio.run(main())