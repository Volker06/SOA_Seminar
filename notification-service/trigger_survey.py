import argparse
import logging
import time

from notifier import TelegramError, TelegramNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    ap = argparse.ArgumentParser(description="Gửi phiếu khảo sát sau bán qua Telegram")
    ap.add_argument("--order", default=f"ORD-{int(time.time()) % 100000}", help="Mã đơn hàng")
    ap.add_argument("--service", default="Dịch vụ demo", help="Tên dịch vụ khách vừa dùng")
    ap.add_argument("--delay", type=int, default=0, help="Số giây chờ trước khi gửi")
    args = ap.parse_args()

    notifier = TelegramNotifier()
    if args.delay:
        print(f"Dịch vụ đang thực hiện... gửi khảo sát sau {args.delay}s")
        time.sleep(args.delay)
    try:
        notifier.send_survey(args.order, args.service)
    except (TelegramError, ValueError) as e:
        raise SystemExit(f"Gửi khảo sát thất bại: {e}")
    print(f"Đã gửi phiếu khảo sát cho đơn {args.order}. Mở Telegram để xem.")


if __name__ == "__main__":
    main()
