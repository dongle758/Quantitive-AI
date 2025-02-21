import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplcursors
import ta

# 读取 Google Finance 数据
data = pd.read_csv('GOOG_historical_data_with_indicators_2020-01-01_to_2025-01-01.csv', skiprows=3,
                   names=['Date', 'Price', 'Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume'])

# 确保日期列正确转换为 datetime
data['Date'] = pd.to_datetime(data['Date'])
data.set_index('Date', inplace=True)

# 打印初始数据
print(f"初始数据行数: {len(data)}")
print("初始数据前几行:\n", data.head())
print("初始数据最后几行:\n", data.tail())
print("初始数据 NaN 数量:\n", data.isna().sum())

# 特征工程
data['MA10'] = data['Adj Close'].rolling(window=10).mean()
data['RSI'] = ta.momentum.RSIIndicator(data['Adj Close'], window=14).rsi()
data['MACD'] = ta.trend.MACD(data['Adj Close']).macd()

# 检查特征工程后的 NaN
print("特征工程后 NaN 数量:\n", data.isna().sum())
print("特征工程后前几行:\n", data.head(15))

# 删除 NaN
data.dropna(inplace=True)
print(f"删除 NaN 后数据行数: {len(data)}")
if len(data) == 0:
    raise ValueError("数据在删除 NaN 后为空，请检查数据文件或特征工程！")

# 选择特征
features = ['Adj Close', 'Volume', 'MA10', 'RSI', 'MACD']
feature_data = data[features].values

# 归一化
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(feature_data)

# 创建时间窗口数据
def create_dataset(data, time_step=60):
    X, y = [], []
    for i in range(len(data) - time_step):
        X.append(data[i:(i + time_step)])
        y.append(data[i + time_step, 0])  # 预测 Adj Close
    return np.array(X), np.array(y)

time_step = 60
X, y = create_dataset(scaled_data, time_step)
X = X.reshape((X.shape[0], X.shape[1], len(features)))

# 划分数据集
train_size = int(len(X) * 0.7)
val_size = int(len(X) * 0.15)
X_train, X_val, X_test = X[:train_size], X[train_size:train_size + val_size], X[train_size + val_size:]
y_train, y_val, y_test = y[:train_size], y[train_size:train_size + val_size], y[train_size + val_size:]

# 构建模型
model = Sequential()
model.add(Bidirectional(LSTM(100, return_sequences=True), input_shape=(time_step, len(features))))
model.add(Dropout(0.2))
model.add(LSTM(100))
model.add(Dropout(0.2))
model.add(Dense(50, activation='relu'))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mean_squared_error')

# 训练模型
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
history = model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_val, y_val),
                    callbacks=[early_stopping], verbose=1)

# 预测未来价格
last_60_days = scaled_data[-time_step:]
future_days = 10
predictions = []
current_input = last_60_days.reshape((1, time_step, len(features)))

for _ in range(future_days):
    pred = model.predict(current_input, verbose=0)
    predictions.append(pred[0, 0])  # 提取标量值
    next_input = np.zeros((1, 1, len(features)))
    next_input[0, 0, 0] = pred.item()  # 使用 .item() 转换为标量
    for i in range(1, len(features)):
        next_input[0, 0, i] = current_input[0, -1, i]
    current_input = np.concatenate((current_input[:, 1:, :], next_input), axis=1)

# 反归一化
predictions_array = np.zeros((len(predictions), len(features)))
predictions_array[:, 0] = predictions
predictions = scaler.inverse_transform(predictions_array)[:, 0]

# 生成未来日期（从最后一天开始）
last_date = data.index[-1]
print(f"最后一天日期: {last_date}")
future_dates = pd.date_range(start=last_date, periods=future_days + 1, freq='B')[1:]

# 计算置信区间
historical_std = data['Adj Close'].pct_change().std() * np.sqrt(future_days) * data['Adj Close'].iloc[-1]
upper_bound = predictions + historical_std
lower_bound = predictions - historical_std

# 可视化
try:
    plt.style.use('seaborn')
except OSError:
    plt.style.use('ggplot')

fig, ax = plt.subplots(figsize=(12, 6))
line1, = ax.plot(data.index, data['Adj Close'], label='Historical Adj Close', color='#1f77b4', linewidth=2)
line2, = ax.plot(future_dates, predictions, label='Predicted Price', color='#ff7f0e', linewidth=2, linestyle='--')
ax.fill_between(future_dates, lower_bound, upper_bound, color='#ff7f0e', alpha=0.2, label='Confidence Interval')
ax.axvline(x=last_date, color='gray', linestyle=':', linewidth=1.5, label='Prediction Start')

ax.set_title('GOOGL Stock Price Prediction (Google Finance)', fontsize=16, fontweight='bold')
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Adjusted Close Price (USD)', fontsize=12)
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
ax.grid(True, linestyle='--', alpha=0.7)
ax.legend(loc='upper left', fontsize=10)

cursor = mplcursors.cursor([line1, line2], hover=True)
@cursor.connect("add")
def on_add(sel):
    x = sel.target[0]
    y = sel.target[1]
    date_str = mdates.num2date(x).strftime('%Y-%m-%d')
    sel.annotation.set_text(f'Date: {date_str}\nPrice: {y:.2f}')

plt.tight_layout()
plt.show()

# 输出预测结果
print("未来10天预测价格:")
for date, pred in zip(future_dates, predictions):
    print(f"{date.strftime('%Y-%m-%d')}: {pred:.2f}")