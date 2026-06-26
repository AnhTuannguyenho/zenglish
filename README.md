# Auto Shutdown khi mất Internet

Ứng dụng tự động **tắt máy tính sau 2 phút** (có thể tùy chỉnh) nếu phát hiện
**mất kết nối internet** liên tục. Nếu mạng phục hồi trước khi hết thời gian,
quá trình đếm ngược sẽ bị hủy.

- Đa nền tảng: **Windows, Linux, macOS**
- Chỉ dùng **thư viện chuẩn của Python** (không cần cài thêm gì)
- Có chế độ **dry-run** để thử an toàn (không thực sự tắt máy)

## Yêu cầu

- Python 3.6 trở lên

## Cách chạy

```bash
# Chạy với cấu hình mặc định: tắt máy sau 120 giây mất mạng, kiểm tra mỗi 10 giây
python auto_shutdown.py

# THỬ AN TOÀN trước (không tắt máy thật, chỉ in ra)
python auto_shutdown.py --dry-run

# Tùy chỉnh thời gian chờ trước khi tắt (giây)
python auto_shutdown.py --grace 120

# Tùy chỉnh khoảng kiểm tra (giây)
python auto_shutdown.py --interval 5
```

> **Lưu ý:** Trên **Linux/macOS**, lệnh tắt máy thường cần quyền quản trị.
> Hãy chạy bằng `sudo python auto_shutdown.py`. Trên **Windows** nên mở
> Command Prompt / PowerShell với quyền Administrator.

## Cách hoạt động

1. Cứ mỗi `--interval` giây, ứng dụng thử mở kết nối TCP tới các máy chủ DNS
   công cộng (Google `8.8.8.8`, Cloudflare `1.1.1.1`, OpenDNS). Chỉ cần một
   máy chủ phản hồi là coi như **còn mạng**.
2. Khi phát hiện **mất mạng**, ứng dụng bắt đầu đếm ngược `--grace` giây.
3. Nếu mạng **phục hồi** trong lúc đếm ngược → **hủy** và tiếp tục giám sát.
4. Nếu mất mạng **liên tục** đủ `--grace` giây → **tắt máy**.

## Các tham số

| Tham số      | Mặc định | Ý nghĩa                                              |
|--------------|----------|-----------------------------------------------------|
| `--grace`    | `120`    | Số giây mất mạng liên tục trước khi tắt máy          |
| `--interval` | `10`     | Khoảng thời gian giữa các lần kiểm tra (giây)        |
| `--timeout`  | `3.0`    | Thời gian chờ tối đa cho mỗi lần thử kết nối (giây)  |
| `--dry-run`  | tắt      | Chỉ mô phỏng, KHÔNG thực sự tắt máy                  |

## Chạy nền tự động (tùy chọn)

### Windows (Task Scheduler)
Tạo một Task chạy `pythonw auto_shutdown.py` khi đăng nhập, với quyền cao nhất
(Run with highest privileges).

### Linux (systemd)
Tạo file `/etc/systemd/system/auto-shutdown.service`:

```ini
[Unit]
Description=Auto shutdown khi mat internet
After=network.target

[Service]
ExecStart=/usr/bin/python3 /duong/dan/auto_shutdown.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Sau đó:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now auto-shutdown.service
```
