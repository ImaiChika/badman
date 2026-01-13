import json
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
#export HF_HUB_DOWNLOAD_TIMEOUT=60  # 默认10秒，改成60秒或更大，如300
#export HF_HUB_ENABLE_HF_TRANSFER=1
import re
import jieba.analyse
import jieba.posseg as pseg
from collections import Counter
import sys
# 新导入：LLM相关
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

# ==========================================
# 1. 环境编码适配 (核心修复：解决乱码)
# ==========================================
def setup_encoding():
    # 强制标准输出使用 UTF-8
    if sys.platform.startswith('win'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print(f"系统当前编码: {sys.stdout.encoding}")
setup_encoding()

# ==========================================
# 2. 通用语义配置 (增强泛化能力)
# ==========================================
# 核心业务词库映射 (用于多场景画像)
INDUSTRY_MAP = {
    "灰黑产/跑分": ["跑分", "车队", "赔付", "通道", "U出", "码商", "点位", "码量", "接单"],
    "网络博彩": ["注单", "包赢", "回血", "上岸", "下注", "特码", "彩票", "反波胆"],
    "资源交易": ["收", "出", "求购", "低价", "实名", "账号", "接码", "CVV", "汇率"],
    "兼职招聘": ["兼职", "求职", "招人", "日结", "工资", "诚意", "包吃住", "海外"],
    "技术/渗透": ["查询", "开房", "记录", "定位", "全家户", "机主", "拖库", "渗透"]
}

class AdvancedUniversalProfiler:
    def __init__(self, filename):
        self.filename = filename
        self.entities = {"phone": [], "crypto": []}
        self.user_stats = Counter()
        self.clean_corpus = []
        
        # 新增：加载LLM (量化高效)
        quantization_config = BitsAndBytesConfig(load_in_8bit=True)
        model_name = "Qwen/Qwen-7B-Chat"  # 或最新Qwen3版本，如"Qwen/Qwen3-7B-Instruct"
        #self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        #self.model = AutoModelForCausalLM.from_pretrained(model_name, quantization_config=quantization_config, device_map="auto")
        model_path = "./Qwen-7B-Chat"  # 根据实际路径调整

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True   # Qwen 系列必须加这个
        )
    def safe_print(self, msg):
        """安全打印函数，防止 GBK 终端因某些字符报错"""
        try:
            print(msg)
        except UnicodeEncodeError:
            # 如果终端实在不支持 UTF-8，则过滤掉无法编码的字符
            print(msg.encode('gbk', 'ignore').decode('gbk'))
    
    def load_and_preprocess(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.safe_print(f"错误：无法读取文件 {e}")
            return
        
        for msg in data:
            text = msg.get('text', '')
            user = msg.get('username', 'unknown')
            if not text or len(text) < 2: continue
            
            # 1. 过滤机械重复垃圾 (如 HJUIUGN)
            if re.match(r'^[a-zA-Z]{5,}$', text) or re.search(r'(.)\1{4,}', text):
                continue
            
            # 2. 核心人物统计 (排除机器人和未知)
            if user != 'unknown':
                self.user_stats[user] += 1
            
            # 修改隐私检测：用LLM验证上下文
            phones = re.findall(r'(?:\+?86)?(?:1[3-9]\d{9})', text)
            if phones:
                prompt = f"""分析中文文本：'{text}'
                - 判断隐私泄露类型：如果含'我'或自述，则'主动'；如果曝光或负面，则'被动'。
                - 输出格式：类型 [手机: {phones[0]}]"""
                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
                outputs = self.model.generate(**inputs, max_new_tokens=50)
                leak_info = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                self.entities["phone"].append(leak_info)
            
            # 修改语义提取：用LLM替换pseg，抽取关键词
            prompt = f"""从中文群聊消息抽取核心名词/动词：'{text}'
            - 排除通用词如'没有'、'可以'。
            - 输出列表：词1,词2,..."""
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(**inputs, max_new_tokens=100)
            extracted_words = self.tokenizer.decode(outputs[0], skip_special_tokens=True).split(',')
            self.clean_corpus.extend([w.strip() for w in extracted_words if len(w) > 1])
    
    def analyze(self):
        full_text = " ".join(self.clean_corpus)
        
        # 修改关键词提取：用LLM
        prompt = f"""从中文群聊语料总结Top 20关键词：'{full_text[:2000]}'  # 截取避免过长
        - 考虑上下文，如黑产相关。
        - 输出：关键词1 (权重), 关键词2 (权重), ..."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, max_new_tokens=200)
        keywords_str = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        keywords = [(k.split(' (')[0], float(k.split(' (')[1][:-1])) for k in keywords_str.split(', ')]  # 解析
        
        # 修改分类：用LLM增强匹配
        prompt = f"""基于关键词：{', '.join([k[0] for k in keywords])}
        和预定义类别：{list(INDUSTRY_MAP.keys())}
        - 分类群组性质，并解释。"""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, max_new_tokens=100)
        final_nature = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 原报告打印，替换为LLM生成的完整画像
        prompt = f"""生成群组画像报告：
        - 核心定位：{final_nature}
        - 关键词云：{', '.join([k[0] for k in keywords[:8]])}
        - 人物Top3：{self.user_stats.most_common(3)}
        - 隐私：{self.entities['phone']}
        - 用中文格式化输出。"""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, max_new_tokens=300)
        report = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        self.safe_print(report)

# 运行
if __name__ == "__main__":
    # 传入你的数据集路径
    profiler = AdvancedUniversalProfiler('nchannel_hc8668.json')
    profiler.load_and_preprocess()
    profiler.analyze()