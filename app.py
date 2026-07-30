import streamlit as st
import requests
import re
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# Page Configuration
st.set_page_config(page_title="Fast Telegram Group Checker", page_icon="⚡", layout="centered")

st.title("⚡ Telegram Bulk Group Checker")
st.write("Fixes applied: Private links (`+`), Joinchat links & Public usernames sabhi support honge!")

# Input Box
input_text = st.text_area(
    "Group Links ya Usernames daalein (Ek line me ek):", 
    placeholder="python\n@telegram\nhttps://t.me/durov\nhttps://t.me/+AbCdEfGh12345\nRandom Sentence Text (Ise Auto-Skip Kar Dega)",
    height=180
)

# 1. Smart Link Extraction & Validation
def parse_telegram_input(raw_input):
    s = raw_input.strip()
    if not s:
        return False, None
    
    # Check 1: Agar line me t.me/ ka link hai (Public, Private +, or Joinchat)
    if "t.me/" in s:
        # Extract full t.me URL portion even if surrounded by whitespace
        match = re.search(r'(https?://)?t\.me/([^\s]+)', s)
        if match:
            path = match.group(2).rstrip('/')
            return True, f"https://t.me/{path}"
            
    # Check 2: Agar @username format hai
    elif s.startswith("@"):
        clean = s[1:].strip()
        if ' ' not in clean and len(clean) >= 3:
            return True, f"https://t.me/{clean}"
            
    # Check 3: Agar direct public username ya + invite code hai bina space ke
    elif ' ' not in s and len(s) >= 3:
        clean = s.replace("https://", "").replace("http://", "").strip("/")
        return True, f"https://t.me/{clean}"

    # Normal text with spaces / invalid format
    return False, None

# 2. Worker function for checking a single group
def check_single_group(raw_input):
    is_valid, target_url = parse_telegram_input(raw_input)
    
    if not is_valid:
        return {
            "Input Link": raw_input,
            "Group Name": "N/A (Not a Telegram Link)",
            "Status": "SKIPPED ⚠️"
        }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    try:
        res = requests.get(target_url, headers=headers, timeout=8)
        html = res.text
        
        # Dead or non-existent check
        if "tgme_page_error" in html or "doesn't exist" in html.lower() or "if you have telegram, you can contact" in html.lower():
            return {
                "Input Link": raw_input,
                "Group Name": "N/A",
                "Status": "DEAD / BANNED ❌"
            }

        # Extract Group/Channel Name from OpenGraph Metadata
        group_name = "Unknown / Private Name"
        match_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if match_title:
            group_name = match_title.group(1)
        else:
            match_span = re.search(r'<div class="tgme_page_title"[^>]*><span dir="auto">([^<]+)</span>', html)
            if match_span:
                group_name = match_span.group(1)

        # Status Checking Logic
        if "you can view and join" in html.lower() or "tgme_page_title" in html or "tgme_page_extra" in html:
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
if st.button("🚀 Check Groups Now", use_container_width=True):
    if not input_text.strip():
        st.warning("⚠️ Kripya kam se kam ek link ya username daalein!")
    else:
        raw_lines = [line.strip() for line in input_text.split("\n") if line.strip()]
        
        st.info(f"Total {len(raw_lines)} items process ho rahe hain...")
        progress_bar = st.progress(0)
        
        # Parallel Multithreading for Fast Checking
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_single_group, line) for line in raw_lines]
            for i, future in enumerate(futures):
                results.append(future.result())
                progress_bar.progress((i + 1) / len(raw_lines))
        
        st.success("✅ Checking Complete!")
        
        # Convert to Pandas DataFrame
        df = pd.DataFrame(results)
        
        # Display Results Table
        st.dataframe(df, use_container_width=True)
        
        # CSV File Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Excel/CSV File (With Group Names)",
            data=csv,
            file_name="telegram_groups_status.csv",
            mime="text/csv"
        )
