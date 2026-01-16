# Telegram 频道消息爬取工具

一个简单、高效的 Telegram 频道历史消息批量下载工具，使用 **Telethon** 实现。

主要用于：

- 频道内容归档
- 数据分析
- 制作对话数据集
- 大模型微调/预训练语料收集
- 内容研究与备份

## 功能特点

- 支持 SOCKS5 代理（Clash/V2Ray/Shadowsocks 常用方式）
- 自动缓存用户名，避免重复查询
- 支持随时 Ctrl+C 中断并保存已爬取数据
- 输出格式为干净的 JSON 数组，便于后续处理
- 可设置最大爬取条数（total_limit）
- 每条消息记录发送者用户名 + 文本内容
- 防 flood wait 机制（可调）

## 输出格式示例

```json
[
    {
        "username": "CryptoWhale",
        "text": "BTC 又双叒叕新高了！🚀"
    },
    {
        "username": "LMYYDS8",
        "text": "今晚8点开播，主题：2025年最值得关注的5个赛道"
    },
    ...
]
```

## 使用方法

```
pip install telethon

前往 https://my.telegram.org → 登录 → API development tools → 创建新应用

大陆用户通常需要代理才能正常连接 Telegram
```
```
api_id = '你的API_ID'           # ← 必填
api_hash = '你的API_HASH'       # ← 必填

channel_username = '@你要爬的频道'   # 如 '@LMYYDS8'
output_file = '爬取结果文件名.json'   # 建议带日期或频道名

total_limit = 1000000           # 想爬多少条？0=全部
limit_per_request = 100         # 一般无需改

# 代理（根据自己实际情况修改或删除）
proxy = (socks.SOCKS5, '127.0.0.1', 7890, True)
# 如果不用代理，直接删除 proxy=proxy 这行参数即可
```
## 执行程序
```
python test_name.py
第一次运行会要求输入手机号 → 验证码 → （如果有）两步验证密码
之后就会开始自动爬取～
随时按 Ctrl+C 可安全中断，程序会自动保存当前已爬取的数据
再次运行会从头开始（目前版本暂不支持断点续传）
```
祝爬取愉快～ 📥✨
