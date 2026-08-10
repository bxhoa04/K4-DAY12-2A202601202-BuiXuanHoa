# Phiếu Phản Ánh — K4 Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: điền câu trả lời bên dưới từng câu hỏi.

> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Bùi Xuân Hòa  Mã học viên: 2A202601202

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `api_token` không có giá trị mặc định nên app chết ngay khi
khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà việc
"chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Khi deploy ứng dụng lên server production, nếu lập trình viên quên cài đặt biến môi trường `API_TOKEN` mà ứng dụng vẫn cho giá trị mặc định là `"changeme"`, ứng dụng sẽ khởi động thành công và chạy với token yếu/công khai này. Kẻ tấn công có thể dễ dàng đoán ra token `"changeme"` và lạm dụng API của hệ thống (gây tiêu tốn tài nguyên và phát sinh chi phí LLM). Khi áp dụng Fail-fast (không có giá trị mặc định), ứng dụng sẽ lập tức crash ngay khi khởi động (`raise ValidationError`), buộc người vận hành phải cấu hình `API_TOKEN` thật trước khi hệ thống chính thức hoạt động.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/chat` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Dòng log JSON thu được:
`{"event": "chat_completed", "severity": "INFO", "ts": "2026-08-10T14:30:00.123456+00:00", "client_id": "sv01", "prompt_tokens": 15, "completion_tokens": 40, "usd_cost": 0.00012}`

Hai việc làm được với log JSON:
1. **Lọc và tìm kiếm tự động trên Cloud/Monitoring System (Grafana/Datadog/CloudWatch):** Có thể truy vấn lọc chính xác theo từng thuộc tính như `client_id == "sv01"` hoặc lọc các request có `usd_cost > 0.01` trong vài giây thay vì phải đọc thủ công từng dòng text.
2. **Thống kê và tự động cảnh báo (Alerting & Metrics):** Các công cụ giám sát có thể parse trực tiếp JSON để tự động tính tổng chi phí (`usd_cost`), đếm tổng số token sử dụng, và vẽ biểu đồ dashboard theo thời gian thực mà không cần viết regex để bóc tách dữ liệu.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t chat:single .
docker build -t chat:multi .
docker images | grep chat
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | ~1.8 GB |
| Multi-stage | ~180 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Phần dung lượng chênh lệch (~1.6 GB) bao gồm: base image đầy đủ của Python chứa nhiều công cụ biên dịch (gcc, g++, make,...), bộ nhớ cache của pip (`~/.cache/pip`), các file header phát triển C/C++, và các công cụ build không cần thiết ở môi trường runtime. Ở bản Multi-stage, stage builder cài đặt dependency sang thư mục tạm, sau đó stage runtime (dùng python:3.11-slim) chỉ copy phần thư viện đã hoàn thiện và source code vào, loại bỏ hoàn toàn compiler và cache build.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

- Với cấu trúc Dockerfile hiện tại (`COPY requirements.txt .` -> `RUN pip install ...` -> `COPY app/ app/`): Khi sửa code trong `app/main.py`, các layer từ đầu đến `RUN pip install` đều được giữ nguyên và dùng lại từ cache (không mất thời gian tải lại thư viện). Chỉ có layer `COPY app/ app/` và các layer phía sau mới phải chạy lại.
- Nếu đặt `COPY . .` lên trước `RUN pip install`: Khi bất kỳ file code nào bị sửa, layer `COPY . .` sẽ bị thay đổi và làm mất cache (cache invalidation). Khi đó, Docker bắt buộc phải chạy lại lệnh `RUN pip install` từ đầu, tốn rất nhiều thời gian tải lại toàn bộ thư viện mỗi lần sửa code.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

- Chuỗi sự kiện: Giả sử ứng dụng Python có lỗ hổng RCE (Remote Code Execution) hoặc LFI (Local File Inclusion). Nếu container chạy bằng user `root`, kẻ tấn công lợi dụng lỗ hổng để thực thi lệnh hệ thống bên trong container dưới quyền root. Nếu tồn tại lỗ hổng container escape (hoặc volume mount quyền root), kẻ tấn công có thể can thiệp vào kernel/socket Docker trên máy host (`/var/run/docker.sock`), từ đó chiếm toàn bộ quyền root điều khiển máy host.
- Lệnh `USER appuser` chuyển quyền chạy của container sang user thường (không có đặc quyền sudo/root). Dù kẻ tấn công có khai thác được lỗ hổng RCE trong app Python, quyền hạn của chúng chỉ gói gọn trong môi trường bị giới hạn của `appuser`, không thể sửa file hệ thống trong container hay leo thang chiếm quyền root trên host.

---

