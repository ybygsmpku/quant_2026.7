#!/usr/bin/env python3
"""
Task2: 兆易创新(603986) 日线数据诊断分析
- 缺失值检查
- 描述性统计量计算
- 数据一致性验证
- 输出诊断结果CSV
"""

import pandas as pd
import numpy as np
from scipy import stats
import os
import warnings
warnings.filterwarnings('ignore')

# ============ 配置 ============
INPUT_CSV = '/Users/ybyy/Desktop/量化交易：AI辅助的金融交易策略/outputs/兆易创新_603986日线数据.csv'
OUTPUT_DIR = '/Users/ybyy/Desktop/量化交易：AI辅助的金融交易策略/outputs'
MPLCONFIGDIR = '/tmp/matplotlib_cache'

# ============ 读取数据 ============
print("=" * 60)
print("兆易创新 (603986.SH) 日线数据诊断分析")
print("=" * 60)

df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
print(f"\n数据概况: {df.shape[0]} 行, {df.shape[1]} 列")
print(f"字段列表: {list(df.columns)}")

numeric_cols = ['open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']

# ============ 1. 缺失值检查 ============
print("\n" + "=" * 60)
print("【1】缺失值检查")
print("=" * 60)

missing_count = df.isnull().sum()
missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
missing_df = pd.DataFrame({
    '字段名': df.columns,
    '非空数量': df.count().values,
    '缺失数量': missing_count.values,
    '缺失率(%)': missing_pct.values,
    '数据类型': df.dtypes.values
})
print(missing_df.to_string(index=False))

total_missing = missing_count.sum()
if total_missing == 0:
    print("\n✅ 结论: 所有字段均无缺失值，数据完整")
else:
    print(f"\n⚠️ 结论: 共发现 {total_missing} 个缺失值")

# ============ 2. 描述性统计量 ============
print("\n" + "=" * 60)
print("【2】描述性统计量计算")
print("=" * 60)

desc_rows = []
for col in numeric_cols:
    series = df[col].astype(float)
    desc_rows.append({
        '字段名': col,
        '样本数': series.count(),
        '均值': round(series.mean(), 4),
        '中位数': round(series.median(), 4),
        '标准差': round(series.std(), 4),
        '最小值': round(series.min(), 4),
        '最大值': round(series.max(), 4),
        '极差': round(series.max() - series.min(), 4),
        'Q1(25%)': round(series.quantile(0.25), 4),
        'Q2(50%)': round(series.quantile(0.50), 4),
        'Q3(75%)': round(series.quantile(0.75), 4),
        '偏度': round(series.skew(), 4),
        '峰度': round(series.kurtosis(), 4),
    })

desc_df = pd.DataFrame(desc_rows)
print(desc_df.to_string(index=False))

# ============ 3. 数据一致性验证 ============
print("\n" + "=" * 60)
print("【3】数据一致性验证")
print("=" * 60)

df['trade_date'] = df['trade_date'].astype(str)
for col in numeric_cols:
    df[col] = df[col].astype(float)

# 3a: change = close - pre_close
df['calc_change'] = df['close'] - df['pre_close']
df['change_diff'] = abs(df['calc_change'] - df['change'])
change_mismatch = df[df['change_diff'] > 0.02]
print(f"\n验证1: change = close - pre_close")
print(f"  允许误差: 0.02元")
print(f"  不一致记录数: {len(change_mismatch)}")
if len(change_mismatch) > 0:
    print(f"  不一致示例:")
    for _, row in change_mismatch.head(5).iterrows():
        print(f"    {row['trade_date']}: close={row['close']}, pre_close={row['pre_close']}, "
              f"calc_change={row['calc_change']:.2f}, recorded_change={row['change']:.2f}, diff={row['change_diff']:.4f}")

# 3b: pct_chg = change / pre_close * 100
df['calc_pct_chg'] = df['change'] / df['pre_close'] * 100
df['pct_diff'] = abs(df['calc_pct_chg'] - df['pct_chg'])
pct_mismatch = df[df['pct_diff'] > 0.05]
print(f"\n验证2: pct_chg = change / pre_close * 100")
print(f"  允许误差: 0.05%")
print(f"  不一致记录数: {len(pct_mismatch)}")
if len(pct_mismatch) > 0:
    print(f"  不一致示例:")
    for _, row in pct_mismatch.head(5).iterrows():
        print(f"    {row['trade_date']}: change={row['change']}, pre_close={row['pre_close']}, "
              f"calc_pct={row['calc_pct_chg']:.4f}, recorded_pct={row['pct_chg']:.4f}, diff={row['pct_diff']:.4f}")

# 3c: high >= max(open, close)
df['expected_high'] = df[['open', 'close']].max(axis=1)
high_violation = df[df['high'] < df['expected_high'] - 0.01]
print(f"\n验证3: high >= max(open, close)")
print(f"  不一致记录数: {len(high_violation)}")
if len(high_violation) > 0:
    for _, row in high_violation.head(5).iterrows():
        print(f"    {row['trade_date']}: high={row['high']}, open={row['open']}, close={row['close']}")

# 3d: low <= min(open, close)
df['expected_low'] = df[['open', 'close']].min(axis=1)
low_violation = df[df['low'] > df['expected_low'] + 0.01]
print(f"\n验证4: low <= min(open, close)")
print(f"  不一致记录数: {len(low_violation)}")
if len(low_violation) > 0:
    for _, row in low_violation.head(5).iterrows():
        print(f"    {row['trade_date']}: low={row['low']}, open={row['open']}, close={row['close']}")

