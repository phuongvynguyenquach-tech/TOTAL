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
  5. Mở GIAO DIỆN GUI (WPF, theme tối sang trọng – vàng đồng "chuẩn men")
     giống một bảng Excel: xem, sửa, chọn vùng để xem SUM/AVERAGE/MIN/MAX/
     PRODUCT tức thời (thanh trạng thái kiểu Excel), chèn công thức
     =SUM(...) / =PRODUCT(...) / =A/B vào ô đích, công thức tự tính lại
     mỗi khi có ô nguồn thay đổi (giống Excel thật).
  6. Khi bấm "Cập nhật vào Revit": ghi toàn bộ giá trị đã tính vào lại
     đúng parameter chữ của từng Generic Annotation tương ứng, TRONG 1
     TRANSACTION DUY NHẤT (siêu nhanh — không mở/đóng transaction theo
     từng ô), rồi cập nhật ngay trên view Revit.

CÁCH DÙNG TRONG DYNAMO:
  - Node "Select Model Elements" (chọn nhiều) -> nối vào IN[0].
    (Bạn quét chọn toàn bộ các Generic Annotation tạo nên bảng trên view.)
  - (Tuỳ chọn) Node trả về 1 ViewSchedule -> nối vào IN[1]. Để trống nếu
    không cần đối chiếu Schedule.
  - IN[2]: tên Parameter chứa chữ hiển thị trên annotation (vd "Text",
    "文字", "Label"...). Để trống (None / "") để script tự dò theo danh
    sách CANDIDATE_PARAM_NAMES bên dưới.
  - IN[3]: True/False — có mở GUI hay không (mặc định True).
  - IN[4], IN[5] (tuỳ chọn, có thể để None): dung sai gom hàng / gom cột
    theo đơn vị nội bộ Revit (feet). Để None để script tự tính.

  Chọn ENGINE của node Python Script này là "CPython3" (Dynamo cho phép
  đổi engine bằng cách click chuột phải vào node -> Change Engine).

OUT:
  Một Dictionary gồm:
    "Status"        : "Updated" / "Cancelled" / "NoSelection" / "Error"
    "UpdatedCount"  : số ô đã ghi vào Revit
    "TotalCells"    : tổng số ô nhận diện được trong bảng
    "Rows", "Cols"  : kích thước lưới nhận diện được
    "Grid"          : lưới giá trị cuối cùng (list các list string)
    "Warnings"      : danh sách cảnh báo/lỗi (nếu có) trong quá trình chạy
    "ElapsedMs"     : thời gian xử lý (mili-giây)

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
    XYZ, Transaction, BuiltInParameter,
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

clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
clr.AddReference('System.Xaml')
clr.AddReference('System.Data')
clr.AddReference('System.Xml')

