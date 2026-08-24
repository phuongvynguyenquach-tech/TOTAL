# -*- coding: utf-8 -*-
"""
Kiểm thử NGOÀI Revit cho các phần logic thuần Python của
ScanGenericAnnotationTable.py: dò lưới hàng/cột (clustering), bộ tính
công thức (FormulaEngine: SUM/AVERAGE/PRODUCT/MIN/MAX/COUNT/ROUND/ABS,
tham chiếu ô, vùng, công thức lồng nhau), và các hàm tiện ích
(col_letter/col_index/format_value).

Vì môi trường này không có Revit/Dynamo/pythonnet, các module .NET
(clr, Autodesk, RevitServices, System.*) được "giả lập" (mock) tối
thiểu trước khi import file script, để chỉ riêng phần LOGIC THUẦN
PYTHON (không đụng Revit API / WinForms) được nạp và kiểm thử thật.

Chạy:  python3 RevitDynamoTable/tests/test_core_logic.py
"""
import sys
import os
import types
import unittest


def _install_fake_revit_modules():
    """Tạo các module giả tối thiểu để file script import được, mà
    không cần Revit/Dynamo/pythonnet thật."""

    def fake_module(name):
        m = types.ModuleType(name)
        sys.modules[name] = m
        return m

    # clr.AddReference(...) -> no-op
    clr = fake_module("clr")
    clr.AddReference = lambda *a, **k: None

    # Autodesk.Revit.DB.* — chỉ cần các tên được import ở đầu file
    autodesk = fake_module("Autodesk")
    revit = fake_module("Autodesk.Revit")
    db = fake_module("Autodesk.Revit.DB")
    autodesk.Revit = revit
    revit.DB = db

    class _Dummy(object):
        def __init__(self, *a, **k):
            pass

    db.XYZ = _Dummy
    db.Transaction = _Dummy
    db.SubTransaction = _Dummy
    db.BuiltInParameter = types.SimpleNamespace(ALL_MODEL_INSTANCE_COMMENTS=1)
    db.SectionType = types.SimpleNamespace(Body=0)
    db.StorageType = types.SimpleNamespace(String=1, Double=2, Integer=3, ElementId=4, none=0)
    db.TextNote = type("TextNote", (object,), {})

    # RevitServices — cố tình để KHÔNG import được, script sẽ tự set
    # DYNAMO_ENV = False và dùng nhánh Transaction thường (đã có sẵn
    # try/except trong script cho trường hợp này) -> không cần giả lập.

    # System.Windows.Forms / System.Drawing (GUI WinForms) — CỐ TÌNH
    # không giả lập: script tự bọc try/except quanh các import này và tự
    # đặt GUI_AVAILABLE=False khi không có (đúng thứ đang xảy ra trong môi
    # trường test này, không phải Windows/.NET thật). Phần logic thuần
    # Python (dò lưới, FormulaEngine) không phụ thuộc gì vào GUI_AVAILABLE
    # nên vẫn kiểm thử được đầy đủ mà không cần WinForms/pythonnet thật.
    system = fake_module("System")
    system.String = str
    system.Action = lambda f: f
    system.Int32 = int


_install_fake_revit_modules()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ScanGenericAnnotationTable as mod  # noqa: E402


class TestColumnLetters(unittest.TestCase):
    def test_round_trip(self):
        for i in [0, 1, 25, 26, 27, 51, 52, 701, 702]:
            letters = mod.col_letter(i)
            self.assertEqual(mod.col_index(letters), i, "round trip fail for %d -> %s" % (i, letters))

    def test_known_values(self):
        self.assertEqual(mod.col_letter(0), "A")
        self.assertEqual(mod.col_letter(25), "Z")
        self.assertEqual(mod.col_letter(26), "AA")
        self.assertEqual(mod.col_index("A"), 0)
        self.assertEqual(mod.col_index("AA"), 26)


