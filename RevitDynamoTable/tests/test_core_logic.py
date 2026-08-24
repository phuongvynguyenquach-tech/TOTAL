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
PYTHON (không đụng Revit API / WPF) được nạp và kiểm thử thật.

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
    db.BuiltInParameter = types.SimpleNamespace(ALL_MODEL_INSTANCE_COMMENTS=1)
    db.SectionType = types.SimpleNamespace(Body=0)
    db.StorageType = types.SimpleNamespace(String=1, Double=2, Integer=3, ElementId=4, none=0)

    # RevitServices — cố tình để KHÔNG import được, script sẽ tự set
    # DYNAMO_ENV = False và dùng nhánh Transaction thường (đã có sẵn
    # try/except trong script cho trường hợp này) -> không cần giả lập.

    # System.* cho phần WPF (không được gọi tới trong test logic thuần,
    # nhưng cần tồn tại để dòng import ở đầu file không crash).
    system = fake_module("System")
    system.String = str
    system.Action = lambda f: f
    system.Int32 = int

    io_mod = fake_module("System.IO")
    io_mod.StringReader = _Dummy

    xml_mod = fake_module("System.Xml")
    xml_mod.XmlReader = types.SimpleNamespace(Create=lambda *a, **k: None)

    markup_mod = fake_module("System.Windows.Markup")
    markup_mod.XamlReader = types.SimpleNamespace(Load=lambda *a, **k: None)

    threading_mod = fake_module("System.Windows.Threading")
    threading_mod.DispatcherPriority = types.SimpleNamespace(Background=0)

    data_mod = fake_module("System.Data")
    data_mod.DataTable = _Dummy
    data_mod.DataColumn = _Dummy

    controls_mod = fake_module("System.Windows.Controls")
    controls_mod.DataGridTextColumn = _Dummy

    data_binding_mod = fake_module("System.Windows.Data")
    data_binding_mod.Binding = _Dummy


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
        self.assertEqual(warnings, [])


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
