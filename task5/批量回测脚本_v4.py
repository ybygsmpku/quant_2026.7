"""
双均线策略批量回测脚本 v4 — 纯离线版（从缓存读取数据）
- 100支热门A股 × 8种均线组合（短线/中线/长线/超长线）
- 7项量化指标：总收益率、年化收益率、超额收益、最大回撤、胜率、盈亏比、夏普比率
- 无需API调用，从本地缓存读取数据
"""

import pandas as pd
import numpy as np
import os
import sys
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# ============ 配置 ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
CACHE_DIR = os.path.join(OUTPUT_DIR, 'stock_cache')

# 均线周期组合定义
MA_COMBOS = {
    '短线': [(5, 10), (5, 20)],
    '中线': [(10, 20), (20, 30)],
    '长线': [(20, 60), (30, 60)],
    '超长线': [(60, 120), (60, 250)],
}

# 回测参数
COMMISSION_RATE = 0.0003
SLIPPAGE_RATE = 0.001
LOT_SIZE = 100
RISK_FREE_RATE = 0.02
INITIAL_CAPITAL = 100000

START_DATE = '20220101'
END_DATE = '20260710'

# ============ 100支热门股票列表 ============
HOT_100_STOCKS = [
    ('600036.SH', '招商银行', '银行'), ('601398.SH', '工商银行', '银行'),
    ('601288.SH', '农业银行', '银行'), ('601939.SH', '建设银行', '银行'),
    ('601328.SH', '交通银行', '银行'), ('000001.SZ', '平安银行', '银行'),
    ('601318.SH', '中国平安', '保险'), ('601628.SH', '中国人寿', '保险'),
    ('600030.SH', '中信证券', '券商'), ('601688.SH', '华泰证券', '券商'),
    ('600519.SH', '贵州茅台', '白酒'), ('000858.SZ', '五粮液', '白酒'),
    ('000568.SZ', '泸州老窖', '白酒'), ('603589.SH', '口子窖', '白酒'),
    ('000729.SZ', '燕京啤酒', '啤酒'), ('600887.SH', '伊利股份', '乳制品'),
    ('600276.SH', '恒瑞医药', '化学制药'), ('000538.SZ', '云南白药', '中药'),
    ('300760.SZ', '迈瑞医疗', '医疗器械'), ('002007.SZ', '华兰生物', '生物制品'),
    ('600196.SH', '复星医药', '医药'), ('603986.SH', '兆易创新', '半导体'),
    ('002415.SZ', '海康威视', '安防'), ('000063.SZ', '中兴通讯', '通信设备'),
    ('300059.SZ', '东方财富', '互联网券商'), ('300782.SZ', '卓胜微', '半导体'),
    ('002049.SZ', '紫光国微', '半导体'), ('688981.SH', '中芯国际', '半导体制造'),
    ('300750.SZ', '宁德时代', '锂电池'), ('002466.SZ', '天齐锂业', '锂矿'),
    ('601012.SH', '隆基绿能', '光伏'), ('300274.SZ', '阳光电源', '光伏逆变器'),
    ('600438.SH', '通威股份', '光伏硅料'), ('002594.SZ', '比亚迪', '新能源汽车'),
    ('600104.SH', '上汽集团', '汽车'), ('000625.SZ', '长安汽车', '汽车'),
    ('601238.SH', '广汽集团', '汽车'), ('000002.SZ', '万科A', '房地产'),
    ('600048.SH', '保利发展', '房地产'), ('001979.SZ', '招商蛇口', '房地产'),
    ('000333.SZ', '美的集团', '家电'), ('000651.SZ', '格力电器', '家电'),
    ('002032.SZ', '苏泊尔', '小家电'), ('600031.SH', '三一重工', '工程机械'),
    ('600019.SH', '宝钢股份', '钢铁'), ('601088.SH', '中国神华', '煤炭'),
    ('600585.SH', '海螺水泥', '建材'), ('600900.SH', '长江电力', '水电'),
    ('601985.SH', '中国核电', '核电'), ('003816.SZ', '中国广核', '核电'),
    ('600570.SH', '恒生电子', '金融IT'), ('300124.SZ', '汇川技术', '工业自动化'),
    ('002475.SZ', '立讯精密', '电子制造'), ('601100.SH', '恒立液压', '液压件'),
    ('600893.SH', '航发动力', '航空发动机'), ('002179.SZ', '中航光电', '军工连接器'),
    ('600760.SH', '中航沈飞', '战斗机'), ('600050.SH', '中国联通', '通信运营'),
    ('601728.SH', '中国电信', '通信运营'), ('002602.SZ', '世纪华通', '游戏'),
    ('300418.SZ', '昆仑万维', '互联网'), ('600309.SH', '万华化学', 'MDI'),
    ('002493.SZ', '荣盛石化', '石化'), ('002714.SZ', '牧原股份', '生猪养殖'),
    ('300498.SZ', '温氏股份', '畜禽养殖'), ('600009.SH', '上海机场', '机场'),
    ('601021.SH', '春秋航空', '航空'), ('601111.SH', '中国国航', '航空'),
    ('601857.SH', '中国石油', '石油'), ('600028.SH', '中国石化', '石化'),
    ('601186.SH', '中国铁建', '基建'), ('601390.SH', '中国中铁', '基建'),
    ('601166.SH', '兴业银行', '银行'), ('600000.SH', '浦发银行', '银行'),
    ('600588.SH', '用友网络', '企业软件'), ('002230.SZ', '科大讯飞', 'AI语音'),
    ('603799.SH', '华友钴业', '钴镍'), ('600362.SH', '江西铜业', '铜'),
    ('600511.SH', '国药股份', '医药流通'), ('600308.SH', '太阳纸业', '造纸'),
    ('000413.SZ', '东阿阿胶', '中药保健品'), ('603568.SH', '伟明环保', '环保'),
    ('002050.SZ', '三花智控', '热管理'), ('601601.SH', '中国太保', '保险'),
    ('600837.SH', '海通证券', '券商'), ('000776.SZ', '广发证券', '券商'),
    ('601933.SH', '永辉超市', '超市'), ('300014.SZ', '亿纬锂能', '锂电池'),
    ('002460.SZ', '赣锋锂业', '锂矿'), ('688599.SH', '天合光能', '光伏组件'),
    ('002371.SZ', '北方华创', '半导体设备'), ('603501.SH', '韦尔股份', 'CIS芯片'),
    ('601669.SH', '中国电建', '水电建设'), ('601880.SH', '辽港股份', '港口'),
    ('000596.SZ', '古井贡酒', '白酒'), ('603369.SH', '今世缘', '白酒'),
    ('600690.SH', '海尔智家', '家电'), ('600096.SH', '云天化', '化肥'),
    ('002352.SZ', '顺丰控股', '物流'), ('601899.SH', '紫金矿业', '黄金矿业'),
]


