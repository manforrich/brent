import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
# import matplotlib.pyplot as plt # 由於未使用，移除此 import 保持程式碼簡潔

# --- 網頁設定 ---
st.set_page_config(
    page_title="布蘭特原油走勢儀表板",
    layout="wide"
)

# --- 標題 ---
# 這裡將標題更新為包含時間間隔的描述
st.title("⛽ 布蘭特原油 (Brent Oil) 歷史走勢分析 (15 分鐘線)")

# -------------------------------------------------------------
## ⚙️ 定義時間間隔參數 (硬編碼為 15m)
# -------------------------------------------------------------
interval = "15m"
selected_interval_label = "15 分鐘線 (15m)"


# --- 側邊欄輸入控制項 ---
st.sidebar.header("設定選項")

# 讓用戶選擇要分析的金融代碼 (預設為布蘭特原油期貨)
ticker_symbol = st.sidebar.text_input("輸入金融代碼 (例如: BZ=F, ^GSPC)", "BZ=F")

# 讓用戶選擇日期範圍
today = datetime.date.today()
# 由於 15 分鐘線屬於日內數據，Yahoo Finance 通常只提供約 60 天的數據。
# 我們將起始日期預設為近 60 天，以確保能抓到數據。
safe_default_start_date = today - datetime.timedelta(days=60) 
start_date = st.sidebar.date_input("起始日期 (建議在近 60 天內)", safe_default_start_date)
end_date = st.sidebar.date_input("結束日期", today)


# --- 數據抓取函式 (使用 Streamlit 的快取功能) ---
@st.cache_data
def load_data(ticker, start, end, interval):
    """從 yfinance 下載數據並快取"""
    try:
        # 關鍵：將 interval 參數傳遞給 yf.download
        data = yf.download(ticker, start=start, end=end, interval=interval)
        if data.empty:
             st.error(f"錯誤：無法獲取代碼 '{ticker}' 的數據，請檢查代碼是否正確或日期範圍是否有效。")
             return pd.DataFrame() # 返回空 DataFrame
        return data
    except Exception as e:
        st.error(f"抓取數據時發生錯誤: {e}")
        return pd.DataFrame()

# --- 執行數據抓取 ---
# 關鍵：將 interval 參數傳遞給 load_data 函數
data_df = load_data(ticker_symbol, start_date, end_date, interval)

# --- 網頁主要內容展示 ---
if not data_df.empty:
    st.subheader(f"📈 {ticker_symbol} 價格走勢圖 - {selected_interval_label} ({start_date} 至 {end_date})")

    # 繪製收盤價折線圖 (使用 Streamlit 內建功能更簡潔)
    st.line_chart(data_df['Close'])
    
    st.subheader("📊 原始數據 (前 10 筆)")
    st.dataframe(data_df.head(10))
    
    # 顯示統計摘要
    st.subheader("📝 統計摘要")
    st.write(data_df['Close'].describe())
    
    # 提示下載
    csv_data = data_df.to_csv().encode('utf-8')
    st.download_button(
        label="下載數據為 CSV",
        data=csv_data,
        file_name=f'{ticker_symbol}_history_{interval}.csv',
        mime='text/csv',
    )