import System
from System import String, Action
from System.IO import StringReader
from System.Xml import XmlReader
from System.Windows.Markup import XamlReader
from System.Windows.Threading import DispatcherPriority
from System.Data import DataTable, DataColumn
from System.Windows.Controls import DataGridTextColumn
from System.Windows.Data import Binding

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
    để việc gom cụm hàng/cột không phụ thuộc vào view bị xoay."""
    origin = view.Origin
    vec = pt - origin
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
        p = get_location_point(e, view)
        if p is None:
            warnings.append(u"Bỏ qua 1 phần tử không xác định được toạ độ (Id=%s)" % getattr(e, "Id", "?"))
            continue
        valid_elems.append(e)
        pts.append(to_uv(view, p))

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

    return grid_elems, n_rows, n_cols, warnings


# ------------------------------------------------------------------------
# 3. ĐỌC PARAMETER TRÊN ANNOTATION / ĐỌC SCHEDULE
# ------------------------------------------------------------------------
def find_text_parameter(elem, forced_name=None):
    """Trả về (Parameter, tên_đang_dùng) đầu tiên phù hợp để đọc/ghi chữ."""
    if forced_name:
        p = elem.LookupParameter(forced_name)
        if p is not None:
            return p, forced_name
    for name in CANDIDATE_PARAM_NAMES:
        p = elem.LookupParameter(name)
        if p is not None:
            return p, name
    # fallback cuối: BuiltInParameter ALL_MODEL_INSTANCE_COMMENTS (ít dùng
    # cho annotation nhưng để tránh trắng tay nếu family dùng comment)
    try:
        p = elem.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if p is not None:
            return p, "Comments"
    except Exception:
        pass
    return None, None


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
# 5. GIAO DIỆN GUI — WPF, THEME TỐI SANG TRỌNG VÀNG ĐỒNG
# ------------------------------------------------------------------------
XAML = u"""
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="BẢNG DỮ LIỆU GENERIC ANNOTATION — EXCEL LIVE"
        Width="1240" Height="760" MinWidth="900" MinHeight="500"
        WindowStartupLocation="CenterScreen"
        Background="{bg}" FontFamily="Segoe UI" ResizeMode="CanResizeWithGrip">
  <Window.Resources>
    <SolidColorBrush x:Key="Gold" Color="{gold}"/>
    <SolidColorBrush x:Key="GoldDark" Color="{gold_dark}"/>
    <SolidColorBrush x:Key="PanelBrush" Color="{panel}"/>
    <SolidColorBrush x:Key="Panel2Brush" Color="{panel2}"/>
    <SolidColorBrush x:Key="TextBrush" Color="{text}"/>
    <SolidColorBrush x:Key="TextDimBrush" Color="{text_dim}"/>
    <SolidColorBrush x:Key="GridLineBrush" Color="{grid_line}"/>
    <SolidColorBrush x:Key="RowAltBrush" Color="{row_alt}"/>

    <Style x:Key="GoldButton" TargetType="Button">
      <Setter Property="Background" Value="{panel2}"/>
      <Setter Property="Foreground" Value="{gold}"/>
      <Setter Property="BorderBrush" Value="{gold_dark}"/>
      <Setter Property="BorderThickness" Value="1"/>
      <Setter Property="Padding" Value="14,7"/>
      <Setter Property="Margin" Value="4,0"/>
      <Setter Property="FontWeight" Value="SemiBold"/>
      <Setter Property="Cursor" Value="Hand"/>
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="Button">
            <Border x:Name="bd" Background="{{TemplateBinding Background}}"
                    BorderBrush="{{TemplateBinding BorderBrush}}"
                    BorderThickness="{{TemplateBinding BorderThickness}}"
                    CornerRadius="6">
              <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"
                                 Margin="{{TemplateBinding Padding}}"/>
            </Border>
            <ControlTemplate.Triggers>
              <Trigger Property="IsMouseOver" Value="True">
                <Setter TargetName="bd" Property="Background" Value="{gold_dark}"/>
                <Setter Property="Foreground" Value="#141414"/>
              </Trigger>
              <Trigger Property="IsPressed" Value="True">
                <Setter TargetName="bd" Property="Background" Value="{gold}"/>
              </Trigger>
            </ControlTemplate.Triggers>
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>

    <Style x:Key="PrimaryButton" TargetType="Button" BasedOn="{{StaticResource GoldButton}}">
      <Setter Property="Background" Value="{gold_dark}"/>
      <Setter Property="Foreground" Value="#141414"/>
      <Setter Property="FontWeight" Value="Bold"/>
    </Style>
  </Window.Resources>

  <Grid>
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="*"/>
      <RowDefinition Height="Auto"/>
    </Grid.RowDefinitions>

    <!-- TOOLBAR -->
    <Border Grid.Row="0" Background="{panel}" BorderBrush="{gold_dark}" BorderThickness="0,0,0,1">
      <DockPanel Margin="12,10,12,10">
        <TextBlock DockPanel.Dock="Left" Text="⬛ BẢNG DỮ LIỆU GENERIC ANNOTATION"
                   Foreground="{gold}" FontSize="16" FontWeight="Bold" VerticalAlignment="Center"/>
        <StackPanel Orientation="Horizontal" DockPanel.Dock="Right" HorizontalAlignment="Right">
          <Button x:Name="BtnRecalc" Content="⟲ Tính lại" Style="{{StaticResource GoldButton}}"/>
          <Button x:Name="BtnApply" Content="✔ Cập nhật vào Revit" Style="{{StaticResource PrimaryButton}}"/>
          <Button x:Name="BtnCancel" Content="✖ Hủy" Style="{{StaticResource GoldButton}}"/>
        </StackPanel>
        <TextBlock x:Name="TxtGridInfo" Text="" Foreground="{text_dim}" FontSize="12"
                    VerticalAlignment="Center" Margin="20,0,0,0"/>
      </DockPanel>
    </Border>

    <!-- FORMULA BAR -->
    <Border Grid.Row="1" Background="{panel2}" BorderBrush="{grid_line}" BorderThickness="0,0,0,1">
      <Grid Margin="12,8,12,8">
        <Grid.ColumnDefinitions>
          <ColumnDefinition Width="Auto"/>
          <ColumnDefinition Width="240"/>
          <ColumnDefinition Width="Auto"/>
          <ColumnDefinition Width="*"/>
        </Grid.ColumnDefinitions>
        <TextBlock Grid.Column="0" Text="Ô đích:" Foreground="{text_dim}" VerticalAlignment="Center" Margin="0,0,8,0"/>
        <TextBox x:Name="TxtDestCell" Grid.Column="1" Height="28" VerticalContentAlignment="Center"
                 Background="{bg}" Foreground="{text}" BorderBrush="{gold_dark}" Padding="6,0"
                 ToolTip="Nhập ô đích (vd: C5), rồi bấm 1 trong 3 nút bên phải để chèn công thức từ vùng đang bôi chọn trong bảng."/>
        <StackPanel Grid.Column="2" Orientation="Horizontal" Margin="10,0,0,0">
          <Button x:Name="BtnInsertSum" Content="Σ SUM" Style="{{StaticResource GoldButton}}"/>
          <Button x:Name="BtnInsertProduct" Content="× PRODUCT" Style="{{StaticResource GoldButton}}"/>
          <Button x:Name="BtnInsertAverage" Content="⌀ AVERAGE" Style="{{StaticResource GoldButton}}"/>
          <Button x:Name="BtnInsertDivide" Content="÷ A / B" Style="{{StaticResource GoldButton}}"/>
        </StackPanel>
        <TextBlock x:Name="TxtStats" Grid.Column="3" Text="Chọn ô trong bảng để xem SUM / AVERAGE / MIN / MAX / PRODUCT..."
                   Foreground="{gold}" FontSize="12" VerticalAlignment="Center" HorizontalAlignment="Right"/>
      </Grid>
    </Border>

    <!-- DATAGRID -->
    <Border Grid.Row="2" Background="{bg}" Margin="12,10,12,6" BorderBrush="{grid_line}" BorderThickness="1">
      <DataGrid x:Name="GridMain"
                Background="{bg}" Foreground="{text}"
                RowBackground="{bg}" AlternatingRowBackground="{row_alt}"
                GridLinesVisibility="All" HorizontalGridLinesBrush="{grid_line}" VerticalGridLinesBrush="{grid_line}"
                BorderThickness="0" AutoGenerateColumns="False"
                CanUserAddRows="False" CanUserDeleteRows="False" CanUserSortColumns="False"
                SelectionUnit="Cell" SelectionMode="Extended"
                HeadersVisibility="Column" RowHeaderWidth="0"
                FontSize="13" ClipboardCopyMode="ExcludeHeader">
        <DataGrid.ColumnHeaderStyle>
          <Style TargetType="DataGridColumnHeader">
            <Setter Property="Background" Value="{panel2}"/>
            <Setter Property="Foreground" Value="{gold}"/>
            <Setter Property="FontWeight" Value="Bold"/>
            <Setter Property="Padding" Value="6,6"/>
            <Setter Property="BorderBrush" Value="{gold_dark}"/>
            <Setter Property="BorderThickness" Value="0,0,1,2"/>
          </Style>
        </DataGrid.ColumnHeaderStyle>
        <DataGrid.CellStyle>
          <Style TargetType="DataGridCell">
            <Setter Property="Padding" Value="6,4"/>
            <Setter Property="BorderThickness" Value="0"/>
            <Style.Triggers>
              <Trigger Property="IsSelected" Value="True">
                <Setter Property="Background" Value="{gold_dark}"/>
                <Setter Property="Foreground" Value="#141414"/>
              </Trigger>
            </Style.Triggers>
          </Style>
        </DataGrid.CellStyle>
      </DataGrid>
    </Border>

    <!-- LOG / STATUS -->
    <Border Grid.Row="3" Background="{panel}" BorderBrush="{gold_dark}" BorderThickness="0,1,0,0">
      <Grid Margin="12,6,12,6">
        <TextBlock x:Name="TxtStatus" Text="Sẵn sàng." Foreground="{text_dim}" FontSize="12" VerticalAlignment="Center"/>
      </Grid>
    </Border>
  </Grid>
