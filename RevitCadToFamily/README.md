# CAD → Revit Family Batch — Dynamo Python (Revit)

> ⚠️ **Mỗi khi cập nhật file này, phải dán lại TOÀN BỘ nội dung mới nhất
> của `CadToFamilyBatch.py` vào node Python Script trong Dynamo**
> (Ctrl+A trong node rồi paste đè). Dán thiếu / dán bản cũ là nguyên nhân
> phổ biến nhất gây ra lỗi trông như "code hỏng" trong khi bản mới nhất
> trong repo đã sửa rồi.

Công cụ **tự tạo hàng loạt Family Revit (`.rfa`) từ file CAD (DWG/DXF)**:
bạn dán đường dẫn 1 file hoặc cả 1 thư mục CAD, script tự đọc bản vẽ, tự
nhận ra đâu là **mặt bằng**, đâu là **mặt đứng chính / mặt sau / mặt bên
trái / phải**, tự suy ra **Dài × Rộng × Cao**, tự đoán **danh mục Revit**,
rồi dựng ra family có **khối 3D + nét vẽ lại đúng theo CAD trên từng hình
chiếu + tham số kéo giãn + tham số công thức**.

Bốn việc "khó" mà công cụ này làm được:

| | |
|---|---|
| **1 file → nhiều family** | File CAD vẽ cả dãy 8 cái tủ, 5 bộ bếp, hay cả trang ký hiệu đồ đạc → script tách ra **đúng số lượng sản phẩm**, mỗi cái 1 family riêng đúng kích thước của nó |
| **Thiếu hình chiếu thì tự suy ra** | Chỉ có mặt đứng → tự dựng mặt bằng (kèm ký hiệu cánh mở) và mặt bên. Chỉ có mặt bằng → tự dựng 2 mặt đứng. Theo đúng phép chiếu vuông góc |
| **Family con lồng vào family mẹ** | Tủ 4 cánh → 4 khoang thành family con, lồng vào family mẹ, **ràng buộc tham số**: kéo `Dài` của mẹ là cả dãy khoang giãn đều theo |
| **Đặt đúng vị trí CAD** | Tuỳ chọn đặt luôn family vào project **đúng toạ độ nó nằm trên bản CAD** |

File chính: [`CadToFamilyBatch.py`](CadToFamilyBatch.py)

---

## 1. Cài đặt trong Dynamo

1. Thả 1 node **Python Script** vào canvas Dynamo.
2. Click phải vào node → **Change Engine → CPython3**.
3. Dán toàn bộ nội dung `CadToFamilyBatch.py` vào node.
4. Nối input — **chỉ cần `IN[1] = Boolean True` là chạy được ngay**, mọi
   input khác để trống đều có mặc định an toàn:

   | IN | Nội dung | Bắt buộc |
   |----|----------|----------|
   | `IN[0]` | List **CAD Link / CAD Import** đã chọn sẵn trong Revit (node *Select Model Elements*). Để trống nếu bạn nhập đường dẫn file/thư mục trên GUI | Không |
   | `IN[1]` | Node **Boolean** True/False — công tắc bảo vệ. `False` = không làm gì cả; `True`/không nối = chạy | Khuyên dùng |
   | `IN[2]` | **String** — đường dẫn 1 file CAD hoặc 1 thư mục chứa CAD (điền sẵn vào ô đường dẫn của GUI) | Không |
   | `IN[3]` | **String** — thư mục xuất `.rfa`. Để trống = tạo `REVIT_FAMILY_OUT` cạnh thư mục CAD | Không |
   | `IN[4]` | **String** — thư mục chứa Family Template `.rft`. Để trống = tự dò `C:\ProgramData\Autodesk\RVT xxxx\Family Templates` | Không |
   | `IN[5]` | **Boolean** — `True` = nạp luôn family vừa tạo vào project đang mở. Mặc định `False` | Không |
   | `IN[6]` | (Nâng cao) **Boolean** — `True` = chạy thẳng, KHÔNG mở GUI. Mặc định `False` | Không |
   | `IN[7]` | **Boolean** — `True` = nạp family vào project **và đặt đúng toạ độ trên bản CAD**. Mặc định `False` | Không |

