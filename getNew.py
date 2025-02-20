import pandas as pd
import requests
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import matplotlib.font_manager as fm

# 下载NLTK数据
print("检查并下载NLTK资源...")
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)


# 获取系统中可用字体并选择支持中文的字体
def get_available_chinese_font():
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    # 常见的支持中文的字体
    chinese_fonts = [
        "Microsoft YaHei",  # Windows常见
        "SimHei",  # Windows常见
        "PingFang SC",  # macOS常见
        "Arial Unicode MS",  # 跨平台常见
        "Noto Sans CJK SC",  # Linux常见
        "STHeiti",  # macOS旧字体
        "WenQuanYi Micro Hei"  # Linux常见
    ]

    for font in chinese_fonts:
        if font in available_fonts:
            print(f"找到支持中文的字体: {font}")
            return font

    print("未找到常见的支持中文字体，使用默认字体（可能不支持中文显示）。")
    print("可用字体列表:", available_fonts[:20])  # 打印前20个字体作为参考
    return "sans-serif"  # 回退到默认字体


# 设置字体
font_family = get_available_chinese_font()
plt.rcParams['font.family'] = font_family
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class NewsSentimentAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

        print("正在加载BERT情绪分析模型（显式PyTorch）...")
        model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def get_news(self, query, language="en", page_size=20):
        params = {"q": query, "apiKey": self.api_key, "language": language, "pageSize": page_size,
                  "sortBy": "publishedAt"}
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json().get('articles', [])
        except requests.exceptions.RequestException as e:
            print(f"获取新闻时出错: {e}")
            return []

    def preprocess_text(self, text):
        if not text or pd.isna(text):
            return ""
        text = text.lower()
        text = re.sub(r'<.*?>', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'http\S+', '', text)
        words = word_tokenize(text)
        words = [self.lemmatizer.lemmatize(word) for word in words if word not in self.stop_words]
        return " ".join(words)

    def analyze_sentiment(self, text):
        if not text or len(text.strip()) == 0:
            return "中性", 0.0

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits

        probs = torch.softmax(logits, dim=1)
        score = probs[0][1].item()
        label = torch.argmax(probs, dim=1).item()

        if label == 1 and score > 0.5:
            return "正面", score
        elif label == 0 and score > 0.5:
            return "负面", -(1 - score)
        else:
            return "中性", 0.0

    def process_and_analyze(self, query):
        print(f"正在获取关于 '{query}' 的新闻...")
        articles = self.get_news(query)
        if not articles:
            return None

        data = [{
            '标题': a.get('title', ''),
            '描述': a.get('description', '') or '',
            '内容': a.get('content', '') or '',
            '发布时间': a.get('publishedAt', ''),
            '来源': a.get('source', {}).get('name', ''),
            '链接': a.get('url', '')
        } for a in articles]

        df = pd.DataFrame(data)

        print("正在预处理数据...")
        df['cleaned_text'] = (df['标题'] + " " + df['描述']).apply(self.preprocess_text)

        print("正在进行情绪分析...")
        df['情绪类别'], df['情绪得分'] = zip(*df['cleaned_text'].apply(self.analyze_sentiment))

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_sentiment_{query}_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"结果已保存到 {filename}")

        return df

    def visualize_results(self, df):
        plt.figure(figsize=(12, 6))

        plt.subplot(1, 2, 1)
        sns.countplot(data=df, x='情绪类别', hue='情绪类别', palette='viridis', legend=False)
        plt.title('情绪类别分布')
        plt.xlabel('情绪类别')
        plt.ylabel('数量')

        plt.subplot(1, 2, 2)
        sns.histplot(data=df, x='情绪得分', bins=20, kde=True, color='blue')
        plt.title('情绪得分分布')
        plt.xlabel('情绪得分 (-1到1)')
        plt.ylabel('频率')

        plt.tight_layout()
        plt.show()


def main():
    API_KEY = "9c51d59aa2094d968a27ac27d0565af6"  # 替换为实际密钥
    analyzer = NewsSentimentAnalyzer(API_KEY)
    query = "000001"
    result = analyzer.process_and_analyze(query)

    if result is not None:
        df = result
        print("\n情绪分析统计:")
        print("=" * 50)
        print(df['情绪类别'].value_counts())
        print(f"平均情绪得分: {df['情绪得分'].mean():.3f}")
        analyzer.visualize_results(df)


if __name__ == "__main__":
    main()