</Window>
"""


def build_xaml():
    xaml = XAML
    for key, value in THEME.items():
        xaml = xaml.replace("{%s}" % key, value)
    return xaml


def load_window():
    xaml = build_xaml()
    reader = XmlReader.Create(StringReader(xaml))
    window = XamlReader.Load(reader)
    return window


def find_name(root, name):
    return root.FindName(name)


# ------------------------------------------------------------------------
# 6. GHI DỮ LIỆU NGƯỢC VÀO REVIT (WRITE-BACK, 1 TRANSACTION)
# ------------------------------------------------------------------------
def write_back(grid_elems, raw_formulas, engine_cache, param_name_by_elem, warnings):
    """Ghi các ô có thay đổi vào Revit trong đúng 1 transaction."""
    updates = []  # (elem, param_name, new_text, old_text)
    n_rows = len(grid_elems)
    n_cols = len(grid_elems[0]) if n_rows else 0
    for r in range(n_rows):
        for c in range(n_cols):
            elem = grid_elems[r][c]
            if elem is None:
                continue
            new_val = engine_cache.get((r, c))
            new_text = format_value(new_val)
            param, pname = find_text_parameter(elem, param_name_by_elem.get(elem.Id.IntegerValue))
            if param is None:
                warnings.append(u"Không tìm thấy parameter chữ trên phần tử Id=%s (hàng %d, cột %s)"
                                 % (elem.Id, r + 1, col_letter(c)))
                continue
            old_text = read_cell_text(param)
            if old_text != new_text:
                updates.append((elem, param, pname, new_text, old_text))

    if not updates:
        return 0

    if DYNAMO_ENV:
        TransactionManager.Instance.EnsureInTransaction(doc)
    else:
        t = Transaction(doc, u"Cập nhật bảng Generic Annotation")
        t.Start()

    updated = 0
    for elem, param, pname, new_text, old_text in updates:
        try:
            if param.IsReadOnly:
                warnings.append(u"Parameter '%s' chỉ đọc trên Id=%s — bỏ qua." % (pname, elem.Id))
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
            updated += 1
        except Exception as ex:
            warnings.append(u"Lỗi ghi Id=%s: %s" % (elem.Id, str(ex)))

    if DYNAMO_ENV:
        TransactionManager.Instance.TransactionTaskDone()
    else:
        t.Commit()

    return updated


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

    raw_formulas = {}
    param_name_by_elem = {}
    for r in range(n_rows):
        for c in range(n_cols):
            elem = grid_elems[r][c]
            if elem is None:
                raw_formulas[(r, c)] = ""
                continue
            param, pname = find_text_parameter(elem, forced_param_name)
            if pname:
                param_name_by_elem[elem.Id.IntegerValue] = pname
            text = read_cell_text(param)
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
        updated = write_back(grid_elems, raw_formulas, cache, param_name_by_elem, warnings)
        out_grid = [[format_value(cache.get((r, c))) for c in range(n_cols)] for r in range(n_rows)]
        return {
            "Status": "Updated", "UpdatedCount": updated, "TotalCells": n_rows * n_cols,
            "Rows": n_rows, "Cols": n_cols, "Grid": out_grid, "Warnings": warnings,
            "ElapsedMs": int((time.time() - t0) * 1000),
        }

    # ---------------- GUI MODE ----------------
    result_holder = {"status": "Cancelled", "updated": 0}

    window = load_window()
    grid_ui = find_name(window, "GridMain")
    txt_status = find_name(window, "TxtStatus")
    txt_stats = find_name(window, "TxtStats")
    txt_grid_info = find_name(window, "TxtGridInfo")
    txt_dest = find_name(window, "TxtDestCell")
    btn_recalc = find_name(window, "BtnRecalc")
    btn_apply = find_name(window, "BtnApply")
    btn_cancel = find_name(window, "BtnCancel")
    btn_sum = find_name(window, "BtnInsertSum")
    btn_product = find_name(window, "BtnInsertProduct")
    btn_average = find_name(window, "BtnInsertAverage")
    btn_divide = find_name(window, "BtnInsertDivide")

    txt_grid_info.Text = u"%d hàng × %d cột — %d ô" % (n_rows, n_cols, n_rows * n_cols)

    # ----- Dựng DataTable (nguồn hiển thị) -----
    dt = DataTable()
    idx_col = DataColumn("#", System.Int32)
    dt.Columns.Add(idx_col)
    col_names = [col_letter(c) for c in range(n_cols)]
    for name in col_names:
        dt.Columns.Add(DataColumn(name, String))

    for r in range(n_rows):
        row = dt.NewRow()
        row["#"] = r + 1
        for c in range(n_cols):
            row[col_names[c]] = ""
        dt.Rows.Add(row)

    grid_ui.ItemsSource = dt.DefaultView

    # cột "#" (không cho sửa)
    idx_dgc = DataGridTextColumn()
    idx_dgc.Header = "#"
    idx_dgc.Binding = Binding("[#]")
    idx_dgc.IsReadOnly = True
    idx_dgc.Width = 42
    grid_ui.Columns.Add(idx_dgc)

    for name in col_names:
        dgc = DataGridTextColumn()
        dgc.Header = name
        dgc.Binding = Binding("[%s]" % name)
        dgc.Width = 110
        dgc.SortMemberPath = name
        grid_ui.Columns.Add(dgc)

    last_cache = {}

    def get_raw(r, c):
        return raw_formulas.get((r, c), "")

    def recalc_all(*_args):
        engine = FormulaEngine(get_raw, n_rows, n_cols)
        cache = {}
        for rr in range(n_rows):
            for cc in range(n_cols):
                try:
                    cache[(rr, cc)] = engine.value_of(rr, cc)
                except FormulaError as fe:
                    cache[(rr, cc)] = fe.code
        last_cache.clear()
        last_cache.update(cache)
        for rr in range(n_rows):
            row = dt.Rows[rr]
            for cc in range(n_cols):
                new_disp = format_value(cache.get((rr, cc)))
                if str(row[col_names[cc]]) != new_disp:
                    row[col_names[cc]] = new_disp
        update_stats()

    def update_stats(*_args):
        try:
            sel_cells = grid_ui.SelectedCells
            nums = []
            count_sel = 0
            for sc in sel_cells:
                col_name = sc.Column.SortMemberPath
                if not col_name:
                    continue
                row_view = sc.Item
                try:
                    r = dt.Rows.IndexOf(row_view.Row)
                except Exception:
                    continue
                c = col_index(col_name)
                count_sel += 1
                v = last_cache.get((r, c))
                if isinstance(v, (int, float)):
                    nums.append(float(v))
            if not nums:
                txt_stats.Text = u"Đã chọn: %d ô — (không có số để tính)" % count_sel
                return
            s = sum(nums)
            avg = s / len(nums)
            mn = min(nums)
            mx = max(nums)
            prod = 1.0
            for n in nums:
                prod *= n
            txt_stats.Text = (u"Đã chọn: %d ô | SUM=%s | AVG=%s | MIN=%s | MAX=%s | PRODUCT=%s"
                               % (count_sel, format_value(s), format_value(avg),
                                  format_value(mn), format_value(mx), format_value(prod)))
        except Exception:
            pass

    def current_selection_range():
        sel_cells = grid_ui.SelectedCells
        rows_cols = []
        for sc in sel_cells:
            col_name = sc.Column.SortMemberPath
            if not col_name:
                continue
            row_view = sc.Item
            try:
                r = dt.Rows.IndexOf(row_view.Row)
            except Exception:
                continue
            c = col_index(col_name)
            rows_cols.append((r, c))
        if not rows_cols:
            return None
        rmin = min(x[0] for x in rows_cols)
        rmax = max(x[0] for x in rows_cols)
        cmin = min(x[1] for x in rows_cols)
        cmax = max(x[1] for x in rows_cols)
        return (rmin, cmin, rmax, cmax), sorted(rows_cols)

    def dest_cell_index():
        text = txt_dest.Text.strip().upper()
        ref = parse_cell_ref(text)
        if ref is None:
            txt_status.Text = u"⚠ Ô đích không hợp lệ. Nhập dạng ví dụ: C5"
            return None
        r, c = ref
        if r < 0 or r >= n_rows or c < 0 or c >= n_cols:
            txt_status.Text = u"⚠ Ô đích ngoài phạm vi bảng (%d hàng × %d cột)." % (n_rows, n_cols)
            return None
        return r, c

    def insert_formula(func_name):
        rng = current_selection_range()
        if rng is None:
            txt_status.Text = u"⚠ Hãy bôi chọn 1 vùng ô trong bảng trước."
            return
        (rmin, cmin, rmax, cmax), _cells = rng
        dest = dest_cell_index()
        if dest is None:
            return
        r0, c0 = dest
        range_str = "%s%d:%s%d" % (col_letter(cmin), rmin + 1, col_letter(cmax), rmax + 1)
        formula = "=%s(%s)" % (func_name, range_str)
        raw_formulas[(r0, c0)] = formula
        txt_status.Text = u"Đã chèn %s vào ô %s%d." % (formula, col_letter(c0), r0 + 1)
        recalc_all()

    def insert_divide(*_args):
        rng = current_selection_range()
        if rng is None:
            txt_status.Text = u"⚠ Hãy bôi chọn đúng 2 ô (A và B) trước."
            return
        _bbox, cells = rng
        if len(cells) != 2:
            txt_status.Text = u"⚠ Phép chia cần bôi chọn đúng 2 ô (đang chọn %d ô)." % len(cells)
            return
        dest = dest_cell_index()
        if dest is None:
            return
        r0, c0 = dest
        (ra, ca), (rb, cb) = cells
        formula = "=%s%d/%s%d" % (col_letter(ca), ra + 1, col_letter(cb), rb + 1)
        raw_formulas[(r0, c0)] = formula
        txt_status.Text = u"Đã chèn %s vào ô %s%d." % (formula, col_letter(c0), r0 + 1)
        recalc_all()

    def on_beginning_edit(sender, e):
        try:
            col_name = e.Column.SortMemberPath
            if not col_name:
                return
            row_view = e.Row.Item
            data_row = row_view.Row
            r = dt.Rows.IndexOf(data_row)
            c = col_index(col_name)
            raw = raw_formulas.get((r, c), "")
            data_row[col_name] = raw
        except Exception as ex:
            txt_status.Text = u"Lỗi BeginningEdit: %s" % str(ex)

    def on_cell_edit_ending(sender, e):
        try:
            if str(e.EditAction) != "Commit":
                return
            col_name = e.Column.SortMemberPath
            if not col_name:
                return
            row_view = e.Row.Item
            data_row = row_view.Row
            r = dt.Rows.IndexOf(data_row)
            c = col_index(col_name)
            editing_element = e.EditingElement
            new_text = editing_element.Text if hasattr(editing_element, "Text") else ""
            raw_formulas[(r, c)] = new_text

            def deferred():
                recalc_all()
            window.Dispatcher.BeginInvoke(DispatcherPriority.Background, Action(deferred))
        except Exception as ex:
            txt_status.Text = u"Lỗi CellEditEnding: %s" % str(ex)

    def on_apply(sender, e):
        try:
            recalc_all()
            n_changed = 0
            for r in range(n_rows):
                for c in range(n_cols):
                    if grid_elems[r][c] is not None:
                        n_changed += 1
            txt_status.Text = u"Đang ghi vào Revit..."
            updated = write_back(grid_elems, raw_formulas, last_cache, param_name_by_elem, warnings)
            result_holder["status"] = "Updated"
            result_holder["updated"] = updated
            txt_status.Text = u"✔ Đã cập nhật %d ô vào Revit." % updated
            window.DialogResult = True
            window.Close()
        except Exception as ex:
            txt_status.Text = u"✖ Lỗi khi cập nhật: %s" % str(ex)
            warnings.append(traceback.format_exc())

    def on_cancel(sender, e):
        result_holder["status"] = "Cancelled"
        window.DialogResult = False
        window.Close()

    grid_ui.add_BeginningEdit(on_beginning_edit)
    grid_ui.add_CellEditEnding(on_cell_edit_ending)
    grid_ui.add_SelectedCellsChanged(update_stats)
    btn_recalc.add_Click(recalc_all)
    btn_apply.add_Click(on_apply)
    btn_cancel.add_Click(on_cancel)
    btn_sum.add_Click(lambda s, e: insert_formula("SUM"))
    btn_product.add_Click(lambda s, e: insert_formula("PRODUCT"))
    btn_average.add_Click(lambda s, e: insert_formula("AVERAGE"))
    btn_divide.add_Click(insert_divide)

    recalc_all()
    window.ShowDialog()

    out_grid = [[format_value(last_cache.get((r, c))) for c in range(n_cols)] for r in range(n_rows)]
    return {
        "Status": result_holder["status"],
        "UpdatedCount": result_holder["updated"],
        "TotalCells": n_rows * n_cols,
        "Rows": n_rows, "Cols": n_cols,
        "Grid": out_grid, "Warnings": warnings,
        "ElapsedMs": int((time.time() - t0) * 1000),
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
    _raw_elements = _get_in(0, [])
    if not isinstance(_raw_elements, list):
        _raw_elements = [_raw_elements] if _raw_elements is not None else []
    # Dynamo có thể bọc phần tử qua .NET wrapper (Revit.Elements.Element)
    # -> lấy về đối tượng RevitAPI thật (thuộc tính InternalElement)
    _elements = []
    for _e in _raw_elements:
        if _e is None:
            continue
        _elements.append(_e.InternalElement if hasattr(_e, "InternalElement") else _e)

    _schedule_in = _get_in(1, None)
    _schedule = None
    if _schedule_in is not None:
        _schedule = _schedule_in.InternalElement if hasattr(_schedule_in, "InternalElement") else _schedule_in

    _param_name = _get_in(2, None)
    if isinstance(_param_name, str) and _param_name.strip() == "":
        _param_name = None

    _show_gui = _get_in(3, True)
    if _show_gui is None:
        _show_gui = True

    _row_tol = _get_in(4, None)
    _col_tol = _get_in(5, None)

    OUT = run(_elements, _schedule, _param_name, _show_gui, _row_tol, _col_tol)
except Exception as _ex:
    OUT = {
        "Status": "Error", "UpdatedCount": 0, "TotalCells": 0,
        "Rows": 0, "Cols": 0, "Grid": [],
        "Warnings": [str(_ex), traceback.format_exc()],
        "ElapsedMs": 0,
    }