5. Chạy node → cửa sổ GUI hiện ra.

### Sơ đồ graph tối giản

```
Boolean (True) ─────────────► IN[1] ┐
String "D:\OUT\REVIT\FAMILY" ► IN[2] ├─► Python Script (CPython3) ─► Watch
                                     ┘
```

Muốn tạo family từ CAD Link đang có sẵn trong project thì thêm:

```
Select Model Elements ──► IN[0]
```

---

## 2. Quy trình dùng (đúng thứ tự trên GUI)

1. **Dán đường dẫn** vào ô *"Đường dẫn CAD"* — có thể là:
   - 1 file: `D:\CAD\LAVABO BỘ 3.dwg`
   - 1 thư mục: `D:\CAD\THU VIEN` (tick *"Thư mục con"* để quét cả cây thư mục)
   - nhiều đường dẫn cách nhau bằng `;`
   - hoặc bấm **📂 Thư mục…** / **📄 File CAD…** để chọn bằng hộp thoại.
2. Bấm **🔍 QUÉT** → mỗi file CAD thành 1 dòng trong bảng, kèm tên family,
   danh mục, Dài/Rộng/Cao, các hình chiếu nhận ra được và lý do nhận ra.
3. **Sửa trực tiếp trên lưới** những gì bạn muốn: tên family, danh mục,
   chế độ dựng khối, Dài/Rộng/Cao. Bỏ tick cột **✔** để không tạo dòng đó.
   Cột **HÌNH CHIẾU** có dấu `*` nghĩa là hình chiếu đó do script *tự suy
   ra*; cột **KHOANG** cho biết sản phẩm sẽ được chia thành mấy family con.
   Muốn sửa nhiều dòng cùng lúc: bôi chọn các dòng → chọn Danh mục / Chế độ
   / Cao ở thanh dưới → bấm **⚙ Áp dụng cho dòng đang chọn**.
4. Chọn **📁 thư mục xuất `.rfa`**.
5. Bấm **▶ TẠO FAMILY HÀNG LOẠT** → xác nhận → xong, hộp thoại báo số
   family đã tạo, số family con đã lồng, số lỗi và **tốc độ thật đo được
   (family/giây)**.

### Các tuỳ chọn trên GUI

| Tuỳ chọn | Mặc định | Ý nghĩa |
|----------|----------|---------|
| Thư mục con | tắt | Quét cả cây thư mục |
| Gộp file cùng tên | bật | `TỦ_MB.dwg` + `TỦ_MĐ.dwg` → 1 family |
| TURBO | tắt | Giản lược nét, chạy nhanh hơn |
| Tham số Instance | bật | `Dài/Rộng/Cao` là tham số Instance (tắt = Type) |
| Vẽ mặt sau/phải | bật | Vẽ thêm nét mặt sau & mặt phải bằng Model Line |
| Nạp vào project | tắt | Nạp `.rfa` vào project đang mở |
| **Tách nhiều sản phẩm / 1 file** | **bật** | 1 file CAD nhiều sản phẩm → nhiều family |
| **Tự suy hình chiếu thiếu** | **bật** | Dựng nốt mặt bằng / mặt đứng / mặt bên còn thiếu |
| **Family con lồng nhau** | **bật** | Mỗi khoang thành 1 family con lồng vào family mẹ |
| **Đặt đúng vị trí CAD** | tắt | Đặt family vào project đúng toạ độ trên bản CAD |

---

## 3. Script "đọc hiểu" bản vẽ CAD như thế nào

Đây là phần cốt lõi, và toàn bộ đã được **kiểm thử tự động** (mục 7).

