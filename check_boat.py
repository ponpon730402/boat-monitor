import os
import datetime
import requests
from bs4 import BeautifulSoup

# 從 GitHub Secrets 讀取密鑰（保護你的 Token 不會外洩）
TARGET_URL = "https://takachiho-kanko.info/boat/" 
TARGET_DATE = "2026-11-18"  # 欲監控的日期

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
LINE_NOTIFY_TOKEN = os.environ.get("LINE_NOTIFY_TOKEN", "")

def send_telegram_msg(message):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram 發送失敗: {e}")

def send_line_notify(message):
    if not LINE_NOTIFY_TOKEN:
        return
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"}
    payload = {"message": message}
    try:
        requests.post(url, headers=headers, data=payload, timeout=10)
    except Exception as e:
        print(f"LINE 發送失敗: {e}")

def main():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now_str}] 開始檢查高千穗船票狀況 ({TARGET_DATE})...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"[警告] 請求失敗，HTTP 狀態碼: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找日期並判斷是否有空位
        date_element = soup.find(text=lambda t: t and TARGET_DATE in t)
        
        is_available = False
        if date_element:
            parent_row = date_element.find_parent(["tr", "div", "li"])
            if parent_row:
                row_text = parent_row.get_text()
                if any(status in row_text for status in ["○", "△", "預約", "有空位"]):
                    is_available = True

        if is_available:
            msg = (
                f"🎉 【高千穗船票釋出通知】\n"
                f"日期：{TARGET_DATE}\n"
                f"偵測到有剩餘名額，請儘速搶購！\n"
                f"搶票網址：{TARGET_URL}"
            )
            print("成功發現空位！已發送通知。")
            send_telegram_msg(msg)
            send_line_notify(msg)
        else:
            print("尚未發現空位。")

    except Exception as e:
        print(f"[錯誤] 執行監控時發生異常: {e}")

if __name__ == "__main__":
    main()