class TestClustering(unittest.TestCase):
    def test_cluster_1d_simple_rows(self):
        # 3 hàng rõ rệt, mỗi hàng có 2 giá trị gần nhau
        values = [0.0, 0.01, 5.0, 5.02, 10.0, 9.98]
        tol = mod.auto_tolerance(values)
        ids, centers = mod.cluster_1d(values, tol)
        self.assertEqual(len(centers), 3)
        # 2 phần tử đầu cùng cụm, 2 kế cùng cụm, 2 cuối cùng cụm
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(ids[2], ids[3])
        self.assertEqual(ids[4], ids[5])
        self.assertNotEqual(ids[0], ids[2])
        self.assertNotEqual(ids[2], ids[4])

    def test_auto_tolerance_clean_grid_no_noise(self):
        # Lưới sạch, không nhiễu, khoảng cách đều 10ft -> vẫn phải tách
        # thành 3 cụm riêng biệt (không được gộp thành 1 cụm lớn).
        values = [0.0, 0.0, 10.0, 10.0, 20.0, 20.0]
        tol = mod.auto_tolerance(values)
        ids, centers = mod.cluster_1d(values, tol)
        self.assertEqual(len(centers), 3)

    def test_auto_tolerance_single_row_with_jitter(self):
        # Chỉ 1 hàng duy nhất, có nhiễu số học rất nhỏ (< sàn nhiễu)
        # -> phải gộp thành đúng 1 cụm, không được tách nhầm.
        values = [0.0, 0.0009, 0.0015, 0.0006]
        tol = mod.auto_tolerance(values)
        ids, centers = mod.cluster_1d(values, tol)
        self.assertEqual(len(centers), 1)

    def test_build_grid_layout(self):
        # Bảng 2 hàng x 3 cột, khoảng cách đều 10 ft (giả lập XYZ đơn giản)
        class FakeXYZ(object):
            def __init__(self, x, y, z=0.0):
                self.X = x
                self.Y = y
                self.Z = z

            def Subtract(self, other):
                # Khớp đúng API thật của Autodesk.Revit.DB.XYZ.Subtract(),
                # vì production code (to_uv) dùng .Subtract() thay vì "-"
                # (xem lý do trong docstring của to_uv trong script chính).
                return FakeXYZ(self.X - other.X, self.Y - other.Y, self.Z - other.Z)

            def DotProduct(self, other):
                return self.X * other.X + self.Y * other.Y + self.Z * other.Z

        class FakeView(object):
            Origin = FakeXYZ(0, 0, 0)
            RightDirection = FakeXYZ(1, 0, 0)
            UpDirection = FakeXYZ(0, 1, 0)

        class FakeLocation(object):
            def __init__(self, pt):
                self.Point = pt

        class FakeElem(object):
            _counter = [0]

            def __init__(self, x, y, tag):
                self.Location = FakeLocation(FakeXYZ(x, y))
                self.tag = tag
                FakeElem._counter[0] += 1
                self.Id = FakeElem._counter[0]

        # hàng trên (Y=10): 3 cột X=0,10,20 ; hàng dưới (Y=0): 3 cột X=0,10,20
        elems = [
            FakeElem(0, 10, "R0C0"), FakeElem(10, 10, "R0C1"), FakeElem(20, 10, "R0C2"),
            FakeElem(0, 0, "R1C0"), FakeElem(10, 0, "R1C1"), FakeElem(20, 0, "R1C2"),
        ]
        grid, n_rows, n_cols, warnings = mod.build_grid(elems, FakeView())
        self.assertEqual(n_rows, 2)
        self.assertEqual(n_cols, 3)
        self.assertEqual(grid[0][0].tag, "R0C0")
        self.assertEqual(grid[0][2].tag, "R0C2")
        self.assertEqual(grid[1][0].tag, "R1C0")
        self.assertEqual(grid[1][2].tag, "R1C2")
        # 1 dòng tóm tắt thông tin (hàng/cột/dung sai) luôn được thêm vào,
        # nhưng không có cảnh báo LỖI nào (đánh dấu bằng "⚠") vì lưới sạch,
        # lấp đầy 100%.
        self.assertTrue(len(warnings) >= 1)
        self.assertFalse(any(u"⚠" in w for w in warnings))
        self.assertIn(u"100%", warnings[-1])