| Bước | Cách làm |
|------|----------|
| **Bóc nét** | `.dxf`: đọc thẳng bằng Python (LINE, LWPOLYLINE có bulge, POLYLINE/VERTEX, ARC, CIRCLE, ELLIPSE, SPLINE, SOLID, TEXT/MTEXT, **INSERT — bung cả block lồng block và mảng hàng/cột**). `.dwg`: nhờ chính Revit Import rồi bóc `GeometryObject` (kể cả CAD 3D thì lấy cạnh khối) |
| **Đơn vị** | Ưu tiên `$INSUNITS` của file; không có thì suy từ độ lớn khung bao (m / cm / mm). Sau khi Revit import còn 1 chốt chặn nữa: kích thước ra ngoài khoảng 3 cm … 500 m thì tự sửa hệ số 1000 và báo lại |
| **Gom cụm** | Rải nét lên lưới ô vuông rồi loang vùng 8 hướng (flood fill) → các hình chiếu vẽ cạnh nhau tách thành từng cụm. Nhanh cả với bản vẽ vài chục nghìn nét (không so từng cặp đối tượng) |
| **Gán ghi chú** | Chữ "MẶT BẰNG", "MĐ CHÍNH"… thường nằm tách rời bên dưới hình → được gán về cụm hình gần nhất (ưu tiên cụm nằm ngay trên chữ) |
| **Nhận diện hình chiếu** | ① chữ ghi chú → ② tên layer → ③ tên file → ④ suy luận hình học: cụm nhiều biên dạng kín nhất = **mặt bằng**; cụm có **bề ngang ≈ Dài mặt bằng** = mặt đứng chính/sau; **bề ngang ≈ Rộng mặt bằng** = mặt bên trái/phải; còn dư thì gán theo thứ tự trái→phải |
| **Kích thước** | Dài × Rộng lấy từ khung bao mặt bằng, Cao lấy từ khung bao mặt đứng. Thiếu dữ liệu thì lấy mặc định theo danh mục (`DEFAULT_DIMS`) |
| **Danh mục** | Từ khoá tiếng Việt (có dấu / không dấu) + tiếng Anh trong tên file, tên layer và chữ trong bản vẽ: `LAVABO/CHẬU RỬA/WC` → Plumbing Fixtures, `CỬA ĐI` → Doors, `CỬA SỔ` → Windows, `TỦ/KỆ/BÀN ĐÁ` → Casework, `BÀN/GHẾ/GIƯỜNG` → Furniture, `ĐÈN` → Lighting Fixtures… |
| **Bỏ nét rác** | Layer kích thước / ghi chú / khung tên / trục / hatch bị loại khỏi phần vẽ lại (nhưng CHỮ vẫn được đọc để nhận diện hình chiếu) |

### Tách nhiều sản phẩm trong cùng 1 file CAD

Bản vẽ thư viện thường xếp cả loạt sản phẩm cạnh nhau. Script gom hình
chiếu về đúng sản phẩm của nó bằng **2 luật loại trừ nhau**:

**Luật 1 — xếp chồng dọc** (bố cục "dãy tủ áo"): mặt bằng nằm ngay dưới mặt
đứng của chính nó. Điều kiện: 2 cụm chồng nhau theo phương ngang ≥ 60%,
**một bên phải giống mặt bằng và bên kia giống mặt đứng**, cụm mặt bằng
thấp hơn, khe hở dọc đủ nhỏ. Mỗi cụm chỉ ghép 1 lần.

```
   ┌────────┐  ┌──────────┐  ┌────┐        mỗi cột = 1 sản phẩm
   │ MĐ tủ1 │  │  MĐ tủ2  │  │MĐ3 │        (mặt đứng + mặt bằng của nó)
   └────────┘  └──────────┘  └────┘
   ┌────────┐  ┌──────────┐  ┌────┐
   │ MB tủ1 │  │  MB tủ2  │  │MB3 │  ← có cung quét cánh → nhận ra là mặt bằng
   └────────┘  └──────────┘  └────┘
```

