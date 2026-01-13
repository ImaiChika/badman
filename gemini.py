import json
import re
import jieba
import jieba.analyse
import jieba.posseg as pseg  # 引入词性标注
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import sys

# --- [修复1] 解决 Windows 控制台打印 Emoji 报错的问题 ---
# 强制标准输出使用 utf-8 编码
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass  # Python版本过低可能不支持，后续代码有兜底方案

# --- [改进2] 通用停用词表 (只保留最基础的中文停用词) ---
# 这些词在任何中文语境下都是无意义的，不需要针对特定群组修改
GENERAL_STOP_WORDS = {
    "什么", "有没有", "可以", "不知道", "怎么", "这个", "那个", "其实", "就是",
    "还有", "因为", "所以", "但是", "需要", "现在", "今天", "明天", "出来",
    "签到", "感觉", "觉得", "时候", "这里", "那里", "一直", "不能", "可能",
    "大家", "兄弟", "老板", "私聊", "私信", "回复", "加我", "好友", "TG", "飞机"
}

# --- [改进3] 扩展的通用语义规则库 ---
# 只要命中这些词，就能给任何群打标签
CONTEXT_RULES = {
    "fraud": ["跑分", "车队", "赔付", "通道", "U出", "点位", "码商", "骗子", "免押", "回U", "日结"],
    "gambling": ["注单", "包赢", "回血", "上岸", "下注", "彩票", "六合", "特码"],
    "trade": ["收", "出", "求购", "低价", "实名", "账号", "汇率", "代开", "接码", "CVV"],
    "social": ["互粉", "小姐姐", "约", "同城", "上门", "兼职", "精聊"],
    "hacking": ["查询", "开房", "记录", "定位", "全家户", "机主"]
}


