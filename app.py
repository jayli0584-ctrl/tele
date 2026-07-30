import streamlit as st
import requests
import time
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Telegram Group Checker", page_icon="✈️", layout="centered")

st.title("✈️ Telegram Bulk Group Checker")
st.write("Ek sath multiple Telegram groups ka status check karein — **Online & Fast!**")

# Input Box
input_text = st.text_area(
    "Group Links ya Usernames daalein (Har line me ek):", 
    placeholder="python\n@telegram\nhttps://t.me/durov",
    height=150
)

if st.button("🚀 Check Groups Now", use_container_width=True):
    if not input_text.strip():
        st.warning("⚠️ Kripya kam se kam ek group username ya link daalein!")
    else:
        groups = [g.strip() for g in input_text.split("\n") if g.strip()]
        results = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, group in enumerate(groups):
            clean_username = group.replace("https://t.me/", "").replace("t.me/", "").replace("@", "").strip()
            url = f"https://t.me/{clean_username}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            try:
                res = requests.get(url, headers=headers, timeout=10)
                html = res.text
                
                if "tgme_page_error" in html or "doesn't exist" in html.lower():
                    status = "DEAD / BANNED ❌"
                elif "you can view and join" in html.lower() or "tgme_page_title" in html:
                    status = "ACTIVE ✅"
                else:
                    status = "PRIVATE / UNKNOWN ⚠️"
            except Exception:
                status = "ERROR ⚠️"
            
            results.append({"Group / Link": group, "Status": status})
            
            # Progress update
            progress_bar.progress((i + 1) / len(groups))
            status_text.text(f"Checking ({i+1}/{len(groups)}): {group}")
            time.sleep(0.5)
            
        status_text.success("✅ Checking Complete!")
        
        # Display Table
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        
        # CSV Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Results (CSV File)",
            data=csv,
            file_name="telegram_status_results.csv",
            mime="text/csv"
        )