**Luật 2 — cùng hàng ngang** (bố cục "bản vẽ bếp", không có mặt bằng):
trong 1 dải ngang, cụm **rộng nhất** là mặt đứng chính; cụm **cùng chiều
cao, hẹp hơn hẳn, đứng sát bên cạnh** là mặt bên của nó.

```
   ┌──┐  ┌──────────────────┐  ┌──┐     3 cụm này = 1 sản phẩm
   │MB│  │   MẶT ĐỨNG CHÍNH │  │MP│     (mặt bên trái + chính + phải)
   └──┘  └──────────────────┘  └──┘
```

Luật 2 **không áp dụng** cho cụm đã có mặt bằng riêng ở luật 1 — nếu không,
cả dãy 8 cái tủ sẽ bị gộp nhầm thành 1 sản phẩm. Và **không gộp 2 cụm cùng
là mặt bằng** — nên cả trang ký hiệu đồ đạc thì mỗi ký hiệu là 1 sản phẩm.

Nhận biết mặt bằng hay mặt đứng bằng **điểm `plan_likeness`**:

| Dấu hiệu | Điểm |
|----------|------|
| Cung quét cánh cửa (cung ~90°) | **+2** mỗi cái (tối đa 4) |
| Biên dạng kín nhỏ (chậu, thiết bị, lỗ khoét) | **+0.8** mỗi cái (tối đa 6) |
| Hình thấp hơn hẳn các hình cùng bản vẽ | **+0.6** |
| Đường chéo dài ký hiệu cánh mở | **−2** mỗi cái (tối đa 4) |
| Chữ ghi chú "MẶT BẰNG" / "MẶT ĐỨNG" | **±10** (quyết định luôn) |

> **Đo đúng kích thước tủ, không đo cả cung quét cánh.** Mặt bằng tủ luôn có
> cung quét cánh vẽ thòi ra ngoài. Script đo theo **biên dạng kín lớn nhất**
> (đường bao vật thể) chứ không theo khung bao toàn cụm — nếu không, tủ sâu
> 600 sẽ bị đo thành 1200.

### Tự suy ra hình chiếu còn thiếu

Chỉ có mặt đứng mà thiếu mặt bằng (hoặc ngược lại) thì script dựng nốt hình
còn thiếu theo đúng **hình học hoạ hình**: 3 hình chiếu dùng chung từng cặp
trục toạ độ, nên đường chia của hình này chiếu thẳng sang hình kia.

```
   MẶT BẰNG cho (x, y)      MẶT ĐỨNG cho (x, z)      MẶT BÊN cho (y, z)

   vách đứng trên MẶT ĐỨNG  (toạ độ x) ──────► vách đứng trên MẶT BẰNG
   mặt kệ  trên MẶT ĐỨNG    (toạ độ z) ──────► đường ngang trên MẶT BÊN
   vách sâu trên MẶT BẰNG   (toạ độ y) ──────► vách đứng trên MẶT BÊN
```

Mặt bằng tự suy còn được vẽ thêm **ký hiệu cánh mở** (nét cánh ở vị trí mở +
cung quét 90°, khoang rộng thì tách 2 cánh mở 2 phía) đúng như cách vẽ trên
bản CAD. Hình chiếu tự suy được đánh dấu `*` trên GUI và **không bao giờ
được dùng để đo kích thước** — kích thước chỉ lấy từ nét CAD thật.

### Family con lồng vào family mẹ

Sản phẩm chia được thành nhiều **khoang** (đọc từ các vách đứng chạy suốt
chiều cao trên mặt đứng) thì mỗi khoang thành 1 **family con**:

- Family con là **hộp tham số hoàn toàn**: `Dài`/`Rộng`/`Cao` là tham số
  **Instance**, các mặt khoá vào Reference Plane → co giãn 100%. Kèm nét CAD
  của đúng khoang đó vẽ trên mặt đứng.
- **Khoang trùng kích thước dùng chung 1 family con** — tủ 4 cánh bằng nhau
  chỉ tốn 1 family con thay vì 4.
