import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from typing import Tuple, Optional


def fetch_stock_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """获取单只股票数据并验证结构"""
    print(f"获取 {ticker} 数据...")
    data = yf.download(ticker, start=start, end=end, progress=False)
    if data.empty:
        raise ValueError(f"无法获取 {ticker} 的数据")

    # 处理多层列名（如果存在）
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]

    print("\n数据结构:")
    print(data.head())
    return data


def fetch_multi_stock_data(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """获取多只股票数据"""
    print("\n获取多只股票数据...")
    data = yf.download(tickers, start=start, end=end, progress=False)
    return data


def fetch_stock_info(ticker: str) -> dict:
    """获取股票基本信息"""
    print("\n获取股票基本信息...")
    stock = yf.Ticker(ticker)
    info = stock.info
    print(f"公司名称: {info.get('longName', 'N/A')}")
    print(f"行业: {info.get('industry', 'N/A')}")
    print(f"市值: {info.get('marketCap', 'N/A')}")
    return info


def clean_data(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """清洗数据并返回处理后的 DataFrame"""
    print("\n开始清洗数据...")

    # 确保索引为日期类型
    df.index = pd.to_datetime(df.index)

    # 处理列名（确保单层）
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    # 核心清洗步骤
    df = (df.dropna()
          .drop_duplicates()
          .sort_index())

    if df.empty:
        print("警告：清洗后数据为空！")
        return None



    # 处理异常值
    if 'Close' in df.columns:
        df['Close'] = df['Close'].where(df['Close'] > 0, df['Close'].shift(1))
    else:
        print("错误：缺少 'Close' 列！")
        return None


    # 转换数据类型
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    print("清洗后数据预览:")
    print(df.head())
    return df


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """处理数据，添加计算指标"""
    df['Returns'] = df['Close'].pct_change()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    return df


def visualize_data(df: pd.DataFrame, ticker: str):
    """可视化数据，包括价格、均线和成交量"""
    if df is None or df.empty:
        print("错误：无法可视化空数据！")
        return

    # 创建子图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True,
                                   gridspec_kw={'height_ratios': [3, 1]})

    # 上图：价格和均线
    ax1.plot(df.index, df['Close'], label='Close Price', color='blue')
    ax1.plot(df.index, df['MA20'], label='20-Day MA', color='orange')
    ax1.plot(df.index, df['MA60'], label='60-Day MA', color='green')
    ax1.set_title(f"{ticker} Stock Price and Moving Averages")
    ax1.set_ylabel("Price")
    ax1.legend()
    ax1.grid(True)

    # 下图：成交量
    ax2.bar(df.index, df['Volume'], color='gray', alpha=0.7)
    ax2.set_title("Trading Volume")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Volume")
    ax2.grid(True)

    # 调整布局
    plt.tight_layout()
    plt.show()


def save_data(df: pd.DataFrame, csv_file: str = "stock_data.csv",
              excel_file: str = "stock_data.xlsx"):
    """保存数据到 CSV 和 Excel"""
    if df is None or df.empty:
        print("错误：无法保存空数据！")
        return

    # 保存到 CSV
    df.to_csv(csv_file, float_format='%.2f')
    print(f"数据已保存到 {csv_file}")

    # 保存到 Excel
    df.index = df.index.strftime('%Y-%m-%d')
    df.to_excel(excel_file, float_format='%.2f', index_label='Date')
    print(f"数据已保存到 {excel_file}")


def main():
    """主函数"""
    # 参数配置
    ticker = "AAPL"
    start_date = "2023-01-01"
    end_date = "2024-02-19"

    # 获取数据
    single_stock = fetch_stock_data(ticker, start_date, end_date)
    multi_stocks = fetch_multi_stock_data(['AAPL', 'GOOGL', 'MSFT'], start_date, end_date)
    fetch_stock_info(ticker)

    # 清洗和处理数据
    cleaned_data = clean_data(single_stock)
    if cleaned_data is None:
        print("错误：数据清洗失败，无法继续！")
        return

    processed_data = process_data(cleaned_data)

    # 可视化和保存
    visualize_data(processed_data, ticker)
    save_data(processed_data, f"{ticker}_stock_data.csv", f"{ticker}_stock_data.xlsx")


if __name__ == "__main__":
    main()