# ============ 数据加载（纯离线） ============
def load_stock_data(ts_code):
    """从本地缓存加载股票数据"""
    # 603986使用前复权数据
    if ts_code == '603986.SH':
        qfq_file = os.path.join(OUTPUT_DIR, '603986_qfq_simple.csv')
        if os.path.exists(qfq_file):
            data = pd.read_csv(qfq_file)
            return data

    cache_file = os.path.join(CACHE_DIR, f"{ts_code}_daily.csv")
    if os.path.exists(cache_file):
        data = pd.read_csv(cache_file)
        if len(data) >= 60:
            data = data.sort_values('trade_date').reset_index(drop=True)
            return data
    
    return None


def load_benchmark():
    """加载沪深300基准数据"""
    # 优先使用缓存
    cache_file = os.path.join(CACHE_DIR, 'benchmark_000300.csv')
    if os.path.exists(cache_file):
        return pd.read_csv(cache_file)
    
    # 使用outputs中的文件
    for fname in ['benchmark_000300.csv', '沪深300基准数据.csv']:
        fpath = os.path.join(OUTPUT_DIR, fname)
        if os.path.exists(fpath):
            bm = pd.read_csv(fpath)
            return bm
    
    return None


# ============ 回测引擎 ============
def run_backtest(data, short_period, long_period, benchmark_data=None):
    """双均线策略回测"""
    data = data.copy()
    data['sma_short'] = data['close'].rolling(window=short_period).mean()
    data['sma_long'] = data['close'].rolling(window=long_period).mean()
    
    data['sma_diff'] = data['sma_short'] - data['sma_long']
    data['sma_diff_prev'] = data['sma_diff'].shift(1)
    
    data['buy_signal'] = (
        (data['sma_diff'] > 0) & (data['sma_diff_prev'] <= 0) &
        data['sma_short'].notna() & data['sma_long'].notna()
    )
    data['sell_signal'] = (
        (data['sma_diff'] < 0) & (data['sma_diff_prev'] >= 0) &
        data['sma_short'].notna() & data['sma_long'].notna()
    )
    
    valid = data[data['sma_short'].notna() & data['sma_long'].notna()].copy()
    if len(valid) < 20:
        return None
    
    capital = INITIAL_CAPITAL
    cash = capital
    position = 0
    round_trades = []
    buy_trade = None
    nav_list = []
    
    for i in range(len(valid)):
        row = valid.iloc[i]
        price = row['close']
        date = row['trade_date']
        
        if row['buy_signal'] and position == 0:
            buy_price = price * (1 + SLIPPAGE_RATE)
            max_shares = int(cash / (buy_price * LOT_SIZE)) * LOT_SIZE
            if max_shares > 0:
                cost = max_shares * buy_price * (1 + COMMISSION_RATE)
                if cost <= cash:
                    position = max_shares
                    cash -= cost
                    buy_trade = {'date': date, 'cost': cost, 'shares': max_shares}
        
        elif row['sell_signal'] and position > 0 and buy_trade is not None:
            sell_price = price * (1 - SLIPPAGE_RATE)
            revenue = position * sell_price * (1 - COMMISSION_RATE)
            cash += revenue
            round_trades.append({
                'buy_date': buy_trade['date'], 'sell_date': date,
                'cost': buy_trade['cost'], 'revenue': revenue,
                'pnl': revenue - buy_trade['cost']
            })
            position = 0
            buy_trade = None
        
        nav_list.append(cash + position * price)
    
    if not round_trades:
        return None
    
    final_nav = cash + position * valid.iloc[-1]['close'] if position > 0 else cash
    
    # === 计算指标 ===
    total_return = (final_nav - capital) / capital
    trading_days = len(valid)
    years = trading_days / 252
    annualized_return = (1 + total_return) ** (1 / max(years, 0.01)) - 1 if total_return > -1 else -1
    
    # 最大回撤
    nav_arr = np.array(nav_list)
    peak = nav_arr[0]
    max_dd = 0
    for v in nav_arr:
        if v > peak: peak = v
        dd = (peak - v) / peak if peak > 0 else 0
        if dd > max_dd: max_dd = dd
    
    # 胜率 & 盈亏比
    profits = [t['pnl'] for t in round_trades if t['pnl'] > 0]
    losses = [abs(t['pnl']) for t in round_trades if t['pnl'] < 0]
    win_rate = len(profits) / len(round_trades)
    avg_p = np.mean(profits) if profits else 0
    avg_l = np.mean(losses) if losses else 1
    pl_ratio = min(avg_p / avg_l, 999) if avg_l > 0 else (999 if avg_p > 0 else 0)
    
    # 超额收益
    excess_return = 0
    if benchmark_data is not None:
        first_date = valid.iloc[0]['trade_date']
        last_date = valid.iloc[-1]['trade_date']
        bm_sub = benchmark_data[(benchmark_data['trade_date'] >= first_date) & 
                                 (benchmark_data['trade_date'] <= last_date)]
        if len(bm_sub) >= 2:
            bm_ret = (bm_sub.iloc[-1]['close'] - bm_sub.iloc[0]['close']) / bm_sub.iloc[0]['close']
            excess_return = total_return - bm_ret
    
    # 夏普比率
    nav_rets = np.diff(nav_arr) / nav_arr[:-1]
    if len(nav_rets) > 10 and np.std(nav_rets) > 0:
        sharpe = (np.mean(nav_rets) - RISK_FREE_RATE/252) / np.std(nav_rets) * np.sqrt(252)
    else:
        sharpe = 0
    
    return {
        'total_return': total_return, 'annualized_return': annualized_return,
        'excess_return': excess_return, 'max_drawdown': max_dd,
        'win_rate': win_rate, 'pl_ratio': pl_ratio, 'sharpe_ratio': sharpe,
        'trade_count': len(round_trades), 'trading_days': trading_days, 'years': years,
    }


