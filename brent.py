import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import matplotlib.pyplot as plt

# --- 網頁設定 ---
st.set_page_config(
    page_title="布蘭特原油走勢儀表板",
    layout="wide"
)

# --- 標題 ---
st.title("⛽ 布蘭特原油 (Brent Oil) 歷史走勢分析")

# --- 側邊欄輸入控制項 ---
st.sidebar.header("設定選項")

# 讓用戶選擇要分析的金融代碼 (預設為布蘭特原油期貨)
ticker_symbol = st.sidebar.text_input("輸入金融代碼 (例如: BZ=F, ^GSPC)", "BZ=F")

# 讓用戶選擇日期範圍
today = datetime.date.today()
start_date = st.sidebar.date_input("起始日期", datetime.date(2020, 1, 1))
end_date = st.sidebar.date_input("結束日期", today)


# --- 數據抓取函式 (使用 Streamlit 的快取功能) ---
@st.cache_data
def load_data(ticker, start, end):
    """從 yfinance 下載數據並快取"""
    try:
        data = yf.download(ticker, start=start, end=end)
        if data.empty:
             st.error(f"錯誤：無法獲取代碼 '{ticker}' 的數據，請檢查代碼是否正確。")
             return pd.DataFrame() # 返回空 DataFrame
        return data
    except Exception as e:
        st.error(f"抓取數據時發生錯誤: {e}")
        return pd.DataFrame()

# --- 執行數據抓取 ---
data_df = load_data(ticker_symbol, start_date, end_date)

# --- 網頁主要內容展示 ---
if not data_df.empty:
    st.subheader(f"📈 {ticker_symbol} 價格走勢圖 ({start_date} 至 {end_date})")

    # 繪製收盤價折線圖 (使用 Streamlit 內建功能更簡潔)
    st.line_chart(data_df['Close'])
    
    # 繪製K線圖的另一種方式 (使用 Matplotlib/Plotly 則更進階)
    # 這裡只使用內建 line_chart 保持簡潔
    
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
        file_name=f'{ticker_symbol}_history.csv',
        mime='text/csv',
    )
