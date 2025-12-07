import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.express as px 
import time 

# ... (程式碼開頭不變) ...

# --- 執行數據抓取 ---
data_df = load_data(ticker_symbol, start_date, end_date, interval, selected_interval_label)

# 視覺化與呈現
if not data_df.empty:
    st.subheader(f"📈 {ticker_symbol} 價格走勢圖 ({selected_interval_label})")

    # --- Plotly 繪圖前的數據標準化 (最終穩定修正，避免 KeyError) ---
    df_plot = data_df.reset_index() 
    
    # 步驟 1: 確定第一個欄位的名稱 (它可能是 'Date' 或 'index')
    date_col_name = df_plot.columns[0]
    
    # 步驟 2: 使用安全的 rename 方法，將日期欄位和 Close 欄位重命名
    df_plot = df_plot.rename(columns={
        date_col_name: 'Datetime',  # 安全地將第一個欄位重命名為 'Datetime'
        'Close': 'Price'            # 將 Close 欄位重命名為 'Price'
    })
    
    # 步驟 3: 移除包含 NaN 值的行 (現在 'Price' 和 'Datetime' 肯定存在)
    # 這是發生錯誤的行，但現在欄位名稱已經被保證
    df_plot = df_plot.dropna(subset=['Price', 'Datetime'])
    
    # 步驟 4: 最終檢查：防止數據清洗後為空
    if df_plot.empty:
        st.error("🚫 **錯誤**：數據經過清洗後已無有效數據點。請檢查日期範圍是否包含交易日。")
        st.stop()


    # --- 使用 Plotly Express 繪製圖表 ---
    fig = px.line(
        df_plot,
        x='Datetime',  # 使用標準化後的穩定名稱
        y='Price',             
        title=f'{ticker_symbol} 收盤價格走勢圖',
        template='plotly_white'
    )
    
    # ... (繪圖與數據呈現程式碼不變) ...
    
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