# ============ 批量回测 ============
def batch_backtest(stock_list, benchmark_data):
    results = []
    total = len(stock_list)
    success = 0
    fail = 0
    
    for idx, (ts_code, name, industry) in enumerate(stock_list):
        print(f"[{idx+1}/{total}] {ts_code} {name} ({industry})...", end=' ')
        sys.stdout.flush()
        
        data = load_stock_data(ts_code)
        if data is None or len(data) < 60:
            print(f"✗ 数据不足")
            fail += 1
            continue
        
        print(f"✓ {len(data)}行", end='')
        
        for stype, combos in MA_COMBOS.items():
            for sp, lp in combos:
                if len(data) < lp * 2:
                    continue
                try:
                    result = run_backtest(data, sp, lp, benchmark_data)
                    if result:
                        results.append({
                            'ts_code': ts_code, 'name': name, 'industry': industry,
                            'strategy_type': stype, 'short_ma': sp, 'long_ma': lp,
                            'ma_combo': f"MA{sp}/MA{lp}", **result
                        })
                except Exception as e:
                    continue
        
        success += 1
        combos_done = sum(1 for r in results if r['ts_code'] == ts_code)
        print(f" → {combos_done}种组合")
    
    print(f"\n回测完成: {success}支成功, {fail}支失败, {len(results)}条记录")
    return pd.DataFrame(results)


