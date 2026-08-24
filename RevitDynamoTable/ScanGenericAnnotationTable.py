# -*- coding: utf-8 -*-
"""
================================================================================
 SCAN GENERIC ANNOTATION TABLE  —  Dynamo Python Script (CPython3 engine)
================================================================================
CHỨC NĂNG (những gì script này làm):
  1. Nhận danh sách các Family Instance (Generic Annotation) đang được QUÉT
     CHỌN (box-select) trong view Revit — chính là các ô chữ tạo thành bảng
     "giống Excel" mà bạn đã dựng bằng family Generic Annotation (xem hình
     minh hoạ: bảng "俩@_STR Framing" / "GROSS BUILDING").
  2. Tự dò toạ độ của từng annotation để DỰNG LẠI cấu trúc bảng (hàng/cột)
     y hệt bố cục hình học trên view — không cần bạn khai báo số hàng/cột.
  3. Đọc nội dung chữ đã điền sẵn trên từng ô (dữ liệu bạn đã điền từ
     Schedule / Text trước đó) để nạp vào lưới dữ liệu ban đầu.
  4. (Tuỳ chọn) Đọc thêm 1 Schedule (ViewSchedule) để lấy dữ liệu gốc, tự
     điền vào các ô annotation đang còn TRỐNG.
  5. Mở GIAO DIỆN GUI (WinForms, theme tối sang trọng – vàng đồng
     "chuẩn men") giống một bảng Excel: xem, sửa, bôi chọn 1 vùng rồi bấm
     "Σ Xem nhanh" để xem SUM/AVERAGE/MIN/MAX/PRODUCT, chọn hàm rồi bấm
     "➕ Chèn công thức" để chèn =SUM(...)/=PRODUCT(...)/=AVERAGE(...)/
     =A/B vào ô đích, bấm "⟲ Tính lại" để tính lại toàn bộ công thức.
  6. Khi bấm "Cập nhật vào Revit": ghi toàn bộ giá trị đã tính vào lại
     đúng parameter chữ của từng Generic Annotation tương ứng, TRONG 1
     TRANSACTION DUY NHẤT (siêu nhanh — không mở/đóng transaction theo
     từng ô), rồi cập nhật ngay trên view Revit.

CÁCH DÙNG TRONG DYNAMO (chỉ cần nối IN[0] và IN[1] là chạy được ngay,
mọi input khác đều có thể để trống — script tự dùng giá trị mặc định an
toàn nếu port đó không tồn tại/không nối):
  - IN[0] (bắt buộc): Node "Select Model Elements" (chọn nhiều) -> danh
    sách các Generic Annotation bạn đã quét chọn tạo nên bảng trên view.
  - IN[1] (khuyên dùng): 1 node Boolean True/False — công tắc bảo vệ.
    False = KHÔNG làm gì cả (an toàn tuyệt đối). True hoặc không nối =
    chạy đầy đủ và mở GUI.
  - IN[2] (tuỳ chọn): 1 ViewSchedule để đối chiếu số liệu gốc, tự điền
    vào các ô annotation đang còn trống. Để trống nếu không cần.
  - IN[3] (tuỳ chọn): tên Parameter chứa chữ hiển thị trên annotation
    (vd "Text", "文字", "Label"...). Để trống để script TỰ DÒ bằng cách
    khảo sát thực tế trên chính các phần tử đã chọn (xem
    detect_best_param_name): thử lần lượt CANDIDATE_PARAM_NAMES bên dưới
    (cả Instance lẫn Type Parameter), nếu family lưu chữ bằng cách đặt
    TÊN TYPE riêng cho từng ô (Family Type Name) thì tự chuyển sang dùng
    tên Type, và nếu vẫn không thấy gì thì quét toàn bộ parameter chữ
    đang có để tự chọn cái phổ biến nhất — không đoán mù theo 1 danh sách
    cố định.
  - IN[4], IN[5] (tuỳ chọn): dung sai gom hàng / gom cột theo đơn vị nội
    bộ Revit (feet). Để trống để script tự tính.
  - IN[6] (nâng cao, hiếm dùng): True = bỏ qua GUI, tự tính và ghi thẳng
    vào Revit không cho xem trước. Mặc định False (luôn mở GUI).

  Chọn ENGINE của node Python Script này là "CPython3" (Dynamo cho phép
  đổi engine bằng cách click chuột phải vào node -> Change Engine).

OUT:
  Một Dictionary gồm:
    "Status"        : "Updated" / "Cancelled" / "NoSelection" / "Idle" / "Error"
    "UpdatedCount"  : số ô đã ghi vào Revit
    "TotalCells"    : tổng số ô nhận diện được trong bảng
    "Rows", "Cols"  : kích thước lưới nhận diện được
    "Grid"          : lưới giá trị cuối cùng (list các list string)
    "Warnings"      : danh sách cảnh báo/lỗi (nếu có) trong quá trình chạy
    "ElapsedMs"     : tổng thời gian xử lý — bao gồm cả thời gian bạn thao
                      tác trên GUI (mili-giây)
    "WriteMs"       : thời gian THỰC TẾ để ghi vào Revit — chỉ tính phần
                      Transaction, không tính thời gian chờ GUI (mili-giây)
    "CellsPerSecond": tốc độ ghi thực đo được = số ô đã ghi / (WriteMs/1000)

LƯU Ý QUAN TRỌNG:
  Script được viết đúng theo chuẩn Revit API / Dynamo (RevitServices,
  TransactionManager, ViewSchedule.GetCellText, v.v.) nhưng CHƯA thể chạy
  thử trực tiếp trên Revit thật trong môi trường tạo mã này (không có
  Revit/Dynamo cài sẵn ở đây). Vì vậy khi dùng lần đầu, nên thử với MỘT
  bảng nhỏ trước, kiểm tra kỹ log cảnh báo, trước khi áp dụng cho bảng lớn.
================================================================================
"""

import re
import time
import traceback

# ------------------------------------------------------------------------
# 1. IMPORTS & MÔI TRƯỜNG REVIT / DYNAMO
# ------------------------------------------------------------------------
import clr

clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
import Autodesk
from Autodesk.Revit.DB import (
    XYZ, Transaction, SubTransaction, BuiltInParameter,
)

try:
    from Autodesk.Revit.DB import SectionType
except Exception:
    SectionType = None

# RevitServices chỉ tồn tại khi chạy trong Dynamo (không có khi chạy
# ngoài, vd RevitPythonShell/pyRevit) -> có fallback ở phần Transaction.
DYNAMO_ENV = True
try:
    clr.AddReference('RevitServices')
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
except Exception:
    DYNAMO_ENV = False
    TransactionManager = None

# --------------------------------------------------------------------
# GUI: WinForms, KHÔNG dùng WPF/XAML.
#
# QUAN TRỌNG — lý do đổi từ WPF sang WinForms "eventless":
# Trên Dynamo 2.19 / Revit 2024 với engine CPython3 (PythonNet 2.5.x),
# việc Python ĐĂNG KÝ sự kiện .NET (vd `control.add_Click(handler)`,
# `control.Click += handler`) hoặc KẾ THỪA (subclass) một control .NET
# (vd `class MyForm(Form)`) có thể ném lỗi:
#   "Constructor on type 'System.Reflection.Emit.TypeBuilder' not found"
# vì PythonNet cần tạo assembly động (TypeBuilder) để nối callback Python
# vào delegate .NET, và việc phát assembly động bị chặn trong tiến trình
# Revit/Dynamo. Cách né hoàn toàn an toàn — dùng ở mọi engine — là:
#   1) KHÔNG BAO GIỜ subclass bất kỳ kiểu .NET nào;
#   2) KHÔNG BAO GIỜ đăng ký sự kiện .NET từ Python;
#   3) Tương tác qua Button.DialogResult + Form.ShowDialog() (100% xử lý
#      trong .NET, không cần callback Python), với 1 vòng lặp Python bên
#      ngoài dựng lại cửa sổ ở mỗi bước — kiểu "wizard eventless".
# --------------------------------------------------------------------
GUI_AVAILABLE = False
GUI_IMPORT_ERROR = ""
try:
    clr.AddReference('System.Windows.Forms')
    clr.AddReference('System.Drawing')
    from System.Windows.Forms import (
        Form, Label, TextBox, Button, ComboBox, ComboBoxStyle, Panel, DockStyle,
        DataGridView, DataGridViewTextBoxColumn, DataGridViewSelectionMode,
        DataGridViewColumnHeadersHeightSizeMode, DataGridViewAutoSizeColumnsMode,
        DataGridViewColumnSortMode,
        DialogResult, FormStartPosition, FormBorderStyle, FlatStyle,
        MessageBox, MessageBoxButtons, MessageBoxIcon, Application,
    )
    from System.Drawing import Color, Font, FontStyle, Point, Size, GraphicsUnit, SystemFonts, ContentAlignment
    try:
        from System import Single
    except Exception:
        Single = float
    GUI_AVAILABLE = True
