import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.express as px 
import time # 新增 time 函式庫用於穩定 API 請求

# --- 網頁設定 ---
st.set_page_config(
    page_title="金融數據分析儀表板",
    layout="wide"
)

# --- 標題 ---
st.title("💰 金融數據走勢分析儀表板 (yfinance & Streamlit)")

# --- 側邊欄輸入控制項 ---
st.sidebar.header("設定選項")

# 1. 輸入金融代碼
ticker_symbol = st.sidebar.text_input("輸入金融代碼 (例如: BZ=F, ^GSPC, 2330.TW)", "BZ=F")

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
    index=0 
)
interval = interval_options[selected_interval_label]

# --- 3. 自動調整日期範圍 ---
today = datetime.date.today()
MAX_DAYS_MAP = {
    "1m": 7,  
    "5m": 7,
    "30m": 7,
    "1h": 60, 
    "1d": 5 * 365 
}
max_days = MAX_DAYS_MAP.get(interval, 5 * 365) 

safe_default_start_date = today - datetime.timedelta(days=max_days)
min_selectable_date = today - datetime.timedelta(days=max_days + 1)

if interval == "1d":
    min_selectable_date = datetime.date(1980, 1, 1)
    
start_date = st.sidebar.date_input(
    "起始日期 (會依頻率自動調整預設值)",
    value=safe_default_start_date, 
    min_value=min_selectable_date 
)
end_date = st.sidebar.date_input("結束日期", today)


# --- 數據抓取函式 (使用 Streamlit 的快取功能) ---
@st.cache_data(show_spinner=f"正在從 Yahoo Finance 下載 {ticker_symbol} 的 {selected_interval_label} 數據...")
def load_data(ticker, start, end, interval, selected_interval_label):
    
    # 顯示數據限制警告
    if interval in ["1m", "5m", "30m"]:
        st.info(f"⚠️ **高頻率數據限制**：選擇 **{selected_interval_label}** 時，Yahoo Finance 通常僅提供**過去約 7 個交易日**的數據。")
    elif interval == "1h":
        st.info(f"⚠️ **小時線數據限制**：選擇 **{selected_interval_label}** 時，Yahoo Finance 通常僅提供**過去約 60 天**的數據。")
        
    try:
        # 新增延遲，提高 API 請求穩定性
        time.sleep(1) 
        
        data = yf.download(
            ticker, 
            start=start.strftime('%Y-%m-%d'), 
            end=end.strftime('%Y-%m-%d'), 
            interval=interval
        )
        
        # 關鍵錯誤檢查：數據為空或缺少欄位
        if data.empty or 'Close' not in data.columns:
             st.error(f"🚫 數據載入失敗或數據為空。請檢查您的代碼 '{ticker}'、日期範圍或時間間隔設定。")
             st.cache_data.clear() 
             return pd.DataFrame()
             
        # 數據結構良好，直接返回
        return data
        
    except Exception as e:
        st.error(f"抓取數據時發生錯誤: {e}")
        st.cache_data.clear() 
        return pd.DataFrame()

# --- 執行數據抓取 ---
data_df = load_data(ticker_symbol, start_date, end_date, interval, selected_interval_label)

# 視覺化與呈現
if not data_df.empty:
    st.subheader(f"📈 {ticker_symbol} 價格走勢圖 ({selected_interval_label})")

    # --- 使用 Plotly Express 繪製圖表 ---
    # 將日期索引重設為欄位，默認名稱為 'Date'
    df_plot = data_df.reset_index() 
    
    fig = px.line(
        df_plot,
        x='Date',  # 直接使用 'Date' 欄位名稱，提高 Plotly 穩定性
        y='Close',             
        title=f'{ticker_symbol} 收盤價格走勢圖',
        template='plotly_white'
    )
    
    # 確保 Y 軸自動縮放並允許互動
    fig.update_yaxes(autorange=True, fixedrange=False) 
    fig.update_xaxes(title_text=f"日期 / 時間 ({selected_interval_label})")

    st.plotly_chart(fig, use_container_width=True)

    # --- 數據表格與統計 ---
    st.markdown("---")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 原始數據 (最新 10 筆)")
        st.dataframe(data_df.tail(10).style.format(precision=2))
    
    with col2:
        st.subheader("📝 統計摘要")
        st.write(data_df['Close'].describe().to_frame().style.format(precision=2))
        
    # 下載按鈕
    csv_data = data_df.to_csv().encode('utf-8')
    st.download_button(
        label=f"📥 下載 {ticker_symbol} ({selected_interval_label}) 數據為 CSV",
        data=csv_data,
        file_name=f'{ticker_symbol}_history_{interval}.csv',
        mime='text/csv',
    )
