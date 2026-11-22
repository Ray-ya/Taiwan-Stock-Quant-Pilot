# -*- coding: utf-8 -*-
"""
Taiwan Stock Quant Scheduler & Boot Compensator
----------------------------------------------
每日 08:00 執行分析與推播。
若 08:00 未開機，開機自動偵測今日是否已發送，若未發送則立即補發。
"""

import os
import sys
import datetime
import subprocess

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(WORKSPACE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def has_sent_today():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    record_file = os.path.join(LOG_DIR, "sent_dates.txt")
    if not os.path.exists(record_file):
        return False
    with open(record_file, "r", encoding="utf-8") as f:
        sent_dates = [line.strip() for line in f if line.strip()]
    return today_str in sent_dates

def mark_sent_today():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    record_file = os.path.join(LOG_DIR, "sent_dates.txt")
    with open(record_file, "a", encoding="utf-8") as f:
        f.write(today_str + "\n")

def run_job(reason="SCHEDULED_0800"):
    now = datetime.datetime.now()
    log_file = os.path.join(LOG_DIR, f"run_{now.strftime('%Y%m%d_%H%M%S')}.log")
    
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 啟動台股量化晨報任務 (原因: {reason})...")
    
    if has_sent_today():
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 今日晨報已發送過，略過不重複推播。")
        return
    
    reporter_script = os.path.join(WORKSPACE_DIR, "reporter", "morning_reporter.py")
    cmd = [sys.executable, reporter_script]
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"Reason: {reason}\nTimestamp: {now.isoformat()}\n")
        f.write("=== STDOUT ===\n" + result.stdout + "\n")
        f.write("=== STDERR ===\n" + result.stderr + "\n")
        
    if result.returncode == 0:
        mark_sent_today()
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 晨報產出成功並標記完成！")
    else:
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 晨報執行失敗，回傳碼: {result.returncode}")

if __name__ == "__main__":
    reason_arg = sys.argv[1] if len(sys.argv) > 1 else "MANUAL"
    run_job(reason=reason_arg)