except Exception as _gui_exc:
    GUI_IMPORT_ERROR = str(_gui_exc)

if DYNAMO_ENV:
    doc = DocumentManager.Instance.CurrentDBDocument
    uiapp = DocumentManager.Instance.CurrentUIApplication
    active_view = doc.ActiveView
else:
    doc = None
    uiapp = None
    active_view = None


# ------------------------------------------------------------------------
# 0. CẤU HÌNH (CONFIG) — chỉnh ở đây, không cần sửa logic bên dưới
# ------------------------------------------------------------------------
CANDIDATE_PARAM_NAMES = [
    u"文字内容", u"文字", u"TEXT", u"Text", u"Label", u"LABEL_TEXT",
    u"Value", u"VALUE", u"内容", u"Comments", u"注释文字", u"文本",
    u"标签", u"标签文字",
]
ROUND_DECIMALS = 3           # số chữ số thập phân khi hiển thị kết quả tính
AUTO_TOL_MIN_FACTOR = 0.5    # khi chỉ có đúng 1 khoảng cách trong dữ liệu
AUTO_TOL_JUMP_RATIO = 3.0    # bước nhảy (gap sau / gap trước) tối thiểu để
                              # coi là ranh giới thật giữa 2 hàng/cột khác nhau
AUTO_TOL_NOISE_FLOOR_FT = 0.01  # ~3mm (đơn vị feet nội bộ Revit) — khoảng
                              # cách đồng đều nhỏ hơn mức này bị coi là nhiễu
MAX_RECALC_PASSES = 8        # số vòng lặp tối đa để giải công thức lồng nhau

THEME = {
    "bg":        "#0F1115",
    "panel":     "#171A21",
    "panel2":    "#1C2028",
    "border":    "#C9A227",
    "border_dim": "#3A3220",
    "gold":      "#E8C468",
    "gold_dark": "#C9A227",
    "text":      "#F1EFEA",
    "text_dim":  "#9AA0AC",
    "grid_line": "#2A2F3A",
    "row_alt":   "#181B22",
    "danger":    "#D9534F",
    "ok":        "#4CC38A",
}


# ------------------------------------------------------------------------
# 2. TIỆN ÍCH HÌNH HỌC — DÒ TÌM LƯỚI BẢNG (GRID DETECTION)
# ------------------------------------------------------------------------
def get_location_point(elem, view):
    """Lấy toạ độ đại diện của 1 annotation: ưu tiên LocationPoint,
    nếu không có thì lấy tâm BoundingBox theo view hiện tại."""
    try:
        loc = elem.Location
        if loc is not None and hasattr(loc, "Point") and loc.Point is not None:
            return loc.Point
    except Exception:
        pass
    try:
        bb = elem.get_BoundingBox(view)
        if bb is not None:
            return XYZ(
                (bb.Min.X + bb.Max.X) / 2.0,
                (bb.Min.Y + bb.Max.Y) / 2.0,
                (bb.Min.Z + bb.Max.Z) / 2.0,
            )
    except Exception:
        pass
    return None


def to_uv(view, pt):
    """Chiếu điểm 3D vào hệ trục 2D (U = ngang, V = dọc) của view,
    để việc gom cụm hàng/cột không phụ thuộc vào view bị xoay.

    QUAN TRỌNG: dùng pt.Subtract(origin) thay vì toán tử "pt - origin".
    Engine CPython3 của Dynamo (pythonnet) không phải lúc nào cũng ánh xạ
    được các toán tử nạp chồng (operator overload) của kiểu XYZ trong
    RevitAPI sang toán tử Python (+ - * /), gây lỗi
    "TypeError: unsupported operand type(s)". Gọi thẳng phương thức .NET
    (Subtract/Add/Multiply/DotProduct...) luôn an toàn ở mọi engine."""
    origin = view.Origin
    vec = pt.Subtract(origin)
    u = vec.DotProduct(view.RightDirection)
    v = vec.DotProduct(view.UpDirection)
    return (u, v)


def auto_tolerance(values):
    """Tự tính dung sai gom cụm 1 chiều theo kiểu 'natural breaks': tìm chỗ
    khoảng-cách-giữa-các-khoảng-cách (gap of gaps) nhảy vọt rõ rệt nhất để
    tách nhóm 'nhiễu trong cùng 1 hàng/cột' (rất nhỏ) khỏi nhóm 'khoảng
    cách thật giữa 2 hàng/cột khác nhau' (lớn hơn hẳn). Nếu không tìm thấy
    bước nhảy nào đủ rõ (tỉ lệ >= AUTO_TOL_JUMP_RATIO) thì coi toàn bộ giá
    trị là CÙNG một cụm (không tách)."""
    vs = sorted(values)
    diffs = [vs[i] - vs[i - 1] for i in range(1, len(vs))]
    diffs = [d for d in diffs if d > 1e-9]
    if not diffs:
        return 0.01  # tất cả trùng nhau -> dung sai an toàn mặc định (~3mm)
    sorted_diffs = sorted(diffs)
    if len(sorted_diffs) == 1:
        return sorted_diffs[0] * AUTO_TOL_MIN_FACTOR

    best_idx = None
    best_ratio = 1.0
    for i in range(1, len(sorted_diffs)):
        prev = sorted_diffs[i - 1]
        cur = sorted_diffs[i]
        ratio = cur / prev if prev > 1e-9 else (cur / 1e-9)
        if ratio > best_ratio:
            best_ratio = ratio
            best_idx = i

    if best_idx is not None and best_ratio >= AUTO_TOL_JUMP_RATIO:
        return (sorted_diffs[best_idx - 1] + sorted_diffs[best_idx]) / 2.0

    # Không tìm thấy bước nhảy rõ rệt -> mọi khoảng cách xấp xỉ đồng đều.
    # Đây có thể là (a) một lưới "sạch" không nhiễu, mỗi khoảng cách đều là
    # ranh giới hàng/cột THẬT (vd lưới annotation copy đều 300mm/500mm...),
    # hoặc (b) chỉ 1 hàng/cột duy nhất với nhiễu số học rất nhỏ. Phân biệt
    # 2 trường hợp bằng một "sàn nhiễu" tuyệt đối (đơn vị feet nội bộ
    # Revit): khoảng cách đồng đều nhưng LỚN hơn sàn nhiễu -> chắc chắn là
    # ranh giới thật; nhỏ hơn hoặc bằng -> chỉ là nhiễu, gộp 1 cụm.
    if sorted_diffs[0] > AUTO_TOL_NOISE_FLOOR_FT:
        return sorted_diffs[0] * AUTO_TOL_MIN_FACTOR
    return sorted_diffs[-1] * 1.5