- Lồng vào family mẹ **có ràng buộc đầy đủ**:

  | Ràng buộc | Cách làm |
  |-----------|----------|
  | Chiều cao | `Cao` của con ← liên kết thẳng vào `Cao` của mẹ |
  | Chiều sâu | `Rộng` của con ← liên kết thẳng vào `Rộng` của mẹ |
  | Bề rộng khoang | khoang đều nhau → `Dài` của con ← tham số `Rộng khoang` = công thức `Dài / n` |
  | Vị trí khoang | mỗi khoang 1 Reference Plane, gắn nhãn tham số `Vị trí khoang i` = công thức `Dài × k`, rồi **Align + Lock** mặt phẳng tâm của instance vào plane đó |

  Kết quả: **kéo `Dài` của family mẹ là cả dãy khoang tự giãn đều theo**.

- Đã lồng family con thì family mẹ **không dựng thêm khối bao** nữa (tránh 2
  lớp khối chồng nhau). Muốn giữ thì đặt `parent_solid_with_nesting = True`.
- Family con được lưu trong thư mục con **`_FAMILY_CON`** cạnh thư mục xuất.

### Đặt vào project đúng vị trí trên CAD

Tick **"Đặt đúng vị trí CAD"** (hoặc `IN[7] = True`): sau khi tạo xong,
family được nạp vào project đang mở và đặt **đúng toạ độ nó nằm trên bản vẽ
CAD**. Quét 1 file mặt bằng đầy ký hiệu đồ đạc là ra ngay cả một mặt bằng
Revit đúng chỗ.

> Toạ độ lấy theo **hệ toạ độ gốc của file CAD**. Muốn khớp tuyệt đối, hãy
> link CAD vào Revit theo kiểu *Origin to Origin* (hoặc kiểm tra lại 1 cái
> rồi move cả nhóm).

### Gộp nhiều file thành 1 family

Nếu bạn tách mỗi hình chiếu 1 file, đặt tên có hậu tố, script tự gộp lại:

```
LAVABO BỘ 3_MB.dwg        ┐
LAVABO BỘ 3_MD.dwg        ├──►  1 family "LAVABO BỘ 3" đủ mặt bằng + 3 mặt đứng
LAVABO BỘ 3_MD TRAI.dwg   ┘
```

Hậu tố hiểu được: `MB / MẶT BẰNG / PLAN`, `MD / MẶT ĐỨNG / FRONT`,
`MS / MẶT SAU / BACK`, `MT / MẶT TRÁI / LEFT`, `MP / MẶT PHẢI / RIGHT`,
`MC / MẶT CẮT / SECTION`.
Chỉ gộp khi **cùng tên gốc và hậu tố khác nhau** — 2 sản phẩm khác nhau
(`CỬA ĐI P1` và `CỬA ĐI P2`) không bao giờ bị gộp nhầm. Bỏ tick *"Gộp file
cùng tên"* nếu muốn mỗi file 1 family.

---

## 4. Family tạo ra có gì

- **Khối 3D (Extrusion)** dựng từ biên dạng kín của mặt bằng, các vòng
  bên trong thành **lỗ rỗng** (ví dụ 3 lỗ chậu trên mặt bàn lavabo), cao
  đúng theo mặt đứng.
- **Nét vẽ lại đúng theo CAD trên từng hình chiếu** (Symbolic Line /
  Model Line), nằm trong các **Subcategory** riêng (`CAD - Mặt bằng`,
  `CAD - Mặt đứng`, `CAD - Mặt bên`, `CAD - Mặt sau & phải`) để bạn bật/tắt
  trong 1 nốt nhạc.
- **Tham số kéo giãn**: `Dài`, `Rộng`, `Cao` — gắn nhãn vào Dimension giữa
  các Reference Plane, và các mặt khối được **Align + Lock** vào chính các
  Reference Plane đó, nên kéo tham số là khối co giãn thật.
