# Scan Generic Annotation Table — Dynamo Python (Revit)

> ⚠️ **Mỗi khi cập nhật file này, phải dán lại TOÀN BỘ nội dung mới nhất
> của `ScanGenericAnnotationTable.py` vào node Python Script trong
> Dynamo** (chọn hết Ctrl+A trong node rồi paste đè). Dán thiếu / dán bản
> cũ là nguyên nhân phổ biến nhất gây ra lỗi trông như "code hỏng" —
> trong khi bản mới nhất trong repo đã không còn lỗi đó. Nếu gặp lỗi,
> luôn xác nhận trước: nội dung trong node đang có đúng bằng file mới
> nhất ở đây không.

Công cụ Dynamo (Python Script node) giúp:

1. **Quét chọn** các Family Instance (Generic Annotation) tạo thành bảng
   "kiểu Excel" bạn đã dựng trên view Revit (giống bảng `俩@_STR Framing` /
   `GROSS BUILDING` trong ảnh minh hoạ) — script tự dò hình học để dựng lại
   đúng cấu trúc hàng/cột của bảng, không cần khai báo thủ công.
2. Đọc dữ liệu chữ đã điền sẵn trên từng ô (đã điền từ Schedule/Text) và
   (tuỳ chọn) đối chiếu thêm với một `ViewSchedule` để tự điền các ô còn
   trống.
