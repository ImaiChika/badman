from telethon import TelegramClient
import socks
api_id = '32805884'
api_hash = '0573c570f9296be684a0ebd0c80dedcf'
proxy = (socks.SOCKS5, '127.0.0.1', 7890, True)
with TelegramClient('anon', api_id, api_hash,proxy=proxy) as client:
   client.loop.run_until_complete(client.send_message('me', 'hello'))