- **Tham số công thức** (khai báo ở `FORMULA_PARAMS`): `Nửa Dài`,
  `Nửa Rộng`, `Diện tích chiếm chỗ = Dài × Rộng`,
  `Thể tích bao = Dài × Rộng × Cao`, `Tỉ lệ Dài/Rộng`.
- **Tham số Vật liệu** liên kết thẳng vào khối.
- **Tham số nhận dạng**: `Mã hiệu`, `Nguồn CAD`, `Ngày tạo`.

### 4 chế độ dựng khối (cột **CHẾ ĐỘ** trên lưới)

| Mã | Ý nghĩa |
|----|---------|
| `HYBRID` | **(mặc định)** Đùn đúng biên dạng CAD + vẽ lại nét đủ các mặt |
| `PROFILE` | Chỉ đùn đúng biên dạng CAD, hình chuẩn nhất |
| `BOX` | Chỉ khối hộp Dài×Rộng×Cao — **co giãn 100% chắc chắn** |
| `LINES` | Chỉ nét CAD, không dựng khối |

### Hai giới hạn có thật, nói trước để bạn không bất ngờ

1. **Biên dạng không phải hình chữ nhật thì `Dài`/`Rộng` không kéo giãn
   được biên dạng.** Revit chỉ khoá chắc chắn được các mặt phẳng vuông góc
   vào Reference Plane. Với biên dạng cong/lồi lõm, script vẫn khoá được
   **chiều Cao**, còn `Dài`/`Rộng` giữ vai trò thông số báo cáo — và có ghi
   cảnh báo rõ trong `Warnings`. Cần co giãn 100% thì chọn chế độ `BOX`.
2. **Symbolic Line của Revit chỉ bật/tắt theo CẶP `Front/Back` và
   `Left/Right`** — không tách riêng Front với Back được. Vì vậy: mặt đứng
   chính và mặt bên trái vẽ bằng Symbolic Line; **mặt sau và mặt phải** vẽ
   bằng **Model Line đặt đúng vị trí thật** (mặt sau ở `y = +Rộng/2`, mặt
   phải ở `x = +Dài/2`), nằm trong subcategory riêng. Bỏ tick *"Vẽ mặt
   sau/phải"* nếu bạn thấy rối.

3. **Việc gom sản phẩm là suy luận, không phải phép màu.** Hai luật ở trên
   xử lý đúng các bố cục bản vẽ thường gặp, nhưng bản vẽ xếp bất thường
   (mặt bằng của tủ này nằm dưới mặt đứng của tủ kia, các hình chiếu cách
   nhau quá xa/quá gần) vẫn có thể bị gom sai. Vì vậy **kết quả luôn hiện
   ra lưới cho bạn duyệt trước khi tạo** — thấy sai thì sửa Dài/Rộng/Cao,
   bỏ tick dòng thừa, hoặc tắt "Tách nhiều sản phẩm / 1 file" rồi tự tách
   file CAD ra.

> Khi bạn sửa `Dài`/`Rộng`/`Cao` trên lưới, nét CAD được **co giãn theo cho
> khớp đúng tham số** (`FIT_CAD_TO_PARAMS`), nên family luôn đúng bằng con
> số bạn đặt, không lệch so với bản vẽ gốc.

---

## 5. Tốc độ

Điều làm nên tốc độ (và cũng là những gì script thật sự làm):

- Mỗi family gói gọn trong **đúng 1 Transaction** → Revit chỉ regenerate
  1 lần cho cả family thay vì mỗi nét 1 lần.
- File `.dxf` đọc thẳng bằng Python, **không cần import vào Revit**.
- File `.dwg` chỉ import **một lần vào 1 tài liệu "nháp" dùng chung**, bóc
  hình học xong thì **RollBack** transaction (tài liệu nháp sạch nguyên,
  không để lại rác), và có **cache theo đường dẫn + thời điểm sửa file** nên
  quét lại lần 2 gần như tức thì.
- Chế độ **TURBO**: giản lược nét bằng Douglas–Peucker và hạ trần số nét
  mỗi hình chiếu — mắt thường gần như không thấy khác nhưng nhanh hơn hẳn.

