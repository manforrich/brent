import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# --- 網頁設定 ---
st.set_page_config(
    page_title="布蘭特原油走勢儀表板",
    layout="wide"
)

# --- 標題 ---
st.title("⛽ 布蘭特原油 (Brent Oil) 歷史走勢分析")

# --- 側邊欄輸入控制項 ---
st.sidebar.header("設定選項")

# 1. 輸入金融代碼
ticker_symbol = st.sidebar.text_input("輸入金融代碼 (例如: BZ=F)", "BZ=F")

# 2. 選擇時間間隔
interval_options = {
    "日線 (1d)": "1d",
    "小時線 (1h)": "1h",
    "30 分鐘線 (30m)": "30m",
    "5 分鐘線 (5m)": "5m",
    "1 分鐘線 (1m)": "1m"
}
selected_interval_label = st.sidebar.selectbox(
    "選擇數據頻率 (時間間隔)",
    list(interval_options.keys()),
    index=0 # 預設為日線
)
interval = interval_options[selected_interval_label]

# --- 3. 自動調整日期範圍 ---
today = datetime.date.today()
# 設定不同時間間隔的最大歷史限制 (yfinance 的經驗值)
MAX_DAYS_MAP = {
    "1m": 7,  # 分鐘線數據限制在約 7 天
    "5m": 7,
    "30m": 7,
    "1h": 60, # 小時線數據限制在約 60 天
    "1d": 5 * 365 # 日線數據預設顯示約 5 年
}
max_days = MAX_DAYS_MAP.get(interval, 5 * 365) # 取得安全的最大天數

# 計算「安全」的預設起始日期
safe_default_start_date = today - datetime.timedelta(days=max_days)
# 設定日期選擇器的最小限制
min_selectable_date = today - datetime.timedelta(days=max_days + 1)
# 確保日線可以選擇很早的日期
if interval == "1d":
    min_selectable_date = datetime.date(1980, 1, 1)
    
# 設定起始日期輸入框
start_date = st.sidebar.date_input(
    "起始日期 (會依頻率自動調整預設值)",
    value=safe_default_start_date, # 預設值會隨頻率變動
    min_value=min_selectable_date # 限制使用者不能選取太舊的日期（針對高頻率）
)

# 設定結束日期輸入框
end_date = st.sidebar.date_input("結束日期", today)


# --- 數據抓取函式 (使用 Streamlit 的快取功能) ---
@st.cache_data(show_spinner="正在從 Yahoo Finance 下載數據...")
def load_data(ticker, start, end, interval):
    """從 yfinance 下載數據並快取，並顯示數據限制警告"""
    
    # 針對高頻率數據顯示警告
    if interval in ["1m", "5m", "30m"]:
        st.info(f"⚠️ **高頻率數據限制**：選擇 **{selected_interval_label}** 時，Yahoo Finance 通常僅提供**過去約 7 個交易日**的數據。")
    elif interval == "1h":
        st.info(f"⚠️ **小時線數據限制**：選擇 **{selected_interval_label}** 時，Yahoo Finance 通常僅提供**過去約 60 天**的數據。")
        
    try:
        data = yf.download(
            ticker, 
            start=start.strftime('%Y-%m-%d'), 
            end=end.strftime('%Y-%m-%d'), 
            interval=interval
        )
        if data.empty:
             st.error(f"錯誤：無法獲取代碼 '{ticker}' 或所選時間範圍的數據。")
             return pd.DataFrame()
        return data
    except Exception as e:
        st.error(f"抓取數據時發生錯誤: {e}")
        return pd.DataFrame()

# --- 執行數據抓取 ---
data_df = load_data(ticker_symbol, start_date, end_date, interval)

# --- 網頁主要內容展示 ---
if not data_df.empty:
    st.subheader(f"📈 {ticker_symbol} 價格走勢圖 ({selected_interval_label} - {data_df.index.min().strftime('%Y-%m-%d')} 至 {data_df.index.max().strftime('%Y-%m-%d')})")

    # 繪製收盤價折線圖
    st.line_chart(data_df['Close'])
    
    st.subheader("📊 原始數據 (最新 10 筆)")
    st.dataframe(data_df.tail(10))
    
    # 顯示統計摘要
    st.subheader("📝 統計摘要")
    st.write(data_df['Close'].describe())
    
    # 下載按鈕
    csv_data = data_df.to_csv().encode('utf-8')
    st.download_button(
        label=f"下載 {ticker_symbol} ({selected_interval_label}) 數據為 CSV",
        data=csv_data,
        file_name=f'{ticker_symbol}_history_{interval}.csv',
        mime='text/csv',
    )