3. Mở **GUI dạng bảng tính** (WinForms, theme tối, viền vàng đồng — "sang
   trọng hiện đại"): xem/sửa từng ô, bôi chọn 1 vùng rồi bấm **"Σ Xem
   nhanh"** để xem ngay SUM / AVERAGE / MIN / MAX / PRODUCT của vùng đó,
   chọn hàm trong ô "Hàm" rồi bấm **"➕ Chèn công thức"** để chèn
   `=SUM(...)`, `=PRODUCT(...)`, `=AVERAGE(...)` hoặc `=A/B` vào ô đích,
   bấm **"⟲ Tính lại"** để tính lại toàn bộ công thức trong bảng.
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
4. Nối input — **chỉ cần `IN[0]` (và `IN[1]` nếu muốn có công tắc bảo
   vệ) là chạy được ngay**, mọi input khác để trống đều có giá trị mặc
   định an toàn:

   | IN | Nội dung | Bắt buộc |
   |----|----------|----------|
   | `IN[0]` | List các Generic Annotation đã quét chọn (nối từ node **Select Model Elements**, chế độ chọn nhiều) | Có |
   | `IN[1]` | Node **Boolean** True/False — công tắc bảo vệ. `False` = không làm gì cả (an toàn); `True`/không nối = chạy đầy đủ | Khuyên dùng |
   | `IN[2]` | 1 `ViewSchedule` để đối chiếu số liệu gốc (có thể để `null`) | Không |
   | `IN[3]` | Tên Parameter chứa chữ hiển thị trên annotation, vd `"Text"`, `"文字"`... Để `""` hoặc `null` để script tự dò | Không |
   | `IN[4]` | Dung sai gom **hàng** (feet nội bộ Revit), để `null` để tự tính | Không |
   | `IN[5]` | Dung sai gom **cột** (feet nội bộ Revit), để `null` để tự tính | Không |
   | `IN[6]` | (Nâng cao) `True` = bỏ qua GUI, tự ghi thẳng vào Revit không cho xem trước. Mặc định `False` (luôn mở GUI) | Không |

   > ⚠️ Lưu ý thứ tự IN đã đổi so với bản trước: `IN[1]` giờ là công tắc
   > **Boolean bảo vệ**, không phải Schedule — đúng với cách bạn đã quen
   > nối 1 node Boolean vào `IN[1]`. Schedule (nếu dùng) chuyển sang `IN[2]`.

5. Chạy node → cửa sổ GUI hiện ra.

### Sơ đồ graph gợi ý (tối giản — chỉ 2 input)

```
Select Model Elements  ──────────────► IN[0]   ┌────────────────────────┐
(chọn các Generic Annotation)                  │  Python Script node    │──► Watch (OUT)
                                                │  ScanGenericAnnotation-│
Boolean toggle (True) ───────────────► IN[1]   │  Table.py              │
                                                │  (engine = CPython3)   │
                                                └────────────────────────┘
```

Muốn dùng thêm Schedule/tên parameter tuỳ biến thì nối thêm vào `IN[2]`,
`IN[3]`... theo bảng ở trên. Có thể ghép trực tiếp phía sau graph "MASTER
DUPLICATE" hiện có của bạn: dùng chính output các phần tử vừa nhân
bản/duplicate làm `IN[0]`.

---

## 2. Cách dùng GUI

Cửa sổ là 1 "wizard" — mỗi lần bạn bấm 1 nút, cửa sổ đóng lại và **tự mở
lại ngay lập tức** với dữ liệu mới nhất (đây là chủ đích thiết kế, xem lý
do kỹ thuật ở mục 6). Vì vậy công thức KHÔNG tự tính lại tức thời từng
phím gõ như Excel thật, mà tính lại mỗi khi bạn bấm 1 nút bất kỳ — vẫn
rất nhanh vì bảng chỉ có vài chục/vài trăm ô.

1. **Sửa trực tiếp trên lưới**: gõ đè giá trị vào bất kỳ ô nào (số, chữ,
   hoặc công thức bắt đầu bằng `=`, ví dụ `=B2+B3`, `=SUM(B2:B10)/2`).
   Giá trị được ghi nhận ngay khi bạn bấm bất kỳ nút nào bên dưới.
2. **"Σ Xem nhanh vùng chọn"**: bôi chọn 1 vùng ô (kéo chuột hoặc
   Ctrl-click), bấm nút này để xem ngay SUM / AVERAGE / MIN / MAX /
   PRODUCT của vùng đó ở dòng chữ vàng bên dưới bảng — giống thanh trạng
   thái Excel, không thay đổi gì trong bảng.
3. **"➕ Chèn công thức"**: gõ **ô đích** (vd `C5`) vào ô "Ô đích:", chọn
   hàm trong ô "Hàm" (SUM / PRODUCT / AVERAGE / DIVIDE A÷B), bôi chọn 1
   vùng dữ liệu trong bảng, rồi bấm nút này — script tự chèn công thức
   (vd `=SUM(B2:B10)`) vào đúng ô đích. Với DIVIDE cần bôi chọn **đúng 2
   ô** (ô có hàng/cột nhỏ hơn được coi là A, ô kia là B).
4. **"⟲ Tính lại"**: tính lại toàn bộ công thức trong bảng (hữu ích sau
   khi sửa nhiều ô liền — dù thật ra công thức đã tự tính lại sau mỗi lần
   bấm nút rồi).
5. **"✔ Cập nhật vào Revit"**: hỏi xác nhận, rồi ghi toàn bộ ô đã đổi khác
   giá trị gốc trở lại đúng Generic Annotation tương ứng trên view.
6. **"✖ Hủy"**: đóng cửa sổ, không ghi gì vào Revit.

### Hàm công thức hỗ trợ

`SUM`, `AVERAGE` (hoặc `AVG`), `PRODUCT`, `MIN`, `MAX`, `COUNT`, `ROUND(x,n)`,
`ABS(x)`, cùng các phép toán `+ - * / ^` và ngoặc đơn — đủ dùng cho hầu hết
nhu cầu tính tổng/nhân/chia số liệu kỹ thuật (khối lượng, số lượng, đơn giá...).

Mã lỗi hiển thị giống Excel: `#DIV/0!`, `#REF!`, `#VALUE!`, `#NAME?`,
`#CYCLE!` (công thức tham chiếu vòng), `#ERR!` (cú pháp sai).

---

## 3. Cách hoạt động (tóm tắt kỹ thuật)

- **Hỗ trợ cả TextNote lẫn Generic Annotation FamilyInstance**, tự nhận
  diện từng phần tử (`is_text_note`), có thể trộn lẫn trong cùng 1 lần
  quét:
  - **TextNote**: định vị bằng `elem.Coord` (điểm neo đặt chữ lúc tạo) —
    KHÔNG dùng `Location.Point` hay tâm BoundingBox, vì cả 2 đều XÊ DỊCH
    theo độ dài nội dung/canh lề (vd `"19.87"` hẹp hơn `"8,338.82"`), gây
    ghép sai hàng/cột. Đọc/ghi trực tiếp qua `elem.Text` — không cần dò
    Parameter nào cả.
  - **Generic Annotation FamilyInstance**: định vị bằng `Location.Point`
    (rồi lùi về tâm BoundingBox), đọc/ghi qua Parameter hoặc Tên Type
    (xem `detect_best_param_name` bên dưới).
- **Dò lưới bảng**: chiếu toạ độ từng phần tử vào hệ trục 2D của view
  (`RightDirection` / `UpDirection`), rồi gom cụm 1 chiều theo thuật toán
  "natural breaks" (tìm bước nhảy khoảng-cách rõ rệt nhất) để tách hàng và
  cột — không cần bạn khai báo số hàng/cột, cũng không bị lệch khi view bị
  xoay.
- **Tự dò nguồn dữ liệu chữ** (`detect_best_param_name`, chỉ áp dụng cho
  phần tử KHÔNG PHẢI TextNote): KHÔNG đoán mù —
  khảo sát thực tế trên chính các phần tử đã chọn để tìm nguồn chứa chữ
  "ăn khớp" nhiều nhất:
  1. Thử lần lượt `CANDIDATE_PARAM_NAMES` (ở đầu file), trên cả Instance
     Parameter lẫn Type Parameter (Label trong family có thể bind vào 1
     trong 2 loại).
  2. Nếu không parameter nào có nội dung, tự chuyển sang dùng **TÊN
     TYPE** (Family Type Name) — kỹ thuật phổ biến khi mỗi ô trong bảng
     là 1 Family Type riêng, chữ "nằm" ngay ở tên Type chứ không phải 1
     parameter.
  3. Nếu vẫn không thấy gì, quét TOÀN BỘ parameter kiểu chữ đang có trên
     các phần tử, chọn tên xuất hiện (có nội dung) nhiều nhất.
  Luôn có thể ép dùng đúng 1 tên cụ thể qua `IN[3]`. Toàn bộ quá trình dò
  được ghi vào `Warnings` (khớp bao nhiêu / bao nhiêu phần tử khảo sát),
  và nếu không tìm thấy gì cả, GUI hiện hộp thoại cảnh báo trước khi mở
  bảng thay vì âm thầm mở 1 bảng toàn ô trống.
- **Đối chiếu Schedule**: dùng `ViewSchedule.GetTableData()` +
  `GetCellText(SectionType.Body, row, col)` — đúng API chuẩn của Revit.
- **Formula Engine**: bộ phân tích công thức tự viết (tokenizer +
  recursive-descent parser), KHÔNG dùng `eval()` — an toàn, không thể chạy
  mã tuỳ ý từ ô dữ liệu.
- **Ghi ngược vào Revit**: gom toàn bộ thay đổi rồi ghi trong **đúng 1
  `Transaction`** (mỗi ô nằm trong 1 `SubTransaction` riêng để 1 ô lỗi
  không huỷ các ô khác) — đây là yếu tố quan trọng nhất giúp tốc độ cập
  nhật nhanh, vì Revit không phải mở/đóng transaction hàng trăm lần.
- **GUI**: WinForms "eventless" — xem lý do và cách hoạt động ở mục 6.

## 4. OUT (kết quả trả về Dynamo)

```jsonc
{
  "Status": "Updated" | "Cancelled" | "NoSelection" | "Idle" | "Error",
  "UpdatedCount": 42,      // số ô đã ghi vào Revit
  "TotalCells": 48,        // tổng số ô trong lưới nhận diện được
  "Rows": 8, "Cols": 6,
  "Grid": [["...","..."], ...],  // lưới giá trị cuối cùng
  "Warnings": ["..."],     // cảnh báo/lỗi trong quá trình chạy
  "ElapsedMs": 187,        // tổng thời gian (kể cả lúc bạn thao tác trên GUI)
  "WriteMs": 9,            // thời gian THỰC ghi vào Revit — chỉ phần Transaction
  "CellsPerSecond": 4666.7 // tốc độ ghi thực đo được = UpdatedCount / (WriteMs/1000)
}
```

`WriteMs`/`CellsPerSecond` là số đo THẬT của riêng bước ghi (không tính thời
gian bạn ngồi sửa dữ liệu trên GUI) — cũng hiển thị ngay trong hộp thoại
"Hoàn tất" sau khi bấm "✔ Cập nhật vào Revit", để bạn tự kiểm chứng tốc độ
thay vì chỉ nghe tuyên bố suông.

---

## 5. Kiểm thử

Phần logic thuần Python (dò lưới hàng/cột, bộ tính công thức) có bộ test
độc lập, chạy được **ngoài Revit** (giả lập tối thiểu các module .NET để
import file script):

```bash
python3 RevitDynamoTable/tests/test_core_logic.py
```

38/38 test hiện đang PASS, bao gồm: SUM/AVERAGE/PRODUCT/MIN/MAX/COUNT,
công thức lồng nhau, tham chiếu vòng (`#CYCLE!`), chia cho 0 (`#DIV/0!`),
độ ưu tiên phép toán, các trường hợp biên của thuật toán dò lưới (lưới
sạch không nhiễu / chỉ 1 hàng có nhiễu số học nhỏ), toàn bộ logic tự dò
nguồn dữ liệu chữ (`detect_best_param_name`/`find_text_source`: ưu tiên
Instance rồi Type Parameter, lùi về Type Name, rồi quét toàn bộ khi cần),
và xử lý TextNote (`.Coord` luôn được ưu tiên tuyệt đối, đọc/ghi qua
`.Text`, bỏ qua mọi tên parameter được truyền vào) bằng các phần tử giả
lập.

> **Lưu ý quan trọng**: phần tương tác trực tiếp với Revit API/WinForms
> (đọc parameter thật, mở cửa sổ GUI, ghi Transaction thật) **chưa được
> chạy thử trên Revit/Dynamo thật** vì môi trường tạo mã này không có
> Revit/Dynamo cài sẵn. Hãy thử trước với **một bảng nhỏ**, kiểm tra kỹ
> mục `Warnings` trong OUT, trước khi áp dụng cho bảng lớn/nhiều sheet.
> Nếu gặp lỗi cụ thể trên máy bạn (tên parameter khác, dung sai gom lưới
> sai do family đặc thù...), gửi lại thông báo lỗi/ảnh chụp để điều chỉnh
> `CANDIDATE_PARAM_NAMES` hoặc `row_tol`/`col_tol` cho đúng gia đình family
> của bạn.

## 6. Lỗi đã gặp & đã fix

**Lỗi `TypeError: unsupported operand type(s) for -` (GUI không hiện ra,
OUT trả về `Rows/Cols = 0`, `Grid` rỗng):** nguyên nhân là dòng tính toạ
độ dùng toán tử Python `pt - origin` để trừ 2 điểm `XYZ` của RevitAPI.
Engine **CPython3** của Dynamo (chạy qua pythonnet) không phải lúc nào
cũng ánh xạ được toán tử nạp chồng (`operator overload`) của kiểu `XYZ`
sang toán tử Python `-`, nên phép trừ bị lỗi ngay khi vừa chạy, trước cả
khi kịp mở GUI. **Đã fix**: đổi sang gọi thẳng phương thức
`pt.Subtract(origin)` của RevitAPI (luôn hoạt động, bất kể engine) thay
vì dùng toán tử `-`. Đồng thời đã bọc thêm try/except quanh việc tính
toạ độ của TỪNG phần tử, để nếu 1 phần tử nào đó vẫn lỗi (vd gia đình
family đặc biệt) thì chỉ bị bỏ qua kèm cảnh báo, không làm sập toàn bộ
lần chạy.

Nếu sau này gặp lại lỗi `TypeError: unsupported operand type(s)` ở chỗ
khác, khả năng cao cũng do cùng nguyên nhân (toán tử `+ - * /` áp dụng
trực tiếp lên 1 kiểu dữ liệu RevitAPI/.NET) — cách sửa luôn là đổi sang
gọi phương thức `.NET` tương ứng (`Add`, `Subtract`, `Multiply`,
`DotProduct`, `Negate`...) thay vì dùng toán tử Python.

**Lỗi `System.Xaml.XamlParseException: Unexpected token 'Open' in rule:
'Mark...'` (không hiện GUI, dù đã dò được lưới bảng):** bản đầu tiên của
GUI dùng WPF + chuỗi XAML. Chuỗi XAML đó vô tình chứa dấu ngoặc nhọn kép
`{{StaticResource ...}}`/`{{TemplateBinding ...}}` (nhầm với cú pháp
escape của Python `.format()`), trong khi cú pháp Markup Extension đúng
của WPF chỉ dùng 1 cặp ngoặc `{...}` — khiến trình phân tích XAML báo lỗi
ngay khi vừa mở cửa sổ.

**Đã đổi hẳn kiến trúc GUI từ WPF sang WinForms "eventless"** — không chỉ
sửa lỗi ngoặc kép, mà loại bỏ triệt để rủi ro thuộc lớp này: trên
**Dynamo 2.19 / Revit 2024 với engine CPython3 (PythonNet 2.5.x)**, việc
Python đăng ký sự kiện .NET (`control.add_Click(handler)`) hoặc kế thừa 1
control .NET (`class MyForm(Form)`) có thể ném lỗi
`"Constructor on type 'System.Reflection.Emit.TypeBuilder' not found"`
vì PythonNet cần phát assembly động (TypeBuilder) để nối callback Python
vào delegate .NET, và việc này bị chặn trong tiến trình Revit/Dynamo.
Bản GUI hiện tại (từ `ScanGenericAnnotationTable.py` v3 trở đi):
- Dùng **WinForms** (`System.Windows.Forms`/`System.Drawing`) — dựng
  control hoàn toàn bằng code Python, không có bước "parse chuỗi XAML"
  nào cả nên không còn lớp lỗi cú pháp XAML.
- **Không** subclass bất kỳ kiểu .NET nào, **không** đăng ký sự kiện .NET
  nào (`add_Click`, `add_CellEditEnding`,...). Tương tác hoàn toàn qua
  `Button.DialogResult` + `Form.ShowDialog()` (xử lý 100% trong .NET,
  không cần callback Python), với 1 vòng lặp Python (`while True`) bên
  ngoài đọc lại toàn bộ dữ liệu trên lưới sau mỗi `ShowDialog()` rồi dựng
  lại 1 cửa sổ mới với dữ liệu đã cập nhật — xem hàm `run_gui_wizard()`.
- Vì vậy các thao tác trước đây là "tức thời" (gõ 1 ô, công thức tự tính
  lại ngay) nay cần bấm 1 nút bất kỳ để "chốt" thay đổi và tính lại — đây
  là đánh đổi bắt buộc để tương thích 100% với môi trường CPython3/
  PythonNet 2.5.x của Dynamo, không phải thiếu sót.

Cách tiếp cận này được rút ra trực tiếp từ 1 tool Dynamo khác của bạn
(`DYNAMO STRUCTURAL FAMILY DUPLICATOR`) — tool đó đã tự phát hiện và ghi
chú rõ đúng giới hạn này trong comment code, và đã dùng chính kỹ thuật
"WinForms eventless" để vượt qua. Nếu môi trường Dynamo/Revit của bạn
nâng cấp lên PythonNet mới hơn (không còn giới hạn TypeBuilder này nữa),
có thể cân nhắc quay lại WPF với event binding thật để có trải nghiệm
tức thời hơn — nhưng bản hiện tại ưu tiên **chắc chắn chạy được** trên
đúng môi trường bạn đang dùng.

**Bảng mở được (không còn crash) nhưng dò ra quá nhiều hàng/cột và toàn
bộ ô đều TRỐNG:** đây không phải lỗi, mà là dấu hiệu family đang dùng
đang lưu chữ theo cách script chưa đoán trúng tên parameter — bản cũ chỉ
thử 1 danh sách tên cố định (`CANDIDATE_PARAM_NAMES`), nếu family của bạn
dùng tên khác thì mọi ô đều đọc ra rỗng. **Đã fix bằng
`detect_best_param_name`** (mục 3): script giờ tự khảo sát THỰC TẾ trên
chính các phần tử đã chọn — thử cả Instance lẫn Type Parameter, rồi lùi
về TÊN TYPE (Family Type Name, rất phổ biến khi mỗi ô = 1 Type riêng),
rồi cuối cùng quét toàn bộ parameter chữ đang có nếu vẫn chưa thấy gì.
Nếu chạy lại vẫn còn ô trống, xem mục `Warnings` trong `OUT` — dòng đầu
tiên cho biết chính xác đã dò ra tên gì và khớp bao nhiêu phần tử; nếu
báo "KHÔNG tìm thấy" thì gửi lại đúng tên Parameter thật trên family của
bạn (xem trong Revit: chọn 1 annotation → Properties) để truyền vào
`IN[3]`. Số hàng/cột dò được cũng được ghi kèm dung sai đã dùng trong
`Warnings`, kèm cảnh báo nếu tỉ lệ lấp đầy quá thấp (< 50%) — dấu hiệu
dung sai gom cụm đang sai, có thể chỉnh qua `IN[4]`/`IN[5]`.

**Bảng vẫn còn hầu hết ô trống dù đã fix ở trên — phần tử thật ra là
TextNote, không phải Generic Annotation:** đối chiếu với 1 graph Dynamo
khác của bạn (`AUTO CHỌN VÙNG TEXT TÍNH TỔNG SCHEDULE&TEXT.dyn`) xác nhận
rõ: nhiều bảng của bạn dựng từ **`TextNote`** (chữ đặt tự do), không phải
Family Instance. `TextNote` không có `Parameter` chứa nội dung — chữ nằm
thẳng ở thuộc tính `.Text` — nên toàn bộ cơ chế dò Parameter/Type Name ở
trên không áp dụng được và luôn ra rỗng cho loại phần tử này. Graph đó
cũng chỉ ra 1 bug tinh vi khác: dùng tâm BoundingBox (hoặc Location.Point)
để định vị TextNote bị XÊ DỊCH theo độ dài nội dung (`"19.87"` hẹp hơn
`"8,338.82"`), khiến việc ghép hàng/cột bị sai ngay từ bước dò lưới.
**Đã fix**: `is_text_note()` nhận diện TextNote và xử lý RIÊNG, ưu tiên
tuyệt đối trên mọi phần tử khác — định vị bằng `elem.Coord` (điểm neo cố
định lúc tạo chữ, không đổi theo nội dung), đọc/ghi thẳng qua `elem.Text`,
bỏ qua hoàn toàn bước dò Parameter/Type Name (không cần thiết và không
đúng cho TextNote). Cả 2 kiểu phần tử giờ dùng chung được 1 lần quét.

## 7. Tuỳ chỉnh nhanh

Mở đầu file `ScanGenericAnnotationTable.py`, phần **`0. CẤU HÌNH`**:

- `CANDIDATE_PARAM_NAMES`: thêm tên parameter riêng của family bạn dùng.
- `ROUND_DECIMALS`: số chữ số thập phân khi hiển thị/ghi kết quả.
- `THEME`: đổi màu sắc GUI (mặc định vàng đồng trên nền đen).
- `AUTO_TOL_JUMP_RATIO`, `AUTO_TOL_NOISE_FLOOR_FT`: chỉnh độ nhạy khi tự
  dò hàng/cột (nếu family có khoảng cách đặc biệt nhỏ/lớn).
