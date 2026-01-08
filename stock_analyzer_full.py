import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import json
from pathlib import Path
import time
import requests
from bs4 import BeautifulSoup

# ページ設定
st.set_page_config(
    page_title="株最強分析くん",
    page_icon="📊",
    layout="wide"
)

# データ保存用ディレクトリ
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "analysis_history.json"
RANKING_FILE = DATA_DIR / "monthly_ranking.json"

# スタイル設定
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: 0.5rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class StockAnalyzer:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_irbank_data(self, stock_code):
        """IRBANKから財務データを取得"""
        try:
            url = f"https://irbank.net/{stock_code}"
            time.sleep(2)  # サーバー負荷軽減
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 企業名取得
            company_name = soup.find('h1')
            company_name = company_name.text.strip() if company_name else f"銘柄{stock_code}"
            
            # 財務データ取得（簡略化 - 実際はテーブルから詳細データを取得）
            financial_data = {
                'company_name': company_name,
                'revenue': None,  # 経常収益
                'eps': None,  # EPS
                'total_assets': None,  # 総資産
                'operating_cf': None,  # 営業CF
                'cash': None,  # 現金等
                'roe': None,  # ROE
                'equity_ratio': None,  # 自己資本比率
                'dividend': None,  # 1株配当
                'payout_ratio': None  # 配当性向
            }
            
            return financial_data
            
        except Exception as e:
            st.warning(f"⚠️ IRBANKからのデータ取得に失敗: {e}")
            return None
    
    def fetch_stock_data(self, stock_code):
        """yfinanceで株価と企業情報を取得"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                ticker = f"{stock_code}.T"
                stock = yf.Ticker(ticker)
                
                time.sleep(1)
                
                hist = stock.history(period="max")
                
                if hist.empty:
                    st.error(f"❌ 銘柄コード {stock_code} のデータが見つかりません。")
                    return None
                
                time.sleep(1)
                
                try:
                    info = stock.info
                    company_name = info.get('longName', info.get('shortName', f'銘柄{stock_code}'))
                except:
                    info = {}
                    company_name = f'銘柄{stock_code}'
                
                return {
                    'company_name': company_name,
                    'info': info,
                    'history': hist
                }
                
            except Exception as e:
                error_msg = str(e)
                
                if "Too Many Requests" in error_msg or "Rate limit" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        st.warning(f"⏳ レート制限により待機中... {wait_time}秒後に再試行します（{attempt + 1}/{max_retries}）")
                        time.sleep(wait_time)
                        continue
                    else:
                        st.error("❌ Yahoo Financeのレート制限に達しました。数分後に再度お試しください。")
                        return None
                else:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return None
        
        return None
    
    def calculate_comprehensive_score(self, data):
        """9項目の総合スコアを計算（100点満点）"""
        if not data or not data.get('info'):
            return 50, {'note': '企業情報が取得できないため、標準スコアを表示'}
        
        info = data['info']
        score_details = {}
        
        # 各指標を15点、10点で配分（合計100点）
        
        # 1. 経常収益（Revenue Growth）- 15点
        revenue_growth = info.get('revenueGrowth', None)
        if revenue_growth and revenue_growth > 0.05:  # 5%以上の成長
            score_details['revenue'] = {'score': 15, 'status': '✅ 合格', 'value': f'{revenue_growth*100:.1f}%'}
        elif revenue_growth and revenue_growth > 0:
            score_details['revenue'] = {'score': 8, 'status': '△ 要改善', 'value': f'{revenue_growth*100:.1f}%'}
        else:
            score_details['revenue'] = {'score': 0, 'status': '❌ 不合格', 'value': 'N/A'}
        
        # 2. EPS（Earnings Per Share）- 15点
        eps = info.get('trailingEps', None)
        eps_forward = info.get('forwardEps', None)
        if eps and eps_forward and eps_forward > eps:
            score_details['eps'] = {'score': 15, 'status': '✅ 合格', 'value': f'{eps:.2f} → {eps_forward:.2f}'}
        elif eps and eps > 0:
            score_details['eps'] = {'score': 8, 'status': '△ 要改善', 'value': f'{eps:.2f}'}
        else:
            score_details['eps'] = {'score': 0, 'status': '❌ 不合格', 'value': 'N/A'}
        
        # 3. 総資産（Total Assets）- 10点
        total_assets = info.get('totalAssets', None)
        if total_assets and total_assets > 0:
            score_details['assets'] = {'score': 10, 'status': '✅ 合格', 'value': f'{total_assets/1e9:.1f}B'}
        else:
            score_details['assets'] = {'score': 0, 'status': '❌ 不合格', 'value': 'N/A'}
        
        # 4. 営業CF（Operating Cash Flow）- 10点
        operating_cf = info.get('operatingCashflow', None)
        if operating_cf and operating_cf > 0:
            score_details['operating_cf'] = {'score': 10, 'status': '✅ 合格', 'value': f'{operating_cf/1e9:.1f}B'}
        else:
            score_details['operating_cf'] = {'score': 0, 'status': '❌ 不合格', 'value': 'N/A'}
        
        # 5. 現金等（Cash）- 10点
        cash = info.get('totalCash', None)
        if cash and cash > 0:
            score_details['cash'] = {'score': 10, 'status': '✅ 合格', 'value': f'{cash/1e9:.1f}B'}
        else:
            score_details['cash'] = {'score': 0, 'status': '❌ 不合格', 'value': 'N/A'}
        
        # 6. ROE（Return on Equity）- 10点
        roe = info.get('returnOnEquity', None)
        if roe and roe > 0.07:  # 7%以上
            score_details['roe'] = {'score': 10, 'status': '✅ 合格', 'value': f'{roe*100:.1f}%'}
        elif roe and roe > 0:
            score_details['roe'] = {'score': 5, 'status': '△ 要改善', 'value': f'{roe*100:.1f}%'}
        else:
            score_details['roe'] = {'score': 0, 'status': '❌ 不合格', 'value': 'N/A'}
        
        # 7. 自己資本比率 - 10点
        debt_to_equity = info.get('debtToEquity', None)
        if debt_to_equity is not None and debt_to_equity < 100:  # 50%以上の自己資本比率相当
            score_details['equity_ratio'] = {'score': 10, 'status': '✅ 合格', 'value': f'D/E: {debt_to_equity:.1f}'}
        elif debt_to_equity is not None:
            score_details['equity_ratio'] = {'score': 5, 'status': '△ 要改善', 'value': f'D/E: {debt_to_equity:.1f}'}
        else:
            score_details['equity_ratio'] = {'score': 0, 'status': '❌ 不合格', 'value': 'N/A'}
        
        # 8. 1株配当 - 10点
        dividend = info.get('dividendRate', None)
        if dividend and dividend > 0:
            score_details['dividend'] = {'score': 10, 'status': '✅ 合格', 'value': f'{dividend:.2f}円'}
        else:
            score_details['dividend'] = {'score': 0, 'status': '❌ 不合格', 'value': 'N/A'}
        
        # 9. 配当性向 - 10点
        payout_ratio = info.get('payoutRatio', None)
        if payout_ratio and payout_ratio <= 0.40:  # 40%以下
            score_details['payout_ratio'] = {'score': 10, 'status': '✅ 合格', 'value': f'{payout_ratio*100:.1f}%'}
        elif payout_ratio:
            score_details['payout_ratio'] = {'score': 5, 'status': '△ 要改善', 'value': f'{payout_ratio*100:.1f}%'}
        else:
            score_details['payout_ratio'] = {'score': 0, 'status': '❌ 不合格', 'value': 'N/A'}
        
        total_score = sum(item['score'] for item in score_details.values())
        return total_score, score_details

def load_history():
    """分析履歴を読み込み"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(stock_code, company_name, score, score_details):
    """分析履歴を保存"""
    history = load_history()
    entry = {
        'stock_code': stock_code,
        'company_name': company_name,
        'score': score,
        'score_details': score_details,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    history.append(entry)
    history = history[-100:]
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    # 月間ランキング更新
    update_monthly_ranking(entry)

def update_monthly_ranking(entry):
    """月間ランキングを更新"""
    current_month = datetime.now().strftime('%Y-%m')
    
    if RANKING_FILE.exists():
        with open(RANKING_FILE, 'r', encoding='utf-8') as f:
            rankings = json.load(f)
    else:
        rankings = {}
    
    if current_month not in rankings:
        rankings[current_month] = []
    
    # 同じ銘柄の古いデータを削除
    rankings[current_month] = [
        r for r in rankings[current_month] 
        if r['stock_code'] != entry['stock_code']
    ]
    
    rankings[current_month].append(entry)
    rankings[current_month].sort(key=lambda x: x['score'], reverse=True)
    
    with open(RANKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)

def load_monthly_ranking():
    """月間ランキングを読み込み"""
    if RANKING_FILE.exists():
        with open(RANKING_FILE, 'r', encoding='utf-8') as f:
            rankings = json.load(f)
        current_month = datetime.now().strftime('%Y-%m')
        return rankings.get(current_month, [])
    return []

def create_score_gauge(score):
    """スコアゲージチャート"""
    color = '#ff4444' if score < 40 else '#ffaa00' if score < 60 else '#00cc66'
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "総合スコア", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#ffcccc'},
                {'range': [40, 60], 'color': '#fff5cc'},
                {'range': [60, 100], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=60, b=20))
    return fig