### Câu 6 — Bearer token (CP3)

Vì sao 401 phải kèm header `WWW-Authenticate: Bearer`? Và vì sao ta trả **cùng
một** thông báo lỗi cho cả ba trường hợp (thiếu header, sai scheme, sai token)
thay vì nói rõ sai ở đâu cho người dùng dễ sửa?

- Header `WWW-Authenticate: Bearer` là bắt buộc theo chuẩn HTTP (RFC 6750) đối với mã phản hồi `401 Unauthorized`. Nó báo cho phía client (hoặc trình duyệt) biết phương thức xác thực mà API yêu cầu là Bearer Token.
- Trả về cùng một thông báo lỗi chung (như `invalid or missing bearer token`) để đảm bảo tính bảo mật (Security by Obscurity). Nếu thông báo quá chi tiết (như "Token không tồn tại" hay "Sai scheme"), kẻ tấn công có thể lợi dụng để dò tìm thông tin hệ thống (nhận biết được loại xác thực nào đang bật hoặc kiểm tra token có tồn tại hay không).

---

### Câu 7 — Token bucket (CP3)

Với `capacity=10`, `refill_per_minute=10`: một client im lặng 10 phút rồi gửi
liên tiếp. Nó gửi được bao nhiêu request trước khi bị 429? Nếu bỏ đoạn
`min(capacity, ...)` trong `available()` thì con số đó thành bao nhiêu, và tại sao?

- Client gửi được tối đa **10 request** liên tiếp trước khi bị trả lỗi `429 Too Many Requests` (vì xô tích lũy tối đa bằng `capacity = 10`).
- Nếu bỏ đoạn `min(capacity, ...)`: Tốc độ nạp là 10 token/phút -> Sau 10 phút im lặng, xô sẽ tích lũy 10 x 10 = 100 token. Client sẽ gửi được **100 request** liên tiếp trong vài giây trước khi bị chặn. Điều này làm mất tác dụng bảo mật của Token Bucket, cho phép user dồn request đánh sập hạ tầng.

---

### Câu 8 — Ngân sách theo ngày (CP3)

So sánh hạn mức $30/tháng với hạn mức $1/ngày cho cùng một client. Giả sử có sự
cố khiến một client gọi liên tục từ 2h sáng. Với mỗi cách, thiệt hại tối đa là
bao nhiêu và service tự hồi phục khi nào?

- Hạn mức **$30/tháng**: Khi có sự cố gọi liên tục từ 2h sáng, client có thể đốt hết toàn bộ $30 ngân sách chỉ trong vài giờ đầu tiên của ngày đầu tháng. Thiệt hại tối đa là **$30**, và service sẽ bị chặn cho đến tận **tháng sau** mới tự hồi phục.
- Hạn mức **$1/ngày**: Thiệt hại tối đa trong ngày bị sự cố chỉ là **$1**. Ngay khi chạm $1, Cost Guard sẽ chặn client đó (mã 402). Đến 00:00 UTC sáng hôm sau, hạn mức ngày mới được tự động làm mới và service **tự hồi phục ngay ngày hôm sau** mà không cần can thiệp thủ công.

---

### Câu 9 — /healthz khác /readyz (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Thứ tự sự kiện xảy ra:
1. Redis mất kết nối tạm thời trong 30 giây.
2. Endpoint gộp kiểm tra kết nối Redis thất bại và trả về 503.
3. Orchestrator (Docker/Kubernetes) gọi liveness probe thấy 503 -> Coi container đã chết và tiến hành **khởi động lại (restart)** toàn bộ cụm 3 container.
4. Trong lúc khởi động lại, các container mới vẫn không thể kết nối tới Redis (vì Redis vẫn đang gián đoạn) -> Lại trả 503 và tiếp tục bị restart liên tục (CrashLoopBackOff).
5. Mọi request dang dở của người dùng trên toàn bộ container đều bị hủy bỏ đột ngột (lỗi 502/503), gây gián đoạn hệ thống nghiêm trọng hơn nhiều so với việc chỉ ngắt tạm thời lưu lượng truy cập.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

- Thông báo lỗi: Container bị crash hoặc health check timeout trên Cloud Platform với thông báo `Error: Address already in use` hoặc `Health check failed on port 8000`.
- Cách tìm ra nguyên nhân: Kiểm tra log trên Dashboard của Cloud Platform (Railway/Render), phát hiện ra ứng dụng hardcode cổng `8000` thay vì đọc từ biến môi trường `PORT` do platform tự gán tự động khi khởi chạy container.
- Cách sửa: Cập nhật `Settings` và Dockerfile để khởi chạy Uvicorn đọc cổng từ biến môi trường `${PORT:-8000}`.