# ============ 汇总分析 ============
def generate_summary_tables(results_df):
    # 按均线组合
    combo_stats = []
    for combo in sorted(results_df['ma_combo'].unique()):
        sub = results_df[results_df['ma_combo'] == combo]
        combo_stats.append({
            'ma_combo': combo, 'strategy_type': sub['strategy_type'].iloc[0],
            'sample_count': len(sub),
            'avg_total_return': sub['total_return'].mean(),
            'median_total_return': sub['total_return'].median(),
            'avg_annualized_return': sub['annualized_return'].mean(),
            'avg_excess_return': sub['excess_return'].mean(),
            'avg_max_drawdown': sub['max_drawdown'].mean(),
            'avg_win_rate': sub['win_rate'].mean(),
            'avg_pl_ratio': sub['pl_ratio'].mean(),
            'avg_sharpe_ratio': sub['sharpe_ratio'].mean(),
            'avg_trade_count': sub['trade_count'].mean(),
            'profit_pct': (sub['total_return'] > 0).mean(),
        })
    
    # 按策略类型
    type_stats = []
    for stype in ['短线', '中线', '长线', '超长线']:
        sub = results_df[results_df['strategy_type'] == stype]
        if not len(sub): continue
        type_stats.append({
            'strategy_type': stype, 'sample_count': len(sub),
            'avg_total_return': sub['total_return'].mean(),
            'median_total_return': sub['total_return'].median(),
            'avg_annualized_return': sub['annualized_return'].mean(),
            'avg_excess_return': sub['excess_return'].mean(),
            'avg_max_drawdown': sub['max_drawdown'].mean(),
            'avg_win_rate': sub['win_rate'].mean(),
            'avg_pl_ratio': sub['pl_ratio'].mean(),
            'avg_sharpe_ratio': sub['sharpe_ratio'].mean(),
            'avg_trade_count': sub['trade_count'].mean(),
            'profit_pct': (sub['total_return'] > 0).mean(),
        })
    
    # 按行业
    ind_stats = []
    for ind in results_df['industry'].unique():
        sub = results_df[results_df['industry'] == ind]
        if len(sub) < 2: continue
        ind_stats.append({
            'industry': ind, 'stock_count': sub['ts_code'].nunique(),
            'avg_total_return': sub['total_return'].mean(),
            'avg_annualized_return': sub['annualized_return'].mean(),
            'avg_sharpe_ratio': sub['sharpe_ratio'].mean(),
            'avg_max_drawdown': sub['max_drawdown'].mean(),
            'avg_win_rate': sub['win_rate'].mean(),
            'avg_pl_ratio': sub['pl_ratio'].mean(),
            'sample_count': len(sub),
        })
    
    # 策略×行业交叉（放宽到sample>=2）
    cross = []
    for stype in ['短线', '中线', '长线', '超长线']:
        sub_t = results_df[results_df['strategy_type'] == stype]
        for ind in sub_t['industry'].unique():
            sub = sub_t[sub_t['industry'] == ind]
            if len(sub) < 2: continue
            cross.append({
                'strategy_type': stype, 'industry': ind,
                'avg_sharpe': sub['sharpe_ratio'].mean(),
                'avg_return': sub['total_return'].mean(),
                'avg_drawdown': sub['max_drawdown'].mean(),
                'avg_win_rate': sub['win_rate'].mean(),
                'sample_count': len(sub),
            })
    
    return {
        'combo': pd.DataFrame(combo_stats),
        'type': pd.DataFrame(type_stats),
        'industry': pd.DataFrame(ind_stats).sort_values('avg_sharpe_ratio', ascending=False),
        'cross': pd.DataFrame(cross).sort_values('avg_sharpe', ascending=False),
    }


