#!/usr/bin/env python3
"""Tự động tắt máy tính khi mất kết nối internet.

Ứng dụng kiểm tra kết nối internet định kỳ. Nếu phát hiện mất kết nối
liên tục đủ thời gian quy định (mặc định 2 phút / 120 giây), máy tính sẽ
được tắt. Nếu kết nối được phục hồi trước khi hết thời gian, quá trình
đếm ngược sẽ bị hủy.

Hỗ trợ Windows, Linux và macOS. Chỉ dùng thư viện chuẩn của Python.

Ví dụ sử dụng:
    python auto_shutdown.py                  # chạy với cấu hình mặc định
    python auto_shutdown.py --grace 120      # tắt sau 120 giây mất mạng
    python auto_shutdown.py --interval 5     # kiểm tra mỗi 5 giây
    python auto_shutdown.py --dry-run        # chỉ in ra, KHÔNG tắt máy (an toàn để thử)
"""

import argparse
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime


# Các máy chủ DNS công cộng đáng tin cậy dùng để kiểm tra kết nối.
# Kiểm tra ở tầng TCP nên không phụ thuộc vào trình duyệt hay DNS cục bộ.
DEFAULT_HOSTS = [
    ("8.8.8.8", 53),       # Google DNS
    ("1.1.1.1", 53),       # Cloudflare DNS
    ("208.67.222.222", 53),  # OpenDNS
]


def log(message: str) -> None:
    """In thông báo kèm thời gian."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def is_online(hosts=DEFAULT_HOSTS, timeout: float = 3.0) -> bool:
    """Trả về True nếu kết nối được tới BẤT KỲ máy chủ nào trong danh sách.

    Chỉ cần một máy chủ phản hồi là coi như còn mạng, tránh báo nhầm
    "mất mạng" khi một dịch vụ cụ thể bị lỗi.
    """
    for host, port in hosts:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def shutdown_command():
    """Trả về lệnh tắt máy phù hợp với hệ điều hành hiện tại."""
    system = platform.system()
    if system == "Windows":
        # /s = shutdown, /t 0 = tắt ngay, /f = đóng các ứng dụng đang chạy
        return ["shutdown", "/s", "/t", "0", "/f"]
    elif system == "Darwin":  # macOS
        return ["shutdown", "-h", "now"]
    else:  # Linux và các hệ Unix khác
        return ["shutdown", "-h", "now"]


def shutdown(dry_run: bool = False) -> None:
    """Thực hiện tắt máy. Nếu dry_run=True chỉ in lệnh ra mà không chạy."""
    cmd = shutdown_command()
    if dry_run:
        log(f"[DRY-RUN] Sẽ tắt máy bằng lệnh: {' '.join(cmd)}")
        return
    log(f"Đang tắt máy: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        log(f"LỖI: Không tắt được máy: {exc}")
        log("Gợi ý: trên Linux/macOS có thể cần quyền sudo/root để tắt máy.")
        sys.exit(1)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Tự động tắt máy tính sau một khoảng thời gian nếu mất kết nối internet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--grace", type=int, default=120,
        help="Số giây mất mạng liên tục trước khi tắt máy.",
    )
    parser.add_argument(
        "--interval", type=int, default=10,
        help="Khoảng thời gian (giây) giữa các lần kiểm tra kết nối.",
    )
    parser.add_argument(
        "--timeout", type=float, default=3.0,
        help="Thời gian chờ tối đa (giây) cho mỗi lần thử kết nối tới máy chủ.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Chỉ mô phỏng: in ra khi đáng lẽ tắt máy nhưng KHÔNG thực sự tắt.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    if args.interval <= 0 or args.grace <= 0:
        log("LỖI: --grace và --interval phải lớn hơn 0.")
        return 2

    log(
        f"Bắt đầu giám sát internet "
        f"(tắt máy sau {args.grace}s mất mạng, kiểm tra mỗi {args.interval}s"
        f"{', chế độ DRY-RUN' if args.dry_run else ''})."
    )
    log("Nhấn Ctrl+C để dừng.")

    offline_since = None  # mốc thời gian bắt đầu mất mạng, None nếu đang online

    try:
        while True:
            online = is_online(timeout=args.timeout)
            now = time.monotonic()

            if online:
                if offline_since is not None:
                    log("Kết nối đã phục hồi. Hủy đếm ngược tắt máy.")
                    offline_since = None
            else:
                if offline_since is None:
                    offline_since = now
                    log(
                        f"Mất kết nối internet! Bắt đầu đếm ngược "
                        f"{args.grace}s trước khi tắt máy."
                    )
                else:
                    elapsed = now - offline_since
                    remaining = args.grace - elapsed
                    if remaining <= 0:
                        log("Đã mất mạng quá thời gian cho phép. Tiến hành tắt máy.")
                        shutdown(dry_run=args.dry_run)
                        if args.dry_run:
                            # Ở chế độ thử, reset để tiếp tục giám sát.
                            offline_since = None
                        else:
                            return 0
                    else:
                        log(f"Vẫn mất mạng... còn {int(remaining)}s trước khi tắt máy.")

            time.sleep(args.interval)
    except KeyboardInterrupt:
        log("Đã dừng giám sát theo yêu cầu người dùng.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