class TestFormulaEngine(unittest.TestCase):
    def _engine(self, table):
        """table: list các list string, hàng 0 = hàng 1 (Excel 1-based)."""
        n_rows = len(table)
        n_cols = len(table[0]) if n_rows else 0

        def get_raw(r, c):
            return table[r][c]

        return mod.FormulaEngine(get_raw, n_rows, n_cols)

    def test_plain_numbers(self):
        e = self._engine([["1", "2"], ["3", "4"]])
        self.assertEqual(e.value_of(0, 0), 1.0)
        self.assertEqual(e.value_of(1, 1), 4.0)

    def test_sum_range(self):
        e = self._engine([["1", "2", "=SUM(A1:B1)"]])
        self.assertEqual(e.value_of(0, 2), 3.0)

    def test_average(self):
        e = self._engine([["2", "4", "=AVERAGE(A1:B1)"]])
        self.assertEqual(e.value_of(0, 2), 3.0)

    def test_product(self):
        e = self._engine([["2", "3", "4", "=PRODUCT(A1:C1)"]])
        self.assertEqual(e.value_of(0, 3), 24.0)

    def test_min_max_count(self):
        e = self._engine([["5", "1", "9", "=MIN(A1:C1)", "=MAX(A1:C1)", "=COUNT(A1:C1)"]])
        self.assertEqual(e.value_of(0, 3), 1.0)
        self.assertEqual(e.value_of(0, 4), 9.0)
        self.assertEqual(e.value_of(0, 5), 3.0)

    def test_divide_two_cells(self):
        e = self._engine([["10", "4", "=A1/B1"]])
        self.assertEqual(e.value_of(0, 2), 2.5)

    def test_divide_by_zero(self):
        e = self._engine([["10", "0", "=A1/B1"]])
        self.assertEqual(e.value_of(0, 2), "#DIV/0!")

    def test_nested_formula_chain(self):
        # C1 = A1+B1 ; D1 = SUM(A1:C1) -> phải tự giải theo đúng thứ tự
        e = self._engine([["1", "2", "=A1+B1", "=SUM(A1:C1)"]])
        self.assertEqual(e.value_of(0, 2), 3.0)
        self.assertEqual(e.value_of(0, 3), 6.0)  # 1+2+3

    def test_circular_reference_detected(self):
        e = self._engine([["=B1", "=A1"]])
        self.assertEqual(e.value_of(0, 0), "#CYCLE!")

    def test_operator_precedence_and_parens(self):
        e = self._engine([["=2+3*4", "=(2+3)*4", "=2^3+1"]])
        self.assertEqual(e.value_of(0, 0), 14.0)
        self.assertEqual(e.value_of(0, 1), 20.0)
        self.assertEqual(e.value_of(0, 2), 9.0)

    def test_round_and_abs(self):
        e = self._engine([["=ROUND(3.14159,2)", "=ABS(-7)"]])
        self.assertEqual(e.value_of(0, 0), 3.14)
        self.assertEqual(e.value_of(0, 1), 7.0)

    def test_text_cell_ignored_in_sum(self):
        e = self._engine([["Tổng", "3", "5", "=SUM(A1:C1)"]])
        self.assertEqual(e.value_of(0, 3), 8.0)  # bỏ qua ô chữ "Tổng"

    def test_blank_cell_is_zero_in_arithmetic(self):
        e = self._engine([["", "5", "=A1+B1"]])
        self.assertEqual(e.value_of(0, 2), 5.0)

    def test_cross_row_reference(self):
        e = self._engine([["10", "20"], ["=A1+B1", ""]])
        self.assertEqual(e.value_of(1, 0), 30.0)

    def test_unknown_function_name_error(self):
        e = self._engine([["=FOO(1,2)"]])
        self.assertEqual(e.value_of(0, 0), "#NAME?")


class TestFormatValue(unittest.TestCase):
    def test_integer_like_float(self):
        self.assertEqual(mod.format_value(4.0), "4")

    def test_decimal_rounding(self):
        self.assertEqual(mod.format_value(1.0 / 3.0), "0.333")

    def test_none_is_empty(self):
        self.assertEqual(mod.format_value(None), "")

    def test_string_passthrough(self):
        self.assertEqual(mod.format_value("#DIV/0!"), "#DIV/0!")


