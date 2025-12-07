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


# 3. 選擇日期範圍
today = datetime.date.today()
# 備註：yfinance 的分鐘數據有歷史長度限制，因此將預設起始日期設為近 30 天
if interval in ["1m", "5m", "30m", "1h"]:
    # 針對高頻率數據，將預設起始日設為近 60 天
    default_start_date = today - datetime.timedelta(days=60)
else:
    # 對於日線等較低頻率數據，保留較長歷史範圍
    default_start_date = datetime.date(2020, 1, 1)

start_date = st.sidebar.date_input("起始日期", default_start_date)
end_date = st.sidebar.date_input("結束日期", today)


# --- 數據抓取函式 (使用 Streamlit 的快取功能) ---
@st.cache_data(show_spinner="正在從 Yahoo Finance 下載數據...")
def load_data(ticker, start, end, interval):
    """從 yfinance 下載數據並快取"""
    st.info(f"注意：使用 {interval_options[selected_interval_label]} 時，Yahoo Finance 僅提供有限的歷史數據（1 分鐘線約 7 天）。")
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
    st.subheader(f"📈 {ticker_symbol} 價格走勢圖 ({selected_interval_label} - {start_date} 至 {end_date})")

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