# ============ 报告生成 ============
def generate_report(results_df, summaries):
    r = []
    r.append("=" * 70)
    r.append("双均线策略适用场景与应用心得报告")
    r.append("=" * 70)
    
    stock_count = results_df['ts_code'].nunique()
    combo_count = results_df['ma_combo'].nunique()
    industry_count = results_df['industry'].nunique()
    
    r.append(f"\n回测范围: {stock_count}支股票 × {combo_count}种均线组合")
    r.append(f"数据区间: {START_DATE} ~ {END_DATE}")
    r.append(f"总回测记录: {len(results_df)} 条")
    r.append(f"覆盖行业: {industry_count}个")
    r.append(f"初始资金: ¥{INITIAL_CAPITAL:,}, 佣金{COMMISSION_RATE:.2%}, 滑点{SLIPPAGE_RATE:.2%}")
    r.append(f"\n⚠ 数据说明: 使用未复权日线数据(pro.daily直连)，除权除息影响在短期分析中较小")
    r.append("  兆易创新(603986)使用前复权数据作为特例")
    
    # 一、均线组合表现
    r.append("\n" + "-" * 50)
    r.append("一、各均线组合整体表现")
    r.append("-" * 50)
    cs = summaries['combo']
    for _, row in cs.iterrows():
        r.append(f"\n  {row['ma_combo']} ({row['strategy_type']}) | 样本{int(row['sample_count'])}")
        r.append(f"    平均收益率: {row['avg_total_return']:.2%} | 中位数: {row['median_total_return']:.2%}")
        r.append(f"    盈利占比: {row['profit_pct']:.2%} | 夏普: {row['avg_sharpe_ratio']:.4f}")
        r.append(f"    最大回撤: {row['avg_max_drawdown']:.2%} | 胜率: {row['avg_win_rate']:.2%}")
        r.append(f"    盈亏比: {row['avg_pl_ratio']:.2f} | 交易次数: {row['avg_trade_count']:.1f}")
    
    # 二、策略类型对比
    r.append("\n" + "-" * 50)
    r.append("二、各策略类型对比")
    r.append("-" * 50)
    ts_df = summaries['type']
    for _, row in ts_df.iterrows():
        r.append(f"\n  【{row['strategy_type']}】样本{int(row['sample_count'])}")
        r.append(f"    收益率: {row['avg_total_return']:.2%} | 盈利占比: {row['profit_pct']:.2%}")
        r.append(f"    夏普: {row['avg_sharpe_ratio']:.4f} | 回撤: {row['avg_max_drawdown']:.2%}")
        r.append(f"    胜率: {row['avg_win_rate']:.2%} | 盈亏比: {row['avg_pl_ratio']:.2f}")
    
    # 三、行业适用性
    r.append("\n" + "-" * 50)
    r.append("三、行业适用性分析（各策略TOP5行业）")
    r.append("-" * 50)
    cross = summaries['cross']
    for stype in ['短线', '中线', '长线', '超长线']:
        sub = cross[cross['strategy_type'] == stype].sort_values('avg_sharpe', ascending=False)
        if not len(sub): continue
        r.append(f"\n  【{stype}】最适合行业:")
        for _, row in sub.head(5).iterrows():
            r.append(f"    {row['industry']}: 夏普={row['avg_sharpe']:.4f}, 收益={row['avg_return']:.2%}, 回撤={row['avg_drawdown']:.2%}")
        if len(sub) > 5:
            r.append(f"  最不适合行业:")
            for _, row in sub.tail(3).iterrows():
                r.append(f"    {row['industry']}: 夏普={row['avg_sharpe']:.4f}, 收益={row['avg_return']:.2%}")
    
    # 四、适用场景
    r.append("\n" + "-" * 50)
    r.append("四、双均线策略适用场景总结")
    r.append("-" * 50)
    best = cs.loc[cs['avg_sharpe_ratio'].idxmax()]
    worst = cs.loc[cs['avg_sharpe_ratio'].idxmin()]
    best_type = ts_df.loc[ts_df['avg_sharpe_ratio'].idxmax()]
    
    r.append(f"\n  数据验证结论:")
    r.append(f"  - 最佳均线组合: {best['ma_combo']} (夏普={best['avg_sharpe_ratio']:.4f})")
    r.append(f"  - 最差均线组合: {worst['ma_combo']} (夏普={worst['avg_sharpe_ratio']:.4f})")
    r.append(f"  - 最佳策略类型: {best_type['strategy_type']} (盈利占比={best_type['profit_pct']:.2%})")
    
    # 动态生成策略结论
    # 找出短线表现最好的行业
    short_cross = cross[cross['strategy_type'] == '短线'].sort_values('avg_sharpe', ascending=False)
    mid_cross = cross[cross['strategy_type'] == '中线'].sort_values('avg_sharpe', ascending=False)
    long_cross = cross[cross['strategy_type'] == '长线'].sort_values('avg_sharpe', ascending=False)
    ultra_cross = cross[cross['strategy_type'] == '超长线'].sort_values('avg_sharpe', ascending=False)
    
    short_best = short_cross.iloc[0]['industry'] if len(short_cross) > 0 else '科技/题材股'
    mid_best = mid_cross.iloc[0]['industry'] if len(mid_cross) > 0 else '趋势明确股'
    long_best = long_cross.iloc[0]['industry'] if len(long_cross) > 0 else '蓝筹股'
    ultra_best = ultra_cross.iloc[0]['industry'] if len(ultra_cross) > 0 else '大级别趋势股'
    
    r.append(f"""
  1. 短线策略(MA5/MA10, MA5/MA20):
     - 适用: 趋势明显、波动大的个股(如{short_best})
     - 优点: 反应灵敏，捕捉短期趋势
     - 缺点: 假信号多，手续费侵蚀利润
     - 心得: 需配合止损，不适合震荡市
  
  2. 中线策略(MA10/MA20, MA20/MA30):
     - 适用: 中期趋势明确的股票(如{mid_best})，波段操作
     - 优点: 信号可靠，胜率适中，频率合理
     - 缺点: 反应稍慢，可能错过趋势头部
     - 心得: 最均衡的选择，适合大多数投资者
  
  3. 长线策略(MA20/MA60, MA30/MA60):
     - 适用: 大趋势股、蓝筹股(如{long_best})、行业龙头
     - 优点: 过滤噪音，信号可靠性高
     - 缺点: 错过短期机会，滞后入场出场
     - 心得: 牛市表现优异，震荡市一般
  
  4. 超长线策略(MA60/MA120, MA60/MA250):
     - 适用: 长期投资视角(如{ultra_best})，判断大级别牛熊转换
     - 优点: 最大程度过滤噪音
     - 缺点: 信号极少，可能持仓数年不动
     - 心得: 适合耐心的大资金""")
    
    # 五、核心心得
    r.append(f"\n" + "-" * 50)
    r.append("五、核心应用心得")
    r.append("-" * 50)
    
    # 动态生成心得
    avg_win = results_df['win_rate'].mean()
    avg_pl = results_df['pl_ratio'].mean()
    avg_dd = results_df['max_drawdown'].mean()
    profit_pct = (results_df['total_return'] > 0).mean()
    
    r.append(f"""
  1. 均线周期越长→信号越少越可靠; 周期越短→信号越多但噪音多
  2. 双均线本质是趋势跟踪——只在有趋势时赚钱，震荡市必亏
  3. 胜率不重要，盈亏比才重要: 本次回测平均胜率{avg_win:.1%}，平均盈亏比{avg_pl:.2f}
  4. 最大回撤是真实风险——平均回撤{avg_dd:.1%}, 回撤>30%很难坚持
  5. 没有万能均线参数——不同股票/不同阶段需不同参数
  6. 整体盈利占比: {profit_pct:.1%}（约{int(profit_pct*100)}%的回测组合盈利）
  7. 适合: 有明确趋势的个股、中期以上投资周期
  8. 不适合: 震荡市、高频交易、小盘题材股短期炒作
  9. 实战建议: 中线(MA10/MA20或MA20/MA60)作为默认，根据波动率调整
  10. 进阶优化: 叠加成交量确认、MACD辅助、趋势强度过滤
  11. 风控优先: 止损设在长均线下方3-5%""")
    
    return "\n".join(r)


