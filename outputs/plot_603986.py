import json, csv, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# 读取数据
input_file = '/Users/ybyy/Desktop/量化交易：AI辅助的金融交易策略/outputs/603986_data.json'
with open(input_file) as f:
    data = json.load(f)

# 按日期正序排列
data.sort(key=lambda x: x['trade_date'])

output_dir = '/Users/ybyy/Desktop/量化交易：AI辅助的金融交易策略/outputs'

# ============ 1. 保存CSV ============
csv_path = f'{output_dir}/兆易创新_603986日线数据.csv'
fieldnames = ['ts_code','trade_date','open','high','low','close','pre_close','change','pct_chg','vol','amount']
with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in data:
        writer.writerow(row)

print(f'CSV已保存: {csv_path}')
print(f'共 {len(data)} 条数据')

# ============ 2. 绘制收盘价曲线图 ============
dates = [datetime.strptime(row['trade_date'], '%Y%m%d') for row in data]
close_prices = [row['close'] for row in data]
pct_changes = [row['pct_chg'] for row in data]

# 设置中文字体
plt.rcParams['font.family'] = ['PingFang SC', 'Heiti TC', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

# === 收盘价曲线 ===
ax1.plot(dates, close_prices, color='#1a73e8', linewidth=1.8, label='收盘价')
ax1.fill_between(dates, close_prices, min(close_prices), alpha=0.08, color='#1a73e8')

# 标注最高点和最低点
max_idx = close_prices.index(max(close_prices))
min_idx = close_prices.index(min(close_prices))
ax1.annotate(f'最高: {max(close_prices):.2f}',
             xy=(dates[max_idx], max(close_prices)),
             xytext=(15, 15), textcoords='offset points', fontsize=10,
             color='#e53935', fontweight='bold',
             arrowprops=dict(arrowstyle='->', color='#e53935'))
ax1.annotate(f'最低: {min(close_prices):.2f}',
             xy=(dates[min_idx], min(close_prices)),
             xytext=(15, -20), textcoords='offset points', fontsize=10,
             color='#43a047', fontweight='bold',
             arrowprops=dict(arrowstyle='->', color='#43a047'))

ax1.set_title('兆易创新 (603986.SH) 收盘价走势\n2025.07 ~ 2026.07', fontsize=16, fontweight='bold', pad=15)
ax1.set_ylabel('收盘价 (元)', fontsize=12)
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator())

# === 涨跌幅柱状图 (红涨绿跌) ===
colors = ['#e53935' if p > 0 else '#43a047' for p in pct_changes]
ax2.bar(dates, pct_changes, width=1.5, color=colors, alpha=0.7)
ax2.set_ylabel('涨跌幅 (%)', fontsize=12)
ax2.set_xlabel('日期', fontsize=12)
ax2.grid(True, alpha=0.3)
ax2.axhline(y=0, color='gray', linewidth=0.5)

plt.tight_layout()

chart_path = f'{output_dir}/兆易创新_603986收盘价走势.png'
plt.savefig(chart_path, dpi=150, bbox_inches='tight')
print(f'图表已保存: {chart_path}')

# 输出统计信息
print(f'\n=== 数据统计 ===')
print(f'时间范围: {dates[0].strftime("%Y-%m-%d")} ~ {dates[-1].strftime("%Y-%m-%d")}')
print(f'数据条数: {len(data)}')
print(f'收盘价最高: {max(close_prices):.2f} ({dates[max_idx].strftime("%Y-%m-%d")})')
print(f'收盘价最低: {min(close_prices):.2f} ({dates[min_idx].strftime("%Y-%m-%d")})')
print(f'期初收盘价: {close_prices[0]:.2f}')
print(f'期末收盘价: {close_prices[-1]:.2f}')
pct_total = (close_prices[-1]/close_prices[0]-1)*100
print(f'区间涨幅: {pct_total:.2f}%')