def cluster_1d(values, tol):
    """Gom các giá trị 1 chiều thành các 'cụm' (hàng hoặc cột).
    Trả về: list chỉ số cụm cho từng phần tử (theo thứ tự input gốc),
             list tâm cụm đã sắp xếp tăng dần."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    cluster_id_by_sorted_pos = []
    centers = []
    current_cluster = 0
    current_values = [values[order[0]]]
    cluster_id_by_sorted_pos.append(0)
    for k in range(1, len(order)):
        v = values[order[k]]
        if v - current_values[-1] > tol:
            centers.append(sum(current_values) / len(current_values))
            current_cluster += 1
            current_values = [v]
        else:
            current_values.append(v)
        cluster_id_by_sorted_pos.append(current_cluster)
    centers.append(sum(current_values) / len(current_values))

    cluster_id_by_original = [0] * len(values)
    for sorted_pos, orig_idx in enumerate(order):
        cluster_id_by_original[orig_idx] = cluster_id_by_sorted_pos[sorted_pos]
    return cluster_id_by_original, centers


def build_grid(elements, view, row_tol=None, col_tol=None):
    """Dò lưới hàng/cột từ toạ độ các annotation đã chọn.
    Trả về: grid_elems[row][col] = element hoặc None,
             n_rows, n_cols, warnings(list)."""
    warnings = []
    pts = []
    valid_elems = []
    for e in elements:
        try:
            p = get_location_point(e, view)
            if p is None:
                warnings.append(u"Bỏ qua 1 phần tử không xác định được toạ độ (Id=%s)" % getattr(e, "Id", "?"))
                continue
            uv = to_uv(view, p)
        except Exception as ex:
            warnings.append(u"Bỏ qua 1 phần tử do lỗi tính toạ độ (Id=%s): %s"
                             % (getattr(e, "Id", "?"), str(ex)))
            continue
        valid_elems.append(e)
        pts.append(uv)

    if not valid_elems:
        return [], 0, 0, warnings

    us = [p[0] for p in pts]
    vs = [p[1] for p in pts]

    rt = row_tol if row_tol else auto_tolerance(vs)
    ct = col_tol if col_tol else auto_tolerance(us)

    row_ids, row_centers = cluster_1d(vs, rt)
    col_ids, col_centers = cluster_1d(us, ct)

    n_rows = len(row_centers)
    n_cols = len(col_centers)

    # Hàng: V lớn (cao) -> hàng trên cùng (hàng số 0)
    row_order = sorted(range(n_rows), key=lambda i: -row_centers[i])
    row_rank = {old: new for new, old in enumerate(row_order)}
    # Cột: U nhỏ -> cột trái cùng (cột số 0)
    col_order = sorted(range(n_cols), key=lambda i: col_centers[i])
    col_rank = {old: new for new, old in enumerate(col_order)}

    grid_elems = [[None for _ in range(n_cols)] for _ in range(n_rows)]
    collisions = 0
    for idx, e in enumerate(valid_elems):
        r = row_rank[row_ids[idx]]
        c = col_rank[col_ids[idx]]
        if grid_elems[r][c] is not None:
            collisions += 1
        grid_elems[r][c] = e

    if collisions:
        warnings.append(
            u"Có %d ô bị trùng vị trí (2 annotation quá gần nhau) — hãy tăng "
            u"dung sai hoặc kiểm tra lại vùng chọn." % collisions
        )

    fill_ratio = (len(valid_elems) / float(n_rows * n_cols)) if n_rows * n_cols else 0.0
    warnings.append(
        u"Dò được lưới %d hàng × %d cột (%d ô) từ %d phần tử hợp lệ — lấp đầy %.0f%%. "
        u"Dung sai gom hàng/cột đang dùng: %.5f / %.5f (feet nội bộ Revit)."
        % (n_rows, n_cols, n_rows * n_cols, len(valid_elems), fill_ratio * 100.0, rt, ct)
    )
    if fill_ratio < 0.5:
        warnings.append(
            u"⚠ Lưới có vẻ DÒ SAI (lấp đầy dưới 50%%, nhiều ô trống bất thường) — nhiều khả năng dung sai "
            u"gom hàng/cột đang quá NHỎ nên các annotation gần nhau bị tách nhầm thành nhiều hàng/cột khác "
            u"nhau thay vì gộp vào cùng 1 hàng/cột. Hãy thử: (1) truyền row_tol/col_tol LỚN HƠN giá trị ở "
            u"trên vào IN[4]/IN[5] (đơn vị feet nội bộ Revit, 1mm ≈ 0.00328ft), hoặc (2) kiểm tra lại đã "
            u"quét đúng CHỈ các annotation của 1 bảng duy nhất (không lẫn phần tử của bảng/family khác)."
        )

    return grid_elems, n_rows, n_cols, warnings


# ------------------------------------------------------------------------
# 3. ĐỌC PARAMETER TRÊN ANNOTATION / ĐỌC SCHEDULE
# ------------------------------------------------------------------------
# Rất nhiều family "bảng kiểu Excel" dựng từ Generic Annotation KHÔNG lưu
# chữ trong 1 Instance Parameter, mà mỗi ô là 1 FAMILY TYPE (Symbol) RIÊNG
# và Label trong family tham chiếu chính TÊN TYPE (hoặc 1 Type Parameter)
# để hiển thị — nghĩa là chữ "nằm" ở elem.Symbol.Name, không phải ở
# elem.LookupParameter(...). TYPE_NAME_SENTINEL đại diện cho nguồn dữ liệu
# đặc biệt này trong toàn bộ phần còn lại của script.
TYPE_NAME_SENTINEL = u"__TYPE_NAME__"


class CellSource(object):
    """Bọc 1 nguồn dữ liệu chữ của 1 ô: hoặc 1 Parameter (Instance/Type),
    hoặc chính TÊN của FamilySymbol (Type Name)."""
    __slots__ = ("kind", "ref", "name")

    def __init__(self, kind, ref, name):
        self.kind = kind        # "PARAM" hoặc "TYPE_NAME"
        self.ref = ref          # Parameter, hoặc FamilySymbol/ElementType
        self.name = name        # tên hiển thị để log/báo cáo


def read_cell_text(param):
    if param is None:
        return ""
    try:
        if param.StorageType == Autodesk.Revit.DB.StorageType.String:
            v = param.AsString()
            return v if v is not None else ""
        v = param.AsValueString()
        return v if v is not None else ""
    except Exception:
        return ""


def _lookup_param_instance_or_type(elem, name):
    """Tìm Parameter theo tên: thử Instance trước, không có thì thử Type
    (Symbol) — vì Label trong family có thể bind vào Type Parameter."""
    p = None
    try:
        p = elem.LookupParameter(name)
    except Exception:
        p = None
    if p is not None:
        return p
    try:
        sym = elem.Symbol
        if sym is not None:
            p = sym.LookupParameter(name)
    except Exception:
        p = None
    return p


def find_text_source(elem, forced_name=None):
    """Trả về CellSource đầu tiên phù hợp để đọc/ghi chữ cho 1 annotation."""
    if forced_name == TYPE_NAME_SENTINEL:
        try:
            sym = elem.Symbol
            if sym is not None:
                return CellSource("TYPE_NAME", sym, TYPE_NAME_SENTINEL)
        except Exception:
            pass
        return None
    if forced_name:
        p = _lookup_param_instance_or_type(elem, forced_name)
        if p is not None:
            return CellSource("PARAM", p, forced_name)
    for name in CANDIDATE_PARAM_NAMES:
        p = _lookup_param_instance_or_type(elem, name)
        if p is not None:
            return CellSource("PARAM", p, name)
    # fallback cuối: BuiltInParameter ALL_MODEL_INSTANCE_COMMENTS (ít dùng
    # cho annotation nhưng để tránh trắng tay nếu family dùng comment)
    try:
        p = elem.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if p is not None:
            return CellSource("PARAM", p, "Comments")
    except Exception:
        pass
    return None


def read_source_text(source):
    if source is None:
        return ""
    if source.kind == "PARAM":
        return read_cell_text(source.ref)
    if source.kind == "TYPE_NAME":
        try:
            v = source.ref.Name
            return v if v is not None else ""
        except Exception:
            return ""
    return ""


def _sample_read(elem, name):
    if name == TYPE_NAME_SENTINEL:
        try:
            sym = elem.Symbol
            return sym.Name if sym is not None and sym.Name else ""
        except Exception:
            return ""
    p = _lookup_param_instance_or_type(elem, name)
    return read_cell_text(p) if p is not None else ""


def detect_best_param_name(elements, forced_name=None, sample_limit=100):
    """Tự động dò nguồn dữ liệu chữ TỐT NHẤT bằng cách khảo sát thực tế
    trên chính các phần tử đã chọn — không đoán mù theo 1 danh sách tên cố
    định. Trả về (tên_hoặc_sentinel, tỉ_lệ_có_chữ, số_phần_tử_đã_khảo_sát).

    Bước 1: thử từng tên trong CANDIDATE_PARAM_NAMES + TYPE_NAME_SENTINEL
            (rẻ, đủ dùng cho đa số trường hợp).
    Bước 2 (chỉ chạy khi bước 1 không ra kết quả nào): quét TOÀN BỘ
            parameter kiểu chữ đang có trên các phần tử, đếm tần suất có
            nội dung không rỗng, chọn tên phổ biến nhất."""
    if forced_name:
        return forced_name, None, 0
    sample = elements[:sample_limit] if len(elements) > sample_limit else elements
    if not sample:
        return None, 0.0, 0

    best_name, best_count = None, 0
    for name in list(CANDIDATE_PARAM_NAMES) + [TYPE_NAME_SENTINEL]:
        count = 0
        for e in sample:
            txt = _sample_read(e, name)
            if txt and txt.strip():
                count += 1
        if count > best_count:
            best_count, best_name = count, name
    if best_count > 0:
        return best_name, best_count / float(len(sample)), len(sample)

    freq = {}
    for e in sample:
        try:
            params = list(e.GetOrderedParameters())
        except Exception:
            try:
                params = list(e.Parameters)
            except Exception:
                params = []
        for p in params:
            try:
                if p.StorageType != Autodesk.Revit.DB.StorageType.String:
                    continue
                nm = p.Definition.Name
                txt = read_cell_text(p)
                if txt and txt.strip():
                    freq[nm] = freq.get(nm, 0) + 1
            except Exception:
                continue
    if not freq:
        return None, 0.0, len(sample)
    best_name = max(freq, key=freq.get)
    return best_name, freq[best_name] / float(len(sample)), len(sample)


def read_schedule_grid(schedule):
    """Đọc toàn bộ vùng Body của 1 ViewSchedule ra list các list chữ."""
    if schedule is None or SectionType is None:
        return None
    try:
        table_data = schedule.GetTableData()
        section = table_data.GetSectionData(SectionType.Body)
        n_rows = section.NumberOfRows
        n_cols = section.NumberOfColumns
        grid = []
        for r in range(n_rows):
            row_vals = []
            for c in range(n_cols):
                try:
                    txt = schedule.GetCellText(SectionType.Body, r, c)
                except Exception:
                    txt = ""
                row_vals.append(txt)
            grid.append(row_vals)
        return grid
    except Exception:
        return None


# ------------------------------------------------------------------------
# 4. FORMULA ENGINE — TÍNH SUM / PRODUCT / DIVIDE / AVERAGE... KIỂU EXCEL
# ------------------------------------------------------------------------
def col_letter(idx):
    """0-based index -> 'A','B',...,'Z','AA','AB',..."""
    idx += 1
    letters = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def col_index(letters):
    """'A'->0, 'B'->1, ... , 'AA'->26"""
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - ord('A') + 1)
    return idx - 1


CELL_REF_RE = re.compile(r'^([A-Za-z]+)([0-9]+)$')
RANGE_REF_RE = re.compile(r'^([A-Za-z]+[0-9]+):([A-Za-z]+[0-9]+)$')


def parse_cell_ref(token):
    m = CELL_REF_RE.match(token)
    if not m:
        return None
    c = col_index(m.group(1).upper())
    r = int(m.group(2)) - 1
    return (r, c)


class FormulaError(Exception):
    def __init__(self, code):
        super(FormulaError, self).__init__(code)
        self.code = code


class _Token(object):
    __slots__ = ("kind", "value")

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value


_TOKEN_PATTERN = re.compile(
    r"\s*(?:"
    r"(?P<RANGE>[A-Za-z]+[0-9]+:[A-Za-z]+[0-9]+)"
    r"|(?P<FUNC>[A-Za-z_][A-Za-z_0-9]*)\("
    r"|(?P<CELL>[A-Za-z]+[0-9]+)"
    r"|(?P<NUM>[0-9]+(?:\.[0-9]+)?)"
    r"|(?P<OP>[()+\-*/^,])"
    r"|(?P<OTHER>\S)"
    r")"
)


def tokenize(expr):
    tokens = []
    pos = 0
    while pos < len(expr):
        m = _TOKEN_PATTERN.match(expr, pos)
        if not m:
            break
        pos = m.end()
        if m.lastgroup == "RANGE":
            tokens.append(_Token("RANGE", m.group("RANGE")))
        elif m.lastgroup == "FUNC":
            tokens.append(_Token("FUNC", m.group("FUNC").upper()))
        elif m.lastgroup == "CELL":
            tokens.append(_Token("CELL", m.group("CELL")))
        elif m.lastgroup == "NUM":
            tokens.append(_Token("NUM", float(m.group("NUM"))))
        elif m.lastgroup == "OP":
            tokens.append(_Token("OP", m.group("OP")))
        else:
            raise FormulaError("#ERR!")
    return tokens


class FormulaEngine(object):
    """Bộ tính công thức an toàn kiểu Excel, chỉ hỗ trợ đúng những gì
    bảng dữ liệu cần: + - * / ^, tham chiếu ô (B2), vùng (B2:B10) và các
    hàm SUM / AVERAGE / PRODUCT / MIN / MAX / COUNT / ROUND / ABS."""

    FUNCS = {"SUM", "AVERAGE", "AVG", "PRODUCT", "MIN", "MAX", "COUNT", "ROUND", "ABS"}

    def __init__(self, get_raw, n_rows, n_cols):
        self.get_raw = get_raw
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.cache = {}
        self.visiting = set()

    # ---- API chính: giá trị đã-tính-xong của 1 ô ----
    def value_of(self, row, col):
        key = (row, col)
        if key in self.cache:
            return self.cache[key]
        if key in self.visiting:
            raise FormulaError("#CYCLE!")
        self.visiting.add(key)
        try:
            raw = self.get_raw(row, col)
            result = self._eval_cell(raw)
        finally:
            self.visiting.discard(key)
        self.cache[key] = result
        return result

    def _eval_cell(self, raw):
        if raw is None:
            return None
        text = raw.strip() if isinstance(raw, str) else str(raw)
        if text == "":
            return None
        if text.startswith("="):
            try:
                tokens = tokenize(text[1:])
                pos = [0]
                val = self._parse_expr(tokens, pos)
                if pos[0] != len(tokens):
                    return "#ERR!"
                return val
            except FormulaError as fe:
                return fe.code
            except ZeroDivisionError:
                return "#DIV/0!"
            except Exception:
                return "#ERR!"
        try:
            return float(text)
        except ValueError:
            return text  # nhãn / chữ thường (vd tiêu đề cột, đơn vị...)

    # ---- ô hoặc vùng -> giá trị số / list số ----
    def _cell_value(self, row, col):
        if row < 0 or row >= self.n_rows or col < 0 or col >= self.n_cols:
            return None
        return self.value_of(row, col)

    def _as_number(self, v):
        if v is None:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str) and v.startswith("#"):
            raise FormulaError(v)
        try:
            return float(v)
        except Exception:
            raise FormulaError("#VALUE!")

    def _range_numbers(self, range_token):
        a, b = range_token.split(":")
        r1, c1 = parse_cell_ref(a)
        r2, c2 = parse_cell_ref(b)
        rlo, rhi = min(r1, r2), max(r1, r2)
        clo, chi = min(c1, c2), max(c1, c2)
        nums = []
        for r in range(rlo, rhi + 1):
            for c in range(clo, chi + 1):
                v = self._cell_value(r, c)
                if isinstance(v, (int, float)):
                    nums.append(float(v))
        return nums

    # ---- recursive-descent parser: expr -> term -> factor -> power -> atom ----
    def _parse_expr(self, tokens, pos):
        val = self._parse_term(tokens, pos)
        while pos[0] < len(tokens) and tokens[pos[0]].kind == "OP" and tokens[pos[0]].value in ("+", "-"):
            op = tokens[pos[0]].value
            pos[0] += 1
            rhs = self._parse_term(tokens, pos)
            val = self._as_number(val) + self._as_number(rhs) if op == "+" else self._as_number(val) - self._as_number(rhs)
        return val

    def _parse_term(self, tokens, pos):
        val = self._parse_factor(tokens, pos)
        while pos[0] < len(tokens) and tokens[pos[0]].kind == "OP" and tokens[pos[0]].value in ("*", "/"):
            op = tokens[pos[0]].value
            pos[0] += 1
            rhs = self._parse_factor(tokens, pos)
            a = self._as_number(val)
            b = self._as_number(rhs)
            if op == "*":
                val = a * b
            else:
                if b == 0:
                    raise FormulaError("#DIV/0!")
                val = a / b
        return val

    def _parse_factor(self, tokens, pos):
        if pos[0] < len(tokens) and tokens[pos[0]].kind == "OP" and tokens[pos[0]].value in ("+", "-"):
            op = tokens[pos[0]].value
            pos[0] += 1
            v = self._as_number(self._parse_factor(tokens, pos))
            return -v if op == "-" else v
        return self._parse_power(tokens, pos)

    def _parse_power(self, tokens, pos):
        base = self._parse_atom(tokens, pos)
        if pos[0] < len(tokens) and tokens[pos[0]].kind == "OP" and tokens[pos[0]].value == "^":
            pos[0] += 1
            exp = self._parse_factor(tokens, pos)
            return self._as_number(base) ** self._as_number(exp)
        return base

    def _parse_atom(self, tokens, pos):
        if pos[0] >= len(tokens):
            raise FormulaError("#ERR!")
        tok = tokens[pos[0]]
        if tok.kind == "NUM":
            pos[0] += 1
            return tok.value
        if tok.kind == "CELL":
            pos[0] += 1
            ref = parse_cell_ref(tok.value)
            if ref is None:
                raise FormulaError("#REF!")
            return self._cell_value(ref[0], ref[1])
        if tok.kind == "RANGE":
            pos[0] += 1
            nums = self._range_numbers(tok.value)
            return sum(nums) if nums else 0.0  # vùng đứng 1 mình -> coi như SUM
        if tok.kind == "FUNC":
            fname = tok.value
            pos[0] += 1  # đã ăn luôn dấu '(' lúc tokenize FUNC
            if fname not in self.FUNCS:
                raise FormulaError("#NAME?")
            args_nums = []
            raw_args = []
            if not (pos[0] < len(tokens) and tokens[pos[0]].kind == "OP" and tokens[pos[0]].value == ")"):
                while True:
                    if pos[0] < len(tokens) and tokens[pos[0]].kind == "RANGE":
                        args_nums.extend(self._range_numbers(tokens[pos[0]].value))
                        pos[0] += 1
                    else:
                        v = self._parse_expr(tokens, pos)
                        raw_args.append(v)
                        if isinstance(v, (int, float)):
                            args_nums.append(float(v))
                    if pos[0] < len(tokens) and tokens[pos[0]].kind == "OP" and tokens[pos[0]].value == ",":
                        pos[0] += 1
                        continue
                    break
            if not (pos[0] < len(tokens) and tokens[pos[0]].kind == "OP" and tokens[pos[0]].value == ")"):
                raise FormulaError("#ERR!")
            pos[0] += 1
            return self._call_func(fname, args_nums, raw_args)
        if tok.kind == "OP" and tok.value == "(":
            pos[0] += 1
            v = self._parse_expr(tokens, pos)
            if not (pos[0] < len(tokens) and tokens[pos[0]].kind == "OP" and tokens[pos[0]].value == ")"):
                raise FormulaError("#ERR!")
            pos[0] += 1
            return v
        raise FormulaError("#ERR!")

    def _call_func(self, fname, nums, raw_args):
        if fname == "SUM":
            return sum(nums) if nums else 0.0
        if fname in ("AVERAGE", "AVG"):
            return (sum(nums) / len(nums)) if nums else "#DIV/0!"
        if fname == "PRODUCT":
            p = 1.0
            for n in nums:
                p *= n
            return p if nums else 0.0
        if fname == "MIN":
            return min(nums) if nums else 0.0
        if fname == "MAX":
            return max(nums) if nums else 0.0
        if fname == "COUNT":
            return float(len(nums))
        if fname == "ROUND":
            if len(raw_args) < 1:
                raise FormulaError("#ERR!")
            x = self._as_number(raw_args[0])
            n = int(self._as_number(raw_args[1])) if len(raw_args) > 1 else 0
            return round(x, n)
        if fname == "ABS":
            if len(raw_args) < 1:
                raise FormulaError("#ERR!")
            return abs(self._as_number(raw_args[0]))
        raise FormulaError("#NAME?")


def format_value(v):
    if v is None:
        return ""
    if isinstance(v, float):
        r = round(v, ROUND_DECIMALS)
        if r == int(r):
            return str(int(r))
        return ("%." + str(ROUND_DECIMALS) + "f") % r
    return str(v)


# ------------------------------------------------------------------------
# 5. GIAO DIỆN GUI — WINFORMS "EVENTLESS", THEME TỐI SANG TRỌNG VÀNG ĐỒNG
# ------------------------------------------------------------------------
def hexcolor(h):
    h = h.lstrip("#")
    return Color.FromArgb(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


FUNC_CHOICES = [u"SUM (Tổng)", u"PRODUCT (Tích)", u"AVERAGE (Trung bình)",
                u"DIVIDE A / B (Chia, đúng 2 ô)"]
FUNC_CODES = ["SUM", "PRODUCT", "AVERAGE", "DIVIDE"]

if GUI_AVAILABLE:
    C_BG = hexcolor(THEME["bg"])
    C_PANEL = hexcolor(THEME["panel"])
    C_PANEL2 = hexcolor(THEME["panel2"])
    C_GOLD = hexcolor(THEME["gold"])
    C_GOLD_DARK = hexcolor(THEME["gold_dark"])
    C_TEXT = hexcolor(THEME["text"])
    C_TEXT_DIM = hexcolor(THEME["text_dim"])
    C_GRID_LINE = hexcolor(THEME["grid_line"])
    C_ROW_ALT = hexcolor(THEME["row_alt"])
    C_INK = Color.FromArgb(20, 20, 20)

    UI_FONT_FALLBACKS = []

    def safe_font(size=9.5, bold=False, family="Segoe UI"):
        """Tạo Font .NET an toàn. Nếu family/size gặp lỗi (đã từng gặp
        trên CPython3: System.ArgumentException 'Parameter is not valid')
        thì lùi về font hệ thống thay vì làm crash cả cửa sổ."""
        style = FontStyle.Bold if bold else FontStyle.Regular
        try:
            em = Single(float(size))
        except Exception:
            em = float(size)
        try:
            return Font(family, em, style, GraphicsUnit.Point)
        except Exception as ex1:
            UI_FONT_FALLBACKS.append("%s %.1f: %s" % (family, float(size), str(ex1)))
            try:
                return Font(SystemFonts.MessageBoxFont.FontFamily, em, style, GraphicsUnit.Point)
            except Exception:
                return SystemFonts.MessageBoxFont

    def set_font(control, size=9.5, bold=False, family="Segoe UI"):
        try:
            control.Font = safe_font(size, bold, family)
        except Exception:
            pass
        return control

    def style_button(btn, primary=False):
        btn.FlatStyle = FlatStyle.Flat
        btn.FlatAppearance.BorderSize = 1
        btn.FlatAppearance.BorderColor = C_GOLD_DARK
        btn.BackColor = C_GOLD_DARK if primary else C_PANEL2
        btn.ForeColor = C_INK if primary else C_GOLD
        set_font(btn, 9.5, True)
        return btn

    def mk_form(title, width, height):
        f = Form()
        f.Text = title
        f.Size = Size(width, height)
        f.MinimumSize = Size(min(width, 900), min(height, 560))
        f.StartPosition = FormStartPosition.CenterScreen
        f.BackColor = C_BG
        f.ForeColor = C_TEXT
        f.FormBorderStyle = FormBorderStyle.Sizable
        set_font(f, 9.5, False)
        return f

    def add_label(parent, text, x, y, w, h, color=None, bold=False, size=9.5):
        l = Label()
        l.Text = text
        l.Location = Point(x, y)
        l.Size = Size(w, h)
        l.ForeColor = color or C_TEXT
        l.BackColor = Color.Transparent
        set_font(l, size, bold)
        parent.Controls.Add(l)
        return l

    def add_textbox(parent, text, x, y, w, h=26):
        tb = TextBox()
        tb.Text = text
        tb.Location = Point(x, y)
        tb.Size = Size(w, h)
        tb.BackColor = Color.White
        tb.ForeColor = Color.Black
        set_font(tb, 9.5, False)
        parent.Controls.Add(tb)
        return tb

    def add_combo(parent, items, x, y, w, h, selected=0):
        cb = ComboBox()
        cb.Location = Point(x, y)
        cb.Size = Size(w, h)
        cb.DropDownStyle = ComboBoxStyle.DropDownList
        cb.BackColor = Color.White
        cb.ForeColor = Color.Black
        set_font(cb, 9.5, False)
        for it in items:
            cb.Items.Add(it)
        if cb.Items.Count > 0:
            cb.SelectedIndex = max(0, min(int(selected), cb.Items.Count - 1))
        parent.Controls.Add(cb)
        return cb

    def build_data_grid(x, y, w, h, n_cols, col_names):
        grid = DataGridView()
        grid.Location = Point(x, y)
        grid.Size = Size(w, h)
        grid.AllowUserToAddRows = False
        grid.AllowUserToDeleteRows = False
        grid.RowHeadersVisible = False
        grid.SelectionMode = DataGridViewSelectionMode.CellSelect
        grid.MultiSelect = True
        grid.BackgroundColor = C_BG
        grid.GridColor = C_GRID_LINE
        grid.EnableHeadersVisualStyles = False
        grid.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.DisableResizing
        grid.ColumnHeadersHeight = 32
        grid.RowTemplate.Height = 26
        grid.AutoSizeColumnsMode = getattr(DataGridViewAutoSizeColumnsMode, "None")
        grid.ColumnHeadersDefaultCellStyle.BackColor = C_PANEL2
        grid.ColumnHeadersDefaultCellStyle.ForeColor = C_GOLD
        grid.ColumnHeadersDefaultCellStyle.Font = safe_font(9.5, True)
        grid.DefaultCellStyle.BackColor = C_BG
        grid.DefaultCellStyle.ForeColor = C_TEXT
        grid.DefaultCellStyle.SelectionBackColor = C_GOLD_DARK
        grid.DefaultCellStyle.SelectionForeColor = C_INK
        grid.AlternatingRowsDefaultCellStyle.BackColor = C_ROW_ALT
        grid.AlternatingRowsDefaultCellStyle.ForeColor = C_TEXT
        set_font(grid, 9.5, False)

        idx_col = DataGridViewTextBoxColumn()
        idx_col.HeaderText = "#"
        idx_col.Width = 42
        idx_col.ReadOnly = True
        # KHÔNG cho click header để sort — nếu không, WinForms sẽ tự sắp
        # xếp lại các hàng và làm lệch hoàn toàn ánh xạ hàng/cột <-> phần
        # tử Revit (grid_elems) mà script đang theo dõi.
        idx_col.SortMode = DataGridViewColumnSortMode.NotSortable
        grid.Columns.Add(idx_col)

        col_w = max(70, min(140, int((w - 70) / max(n_cols, 1))))
        for name in col_names:
            c = DataGridViewTextBoxColumn()
            c.HeaderText = name
            c.Width = col_w
            c.SortMode = DataGridViewColumnSortMode.NotSortable
            grid.Columns.Add(c)
        return grid


def run_gui_wizard(doc_, n_rows, n_cols, grid_elems, raw_formulas, param_name_by_elem, warnings):
    """Vòng lặp GUI "eventless": mỗi lần bấm nút, cửa sổ đóng lại (nhờ
    Button.DialogResult xử lý hoàn toàn trong .NET, không cần callback
    Python), Python đọc lại dữ liệu trên lưới + DialogResult, xử lý, rồi
    dựng lại 1 cửa sổ MỚI với dữ liệu đã cập nhật — lặp lại cho tới khi
    người dùng bấm "Cập nhật vào Revit" hoặc "Hủy"."""
    col_names = [col_letter(c) for c in range(n_cols)]

    try:
        Application.EnableVisualStyles()
    except Exception:
        pass  # đã gọi rồi ở lần chạy trước trong cùng phiên Revit -> bỏ qua

    def recompute():
        engine = FormulaEngine(lambda r, c: raw_formulas.get((r, c), ""), n_rows, n_cols)
        cache = {}
        for r in range(n_rows):
            for c in range(n_cols):
                try:
                    cache[(r, c)] = engine.value_of(r, c)
                except FormulaError as fe:
                    cache[(r, c)] = fe.code
        return cache

    cache = recompute()
    status_msg = u"Sẵn sàng."
    stats_msg = u"Bôi chọn 1 vùng ô rồi bấm \"Σ Xem nhanh\" để xem SUM / AVERAGE / MIN / MAX / PRODUCT."
    dest_text = ""
    func_selected = 0
    result = {"status": "Cancelled", "updated": 0, "write_ms": 0}
    NONE_RESULT = getattr(DialogResult, "None")

    while True:
        last_displayed = {}
        for r in range(n_rows):
            for c in range(n_cols):
                last_displayed[(r, c)] = format_value(cache.get((r, c)))

        f = mk_form(u"BẢNG DỮ LIỆU GENERIC ANNOTATION — EXCEL LIVE", 1240, 780)
        cw = f.ClientSize.Width
        ch = f.ClientSize.Height

        header = Panel()
        header.Dock = DockStyle.Top
        header.Height = 54
        header.BackColor = C_PANEL
        f.Controls.Add(header)
        add_label(header, u"⬛ BẢNG DỮ LIỆU GENERIC ANNOTATION", 16, 6, 560, 26, C_GOLD, True, 14.0)
        add_label(header, u"%d hàng × %d cột — %d ô" % (n_rows, n_cols, n_rows * n_cols),
                  16, 31, 500, 20, C_TEXT_DIM, False, 9.0)
        badge = Label()
        badge.Text = u"⚡ SIÊU NHANH — 1 TRANSACTION"
        badge.Size = Size(220, 30)
        badge.Location = Point(cw - 12 - 220, 12)
        badge.TextAlign = ContentAlignment.MiddleCenter
        badge.BackColor = C_GOLD_DARK
        badge.ForeColor = C_INK
        set_font(badge, 9.0, True)
        header.Controls.Add(badge)

        add_label(f, u"Ô đích:", 12, 66, 55, 22, C_TEXT_DIM, False, 9.0)
        txt_dest = add_textbox(f, dest_text, 68, 62, 90, 26)
        add_label(f, u"Hàm:", 168, 66, 40, 22, C_TEXT_DIM, False, 9.0)
        cmb_func = add_combo(f, FUNC_CHOICES, 212, 62, 250, 26, func_selected)
        btn_insert = Button()
        btn_insert.Text = u"➕ Chèn công thức"
        btn_insert.Size = Size(160, 28)
        btn_insert.Location = Point(472, 61)
        btn_insert.DialogResult = DialogResult.Yes
        style_button(btn_insert)
        f.Controls.Add(btn_insert)
        btn_quick = Button()
        btn_quick.Text = u"Σ Xem nhanh vùng chọn"
        btn_quick.Size = Size(190, 28)
        btn_quick.Location = Point(642, 61)
        btn_quick.DialogResult = DialogResult.Ignore
        style_button(btn_quick)
        f.Controls.Add(btn_quick)

        grid_top = 100
        grid_h = max(150, ch - grid_top - 132)
        grid = build_data_grid(12, grid_top, cw - 24, grid_h, n_cols, col_names)
        for r in range(n_rows):
            ridx = grid.Rows.Add()
            row = grid.Rows[ridx]
            row.Cells[0].Value = str(r + 1)
            for c in range(n_cols):
                row.Cells[c + 1].Value = last_displayed[(r, c)]
        f.Controls.Add(grid)

        stats_y = grid_top + grid_h + 8
        add_label(f, stats_msg, 12, stats_y, cw - 24, 20, C_GOLD, True, 9.0)
        add_label(f, status_msg, 12, stats_y + 22, cw - 24, 20, C_TEXT_DIM, False, 9.0)

        by = ch - 46
        btn_cancel = Button()
        btn_cancel.Text = u"✖ Hủy"
        btn_cancel.Size = Size(110, 32)
        btn_cancel.Location = Point(cw - 12 - 110, by)
        btn_cancel.DialogResult = DialogResult.Cancel
        style_button(btn_cancel)
        f.Controls.Add(btn_cancel)
        f.CancelButton = btn_cancel

        btn_apply = Button()
        btn_apply.Text = u"✔ Cập nhật vào Revit"
        btn_apply.Size = Size(210, 34)
        btn_apply.Location = Point(btn_cancel.Location.X - 12 - 210, by - 1)
        btn_apply.DialogResult = DialogResult.OK
        style_button(btn_apply, True)
        f.Controls.Add(btn_apply)
        f.AcceptButton = btn_apply

        btn_recalc = Button()
        btn_recalc.Text = u"⟲ Tính lại"
        btn_recalc.Size = Size(120, 32)
        btn_recalc.Location = Point(btn_apply.Location.X - 12 - 120, by)
        btn_recalc.DialogResult = DialogResult.Retry
        style_button(btn_recalc)
        f.Controls.Add(btn_recalc)

        dr = f.ShowDialog()

        # ----- Đọc lại toàn bộ trạng thái control NGAY sau ShowDialog -----
        dest_text = txt_dest.Text.strip()
        func_selected = cmb_func.SelectedIndex if cmb_func.SelectedIndex >= 0 else 0

        changed_any = False
        for r in range(n_rows):
            row = grid.Rows[r]
            for c in range(n_cols):
                cell_val = row.Cells[c + 1].Value
                new_text = u"" if cell_val is None else str(cell_val)
                if new_text != last_displayed.get((r, c), u""):
                    raw_formulas[(r, c)] = new_text
                    changed_any = True
        if changed_any:
            cache = recompute()

        if dr == DialogResult.Ignore:
            sel = grid.SelectedCells
            nums = []
            count_sel = 0
            for cell in sel:
                if cell.ColumnIndex == 0:
                    continue
                count_sel += 1
                v = cache.get((cell.RowIndex, cell.ColumnIndex - 1))
                if isinstance(v, (int, float)):
                    nums.append(float(v))
            if not nums:
                stats_msg = u"Đã chọn %d ô — không có số để tính." % count_sel
            else:
                s = sum(nums)
                avg = s / len(nums)
                mn = min(nums)
                mx = max(nums)
                prod = 1.0
                for n in nums:
                    prod *= n
                stats_msg = (u"Đã chọn %d ô | SUM=%s | AVG=%s | MIN=%s | MAX=%s | PRODUCT=%s"
                             % (count_sel, format_value(s), format_value(avg),
                                format_value(mn), format_value(mx), format_value(prod)))
            status_msg = u"Sẵn sàng."
            continue

        if dr == DialogResult.Retry:
            status_msg = u"Đã tính lại toàn bộ công thức."
            continue

        if dr == DialogResult.Yes:
            sel = grid.SelectedCells
            cells = sorted(set(
                (cell.RowIndex, cell.ColumnIndex - 1) for cell in sel if cell.ColumnIndex != 0
            ))
            func_code = FUNC_CODES[func_selected] if 0 <= func_selected < len(FUNC_CODES) else "SUM"
            dest_ref = parse_cell_ref(dest_text.upper())
            if not cells:
                status_msg = u"⚠ Hãy bôi chọn 1 vùng ô trong bảng trước."
            elif dest_ref is None:
                status_msg = u"⚠ Ô đích không hợp lệ. Nhập dạng ví dụ: C5"
            elif not (0 <= dest_ref[0] < n_rows and 0 <= dest_ref[1] < n_cols):
                status_msg = u"⚠ Ô đích ngoài phạm vi bảng (%d hàng × %d cột)." % (n_rows, n_cols)
            elif func_code == "DIVIDE":
                if len(cells) != 2:
                    status_msg = u"⚠ Phép chia cần bôi chọn đúng 2 ô (đang chọn %d ô)." % len(cells)
                else:
                    (ra, ca), (rb, cb) = cells
                    r0, c0 = dest_ref
                    formula = "=%s%d/%s%d" % (col_letter(ca), ra + 1, col_letter(cb), rb + 1)
                    raw_formulas[(r0, c0)] = formula
                    cache = recompute()
                    status_msg = u"Đã chèn %s vào ô %s%d." % (formula, col_letter(c0), r0 + 1)
            else:
                rmin = min(c[0] for c in cells)
                rmax = max(c[0] for c in cells)
                cmin = min(c[1] for c in cells)
                cmax = max(c[1] for c in cells)
                r0, c0 = dest_ref
                range_str = "%s%d:%s%d" % (col_letter(cmin), rmin + 1, col_letter(cmax), rmax + 1)
                formula = "=%s(%s)" % (func_code, range_str)
                raw_formulas[(r0, c0)] = formula
                cache = recompute()
                status_msg = u"Đã chèn %s vào ô %s%d." % (formula, col_letter(c0), r0 + 1)
            continue

        if dr == DialogResult.Cancel or dr == NONE_RESULT:
            result["status"] = "Cancelled"
            break

        if dr == DialogResult.OK:
            cache = recompute()
            n_writable = sum(1 for r in range(n_rows) for c in range(n_cols) if grid_elems[r][c] is not None)
            confirm = MessageBox.Show(
                u"Sẽ ghi kết quả vào tối đa %d ô Generic Annotation trên view.\nBạn có chắc muốn cập nhật vào Revit?"
                % n_writable,
                u"Xác nhận cập nhật", MessageBoxButtons.YesNo, MessageBoxIcon.Question)
            if confirm != DialogResult.Yes:
                status_msg = u"Đã huỷ thao tác cập nhật."
                continue
            try:
                updated, write_ms = write_back(doc_, grid_elems, raw_formulas, cache, param_name_by_elem, warnings)
                result["status"] = "Updated"
                result["updated"] = updated
                result["write_ms"] = write_ms
                rate = (updated / (write_ms / 1000.0)) if write_ms > 0 and updated > 0 else 0.0
                MessageBox.Show(
                    u"Đã cập nhật %d ô vào Revit trong %d ms (~%.0f ô/giây)."
                    % (updated, write_ms, rate),
                    u"Hoàn tất — SIÊU NHANH", MessageBoxButtons.OK, MessageBoxIcon.Information)
            except Exception as ex:
                warnings.append(str(ex))
                warnings.append(traceback.format_exc())
                MessageBox.Show(u"Lỗi khi cập nhật vào Revit:\n%s" % str(ex), u"Lỗi",
                                 MessageBoxButtons.OK, MessageBoxIcon.Error)
                status_msg = u"✖ Lỗi khi cập nhật — xem chi tiết trong Warnings."
                continue
            break

        result["status"] = "Cancelled"
        break

    return result, cache


# ------------------------------------------------------------------------
# 6. GHI DỮ LIỆU NGƯỢC VÀO REVIT (WRITE-BACK, 1 TRANSACTION)
# ------------------------------------------------------------------------
def write_back(doc_, grid_elems, raw_formulas, engine_cache, param_name_by_elem, warnings):
    """Ghi các ô có thay đổi vào Revit trong đúng 1 Transaction (mỗi ô
    nằm trong 1 SubTransaction riêng, để 1 ô lỗi không huỷ các ô khác đã
    ghi thành công) — cùng kiểu Transaction/SubTransaction .NET thường,
    KHÔNG dùng TransactionManager.Instance.EnsureInTransaction, vì luồng
    chính đang bị chặn bởi Form.ShowDialog() (modal) trong lúc GUI mở,
    và Transaction .NET thường cho toàn quyền kiểm soát start/commit/
    rollback một cách tường minh, dễ dự đoán hơn.

    TỐI ƯU TỐC ĐỘ ("1s/200 ô"): chỉ những ô THỰC SỰ đổi giá trị mới được
    ghi (so sánh old_text != new_text trước khi đưa vào danh sách ghi);
    toàn bộ nằm trong ĐÚNG 1 Transaction (Revit chỉ Regenerate/rebuild đồ
    hoạ 1 lần ở cuối, không phải hàng trăm lần); tên nguồn dữ liệu mỗi
    phần tử đã được xác định sẵn từ bước quét (param_name_by_elem) nên ở
    đây chỉ còn đúng 1 lệnh LookupParameter theo tên — không dò lại danh
    sách candidate. Trả về (số ô đã ghi, thời gian ghi mili-giây) để báo
    cáo tốc độ thực tế cho người dùng, thay vì chỉ tuyên bố suông.

    Hỗ trợ cả 2 loại nguồn dữ liệu (xem CellSource): "PARAM" (ghi bằng
    Parameter.Set như bình thường) và "TYPE_NAME" (chữ nằm ở TÊN của
    FamilySymbol/Type — ghi bằng cách đổi tên Type). Vì đổi tên 1 Type sẽ
    ảnh hưởng TẤT CẢ phần tử đang dùng Type đó, script chỉ tự động đổi
    tên khi Type đó CHỈ được đúng 1 ô trong bảng tham chiếu tới — nếu 1
    Type bị nhiều ô dùng chung, các ô đó bị bỏ qua kèm cảnh báo thay vì
    đổi tên "nhầm" ảnh hưởng dây chuyền ra ngoài bảng."""
    t_start = time.time()
    n_rows = len(grid_elems)
    n_cols = len(grid_elems[0]) if n_rows else 0

    # Đếm số ô đang dùng chung mỗi Type (chỉ cần cho nguồn TYPE_NAME).
    symbol_cell_count = {}
    for r in range(n_rows):
        for c in range(n_cols):
            elem = grid_elems[r][c]
            if elem is None:
                continue
            if param_name_by_elem.get(elem.Id.IntegerValue) == TYPE_NAME_SENTINEL:
                try:
                    sid = elem.Symbol.Id.IntegerValue
                    symbol_cell_count[sid] = symbol_cell_count.get(sid, 0) + 1
                except Exception:
                    pass

    updates = []  # (elem, source, new_text)
    for r in range(n_rows):
        for c in range(n_cols):
            elem = grid_elems[r][c]
            if elem is None:
                continue
            new_text = format_value(engine_cache.get((r, c)))
            source = find_text_source(elem, param_name_by_elem.get(elem.Id.IntegerValue))
            if source is None:
                warnings.append(u"Không tìm thấy nguồn dữ liệu chữ trên phần tử Id=%s (hàng %d, cột %s)"
                                 % (elem.Id, r + 1, col_letter(c)))
                continue
            if source.kind == "TYPE_NAME":
                try:
                    sid = elem.Symbol.Id.IntegerValue
                except Exception:
                    sid = None
                if sid is not None and symbol_cell_count.get(sid, 0) > 1:
                    warnings.append(
                        u"Bỏ qua ô (hàng %d, cột %s): Type '%s' đang dùng chung cho %d ô khác nhau — "
                        u"đổi tên Type sẽ ảnh hưởng tất cả các ô đó nên không tự động ghi."
                        % (r + 1, col_letter(c), source.ref.Name, symbol_cell_count.get(sid, 0)))
                    continue
            old_text = read_source_text(source)
            if old_text != new_text:
                updates.append((elem, source, new_text))

    if not updates:
        return 0, int((time.time() - t_start) * 1000)

    # Đóng transaction "lơ lửng" của Dynamo (nếu có) trước khi tự mở 1
    # Transaction thường — tránh xung đột giữa 2 cơ chế quản lý transaction.
    if DYNAMO_ENV and TransactionManager is not None:
        try:
            TransactionManager.Instance.ForceCloseTransaction()
        except Exception:
            pass

    updated = 0
    t = Transaction(doc_, u"Cập nhật bảng Generic Annotation")
    t.Start()
    try:
        for elem, source, new_text in updates:
            st = SubTransaction(doc_)
            st.Start()
            try:
                if source.kind == "TYPE_NAME":
                    source.ref.Name = new_text
                else:
                    param = source.ref
                    if param.IsReadOnly:
                        warnings.append(u"Parameter '%s' chỉ đọc trên Id=%s — bỏ qua."
                                         % (source.name, elem.Id))
                        st.RollBack()
                        continue
                    if param.StorageType == Autodesk.Revit.DB.StorageType.String:
                        param.Set(new_text)
                    else:
                        # cố gắng ép kiểu nếu parameter là số (Double/Integer)
                        try:
                            if param.StorageType == Autodesk.Revit.DB.StorageType.Double:
                                param.Set(float(new_text))
                            elif param.StorageType == Autodesk.Revit.DB.StorageType.Integer:
                                param.Set(int(round(float(new_text))))
                            else:
                                param.Set(new_text)
                        except Exception:
                            param.Set(new_text)
                st.Commit()
                updated += 1
            except Exception as ex:
                try:
                    st.RollBack()
                except Exception:
                    pass
                warnings.append(u"Lỗi ghi Id=%s: %s" % (elem.Id, str(ex)))
        try:
            doc_.Regenerate()
        except Exception:
            pass
        t.Commit()
    except Exception:
        try:
            t.RollBack()
        except Exception:
            pass
        raise

    return updated, int((time.time() - t_start) * 1000)


# ------------------------------------------------------------------------
# 7. MAIN — ĐIỀU PHỐI TOÀN BỘ QUY TRÌNH
# ------------------------------------------------------------------------
def run(elements, schedule, forced_param_name, show_gui, row_tol, col_tol):
    t0 = time.time()
    warnings = []

    if not elements:
        return {
            "Status": "NoSelection", "UpdatedCount": 0, "TotalCells": 0,
            "Rows": 0, "Cols": 0, "Grid": [], "Warnings": [u"Chưa có phần tử nào được chọn ở IN[0]."],
            "ElapsedMs": 0,
        }

    view = active_view
    grid_elems, n_rows, n_cols, w1 = build_grid(elements, view, row_tol, col_tol)
    warnings.extend(w1)

    if n_rows == 0 or n_cols == 0:
        return {
            "Status": "Error", "UpdatedCount": 0, "TotalCells": 0,
            "Rows": 0, "Cols": 0, "Grid": [], "Warnings": warnings + [u"Không dò được lưới bảng từ vùng chọn."],
            "ElapsedMs": int((time.time() - t0) * 1000),
        }

    schedule_grid = read_schedule_grid(schedule) if schedule is not None else None

    # ----- Tự động dò nguồn dữ liệu chữ TỐT NHẤT dựa trên khảo sát thực
    # tế các phần tử đã chọn (không đoán mù) — xem detect_best_param_name.
    flat_elements = [grid_elems[r][c] for r in range(n_rows) for c in range(n_cols)
                      if grid_elems[r][c] is not None]
    auto_name, coverage, sample_n = detect_best_param_name(flat_elements, forced_param_name)
    if forced_param_name:
        warnings.append(u"Dùng đúng tên parameter đã truyền vào IN[3]: '%s'." % forced_param_name)
    elif auto_name == TYPE_NAME_SENTINEL:
        warnings.append(
            u"Không tìm thấy Parameter chữ nào có nội dung — tự động dùng TÊN TYPE (Family Type Name) "
            u"làm nguồn dữ liệu (khớp %d/%d phần tử khảo sát). Ghi ngược sẽ đổi tên Type tương ứng." % (
                int(round((coverage or 0) * sample_n)), sample_n))
    elif auto_name:
        warnings.append(u"Tự động dò được parameter chữ: '%s' (khớp %d/%d phần tử khảo sát)."
                         % (auto_name, int(round((coverage or 0) * sample_n)), sample_n))
    else:
        warnings.append(
            u"⚠ KHÔNG tìm thấy bất kỳ Parameter/Type Name nào có nội dung chữ trên các phần tử đã chọn. "
            u"Bảng sẽ mở với các ô trống — hãy kiểm tra lại family, hoặc truyền đúng tên parameter vào IN[3]."
        )

    raw_formulas = {}
    param_name_by_elem = {}
    for r in range(n_rows):
        for c in range(n_cols):
            elem = grid_elems[r][c]
            if elem is None:
                raw_formulas[(r, c)] = ""
                continue
            source = find_text_source(elem, auto_name)
            if source is not None:
                param_name_by_elem[elem.Id.IntegerValue] = source.name
            text = read_source_text(source)
            if (not text or text.strip() == "") and schedule_grid is not None:
                if r < len(schedule_grid) and c < len(schedule_grid[r]):
                    text = schedule_grid[r][c]
            raw_formulas[(r, c)] = text

    if not show_gui:
        engine = FormulaEngine(lambda r, c: raw_formulas.get((r, c), ""), n_rows, n_cols)
        cache = {}
        for r in range(n_rows):
            for c in range(n_cols):
                cache[(r, c)] = engine.value_of(r, c)
        updated, write_ms = write_back(doc, grid_elems, raw_formulas, cache, param_name_by_elem, warnings)
        out_grid = [[format_value(cache.get((r, c))) for c in range(n_cols)] for r in range(n_rows)]
        return {
            "Status": "Updated", "UpdatedCount": updated, "TotalCells": n_rows * n_cols,
            "Rows": n_rows, "Cols": n_cols, "Grid": out_grid, "Warnings": warnings,
            "ElapsedMs": int((time.time() - t0) * 1000),
            "WriteMs": write_ms,
            "CellsPerSecond": round(updated / (write_ms / 1000.0), 1) if write_ms > 0 and updated > 0 else 0,
        }

    # ---------------- GUI MODE ----------------
    if not GUI_AVAILABLE:
        return {
            "Status": "Error", "UpdatedCount": 0, "TotalCells": n_rows * n_cols,
            "Rows": n_rows, "Cols": n_cols, "Grid": [],
            "Warnings": warnings + [u"Không nạp được WinForms GUI: %s" % GUI_IMPORT_ERROR],
            "ElapsedMs": int((time.time() - t0) * 1000),
            "WriteMs": 0, "CellsPerSecond": 0,
        }

    if auto_name is None and not forced_param_name:
        try:
            MessageBox.Show(
                u"Không tìm thấy Parameter hoặc Type Name nào có nội dung chữ trên %d phần tử đã chọn.\n\n"
                u"Bảng sẽ mở với các ô trống để bạn tự điền, hoặc bấm Hủy rồi truyền đúng tên parameter "
                u"vào IN[3] của node Python Script." % len(flat_elements),
                u"Không tìm thấy dữ liệu chữ", MessageBoxButtons.OK, MessageBoxIcon.Warning)
        except Exception:
            pass

    gui_result, cache = run_gui_wizard(doc, n_rows, n_cols, grid_elems, raw_formulas, param_name_by_elem, warnings)

    out_grid = [[format_value(cache.get((r, c))) for c in range(n_cols)] for r in range(n_rows)]
    write_ms = gui_result.get("write_ms", 0)
    updated = gui_result["updated"]
    return {
        "Status": gui_result["status"],
        "UpdatedCount": updated,
        "TotalCells": n_rows * n_cols,
        "Rows": n_rows, "Cols": n_cols,
        "Grid": out_grid, "Warnings": warnings,
        "ElapsedMs": int((time.time() - t0) * 1000),
        "WriteMs": write_ms,
        "CellsPerSecond": round(updated / (write_ms / 1000.0), 1) if write_ms > 0 and updated > 0 else 0,
    }


# ------------------------------------------------------------------------
# 8. DYNAMO IN / OUT
# ------------------------------------------------------------------------
def _get_in(index, default=None):
    try:
        return IN[index]
    except Exception:
        return default


try:
    _raw_in0 = _get_in(0, [])
    # Chuẩn hoá IN[0] về list Python — KHÔNG dùng isinstance(x, list) vì
    # tuỳ engine/phiên bản Dynamo, "Select Model Elements" (chọn nhiều) có
    # thể trả về 1 list .NET (IEnumerable) chứ không phải list Python
    # thật; isinstance sẽ sai và bọc nhầm CẢ danh sách thành 1 phần tử.
    # Cách an toàn: thử duyệt (list(...)) — nếu không duyệt được (đúng là
    # 1 phần tử đơn lẻ) thì mới bọc thành list 1 phần tử.
    if _raw_in0 is None:
        _raw_elements = []
    elif isinstance(_raw_in0, (list, tuple)):
        _raw_elements = list(_raw_in0)
    else:
        try:
            _raw_elements = list(_raw_in0)
        except TypeError:
            _raw_elements = [_raw_in0]

    # Dynamo có thể bọc phần tử qua .NET wrapper (Revit.Elements.Element)
    # -> lấy về đối tượng RevitAPI thật (thuộc tính InternalElement)
    _elements = []
    for _e in _raw_elements:
        if _e is None:
            continue
        _elements.append(_e.InternalElement if hasattr(_e, "InternalElement") else _e)

    # IN[1]: nút bảo vệ chạy/không chạy (Boolean) — đúng kiểu bạn đã quen
    # dùng (nối 1 node Boolean True/False). False -> KHÔNG làm gì cả (an
    # toàn tuyệt đối, không đụng tới Revit); True/không nối -> chạy đầy đủ.
    _run_guard = _get_in(1, True)
    if _run_guard is None:
        _run_guard = True

    if not _run_guard:
        OUT = {
            "Status": "Idle", "UpdatedCount": 0, "TotalCells": 0,
            "Rows": 0, "Cols": 0, "Grid": [],
            "Warnings": [u"IN[1] = False — script tạm dừng, chưa xử lý gì. Đặt lại True để chạy."],
            "ElapsedMs": 0,
        }
    else:
        _schedule_in = _get_in(2, None)
        _schedule = None
        if _schedule_in is not None:
            _schedule = _schedule_in.InternalElement if hasattr(_schedule_in, "InternalElement") else _schedule_in

        _param_name = _get_in(3, None)
        if isinstance(_param_name, str) and _param_name.strip() == "":
            _param_name = None

        _row_tol = _get_in(4, None)
        _col_tol = _get_in(5, None)

        # IN[6] (nâng cao, hiếm dùng): True -> bỏ qua GUI, tự tính và ghi
        # thẳng vào Revit (không cho xem/chỉnh trước). Mặc định False —
        # LUÔN mở GUI để bạn xem và chỉnh trước khi ghi, đúng như yêu cầu.
        _headless = _get_in(6, False)
        if _headless is None:
            _headless = False
        _show_gui = not _headless

        OUT = run(_elements, _schedule, _param_name, _show_gui, _row_tol, _col_tol)
except Exception as _ex:
    OUT = {
        "Status": "Error", "UpdatedCount": 0, "TotalCells": 0,
        "Rows": 0, "Cols": 0, "Grid": [],
        "Warnings": [str(_ex), traceback.format_exc()],
        "ElapsedMs": 0,
    }