class UniversalProfiler:
    def __init__(self, filepath):
        self.filepath = filepath
        self.messages = []
        self.users = []
        self.full_text = ""
        self.words_with_pos = []  # 存储 (词, 词性)
        self.entities = {"phone": [], "crypto": [], "sensitive": []}
        self.load_data()

    def load_data(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 预处理：只保留有内容的文本
                self.messages = [m for m in data if m.get('text') and len(m.get('text')) > 1]
        except Exception as e:
            print(f"读取文件失败: {e}")

    def is_garbage_string(self, text):
        """[核心算法] 自动识别乱码/垃圾字符串"""
        # 1. 如果全是字母且长度超过8，大概率是炸群乱码 (如 HJUIUGN...)
        if re.match(r'^[a-zA-Z]{8,}$', text):
            return True
        # 2. 如果包含大量重复字符 (如 111111, aaaaaa)
        if re.search(r'(.)\1{4,}', text):
            return True
        return False

    def clean_and_extract(self):
        """清洗文本并分离实体"""
        clean_sentences = []

        for msg in self.messages:
            text = msg.get('text', '')
            user = msg.get('username', 'unknown')

            if user != 'unknown':
                self.users.append(user)

            # 1. 垃圾过滤 (通用算法，不再依赖硬编码)
            if self.is_garbage_string(text):
                continue

            # 2. 隐私提取 (正则增强)
            # 手机号
            phones = re.findall(r'(?:\+?86)?(?:1[3-9]\d{9})', text)
            if phones:
                tag = "被动曝光" if any(x in text for x in ['骗', '死', '狗']) else "主动引流"
                for p in phones: self.entities['phone'].append(f"{p} ({tag})")

            # 虚拟币地址 (TRC20)
            cryptos = re.findall(r'T[A-Za-z0-9]{33}', text)
            self.entities['crypto'].extend(cryptos)

            # 3. 文本预处理
            # 去除URL、表情、数字
            text_clean = re.sub(r'http\S+', '', text)
            text_clean = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', '', text_clean)  # 仅保留中英文

            clean_sentences.append(text_clean)

        # 4. [核心算法] 词性标注过滤 (NLP通用方案)
        # 将所有句子合并处理，利用 jieba.posseg 提取有意义的词
        big_text = " ".join(clean_sentences)
        words = pseg.cut(big_text)

        valid_words = []
        for word, flag in words:
            # 过滤规则：
            # 1. 长度必须 > 1
            # 2. 不在通用停用词表中
            # 3. 词性必须是：名词(n), 动词(v), 英文(eng)
            if (len(word) > 1 and
                    word not in GENERAL_STOP_WORDS and
                    (flag.startswith('n') or flag.startswith('v') or flag == 'eng')):
                valid_words.append(word)

        self.full_text = " ".join(valid_words)

    def analyze_keywords(self):
        """基于 TF-IDF 提取关键词 (具有统计学意义)"""
        if not self.full_text: return []
        # 使用 jieba 的 TF-IDF 算法，它内部有 IDF 语料库，能自动降低常见词的权重
        keywords = jieba.analyse.extract_tags(self.full_text, topK=30, withWeight=True)
        return keywords

    def determine_group_nature(self, keywords):
        """规则推理引擎"""
        scores = {k: 0 for k in CONTEXT_RULES.keys()}
        word_list = [k[0] for k in keywords]

        for word in word_list:
            for category, vocab in CONTEXT_RULES.items():
                # 模糊匹配：只要关键词包含库里的词 (如 "收U" 包含 "U")
                if any(v in word for v in vocab):
                    scores[category] += 1

        nature = max(scores, key=scores.get)
        if scores[nature] == 0: return "综合闲聊/未定义"

        mapping = {
            "fraud": "灰产供需/高风险 (涉及跑分/赔付)",
            "gambling": "非法博彩/网赌推广",
            "trade": "账号/资源交易",
            "social": "社交/引流",
            "hacking": "社工查询/隐私窃取"
        }
        return mapping[nature]

    def generate_report(self, keywords, nature):
        """生成文本报告"""

        # 安全打印：移除可能导致 GBK 报错的字符
        def safe_str(s):
            return s.encode('gbk', 'ignore').decode('gbk')

        top_words = "、".join([k[0] for k in keywords[:8]])
        leak_count = len(self.entities['phone'])

        print("\n" + "=" * 40)
        print(f"【群组画像报告】")
        print(f"核心属性: {safe_str(nature)}")
        print(f"高频话题: {safe_str(top_words)}")
        print(f"隐私风险: 监测到 {leak_count} 条手机号/钱包地址泄露。")
        print("=" * 40)

        print("\n[Top 15 关键热词权重]")
        for k, w in keywords[:15]:
            print(f" - {safe_str(k):<10} : {w:.4f}")

    def draw_wordcloud(self):
        """生成词云图"""
        if not self.full_text: return
        try:
            # 这里的 font_path 需要确保你电脑上有，Windows 一般都有
            wc = WordCloud(
                font_path='msyh.ttc',
                width=800, height=400,
                background_color='white',
                max_words=100,
                collocations=False  # 避免词语重复
            ).generate(self.full_text)

            plt.figure(figsize=(10, 5))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis('off')
            plt.title("Group Content WordCloud")
            plt.show()
        except Exception as e:
            print(f"词云生成失败，可能是字体路径问题: {e}")


# --- 主程序执行 ---
if __name__ == "__main__":
    # 请确保文件名正确
    profiler = UniversalProfiler('nchannel_hc8668.json')
    profiler.clean_and_extract()

    # 如果数据太少，提示用户
    if not profiler.full_text:
        print("数据量过少或已被完全过滤，无法生成画像。")
    else:
        keywords = profiler.analyze_keywords()
        nature = profiler.determine_group_nature(keywords)

        profiler.generate_report(keywords, nature)

        # 核心人物
        core_users = Counter(profiler.users).most_common(5)
        print("\n[活跃核心用户]")
        for u, c in core_users:
            print(f" - {u}: {c} 次")

        # 生成可视化
        # profiler.draw_wordcloud()