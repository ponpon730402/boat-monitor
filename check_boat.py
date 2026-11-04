import os
import datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from bs4 import BeautifulSoup

TARGET_URL = "https://takachiho-kanko.info/boat/" 
TARGET_DATE = "2026-11-18"  # 欲監控的日期

# 從 GitHub Secrets 讀取 Email 設定
MAIL_SENDER = os.environ.get("MAIL_SENDER", "")       # 您的 Gmail 帳號
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")   # 您的 Gmail 應用程式密碼
MAIL_RECEIVER = os.environ.get("MAIL_RECEIVER", "")   # 收件人信箱（通常跟寄件人一樣）

def send_email_notification(message_body):
    if not MAIL_SENDER or not MAIL_PASSWORD or not MAIL_RECEIVER:
        print("未完整設定 Email 密鑰，略過寄信通知。")
        return
    
    try:
        message = MIMEText(message_body, 'plain', 'utf-8')
        message['From'] = Header(MAIL_SENDER, 'utf-8')
        message['To'] = Header(MAIL_RECEIVER, 'utf-8')
        message['Subject'] = Header(f"【高千穗船票通知】{TARGET_DATE} 有空位了！", 'utf-8')

        # 使用 Gmail SMTP 伺服器發信
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(MAIL_SENDER, MAIL_PASSWORD)
        server.sendmail(MAIL_SENDER, [MAIL_RECEIVER], message.as_string())
        server.quit()
        print("成功發送 Email 通知！")
    except Exception as e:
        print(f"Email 發送失敗: {e}")

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
            print("成功發現空位！已發送 Email 通知。")
            send_email_notification(msg)
        else:
            print("尚未發現空位。")

    except Exception as e:
        print(f"[錯誤] 執行監控時發生異常: {e}")

if __name__ == "__main__":
    main()
