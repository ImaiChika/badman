from telethon import TelegramClient
import socks
api_id = ''
api_hash = ''
proxy = (socks.SOCKS5, '127.0.0.1', 7890, True)
with TelegramClient('anon', api_id, api_hash,proxy=proxy) as client:
   client.loop.run_until_complete(client.send_message('me', 'hello'))