**Về con số "1 giây / 50 family":** script **đo và báo tốc độ thật**
(`FamiliesPerSec` trong OUT, và hiện ngay trên hộp thoại kết thúc) chứ
không tuyên bố suông. Tốc độ thực tế phụ thuộc máy bạn, độ nặng của file
CAD và số nét phải vẽ lại — bản vẽ đơn giản, chế độ TURBO thì rất nhanh;
bản vẽ nhiều chục nghìn nét thì chậm hơn. Hãy đọc con số đo được rồi chỉnh
`MAX_CURVES_PER_VIEW` / bật TURBO cho phù hợp.

---

## 6. OUT trả về gì

```python
{
  "Status":         "Done" | "Cancelled" | "Idle" | "NoInput" | "Error",
  "Created":        12,          # số family tạo thành công
  "Failed":         1,
  "Files":          [".../LAVABO BỘ 3.rfa", ...],
  "Loaded":         0,           # số family đã nạp vào project (nếu bật)
  "Placed":         0,           # số family đã đặt đúng vị trí CAD
  "ChildFamilies":  3,           # số family con đã dựng
  "Nested":         12,          # số lần family con được lồng vào family mẹ
  "Report":         [[...], ...],# bảng tóm tắt từng dòng
  "Warnings":       [...],       # cảnh báo/lỗi chi tiết theo từng family
  "BuildMs":        8450,        # thời gian THỰC dựng family (không tính lúc mở GUI)
  "FamiliesPerSec": 1.42,        # tốc độ thật đo được
  "ElapsedMs":      93000        # tổng thời gian kể cả thời gian bạn thao tác GUI
}
```

**Luôn xem `Warnings`** — mỗi bước lỗi đều được ghi lại kèm tên family, và
family vẫn được tạo ở mức tốt nhất có thể thay vì bỏ trắng.

---

## 7. Kiểm thử

Toàn bộ phần logic thuần Python (đọc DXF, gom cụm, nhận diện hình chiếu,
suy kích thước, ghép vòng kín, đoán danh mục, gộp file, chọn template) có
kiểm thử tự động chạy được **ngoài Revit**:

```bash
python3 RevitCadToFamily/tests/test_cad_family_core.py
```

Bộ test dựng sẵn các bản vẽ DXF mẫu **đúng như 3 ảnh hướng dẫn** và kiểm
tra kết quả:

| Bản vẽ mẫu | Phải ra |
|------------|---------|
| Bàn lavabo 1500×500 có 3 chậu tròn (block) + mặt đứng 1500×800 | 2 hình chiếu, 3 lỗ chậu, `1500/500/800`, danh mục *Plumbing Fixtures* — **kể cả khi xoá hết chữ ghi chú** |
| Dãy 3 cái tủ áo, mỗi cái có mặt đứng ở trên + mặt bằng có cung quét cánh ở dưới | **3 family riêng**, mỗi cái `1200/600/2400` (cung quét cánh **không** được tính vào chiều sâu), 2 khoang đều nhau, mặt bên **tự suy ra** |
| Bản vẽ bếp chỉ có mặt đứng chính + 2 mặt bên, **không có mặt bằng** | **1 sản phẩm**, mặt bằng **tự suy ra**, `Rộng` lấy đúng từ bề ngang mặt bên, 4 khoang |
| Mặt đứng có 2 mặt kệ ngang | 2 mặt kệ đó phải xuất hiện **đúng cao độ** trên mặt bên tự suy |

Trong quá trình phát triển, chính bộ test này đã bắt được 4 lỗi thật đã
được sửa: nhận nhầm "CỬA SỔ" thành cửa đi; đọc `1200,5` thành `12005`; vị
trí vách bị "hít" về bội số dung sai (vách 600 mm trả về 576 mm); và **khe
hở nhỏ hơn 1 ô lưới làm mặt bằng dính vào mặt đứng** khi gom cụm.

---

## 8. Chỉnh sâu (phần CONFIG đầu file)

