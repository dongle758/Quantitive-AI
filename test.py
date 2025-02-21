import yfinance as yf
import pandas as pd
import numpy as np

# 设置股票代码和时间范围
ticker = 'GOOG'  # 或者 'GOOGL'
start_date = '2020-01-01'  # 起始日期
end_date = '2025-01-01'    # 结束日期

# 获取股票数据
google = yf.Ticker(ticker)
data = google.history(start=start_date, end=end_date)

# 使用 'Close' 列，并创建 'Adj Close' 列填充数据
data['Adj Close'] = data['Close']

# 计算 MA10（10日均线）
data['MA10'] = data['Close'].rolling(window=10).mean()

# 计算 RSI（14日相对强弱指数）
delta = data['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
data['RSI'] = 100 - (100 / (1 + rs))

# 计算 MACD（12日和26日EMA差，9日EMA作为信号线）
data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
data['MACD'] = data['EMA12'] - data['EMA26']
data['MACD_signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

# 打印数据的前几行，查看新增的指标
print(data[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'MA10', 'RSI', 'MACD', 'MACD_signal']].head())

# 保存数据到 CSV 文件
data.to_csv(f'{ticker}_historical_data_with_indicators_{start_date}_to_{end_date}.csv')

print(f"数据已保存为 {ticker}_historical_data_with_indicators_{start_date}_to_{end_date}.csv")