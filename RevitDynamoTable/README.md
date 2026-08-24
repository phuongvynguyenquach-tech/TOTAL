# Scan Generic Annotation Table — Dynamo Python (Revit)

Công cụ Dynamo (Python Script node) giúp:

1. **Quét chọn** các Family Instance (Generic Annotation) tạo thành bảng
   "kiểu Excel" bạn đã dựng trên view Revit (giống bảng `俩@_STR Framing` /
   `GROSS BUILDING` trong ảnh minh hoạ) — script tự dò hình học để dựng lại
   đúng cấu trúc hàng/cột của bảng, không cần khai báo thủ công.
2. Đọc dữ liệu chữ đã điền sẵn trên từng ô (đã điền từ Schedule/Text) và
   (tuỳ chọn) đối chiếu thêm với một `ViewSchedule` để tự điền các ô còn
   trống.
3. Mở **GUI dạng bảng tính** (theme tối, viền vàng đồng — "sang trọng hiện
   đại"): xem/sửa từng ô, bôi chọn 1 vùng để xem ngay SUM / AVERAGE / MIN /
   MAX / PRODUCT (thanh trạng thái kiểu Excel), chèn công thức
   `=SUM(...)`, `=PRODUCT(...)`, `=AVERAGE(...)`, `=A/B` vào bất kỳ ô nào;
   công thức tự tính lại mỗi khi ô nguồn thay đổi.
4. Khi bấm **"✔ Cập nhật vào Revit"**: ghi toàn bộ ô đã thay đổi trở lại
   đúng Generic Annotation tương ứng, **trong đúng 1 Transaction** (không
   mở/đóng transaction theo từng ô) để cập nhật cực nhanh trên view.

File chính: [`ScanGenericAnnotationTable.py`](ScanGenericAnnotationTable.py)

---

## 1. Cài đặt trong Dynamo

1. Thả 1 node **Python Script** vào canvas Dynamo.
2. Click phải vào node → **Change Engine → CPython3** (script được viết
   cho engine CPython3, có hỗ trợ `clr` để gọi thẳng RevitAPI + WPF).
3. Dán toàn bộ nội dung `ScanGenericAnnotationTable.py` vào node.
4. Nối input:

   | IN | Nội dung | Bắt buộc |
   |----|----------|----------|
   | `IN[0]` | List các Generic Annotation đã quét chọn (nối từ node **Select Model Elements**, chế độ chọn nhiều) | Có |
   | `IN[1]` | 1 `ViewSchedule` để đối chiếu số liệu gốc (có thể để `null`) | Không |
   | `IN[2]` | Tên Parameter chứa chữ hiển thị trên annotation, vd `"Text"`, `"文字"`... Để `""` hoặc `null` để script tự dò | Không |
   | `IN[3]` | `True/False` — mở GUI hay chạy ngầm không GUI (mặc định `True`) | Không |
   | `IN[4]` | Dung sai gom **hàng** (feet nội bộ Revit), để `null` để tự tính | Không |
   | `IN[5]` | Dung sai gom **cột** (feet nội bộ Revit), để `null` để tự tính | Không |

5. Chạy node → cửa sổ GUI hiện ra.

### Sơ đồ graph gợi ý

```
Select Model Elements  ──────────────► IN[0]
(chọn các Generic Annotation)
                                       ┌────────────────────────┐
Views.GetSchedule (tuỳ chọn) ────────► IN[1]  │ Python Script node   │──► Watch (OUT)
                                       │ ScanGenericAnnotation-│
"Text" (Code Block, tuỳ chọn) ───────► IN[2]  │ Table.py               │
                                       │ (engine = CPython3)    │
Boolean toggle (True) ───────────────► IN[3]  └────────────────────────┘
```

Có thể ghép trực tiếp phía sau graph "MASTER DUPLICATE" hiện có của bạn:
dùng chính output các phần tử vừa nhân bản/duplicate làm `IN[0]`.

---

## 2. Cách dùng GUI

1. **Thanh công cụ trên cùng**: hiển thị số hàng × cột đã dò được; nút
   **"⟲ Tính lại"** (ép tính lại toàn bộ công thức), **"✔ Cập nhật vào
   Revit"** (ghi kết quả), **"✖ Hủy"** (đóng, không ghi gì).
2. **Thanh công thức**: gõ **ô đích** (vd `C5`) vào ô "Ô đích:", bôi chọn
   1 vùng dữ liệu trong bảng (kéo chuột hoặc Ctrl-click nhiều ô), rồi bấm:
   - **Σ SUM** — chèn `=SUM(vùng đã chọn)` vào ô đích.
   - **× PRODUCT** — chèn `=PRODUCT(vùng đã chọn)`.
   - **⌀ AVERAGE** — chèn `=AVERAGE(vùng đã chọn)`.
   - **÷ A / B** — cần bôi chọn **đúng 2 ô**, chèn `=A/B` (ô có hàng/cột
     nhỏ hơn được coi là A).
3. **Thanh trạng thái bên phải thanh công thức**: giống thanh trạng thái
   Excel — bôi chọn vùng bất kỳ để xem ngay SUM / AVERAGE / MIN / MAX /
   PRODUCT của vùng đó, không cần chèn công thức.
4. Có thể gõ công thức trực tiếp vào bất kỳ ô nào, bắt đầu bằng `=`, ví dụ
   `=B2+B3`, `=SUM(B2:B10)/2`, `=ROUND(C4*1.15,2)`. Công thức tự tính lại
   ngay khi bạn rời khỏi ô vừa sửa, và tự lan truyền qua các ô phụ thuộc.
5. Bấm **"✔ Cập nhật vào Revit"** để ghi toàn bộ ô đã đổi khác giá trị gốc
   trở lại đúng Generic Annotation tương ứng trên view.

### Hàm công thức hỗ trợ

`SUM`, `AVERAGE` (hoặc `AVG`), `PRODUCT`, `MIN`, `MAX`, `COUNT`, `ROUND(x,n)`,
`ABS(x)`, cùng các phép toán `+ - * / ^` và ngoặc đơn — đủ dùng cho hầu hết
nhu cầu tính tổng/nhân/chia số liệu kỹ thuật (khối lượng, số lượng, đơn giá...).

Mã lỗi hiển thị giống Excel: `#DIV/0!`, `#REF!`, `#VALUE!`, `#NAME?`,
`#CYCLE!` (công thức tham chiếu vòng), `#ERR!` (cú pháp sai).

---

## 3. Cách hoạt động (tóm tắt kỹ thuật)

- **Dò lưới bảng**: chiếu toạ độ từng annotation vào hệ trục 2D của view
  (`RightDirection` / `UpDirection`), rồi gom cụm 1 chiều theo thuật toán
  "natural breaks" (tìm bước nhảy khoảng-cách rõ rệt nhất) để tách hàng và
  cột — không cần bạn khai báo số hàng/cột, cũng không bị lệch khi view bị
  xoay.
- **Đọc/ghi chữ trên annotation**: thử lần lượt danh sách tên parameter
  thường gặp (`CANDIDATE_PARAM_NAMES` ở đầu file) hoặc dùng đúng tên bạn
  truyền vào `IN[2]`.
- **Đối chiếu Schedule**: dùng `ViewSchedule.GetTableData()` +
  `GetCellText(SectionType.Body, row, col)` — đúng API chuẩn của Revit.
- **Formula Engine**: bộ phân tích công thức tự viết (tokenizer +
  recursive-descent parser), KHÔNG dùng `eval()` — an toàn, không thể chạy
  mã tuỳ ý từ ô dữ liệu.
- **Ghi ngược vào Revit**: gom toàn bộ thay đổi rồi ghi trong **đúng 1
  Transaction** (`TransactionManager.Instance` khi chạy trong Dynamo, hoặc
  `Transaction` thường khi chạy ngoài Dynamo) — đây là yếu tố quan trọng
  nhất giúp tốc độ cập nhật nhanh, vì Revit không phải mở/đóng transaction
  hàng trăm lần.

## 4. OUT (kết quả trả về Dynamo)

```jsonc
{
  "Status": "Updated" | "Cancelled" | "NoSelection" | "Error",
  "UpdatedCount": 42,      // số ô đã ghi vào Revit
  "TotalCells": 48,        // tổng số ô trong lưới nhận diện được
  "Rows": 8, "Cols": 6,
  "Grid": [["...","..."], ...],  // lưới giá trị cuối cùng
  "Warnings": ["..."],     // cảnh báo/lỗi trong quá trình chạy
  "ElapsedMs": 187
}
```

---

## 5. Kiểm thử

Phần logic thuần Python (dò lưới hàng/cột, bộ tính công thức) có bộ test
độc lập, chạy được **ngoài Revit** (giả lập tối thiểu các module .NET để
import file script):

```bash
python3 RevitDynamoTable/tests/test_core_logic.py
```

25/25 test hiện đang PASS, bao gồm: SUM/AVERAGE/PRODUCT/MIN/MAX/COUNT,
công thức lồng nhau, tham chiếu vòng (`#CYCLE!`), chia cho 0 (`#DIV/0!`),
độ ưu tiên phép toán, và các trường hợp biên của thuật toán dò lưới
(lưới sạch không nhiễu / chỉ 1 hàng có nhiễu số học nhỏ).

> **Lưu ý quan trọng**: phần tương tác trực tiếp với Revit API/WPF (đọc
> parameter thật, mở cửa sổ GUI, ghi Transaction thật) **chưa được chạy
> thử trên Revit/Dynamo thật** vì môi trường tạo mã này không có
> Revit/Dynamo cài sẵn. Hãy thử trước với **một bảng nhỏ**, kiểm tra kỹ
> mục `Warnings` trong OUT, trước khi áp dụng cho bảng lớn/nhiều sheet.
> Nếu gặp lỗi cụ thể trên máy bạn (tên parameter khác, dung sai gom lưới
> sai do family đặc thù...), gửi lại thông báo lỗi/ảnh chụp để điều chỉnh
> `CANDIDATE_PARAM_NAMES` hoặc `row_tol`/`col_tol` cho đúng gia đình family
> của bạn.

## 6. Tuỳ chỉnh nhanh

Mở đầu file `ScanGenericAnnotationTable.py`, phần **`0. CẤU HÌNH`**:

- `CANDIDATE_PARAM_NAMES`: thêm tên parameter riêng của family bạn dùng.
- `ROUND_DECIMALS`: số chữ số thập phân khi hiển thị/ghi kết quả.
- `THEME`: đổi màu sắc GUI (mặc định vàng đồng trên nền đen).
- `AUTO_TOL_JUMP_RATIO`, `AUTO_TOL_NOISE_FLOOR_FT`: chỉnh độ nhạy khi tự
  dò hàng/cột (nếu family có khoảng cách đặc biệt nhỏ/lớn).