| Hằng số | Ý nghĩa |
|---------|---------|
| `ISLAND_GAP_RATIO` | Khoảng hở tối thiểu (theo % cạnh lớn nhất) để tách 2 hình chiếu. Bản vẽ vẽ sát nhau quá thì giảm xuống |
| `LOOP_JOIN_TOL_MM` | Dung sai ghép nét hở thành vòng kín (mm). CAD vẽ ẩu, nét hở nhiều thì tăng lên |
| `MAX_CURVES_PER_VIEW` | Trần số nét vẽ lại mỗi hình chiếu (chống treo Revit) |
| `TURBO_SIMPLIFY_TOL_MM` | Độ giản lược nét ở chế độ TURBO |
| `DEFAULT_DIMS` | Kích thước mặc định theo danh mục khi bản vẽ không đủ dữ liệu |
| `CATEGORY_KEYWORDS` | Từ khoá đoán danh mục — thêm từ khoá riêng của công ty bạn vào đây |
| `VIEW_KEYWORDS` | Từ khoá nhận diện hình chiếu trong chữ/layer |
| `NOISE_LAYER_KEYWORDS` | Layer bị coi là rác, không vẽ lại |
| `FORMULA_PARAMS` | Danh sách tham số công thức tự thêm vào family |
| `P_LEN / P_WID / P_HGT` | Tên 3 tham số chính (`Dài`/`Rộng`/`Cao`) |
| `MAX_NESTED_PARTS` | Trần số family con lồng vào 1 family mẹ (mặc định 12) |
| `PLAN_SCORE_MIN` | Ngưỡng điểm để coi 1 cụm là mặt bằng |
| `SWING_CATEGORIES` | Các danh mục được vẽ thêm ký hiệu cánh mở khi tự suy mặt bằng |

---

## 9. Ghi chú kỹ thuật quan trọng

- **GUI viết theo kiểu "eventless"**: không WPF/XAML, **không đăng ký sự
  kiện .NET**, **không kế thừa class .NET** nào. Lý do: trên Dynamo 2.19 /
  Revit 2024 với engine CPython3, PythonNet phải phát assembly động
  (`System.Reflection.Emit.TypeBuilder`) để nối callback Python vào delegate
  .NET, và việc đó bị chặn trong tiến trình Revit → lỗi
  *"Constructor on type 'System.Reflection.Emit.TypeBuilder' not found"*.
  Mọi tương tác đi qua `Button.DialogResult` + `Form.ShowDialog()`.
  **Hệ quả:** cũng vì lý do này, script nạp family bằng
  `Document.LoadFamily(path)` bản string chứ không hiện thực
  `IFamilyLoadOptions` (hiện thực interface = subclass = crash).
- **Không dùng toán tử `+`/`-` trên đối tượng `XYZ`** — đã từng gây crash
  CPython3 ở dự án này. Mọi phép tính toạ độ làm bằng số thực rồi mới dựng
  `XYZ`.
- **Danh sách import Revit được giữ tối thiểu**: cả khối nằm trong 1
  `try/except`, chỉ cần 1 tên không tồn tại trên một đời Revit nào đó là
  `REVIT_API` tụt về `False` và cả script "chết" oan.
- **Cửa & Cửa sổ không bị đổi danh mục**: 2 danh mục này bắt buộc dùng
  đúng template gốc (có tường chủ + lỗ mở dựng sẵn), nên script chọn đúng
  `Metric Door.rft` / `Metric Window.rft` thay vì đổi category.
- **Chưa chạy thử trên Revit thật trong môi trường tạo mã này** (không có
  Revit/Dynamo cài sẵn ở đây). Phần logic thuần Python đã test đầy đủ; phần
  gọi Revit API viết đúng chuẩn tài liệu API và mỗi bước đều có try/except
  riêng + ghi cảnh báo. **Lần đầu dùng hãy chạy thử 1–2 file, mở `.rfa` ra
  kiểm tra, rồi mới chạy cả thư mục.**