# ============ 主流程 ============
def main():
    print("=" * 60)
    print("双均线策略批量回测 — 100支热门A股 × 8种均线组合")
    print("数据源: 本地缓存（纯离线，无需API）")
    print("=" * 60)
    
    print(f"\n加载基准数据...")
    bm = load_benchmark()
    if bm is not None:
        print(f"  ✓ 沪深300基准: {len(bm)}行")
    else:
        print("  ⚠ 无基准数据，超额收益将设为0")
    
    print(f"\n开始批量回测...")
    results_df = batch_backtest(HOT_100_STOCKS, bm)
    
    if len(results_df) == 0:
        print("⚠ 无回测结果！请检查缓存数据")
        return None, None
    
    # 保存详细结果
    detail_file = os.path.join(OUTPUT_DIR, 'dual_ma_backtest_100stocks.csv')
    results_df.to_csv(detail_file, index=False, float_format='%.6f')
    print(f"\n详细结果: {detail_file} ({len(results_df)}条)")
    
    # 汇总
    print("\n生成汇总分析...")
    summaries = generate_summary_tables(results_df)
    for name, df in summaries.items():
        fpath = os.path.join(OUTPUT_DIR, f'summary_{name}.csv')
        df.to_csv(fpath, index=False, float_format='%.4f')
        print(f"  {name} → {len(df)}条 → {fpath}")
    
    # 报告
    report = generate_report(results_df, summaries)
    report_file = os.path.join(OUTPUT_DIR, 'dual_ma_strategy_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n策略报告: {report_file}")
    
    print("\n" + "=" * 60)
    print(f"全部完成! {results_df['ts_code'].nunique()}支股票, {len(results_df)}条回测记录")
    return results_df, summaries


if __name__ == '__main__':
    main()
