# TOTAL

Bộ công cụ Dynamo Python (Revit) — viết cho engine **CPython3**, giao diện
WinForms "eventless" theme tối vàng đồng, mọi thao tác ghi vào Revit đều
gói trong Transaction tối thiểu để chạy nhanh nhất có thể.

## 1. RevitCadToFamily — Tự tạo Family hàng loạt từ file CAD

Dán 1 file CAD hoặc cả 1 thư mục (DWG/DXF) → script tự đọc bản vẽ, tự nhận
ra **mặt bằng / mặt đứng chính / mặt sau / mặt bên trái / phải**, tự suy
**Dài × Rộng × Cao** và **danh mục Revit**, rồi xuất ra `.rfa` có khối 3D,
nét vẽ lại đúng theo CAD trên từng hình chiếu, tham số kéo giãn và tham số
công thức. Có GUI dạng bảng để bạn duyệt và hiệu chỉnh từng dòng trước khi
tạo.

Tách được **nhiều sản phẩm trong 1 file CAD**, **tự suy ra hình chiếu còn
thiếu**, và dựng **family con lồng vào family mẹ** có ràng buộc tham số.

Xem chi tiết: [`RevitCadToFamily/README.md`](RevitCadToFamily/README.md)

## 2. RevitDynamoTable — Bảng dữ liệu kiểu Excel trên view Revit

Tự dò và cập nhật bảng dữ liệu dựng từ Family Generic Annotation / TextNote,
với GUI kiểu Excel (tính SUM/PRODUCT/DIVIDE/AVERAGE) và ghi kết quả ngược
lại view Revit trong 1 transaction duy nhất.

Xem chi tiết: [`RevitDynamoTable/README.md`](RevitDynamoTable/README.md)

---

## Kiểm thử

Phần logic thuần Python của cả 2 công cụ chạy test được **ngoài Revit**:

```bash
python3 RevitCadToFamily/tests/test_cad_family_core.py
python3 RevitDynamoTable/tests/test_core_logic.py
```
