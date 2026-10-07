"""
monitor.py - Giám sát tài nguyên máy chủ và gửi cảnh báo qua Telegram.

Cơ chế chống spam:
  - Chỉ báo khi vượt ngưỡng lần đầu, hoặc sau thời gian COOLDOWN nếu vẫn còn vượt.
  - Khi giá trị trở lại bình thường -> gửi thông báo "RECOVERED".

Demo nhanh: đặt ngưỡng thấp để dễ kích hoạt
  Linux/Mac : CPU_THRESHOLD=1 python monitor.py
  Windows   : set CPU_THRESHOLD=1 && python monitor.py
"""
import logging
import os
import time
from datetime import datetime, timedelta

import psutil

from notifier import TelegramNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("monitor")

THRESHOLDS = {
    "CPU": float(os.getenv("CPU_THRESHOLD", 85)),
    "RAM": float(os.getenv("RAM_THRESHOLD", 85)),
    "DISK": float(os.getenv("DISK_THRESHOLD", 90)),
}
CRITICAL_LEVEL = 95.0                                  # >= mức này -> CRITICAL
INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))        # giây giữa các lần kiểm tra
COOLDOWN = timedelta(seconds=int(os.getenv("ALERT_COOLDOWN", 600)))


def collect():
    return {
        "CPU": psutil.cpu_percent(interval=1),
        "RAM": psutil.virtual_memory().percent,
        "DISK": psutil.disk_usage(os.path.abspath(os.sep)).percent,
    }


def main():
    notifier = TelegramNotifier()
    active = {}  # metric -> thời điểm gửi cảnh báo gần nhất (đang trong trạng thái báo động)

    notifier.notify(
        "INFO", "Monitor đã khởi động",
        f"Ngưỡng: CPU {THRESHOLDS['CPU']}% | RAM {THRESHOLDS['RAM']}% | DISK {THRESHOLDS['DISK']}%\n"
        f"Chu kỳ kiểm tra: {INTERVAL}s",
        service="system-monitor",
    )
    log.info("Monitor đang chạy. Nhấn Ctrl+C để dừng.")

    try:
        while True:
            metrics = collect()
            log.info("CPU=%.1f%% RAM=%.1f%% DISK=%.1f%%", *metrics.values())
            now = datetime.now()

            for name, value in metrics.items():
                limit = THRESHOLDS[name]

                if value >= limit:
                    last = active.get(name)
                    if last is None or now - last >= COOLDOWN:
                        level = "CRITICAL" if value >= CRITICAL_LEVEL else "WARNING"
                        notifier.notify(
                            level, f"{name} vượt ngưỡng",
                            f"{name} hiện tại: {value:.1f}% (ngưỡng {limit}%)",
                            service="system-monitor",
                        )
                        active[name] = now
                elif name in active:
                    notifier.notify(
                        "SUCCESS", f"{name} đã trở lại bình thường",
                        f"{name} hiện tại: {value:.1f}% (ngưỡng {limit}%)",
                        service="system-monitor",
                    )
                    del active[name]

            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        notifier.notify("WARNING", "Monitor đã dừng", "Tiến trình giám sát bị tắt thủ công.",
                        service="system-monitor")
        log.info("Đã dừng.")


if __name__ == "__main__":
    main()