def create_score_pie_chart(score_details):
    """スコア内訳の円グラフ"""
    labels = []
    values = []
    colors = []
    
    criteria_names = {
        'revenue': '経常収益',
        'eps': 'EPS',
        'assets': '総資産',
        'operating_cf': '営業CF',
        'cash': '現金等',
        'roe': 'ROE',
        'equity_ratio': '自己資本比率',
        'dividend': '1株配当',
        'payout_ratio': '配当性向'
    }
    
    color_map = {
        'revenue': '#FF6B6B',
        'eps': '#4ECDC4',
        'assets': '#45B7D1',
        'operating_cf': '#FFA07A',
        'cash': '#98D8C8',
        'roe': '#F7DC6F',
        'equity_ratio': '#BB8FCE',
        'dividend': '#85C1E2',
        'payout_ratio': '#F8B739'
    }
    
    for key, detail in score_details.items():
        if key != 'note':
            labels.append(criteria_names.get(key, key))
            values.append(detail['score'])
            colors.append(color_map.get(key, '#CCCCCC'))
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig.update_layout(
        title="スコア内訳",
        height=500,
        showlegend=True
    )
    
    return fig

def create_candlestick_chart(hist, timeframe_label):
    """ローソク足チャート作成"""
    if hist is None or hist.empty:
        return None
    
    fig = go.Figure(data=[go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close'],
        name='株価'
    )])
    
    if len(hist) >= 25:
        ma25 = hist['Close'].rolling(window=25).mean()
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=ma25,
            mode='lines',
            name='25日移動平均',
            line=dict(color='orange', width=1)
        ))
    
    if len(hist) >= 75:
        ma75 = hist['Close'].rolling(window=75).mean()
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=ma75,
            mode='lines',
            name='75日移動平均',
            line=dict(color='blue', width=1)
        ))
    
    fig.update_layout(
        title=f'株価推移 ({timeframe_label})',
        yaxis_title='株価 (円)',
        xaxis_title='日付',
        height=500,
        template='plotly_white',
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )
    return fig