class _FakeParameter(object):
    """Giả lập Autodesk.Revit.DB.Parameter đủ dùng cho find_text_source /
    detect_best_param_name — chỉ cần .StorageType, .AsString(), .Definition.Name."""

    def __init__(self, name, value, is_double=False, read_only=False):
        self.name = name
        self.value = value
        self.StorageType = (mod.Autodesk.Revit.DB.StorageType.Double if is_double
                             else mod.Autodesk.Revit.DB.StorageType.String)
        self.IsReadOnly = read_only
        self.Definition = types.SimpleNamespace(Name=name)

    def AsString(self):
        return self.value

    def AsValueString(self):
        return self.value

    def Set(self, v):
        self.value = v


class _FakeSymbol(object):
    def __init__(self, sid, name, params=None):
        self.Id = types.SimpleNamespace(IntegerValue=sid)
        self.Name = name
        self._params = {p.name: p for p in (params or [])}

    def LookupParameter(self, name):
        return self._params.get(name)


class _FakeAnnotation(object):
    """Giả lập 1 Generic Annotation FamilyInstance: có Parameter riêng
    (Instance) và 1 Symbol/Type (có thể có Parameter + Name riêng)."""

    def __init__(self, elem_id, params=None, symbol=None):
        self.Id = types.SimpleNamespace(IntegerValue=elem_id)
        self._params = {p.name: p for p in (params or [])}
        self.Symbol = symbol

    def LookupParameter(self, name):
        return self._params.get(name)

    def GetOrderedParameters(self):
        return list(self._params.values())

    def get_Parameter(self, _bip):
        return self._params.get("Comments")


class _FakeTextNoteElem(mod.TextNote):
    """Giả lập Autodesk.Revit.DB.TextNote — subclass đúng lớp TextNote mà
    script đã import, để isinstance(elem, TextNote)/is_text_note() nhận
    diện đúng như trên Revit thật."""

    def __init__(self, elem_id, text, coord, bbox_center=None, location_point=None):
        self.Id = types.SimpleNamespace(IntegerValue=elem_id)
        self.Text = text
        self.Coord = coord
        # location_point / bbox_center (nếu có) CỐ Ý đặt khác Coord, để
        # test xác nhận .Coord luôn được ưu tiên tuyệt đối cho TextNote.
        if location_point is not None:
            self.Location = types.SimpleNamespace(Point=location_point)
        self._bbox_center = bbox_center

    def get_BoundingBox(self, _view):
        if self._bbox_center is None:
            return None
        cx, cy = self._bbox_center
        return types.SimpleNamespace(
            Min=types.SimpleNamespace(X=cx - 1, Y=cy - 1, Z=0),
            Max=types.SimpleNamespace(X=cx + 1, Y=cy + 1, Z=0),
        )


class TestTextNoteHandling(unittest.TestCase):
    def test_is_text_note_true_for_textnote_false_for_other(self):
        tn = _FakeTextNoteElem(1, u"300", coord="COORD")
        other = _FakeAnnotation(2, params=[])
        self.assertTrue(mod.is_text_note(tn))
        self.assertFalse(mod.is_text_note(other))

    def test_get_location_point_prefers_coord_over_location_and_bbox(self):
        # location_point và bbox_center CỐ Ý khác Coord — phải luôn trả
        # về đúng Coord (đây là bài học/lỗi thực tế đã fix: dùng
        # Location.Point hay tâm BoundingBox cho TextNote gây ghép sai
        # hàng/cột vì xê dịch theo độ dài nội dung).
        tn = _FakeTextNoteElem(
            1, u"300", coord="THE_COORD",
            bbox_center=(999.0, 999.0), location_point="WRONG_LOCATION_POINT",
        )
        result = mod.get_location_point(tn, view=None)
        self.assertEqual(result, "THE_COORD")

    def test_find_text_source_reads_and_writes_dot_text(self):
        tn = _FakeTextNoteElem(1, u"8,338.82", coord="C")
        source = mod.find_text_source(tn)
        self.assertIsNotNone(source)
        self.assertEqual(source.kind, "TEXTNOTE")
        self.assertEqual(mod.read_source_text(source), u"8,338.82")

    def test_find_text_source_ignores_forced_name_for_textnote(self):
        # TextNote không có Parameter nào cả — dù IN[3] truyền tên bất kỳ,
        # vẫn phải đọc/ghi qua .Text, không được cố LookupParameter().
        tn = _FakeTextNoteElem(1, u"42", coord="C")
        source = mod.find_text_source(tn, forced_name="KhongTonTai")
        self.assertEqual(source.kind, "TEXTNOTE")
        self.assertEqual(mod.read_source_text(source), u"42")


