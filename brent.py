import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.express as px 
import time 

# --- 網頁設定 ---
st.set_page_config(
    page_title="金融數據分析儀表板 (含技術指標)",
    layout="wide"
)

# --- 標題 ---
st.title("💰 金融數據走勢分析儀表板 (15 分鐘線)")

# -------------------------------------------------------------
## 🛠️ 數據抓取與指標計算 (硬編碼為 15m)
# -------------------------------------------------------------
interval = "15m"
selected_interval_label = "15 分鐘線 (15m)"

@st.cache_data(show_spinner=f"正在下載 {selected_interval_label} 數據...")
def load_data(ticker, start, end, interval, selected_interval_label):
    
    # 顯示數據限制警告 (針對 15 分鐘線)
    st.info(f"⚠️ **數據限制**：本應用程式僅提供 **{selected_interval_label}** 數據，Yahoo Finance 通常僅提供**過去約 60 天**的歷史數據。")
        
    try:
        time.sleep(1) 
        
        data = yf.download(
            ticker, 
            start=start.strftime('%Y-%m-%d'), 
            end=end.strftime('%Y-%m-%d'), 
            interval=interval
        )
        
        if data.empty or 'Close' not in data.columns:
             st.error(f"🚫 數據載入失敗或數據為空。請檢查您的代碼 '{ticker}' 或日期範圍設定。")
             st.cache_data.clear() 
             return pd.DataFrame()
             
        # --- 新增技術指標計算 ---
        # 計算 20 週期簡單移動平均線 (SMA)
        # 由於是 15m K 線，20 週期 SMA 代表近 5 小時的平均價格 (20*15/60 = 5小時)
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        
        return data
        
    except Exception as e:
        st.error(f"抓取數據時發生錯誤: {e}")
        st.cache_data.clear() 
        return pd.DataFrame()

# -------------------------------------------------------------
## ⚙️ 輸入控制項與變數設定
# -------------------------------------------------------------

st.sidebar.header("設定選項")

# 1. 輸入金融代碼 (預設替換為 CL=F)
# 使用 CL=F (西德州原油) 提高數據穩定性
ticker_symbol = st.sidebar.text_input("輸入金融代碼 (例如: CL=F, ^GSPC, 2330.TW)", "CL=F")

# 2. 顯示固定時間間隔
st.sidebar.metric("數據頻率", selected_interval_label)

# 3. 自動調整日期範圍 (限制在 60 天內)
today = datetime.date.today()
MAX_DAYS = 60 
safe_default_start_date = today - datetime.timedelta(days=MAX_DAYS)
min_selectable_date = today - datetime.timedelta(days=MAX_DAYS + 1)
    
start_date = st.sidebar.date_input(
    "起始日期 (限於 60 天內)",
    value=safe_default_start_date, 
    min_value=min_selectable_date 
)
end_date = st.sidebar.date_input("結束日期", today)


# -------------------------------------------------------------
## 📈 主程式邏輯與繪圖
# -------------------------------------------------------------

data_df = load_data(ticker_symbol, start_date, end_date, interval, selected_interval_label)

# 視覺化與呈現
if not data_df.empty:
    st.subheader(f"📈 {ticker_symbol} 價格走勢圖 - {selected_interval_label} (含 20 期 SMA)")

    # --- Plotly 繪圖前的數據標準化 (確保穩定性) ---
    df_plot = data_df.reset_index() 
    
    # 1. 確定第一個欄位的名稱
    date_col_name = df_plot.columns[0]
    
    # 2. 使用安全的 rename 方法，將欄位名稱標準化
    col_mapping = {
        date_col_name: 'Datetime',  
        'Close': 'Price'            # 確保 Close 欄位被命名為 Price
    }
    df_plot = df_plot.rename(columns=col_mapping)
    
    # 3. 移除包含 NaN 值的行 (現在我們同時需要 Price 和 SMA_20)
    # **注意:** SMA_20 在前 19 個數據點會是 NaN，這是正常的。
    df_plot = df_plot.dropna(subset=['Price', 'Datetime'])
    
    # 4. 最終檢查：防止數據清洗後為空
    if df_plot.empty:
        st.error("🚫 **錯誤**：數據經過清洗後已無有效數據點。請檢查日期範圍是否包含交易日。")
        st.stop()

    # --- 使用 Plotly Express 繪製圖表 (包含 SMA_20) ---
    
    # 將數據從寬格式 (Wide Format) 轉換為長格式 (Long Format) 以便 Plotly 繪製多條線
    df_melt = df_plot.melt(
        id_vars=['Datetime'], 
        value_vars=['Price', 'SMA_20'], 
        var_name='Series', 
        value_name='Value'
    )
    
    fig = px.line(
        df_melt,
        x='Datetime',  
        y='Value',             
        color='Series',        # 根據 Series 欄位 (Price, SMA_20) 繪製不同顏色
        line_dash='Series',    # 區分 Price (實線) 和 SMA_20 (虛線)
        color_discrete_map={'Price': 'blue', 'SMA_20': 'red'}, # 自定義顏色
        title=f'{ticker_symbol} 價格與 20 期 SMA 走勢圖',
        template='plotly_white'
    )
    
    fig.update_layout(
        legend_title_text='圖例'
    )
    fig.update_traces(line=dict(width=1.5)) # 讓線條細一點
    fig.update_yaxes(title_text="價格 / 指標值")
    fig.update_xaxes(title_text=f"日期 / 時間 ({selected_interval_label})")

    st.plotly_chart(fig, use_container_width=True)

    # --- 數據表格與統計 ---
    st.markdown("---")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 原始數據 (含 SMA，最新 10 筆)")
        # 顯示 Close 和 SMA_20 欄位
        st.dataframe(data_df[['Close', 'SMA_20', 'Volume']].tail(10).style.format(precision=2))
    
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