# 3e: 交易日连续性（简单检查：日期不应有倒序）
dates_sorted = df['trade_date'].sort_values().tolist()
is_sorted = df['trade_date'].tolist() == dates_sorted
print(f"\n验证5: 交易日排序")
print(f"  日期是否按升序排列: {is_sorted}")
print(f"  日期范围: {df['trade_date'].min()} ~ {df['trade_date'].max()}")

# ============ 4. 异常标记 ============
print("\n" + "=" * 60)
print("【4】异常标记")
print("=" * 60)

# 涨停/跌停
limit_up = df[abs(df['pct_chg'] - 10) < 0.1]
limit_down = df[abs(df['pct_chg'] + 10) < 0.1]
print(f"接近涨停(+10%): {len(limit_up)} 天")
print(f"接近跌停(-10%): {len(limit_down)} 天")

# 成交量异常（超过均值+2倍标准差）
vol_mean = df['vol'].mean()
vol_std = df['vol'].std()
vol_anomaly = df[df['vol'] > vol_mean + 2 * vol_std]
print(f"成交量异常放大(>均值+2σ): {len(vol_anomaly)} 天")

# ============ 5. 输出诊断结果CSV ============
print("\n" + "=" * 60)
print("【5】输出诊断结果CSV")
print("=" * 60)

# Sheet1: 缺失值报告
# Sheet2: 描述性统计量
# Sheet3: 数据一致性验证结果

# 合并所有诊断结果到一个CSV中（用分隔行区分不同部分）
# 采用多表合并输出方式

# ---- 生成一致性验证结果表 ----
consistency_rows = []
for _, row in df.iterrows():
    consistency_rows.append({
        'trade_date': row['trade_date'],
        'change验证差值': round(row.get('change_diff', 0), 4),
        'pct_chg验证差值': round(row.get('pct_diff', 0), 4),
        'high>=max(open,close)': '通过' if row['high'] >= row[['open', 'close']].max() - 0.01 else '异常',
        'low<=min(open,close)': '通过' if row['low'] <= row[['open', 'close']].min() + 0.01 else '异常',
    })
consistency_df = pd.DataFrame(consistency_rows)

# ---- 生成缺失值报告 ----
missing_report = missing_df.copy()

# ---- 生成描述性统计量报告 ----
desc_report = desc_df.copy()

# ---- 生成异常标记 ----
anomaly_df = df.copy()
anomaly_df['涨停标记'] = (abs(anomaly_df['pct_chg'] - 10) < 0.1).map({True: '涨停', False: ''})
anomaly_df['跌停标记'] = (abs(anomaly_df['pct_chg'] + 10) < 0.1).map({True: '跌停', False: ''})
anomaly_df['成交量异常'] = (anomaly_df['vol'] > vol_mean + 2 * vol_std).map({True: '异常放大', False: ''})
anomaly_cols = ['trade_date', 'ts_code', 'open', 'high', 'low', 'close', 'pre_close',
                'change', 'pct_chg', 'vol', 'amount', '涨停标记', '跌停标记', '成交量异常']
anomaly_report = anomaly_df[anomaly_cols].copy()

# ---- 输出到单个CSV ----
output_path = os.path.join(OUTPUT_DIR, '兆易创新_603986诊断分析.csv')

# 用多段写入方式，每段之间空2行
with open(output_path, 'w', encoding='utf-8-sig') as f:
    # 写入缺失值报告
    f.write("# ===== 缺失值检查报告 =====\n")
    missing_report.to_csv(f, index=False)
    f.write("\n\n")

    # 写入描述性统计量
    f.write("# ===== 描述性统计量 =====\n")
    desc_report.to_csv(f, index=False)
    f.write("\n\n")

    # 写入一致性验证
    f.write("# ===== 数据一致性验证 =====\n")
    consistency_df.to_csv(f, index=False)
    f.write("\n\n")

    # 写入异常标记
    f.write("# ===== 异常标记 =====\n")
    anomaly_report.to_csv(f, index=False)

print(f"\n✅ 诊断分析CSV已保存: {output_path}")
print(f"\n文件包含4个分析板块:")
print(f"  1. 缺失值检查报告")
print(f"  2. 描述性统计量")
print(f"  3. 数据一致性验证")
print(f"  4. 异常标记")

# ---- 同时输出一个更规范的4-sheet Excel兼容格式: 每个板块单独CSV ----
# 缺失值
missing_csv = os.path.join(OUTPUT_DIR, '兆易创新_603986_缺失值检查.csv')
missing_report.to_csv(missing_csv, index=False, encoding='utf-8-sig')

# 描述性统计
desc_csv = os.path.join(OUTPUT_DIR, '兆易创新_603986_描述性统计量.csv')
desc_report.to_csv(desc_csv, index=False, encoding='utf-8-sig')

# 一致性验证
consist_csv = os.path.join(OUTPUT_DIR, '兆易创新_603986_一致性验证.csv')
consistency_df.to_csv(consist_csv, index=False, encoding='utf-8-sig')

# 异常标记
anomaly_csv = os.path.join(OUTPUT_DIR, '兆易创新_603986_异常标记.csv')
anomaly_report.to_csv(anomaly_csv, index=False, encoding='utf-8-sig')

print(f"\n✅ 同时输出4个独立CSV文件:")
print(f"  1. {missing_csv}")
print(f"  2. {desc_csv}")
print(f"  3. {consist_csv}")
print(f"  4. {anomaly_csv}")

print("\n" + "=" * 60)
print("诊断分析完成!")
print("=" * 60)