class TestFindTextSource(unittest.TestCase):
    def test_uses_matching_candidate_instance_param(self):
        e = _FakeAnnotation(1, params=[_FakeParameter("Text", u"Hello")])
        source = mod.find_text_source(e)
        self.assertIsNotNone(source)
        self.assertEqual(source.kind, "PARAM")
        self.assertEqual(source.name, "Text")
        self.assertEqual(mod.read_source_text(source), u"Hello")

    def test_falls_back_to_type_parameter_when_no_instance_param(self):
        sym = _FakeSymbol(9, u"TYPE-9", params=[_FakeParameter("Label", u"Từ Type")])
        e = _FakeAnnotation(1, params=[], symbol=sym)
        source = mod.find_text_source(e, forced_name="Label")
        self.assertIsNotNone(source)
        self.assertEqual(source.kind, "PARAM")
        self.assertEqual(mod.read_source_text(source), u"Từ Type")

    def test_type_name_sentinel_reads_symbol_name(self):
        sym = _FakeSymbol(9, u"A1-300x500")
        e = _FakeAnnotation(1, params=[], symbol=sym)
        source = mod.find_text_source(e, forced_name=mod.TYPE_NAME_SENTINEL)
        self.assertIsNotNone(source)
        self.assertEqual(source.kind, "TYPE_NAME")
        self.assertEqual(mod.read_source_text(source), u"A1-300x500")

    def test_returns_none_when_nothing_matches(self):
        e = _FakeAnnotation(1, params=[])
        source = mod.find_text_source(e, forced_name="KhongTonTai")
        self.assertIsNone(source)


class TestDetectBestParamName(unittest.TestCase):
    def test_picks_highest_coverage_candidate(self):
        elems = [
            _FakeAnnotation(1, params=[_FakeParameter(u"文字", u"300"), _FakeParameter("Comments", u"")]),
            _FakeAnnotation(2, params=[_FakeParameter(u"文字", u"350"), _FakeParameter("Comments", u"")]),
            _FakeAnnotation(3, params=[_FakeParameter(u"文字", u""), _FakeParameter("Comments", u"x")]),
        ]
        name, coverage, n = mod.detect_best_param_name(elems)
        self.assertEqual(name, u"文字")
        self.assertAlmostEqual(coverage, 2.0 / 3.0)
        self.assertEqual(n, 3)

    def test_falls_back_to_type_name_when_no_param_has_content(self):
        elems = [
            _FakeAnnotation(1, params=[], symbol=_FakeSymbol(1, u"SIZE-A")),
            _FakeAnnotation(2, params=[], symbol=_FakeSymbol(2, u"SIZE-B")),
        ]
        name, coverage, n = mod.detect_best_param_name(elems)
        self.assertEqual(name, mod.TYPE_NAME_SENTINEL)
        self.assertEqual(coverage, 1.0)

    def test_generic_scan_finds_uncommon_param_name(self):
        # Không phần tử nào khớp CANDIDATE_PARAM_NAMES lẫn Type Name, nhưng
        # có 1 parameter chữ "MyCustomLabel" với nội dung -> phải tự dò ra.
        elems = [
            _FakeAnnotation(1, params=[_FakeParameter("MyCustomLabel", u"100")]),
            _FakeAnnotation(2, params=[_FakeParameter("MyCustomLabel", u"200")]),
        ]
        name, coverage, n = mod.detect_best_param_name(elems)
        self.assertEqual(name, "MyCustomLabel")
        self.assertEqual(coverage, 1.0)

    def test_returns_none_when_truly_nothing_found(self):
        elems = [_FakeAnnotation(1, params=[]), _FakeAnnotation(2, params=[])]
        name, coverage, n = mod.detect_best_param_name(elems)
        self.assertIsNone(name)
        self.assertEqual(coverage, 0.0)

    def test_forced_name_short_circuits_detection(self):
        elems = [_FakeAnnotation(1, params=[_FakeParameter(u"文字", u"300")])]
        name, coverage, n = mod.detect_best_param_name(elems, forced_name="MyParam")
        self.assertEqual(name, "MyParam")
        self.assertIsNone(coverage)


if __name__ == "__main__":
    unittest.main(verbosity=2)
