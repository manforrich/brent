import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.express as px # 引入 Plotly 進行互動式繪圖

# --- 網頁設定 ---
st.set_page_config(
    page_title="金融數據分析儀表板",
    layout="wide"
)

# --- 標題 ---
st.title("💰 金融數據走勢分析儀表板 (yfinance & Streamlit)")

# --- 側邊欄輸入控制項 ---
st.sidebar.header("設定選項")

# 1. 輸入金融代碼 (預設為布蘭特原油期貨)
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
# 使用 st.cache_data 確保數據只在參數變動時才重新下載
@st.cache_data(show_spinner=f"正在從 Yahoo Finance 下載 {ticker_symbol} 的 {selected_interval_label} 數據...")
def load_data(ticker, start, end, interval, selected_interval_label):
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
        # 檢查數據是否真的抓取成功，防止返回空 DataFrame
        if data.empty or 'Close' not in data.columns:
             st.error(f"🚫 數據載入失敗或數據為空。請檢查您的代碼 '{ticker}'、日期範圍或時間間隔設定。")
             return pd.DataFrame()
        return data
    except Exception as e:
        # 捕捉所有錯誤，並返回空的 DataFrame，避免後續 Plotly 報錯
        st.error(f"抓取數據時發生錯誤: {e}")
        return pd.DataFrame()

# --- 執行數據抓取 ---
data_df = load_data(ticker_symbol, start_date, end_date, interval, selected_interval_label)

# 視覺化與呈現
if not data_df.empty:
    st.subheader(f"📈 {ticker_symbol} 價格走勢圖 ({selected_interval_label})")

    # --- 使用 Plotly Express 繪製圖表 (自動縮放效果佳) ---
    # 繪圖前，將日期索引轉為可識別的欄位名稱
    df_plot = data_df.reset_index() 
    
    fig = px.line(
        df_plot,
        x=df_plot.columns[0],  # X 軸為第一個欄位 (通常是 Date/Datetime)
        y='Close',             # Y 軸為收盤價
        title=f'{ticker_symbol} 收盤價格走勢圖',
        template='plotly_white'
    )
    
    # 確保 Y 軸自動縮放並允許互動 (這解決了座標不自動調整的問題)
    fig.update_yaxes(autorange=True, fixedrange=False) 
    
    # 確保 X 軸標籤清晰
    fig.update_xaxes(title_text=f"日期 / 時間 ({selected_interval_label})")

    # 

    st.plotly_chart(fig, use_container_width=True)

    # --- 數據表格與統計 ---
    st.markdown("---")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 原始數據 (最新 10 筆)")
        # 顯示最新數據，更符合分析習慣
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