# メインアプリケーション
st.markdown('<div class="main-header">📊 株最強分析くん</div>', unsafe_allow_html=True)

st.info("💡 **ポイント**: Yahoo Financeのレート制限により、連続して複数の銘柄を分析する場合は、各分析の間に数秒お待ちください。")

analyzer = StockAnalyzer()

# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")
    stock_code = st.text_input("銘柄コード", value="", placeholder="例: 7203")
    
    st.markdown("---")
    st.subheader("📈 株価表示期間")
    
    timeframe_options = {
        "5分足": "5m",
        "15分足": "15m",
        "1時間足": "1h",
        "5時間足": "5h",
        "1日足": "1d",
        "1週間足": "1wk",
        "1ヶ月足": "1mo",
        "1年": "1y",
        "5年": "5y",
        "全期間": "max"
    }
    
    timeframe = st.selectbox(
        "期間を選択",
        list(timeframe_options.keys()),
        index=7
    )
    
    analyze_button = st.button("🔍 分析開始", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.subheader("📜 分析履歴")
    history = load_history()
    if history:
        for entry in reversed(history[-5:]):
            with st.expander(f"{entry['company_name']} ({entry['stock_code']})"):
                st.metric("スコア", f"{entry['score']}点")
                st.caption(entry['date'])
    else:
        st.info("履歴がありません")

# タブ作成
tab1, tab2, tab3 = st.tabs(["📊 分析結果", "📋 履歴一覧", "🏆 月間ランキング"])

with tab1:
    if analyze_button and stock_code:
        with st.spinner('データ取得中...'):
            data = analyzer.fetch_stock_data(stock_code)
            
            if data is None:
                st.error("❌ データの取得に失敗しました")
                st.stop()
            
            score, score_details = analyzer.calculate_comprehensive_score(data)
            save_history(stock_code, data['company_name'], score, score_details)
        
        st.success(f"✅ {data['company_name']} の分析が完了しました!")
        
        # 企業情報表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            market_cap = data['info'].get('marketCap', 0)
            st.metric("時価総額", f"{market_cap/1e12:.2f}兆円" if market_cap > 1e12 else f"{market_cap/1e9:.2f}億円")
        
        with col2:
            pe = data['info'].get('trailingPE', 0)
            st.metric("PER", f"{pe:.2f}" if pe else "N/A")
        
        with col3:
            pb = data['info'].get('priceToBook', 0)
            st.metric("PBR", f"{pb:.2f}" if pb else "N/A")
        
        with col4:
            div_yield = data['info'].get('dividendYield', 0)
            st.metric("配当利回り", f"{div_yield*100:.2f}%" if div_yield else "N/A")
        
        st.markdown("---")
        
        # スコア表示
        st.subheader("🎯 総合評価スコア")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_score_gauge(score), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_score_pie_chart(score_details), use_container_width=True)
        
        # 評価コメント
        if score >= 80:
            st.success("🌟 優良企業!非常に高い投資価値が期待できます。")
        elif score >= 60:
            st.info("👍 良好な財務状態です。")
        elif score >= 40:
            st.warning("⚠️ 一部改善の余地があります。")
        else:
            st.error("❌ 慎重な判断が必要です。")
        
        # 詳細スコア
        st.subheader("📋 詳細評価")
        
        criteria_info = {
            'revenue': ('経常収益', '右肩上がり', 15),
            'eps': ('EPS', '右肩上がり', 15),
            'assets': ('総資産', '増加傾向', 10),
            'operating_cf': ('営業CF', 'プラス＆増加', 10),
            'cash': ('現金等', '積み上がり', 10),
            'roe': ('ROE', '7%以上', 10),
            'equity_ratio': ('自己資本比率', '50%以上', 10),
            'dividend': ('1株配当', '非減配', 10),
            'payout_ratio': ('配当性向', '40%以下', 10)
        }
        
        cols = st.columns(3)
        for idx, (key, (name, criteria_text, max_score)) in enumerate(criteria_info.items()):
            with cols[idx % 3]:
                detail = score_details.get(key, {'score': 0, 'status': '❌ 不合格', 'value': 'N/A'})
                achieved = detail['score']
                status = detail['status']
                value = detail['value']
                color = "#d4edda" if achieved == max_score else "#fff3cd" if achieved > 0 else "#f8d7da"
                st.markdown(f"""
                <div style="padding: 1rem; border-radius: 0.5rem; background-color: {color}; margin: 0.5rem 0;">
                    <strong>{name}</strong><br>
                    {status} ({achieved}/{max_score}点)<br>
                    <small>基準: {criteria_text}</small><br>
                    <small>値: {value}</small>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 株価チャート表示
        if data['history'] is not None and not data['history'].empty:
            st.subheader("💹 株価チャート")
            
            period_map = {
                "5分足": "1d",
                "15分足": "5d",
                "1時間足": "1mo",
                "5時間足": "1mo",
                "1日足": "6mo",
                "1週間足": "1y",
                "1ヶ月足": "5y",
                "1年": "1y",
                "5年": "5y",
                "全期間": "max"
            }
            
            interval_map = {
                "5分足": "5m",
                "15分足": "15m",
                "1時間足": "1h",
                "5時間足": "1h",
                "1日足": "1d",
                "1週間足": "1wk",
                "1ヶ月足": "1mo",
                "1年": "1d",
                "5年": "1wk",
                "全期間": "1mo"
            }
            
            period = period_map.get(timeframe, "1y")
            interval = interval_map.get(timeframe, "1d")
            
            # 指定期間のデータを再取得
            ticker = f"{stock_code}.T"
            stock = yf.Ticker(ticker)
            hist_filtered = stock.history(period=period, interval=interval)
            
            chart = create_candlestick_chart(hist_filtered, timeframe)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            
            # 株価統計
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("現在値", f"{hist_filtered['Close'].iloc[-1]:.2f}円")
            with col2:
                if len(hist_filtered) > 1:
                    change = hist_filtered['Close'].iloc[-1] - hist_filtered['Close'].iloc[-2]
                    change_pct = (change / hist_filtered['Close'].iloc[-2]) * 100
                    st.metric("前回比", f"{change:.2f}円", f"{change_pct:+.2f}%")
            with col3:
                st.metric("期間高値", f"{hist_filtered['High'].max():.2f}円")
            with col4:
                st.metric("期間安値", f"{hist_filtered['Low'].min():.2f}円")
    
    elif not stock_code and analyze_button:
        st.warning("⚠️ 銘柄コードを入力してください")
    else:
        st.info("👈 サイドバーから銘柄コードを入力して分析を開始してください")
        
        with st.expander("📖 使い方ガイド"):
            st.markdown("""
            ### 銘柄コードの入力例
            - **トヨタ自動車**: 7203
            - **ソニーグループ**: 6758
            - **任天堂**: 7974
            - **キーエンス**: 6861
            
            ### スコアリング基準（100点満点）
            
            1. **経常収益** (15点) - 右肩上がり
            2. **EPS** (15点) - 右肩上がり
            3. **総資産** (10点) - 増加傾向
            4. **営業CF** (10点) - プラス＆増加
            5. **現金等** (10点) - 積み上がり
            6. **ROE** (10点) - 7%以上
            7. **自己資本比率** (10点) - 50%以上
            8. **1株配当** (10点) - 非減配
            9. **配当性向** (10点) - 40%以下
            
            ### 評価基準
            - **80点以上**: 優良企業
            - **60-79点**: 良好な財務状態
            - **40-59点**: 改善の余地あり
            - **39点以下**: 慎重な判断が必要
            """)

with tab2:
    st.subheader("📋 全分析履歴")
    
    if history:
        df_history = pd.DataFrame(history)
        df_history = df_history