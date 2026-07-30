import streamlit as st
import requests
import re
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# Page Configuration
st.set_page_config(page_title="Fast Telegram Group Checker", page_icon="⚡", layout="centered")

st.title("⚡ Fast Telegram Bulk Checker")
st.write("Link Filter + Group Name Extraction + Super Fast Speed!")

# Input Box
input_text = st.text_area(
    "Group Links ya Usernames daalein (Ek line me ek):", 
    placeholder="python\n@telegram\nhttps://t.me/durov\nRandom Group Text (Ise Auto-Skip Kar Dega)",
    height=180
)

# 1. Helper function: Check if input is a valid link/username format
def is_valid_telegram_input(raw_input):
    s = raw_input.strip()
    # Agar space hai, toh wo username/link nahi balki normal text hai
    if ' ' in s:
        return False, None
    
    clean = s.replace("https://t.me/", "").replace("http://t.me/", "").replace("t.me/", "").replace("@", "").strip("/")
    
    # Telegram username validation (5 to 32 characters, A-Z, 0-9, _)
    if re.match(r'^[a-zA-Z0-9_]{5,32}$', clean):
        return True, clean
    return False, None

# 2. Worker function for checking a single group
def check_single_group(raw_input):
    is_valid, clean_username = is_valid_telegram_input(raw_input)
    
    if not is_valid:
        return {
            "Input Link": raw_input,
            "Group Name": "N/A (Invalid Link)",
            "Status": "SKIPPED ⚠️"
        }

    url = f"https://t.me/{clean_username}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=6)
        html = res.text
        
        # Dead or non-existent check
        if "tgme_page_error" in html or "doesn't exist" in html.lower():
            return {
                "Input Link": raw_input,
                "Group Name": "N/A",
                "Status": "DEAD / BANNED ❌"
            }

        # Scraping Group Name from Telegram Web Preview
        group_name = "Unknown Name"
        match_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if match_title:
            group_name = match_title.group(1)
        else:
            match_span = re.search(r'<div class="tgme_page_title"[^>]*><span dir="auto">([^<]+)</span>', html)
            if match_span:
                group_name = match_span.group(1)

        # Status Check
        if "you can view and join" in html.lower() or "tgme_page_title" in html:
            status = "ACTIVE ✅"
        else:
            status = "PRIVATE / UNKNOWN ⚠️"

        return {
            "Input Link": raw_input,
            "Group Name": group_name,
            "Status": status
        }
        
    except Exception:
        return {
            "Input Link": raw_input,
            "Group Name": "N/A",
            "Status": "ERROR ⚠️"
        }

# Main Action Button
if st.button("🚀 Fast Check Groups", use_container_width=True):
    if not input_text.strip():
        st.warning("⚠️ Kripya kam se kam ek link ya username daalein!")
    else:
        raw_lines = [line.strip() for line in input_text.split("\n") if line.strip()]
        
        st.info(f"Total {len(raw_lines)} items process ho rahe hain...")
        progress_bar = st.progress(0)
        
        # Multithreading for Super Fast checking (10 workers in parallel)
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_single_group, line) for line in raw_lines]
            for i, future in enumerate(futures):
                results.append(future.result())
                progress_bar.progress((i + 1) / len(raw_lines))
        
        st.success("✅ Complete!")
        
        # Convert to Pandas DataFrame
        df = pd.DataFrame(results)
        
        # Display Table
        st.dataframe(df, use_container_width=True)
        
        # CSV File Download with Group Name column
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Excel/CSV File (With Group Names)",
            data=csv,
            file_name="telegram_groups_detailed_status.csv",
            mime="text/csv"
        )
