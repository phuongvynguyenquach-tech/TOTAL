# -*- coding: utf-8 -*-
"""
Kiểm thử NGOÀI Revit cho toàn bộ phần logic thuần Python của
CadToFamilyBatch.py:
  - đọc DXF (LINE/LWPOLYLINE/ARC/CIRCLE/TEXT/INSERT-block, $INSUNITS, bulge)
  - gom cụm bản vẽ (cluster_islands) + gán ghi chú (attach_labels)
  - "tư duy" nhận diện hình chiếu (classify_islands) và suy kích thước
  - ghép vòng kín (chain_loops / collect_loops / pick_profile_loops)
  - đoán danh mục Revit, đặt tên family, gộp file theo hậu tố hình chiếu
  - tiện ích số học/hình học (simplify_polyline, polygon_area, ...)

Môi trường này không có Revit/Dynamo/pythonnet — điều đó là CỐ Ý: mọi
import Revit trong file script đều nằm trong 1 try/except và tự đặt
REVIT_API = False, nên phần logic thuần Python nạp và chạy được bình
thường mà không cần giả lập .NET.

Chạy:  python3 RevitCadToFamily/tests/test_cad_family_core.py
"""
import os
import sys
import math
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import CadToFamilyBatch as mod  # noqa: E402


# ------------------------------------------------------------------------
# Tiện ích dựng file DXF giả lập để kiểm thử
# ------------------------------------------------------------------------
def dxf(*pairs):
    """Nhận các cặp (mã, giá trị) -> chuỗi DXF đúng định dạng 2 dòng/cặp."""
    out = []
    for code, val in pairs:
        out.append(u"%d" % code)
        out.append(u"%s" % val)
    return u"\n".join(out) + u"\n"


def lwpoly(layer, pts, closed=True):
    p = [(0, "LWPOLYLINE"), (8, layer), (90, len(pts)), (70, 1 if closed else 0)]
    for (x, y) in pts:
        p.append((10, x))
        p.append((20, y))
    return p


def rect(layer, x0, y0, x1, y1):
    return lwpoly(layer, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True)


def text(layer, x, y, s):
    return [(0, "TEXT"), (8, layer), (10, x), (20, y), (1, s)]


def make_lavabo_dxf():
    """Bản vẽ mẫu giống ảnh hướng dẫn: MẶT BẰNG bàn lavabo 1500×500 có 3
    chậu tròn (đặt bằng block INSERT), và MẶT ĐỨNG CHÍNH 1500×800."""
    head = [(0, "SECTION"), (2, "HEADER"), (9, "$INSUNITS"), (70, 4), (0, "ENDSEC")]
    blocks = ([(0, "SECTION"), (2, "BLOCKS"),
               (0, "BLOCK"), (2, "CHAU"), (10, 0.0), (20, 0.0),
               (0, "CIRCLE"), (8, "TB-VS"), (10, 0.0), (20, 0.0), (40, 150.0),
               (0, "ENDBLK"), (0, "ENDSEC")])
    ents = [(0, "SECTION"), (2, "ENTITIES")]
    ents += rect("BAN-DA", 0, 0, 1500, 500)
    for cx in (250, 750, 1250):
        ents += [(0, "INSERT"), (8, "TB-VS"), (2, "CHAU"), (10, cx), (20, 250)]
    ents += text("GHI-CHU", 750, -200, u"MẶT BẰNG")
    ents += rect("BAN-DA", 0, 2000, 1500, 2800)
    ents += text("GHI-CHU", 750, 1800, u"MẶT ĐỨNG CHÍNH")
    ents += [(0, "ENDSEC"), (0, "EOF")]
    return dxf(*(head + blocks + ents))


def write_tmp(content, suffix=".dxf", name=None):
    d = tempfile.mkdtemp()
    path = os.path.join(d, name or ("test%s" % suffix))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


# ------------------------------------------------------------------------
class TestTextUtils(unittest.TestCase):
    def test_strip_accents(self):
        self.assertEqual(mod.strip_accents(u"MẶT ĐỨNG"), u"MAT DUNG")
        self.assertEqual(mod.strip_accents(u"Chậu rửa"), u"Chau rua")
        self.assertEqual(mod.strip_accents(u"đèn Đôi"), u"den Doi")

    def test_norm_key(self):
        self.assertEqual(mod.norm_key(u"cua_di-P1.dwg"), u"CUA DI P1 DWG")
        self.assertEqual(mod.norm_key(u"  Tủ   bếp  "), u"TU BEP")

    def test_contains_keyword_respects_word_boundary(self):
        self.assertTrue(mod.contains_keyword(u"TU BEP TREN", u" TU "))
        self.assertFalse(mod.contains_keyword(u"TUONG GACH", u" TU "))

    def test_parse_number(self):
        self.assertEqual(mod.parse_number(u"1200"), 1200.0)
        self.assertEqual(mod.parse_number(u"1200,5"), 1200.5)
        self.assertEqual(mod.parse_number(u"1,200"), 1200.0)
        self.assertEqual(mod.parse_number(u"1.200,5"), 1200.5)
        self.assertEqual(mod.parse_number(u"1200 mm"), 1200.0)
        self.assertIsNone(mod.parse_number(u"", None))

    def test_fmt_mm(self):
        self.assertEqual(mod.fmt_mm(900.0), u"900")
        self.assertEqual(mod.fmt_mm(899.75), u"899.8")

    def test_sanitize_and_unique(self):
        self.assertEqual(mod.sanitize_family_name(u'LAVABO/BỘ:3'), u"LAVABO-BỘ-3")
        used = set()
        self.assertEqual(mod.unique_name(u"CUA", used), u"CUA")
        self.assertEqual(mod.unique_name(u"CUA", used), u"CUA_2")
        self.assertEqual(mod.unique_name(u"CUA", used), u"CUA_3")


class TestCategoryGuess(unittest.TestCase):
    def test_vietnamese_names(self):
        self.assertEqual(mod.guess_category(u"LAVABO BỘ 3"), "PlumbingFixtures")
        self.assertEqual(mod.guess_category(u"CHẬU RỬA ÂM BÀN"), "PlumbingFixtures")
        self.assertEqual(mod.guess_category(u"CỬA ĐI 1 CÁNH"), "Doors")
        self.assertEqual(mod.guess_category(u"CỬA SỔ 2 CÁNH"), "Windows")
        self.assertEqual(mod.guess_category(u"TỦ BẾP DƯỚI"), "Casework")
        self.assertEqual(mod.guess_category(u"GHẾ LÀM VIỆC"), "Furniture")
        self.assertEqual(mod.guess_category(u"ĐÈN LED ÂM TRẦN"), "LightingFixtures")

    def test_english_names(self):
        self.assertEqual(mod.guess_category(u"WC-basin-01"), "PlumbingFixtures")
        self.assertEqual(mod.guess_category(u"door_single"), "Doors")

    def test_unknown_falls_back(self):
        self.assertEqual(mod.guess_category(u"XYZ-123"), "GenericModel")


class TestUnits(unittest.TestCase):
    def test_insunits_wins(self):
        k, name, ok = mod.infer_units_scale(6, 12.0)
        self.assertEqual(k, 1000.0)
        self.assertTrue(ok)

    def test_guess_from_size(self):
        self.assertEqual(mod.infer_units_scale(0, 1.5)[0], 1000.0)     # mét
        self.assertEqual(mod.infer_units_scale(0, 150.0)[0], 10.0)     # cm
        self.assertEqual(mod.infer_units_scale(0, 1500.0)[0], 1.0)     # mm
        self.assertFalse(mod.infer_units_scale(0, 1500.0)[2])

    def test_mm_ft_round_trip(self):
        self.assertAlmostEqual(mod.ft_to_mm(mod.mm_to_ft(1234.5)), 1234.5, places=6)


class TestGeometryHelpers(unittest.TestCase):
    def test_polygon_area(self):
        sq = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.assertAlmostEqual(abs(mod.polygon_area(sq)), 100.0)

    def test_point_in_polygon(self):
        sq = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.assertTrue(mod.point_in_polygon((5, 5), sq))
        self.assertFalse(mod.point_in_polygon((15, 5), sq))

    def test_arc_points(self):
        pts = mod.arc_points((0, 0), 100.0, 0.0, 90.0)
        self.assertGreaterEqual(len(pts), 3)
        self.assertAlmostEqual(pts[0][0], 100.0, places=6)
        self.assertAlmostEqual(pts[-1][1], 100.0, places=6)
        for (x, y) in pts:
            self.assertAlmostEqual(math.hypot(x, y), 100.0, places=6)

    def test_bulge_half_circle(self):
        pts = mod.bulge_points((0, 0), (100, 0), 1.0)
        self.assertGreater(len(pts), 3)
        self.assertAlmostEqual(pts[0][0], 0.0, places=6)
        self.assertAlmostEqual(pts[-1][0], 100.0, places=6)
        top = max(abs(p[1]) for p in pts)
        self.assertAlmostEqual(top, 50.0, places=3)

    def test_simplify_polyline(self):
        pts = [(i, 0.0) for i in range(50)]
        self.assertEqual(len(mod.simplify_polyline(pts, 1.0)), 2)
        zig = [(0, 0), (10, 50), (20, 0)]
        self.assertEqual(len(mod.simplify_polyline(zig, 1.0)), 3)

    def test_chain_loops_from_separate_lines(self):
        segs = [((0, 0), (100, 0)), ((100, 0), (100, 50)),
                ((100, 50), (0, 50)), ((0, 50), (0, 0))]
        loops = mod.chain_loops(segs, 0.5)
        self.assertEqual(len(loops), 1)
        self.assertAlmostEqual(abs(mod.polygon_area(loops[0])), 5000.0, places=3)

    def test_is_rectangleish(self):
        self.assertTrue(mod.is_rectangleish([(0, 0), (100, 0), (100, 50), (0, 50)]))
        self.assertFalse(mod.is_rectangleish([(0, 0), (100, 0), (50, 80)]))
        circle = mod.arc_points((0, 0), 100.0, 0.0, 360.0)
        self.assertFalse(mod.is_rectangleish(circle))


class TestDxfReader(unittest.TestCase):
    def setUp(self):
        self.path = write_tmp(make_lavabo_dxf(), name=u"LAVABO BỘ 3.dxf")
        self.cad, self.err = mod.read_dxf(self.path)

    def test_reads_without_error(self):
        self.assertIsNone(self.err)
        self.assertIsNotNone(self.cad)
        self.assertTrue(self.cad.unit_ok)
        self.assertEqual(self.cad.unit_scale, 1.0)

    def test_expands_insert_blocks(self):
        circles = [e for e in self.cad.entities if e.kind == "CIRCLE"]
        self.assertEqual(len(circles), 3, u"3 INSERT của block CHAU phải bung thành 3 hình tròn")
        xs = sorted(round(c.center[0]) for c in circles)
        self.assertEqual(xs, [250, 750, 1250])
        self.assertTrue(all(abs(c.radius - 150.0) < 1e-6 for c in circles))

    def test_reads_text(self):
        texts = [mod.norm_key(t) for t in self.cad.texts()]
        self.assertIn(u"MAT BANG", texts)
        self.assertIn(u"MAT DUNG CHINH", texts)

    def test_layers(self):
        self.assertIn(u"BAN-DA", self.cad.layers())
        self.assertIn(u"TB-VS", self.cad.layers())


class TestIslandsAndClassification(unittest.TestCase):
    def setUp(self):
        self.path = write_tmp(make_lavabo_dxf(), name=u"LAVABO BỘ 3.dxf")
        cad, err = mod.read_dxf(self.path)
        self.assertIsNone(err)
        ents = mod.filter_for_analysis(cad.entities)
        self.islands = mod.drop_noise_islands(mod.attach_labels(mod.cluster_islands(ents)))
        mod.classify_islands(self.islands, os.path.basename(self.path))
        self.by_kind = dict((il.kind, il) for il in self.islands)

    def test_two_islands(self):
        self.assertEqual(len(self.islands), 2,
                         u"Mặt bằng và mặt đứng phải tách thành 2 cụm rời")

    def test_labels_attached(self):
        for il in self.islands:
            self.assertTrue(il.text_blob().strip(), u"Mỗi cụm phải nhận được ghi chú của nó")

    def test_classified_plan_and_front(self):
        self.assertIn("PLAN", self.by_kind)
        self.assertIn("FRONT", self.by_kind)

    def test_dimensions(self):
        L, W, H, note = mod.infer_dimensions(self.islands, "PlumbingFixtures")
        self.assertAlmostEqual(L, 1500.0, places=3)
        self.assertAlmostEqual(W, 500.0, places=3)
        self.assertAlmostEqual(H, 800.0, places=3)
        self.assertIn(u"mặt bằng", note)

    def test_plan_profile_loops(self):
        plan = self.by_kind["PLAN"]
        loops = mod.collect_loops(plan.drawable())
        outer, inner = mod.pick_profile_loops(loops)
        self.assertIsNotNone(outer)
        self.assertAlmostEqual(abs(mod.polygon_area(outer)), 1500.0 * 500.0, delta=1.0)
        self.assertEqual(len(inner), 3, u"3 chậu tròn phải thành 3 lỗ rỗng bên trong mặt bàn")

    def test_geometric_fallback_without_labels(self):
        """Bỏ hết chữ ghi chú -> vẫn phải suy ra được mặt bằng/mặt đứng bằng
        hình học (cụm nhiều vòng kín = mặt bằng; cụm có bề ngang bằng Dài
        mặt bằng = mặt đứng chính)."""
        cad, _ = mod.read_dxf(self.path)
        ents = [e for e in mod.filter_for_analysis(cad.entities) if e.kind != "TEXT"]
        islands = mod.drop_noise_islands(mod.attach_labels(mod.cluster_islands(ents)))
        mod.classify_islands(islands, u"khong-ten.dxf")
        kinds = dict((il.kind, il) for il in islands)
        self.assertIn("PLAN", kinds)
        self.assertIn("FRONT", kinds)
        self.assertAlmostEqual(kinds["PLAN"].size()[0], 1500.0, places=3)
        self.assertAlmostEqual(kinds["FRONT"].size()[1], 800.0, places=3)


class TestScanPlan(unittest.TestCase):
    def test_full_pipeline_on_dxf(self):
        path = write_tmp(make_lavabo_dxf(), name=u"LAVABO BỘ 3.dxf")
        plans = mod.group_files_into_plans([path], True)
        self.assertEqual(len(plans), 1)
        p = plans[0]
        mod.scan_plan(p, mod.dxf_reader)
        self.assertTrue(p.scanned)
        self.assertEqual(p.category, "PlumbingFixtures")
        self.assertAlmostEqual(p.length, 1500.0, places=3)
        self.assertAlmostEqual(p.width, 500.0, places=3)
        self.assertAlmostEqual(p.height, 800.0, places=3)
        self.assertTrue(p.status.startswith(u"✔"), p.status)
        self.assertIn(u"MB", p.views_display())
        self.assertIn(u"MĐ", p.views_display())

    def test_bad_file_is_reported_not_raised(self):
        path = write_tmp(u"day khong phai file dxf\n", name=u"hong.dxf")
        p = mod.group_files_into_plans([path], True)[0]
        mod.scan_plan(p, mod.dxf_reader)
        self.assertTrue(p.status.startswith(u"✖"))
        self.assertTrue(p.warnings)


class TestFileGrouping(unittest.TestCase):
    def test_split_view_suffix(self):
        self.assertEqual(mod.split_view_suffix(u"LAVABO BO 3_MB")[1], "PLAN")
        self.assertEqual(mod.split_view_suffix(u"LAVABO BO 3_MD TRAI")[1], "LEFT")
        self.assertEqual(mod.split_view_suffix(u"CUA DI P1")[1], None)

    def test_group_same_base_different_views(self):
        d = tempfile.mkdtemp()
        paths = []
        for suffix in (u"MB", u"MD", u"MD TRAI"):
            p = os.path.join(d, u"LAVABO BỘ 3_%s.dxf" % suffix)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(make_lavabo_dxf())
            paths.append(p)
        plans = mod.group_files_into_plans(paths, True)
        self.assertEqual(len(plans), 1, u"3 hình chiếu cùng tên gốc phải gộp thành 1 family")
        self.assertEqual(len(plans[0].sources), 3)
        self.assertEqual(sorted(s.forced_kind for s in plans[0].sources),
                         ["FRONT", "LEFT", "PLAN"])
        self.assertIn(u"LAVABO", plans[0].family_name.upper())

    def test_do_not_group_different_products(self):
        d = tempfile.mkdtemp()
        paths = []
        for n in (u"CUA DI P1.dxf", u"CUA DI P2.dxf"):
            p = os.path.join(d, n)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(make_lavabo_dxf())
            paths.append(p)
        plans = mod.group_files_into_plans(paths, True)
        self.assertEqual(len(plans), 2, u"2 sản phẩm khác nhau KHÔNG được gộp")

    def test_group_disabled(self):
        d = tempfile.mkdtemp()
        paths = []
        for suffix in (u"MB", u"MD"):
            p = os.path.join(d, u"TU BEP_%s.dxf" % suffix)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(make_lavabo_dxf())
            paths.append(p)
        self.assertEqual(len(mod.group_files_into_plans(paths, False)), 2)


class TestForcedViewFromFileName(unittest.TestCase):
    def test_suffix_forces_view_kind(self):
        """File đặt tên "..._MD TRAI" phải được gán thẳng thành mặt bên
        trái, kể cả khi trong file có chữ ghi chú nói điều khác."""
        import tempfile as _tf
        d = _tf.mkdtemp()
        paths = []
        for suffix in (u"MB", u"MD TRAI"):
            p = os.path.join(d, u"TỦ BẾP_%s.dxf" % suffix)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(make_lavabo_dxf())
            paths.append(p)
        plan = mod.group_files_into_plans(paths, True)[0]
        mod.scan_plan(plan, mod.dxf_reader)
        self.assertIn("PLAN", plan.views)
        self.assertIn("LEFT", plan.views)
        self.assertEqual(plan.category, "Casework")
        self.assertIn(u"Trái", plan.views_display())


class TestBuildModes(unittest.TestCase):
    def test_modes_declared(self):
        self.assertIn(mod.MODE_HYBRID, mod.BUILD_MODES)
        for m in mod.BUILD_MODES:
            self.assertIn(m, mod.BUILD_MODE_LABEL)

    def test_default_dims_cover_every_category(self):
        for cat in mod.CATEGORY_BIC:
            self.assertIn(cat, mod.DEFAULT_DIMS)
            self.assertIn(cat, mod.TEMPLATE_KEYWORDS)

    def test_formula_params_reference_existing_params(self):
        names = {mod.P_LEN, mod.P_WID, mod.P_HGT}
        for name, kind, formula, is_inst in mod.FORMULA_PARAMS:
            used = [n for n in names if n in formula]
            self.assertTrue(used, u"Công thức '%s' phải dùng tham số gốc" % formula)


class TestFileListing(unittest.TestCase):
    def test_list_files_and_folder(self):
        d = tempfile.mkdtemp()
        sub = os.path.join(d, "sub")
        os.makedirs(sub)
        for p in (os.path.join(d, "a.dxf"), os.path.join(d, "b.DWG"),
                  os.path.join(d, "c.txt"), os.path.join(sub, "d.dxf")):
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("x")
        self.assertEqual(len(mod.list_cad_files(d, False)), 2)
        self.assertEqual(len(mod.list_cad_files(d, True)), 3)
        multi = u"%s;%s" % (os.path.join(d, "a.dxf"), os.path.join(sub, "d.dxf"))
        self.assertEqual(len(mod.list_cad_files(multi)), 2)
        self.assertEqual(mod.list_cad_files(u""), [])

    def test_default_output_dir(self):
        d = tempfile.mkdtemp()
        f = os.path.join(d, "a.dxf")
        self.assertEqual(mod.default_output_dir([f]), os.path.join(d, "REVIT_FAMILY_OUT"))
        self.assertEqual(mod.default_output_dir([f], u"D:\\OUT"), u"D:\\OUT")


class TestTemplatePick(unittest.TestCase):
    def test_scores_metric_and_avoids_variants(self):
        d = tempfile.mkdtemp()
        names = ["Metric Casework.rft", "Metric Casework wall based.rft",
                 "Metric Generic Model.rft", "Metric Furniture.rft"]
        for n in names:
            with open(os.path.join(d, n), "w", encoding="utf-8") as fh:
                fh.write("x")
        mod._TEMPLATE_CACHE.clear()
        got = mod.pick_template("Casework", d)
        self.assertEqual(os.path.basename(got), "Metric Casework.rft")
        mod._TEMPLATE_CACHE.clear()
        got = mod.pick_template("LightingFixtures", d)
        self.assertEqual(os.path.basename(got), "Metric Generic Model.rft",
                         u"Không có template đúng danh mục thì phải lùi về Generic Model")


class TestNoiseLayers(unittest.TestCase):
    def test_noise_detection(self):
        self.assertTrue(mod.is_noise_layer(u"DIM-KICH THUOC"))
        self.assertTrue(mod.is_noise_layer(u"GHI CHU"))
        self.assertTrue(mod.is_noise_layer(u"Defpoints"))
        self.assertFalse(mod.is_noise_layer(u"BAN-DA"))
        self.assertFalse(mod.is_noise_layer(u"TB-VS"))

    def test_no_false_positive_on_word_fragments(self):
        """Layer vật liệu chứa chuỗi con của từ khoá rác vẫn phải được GIỮ."""
        self.assertFalse(mod.is_noise_layer(u"BAN CHU NHAT"))
        self.assertFalse(mod.is_noise_layer(u"MAT DA GRANITE"))
        self.assertFalse(mod.is_noise_layer(u"TRUCTIEP-BEP"))


# ------------------------------------------------------------------------
# Tiện ích dựng "cụm" trực tiếp (không qua file) cho các test thuật toán
# ------------------------------------------------------------------------
def E_rect(x0, y0, x1, y1, layer=u"A"):
    return mod.CadEnt("POLY", layer, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True)


def E_line(x0, y0, x1, y1, layer=u"A"):
    return mod.CadEnt("POLY", layer, [(x0, y0), (x1, y1)], False)


def E_arc(cx, cy, r, a0, a1, layer=u"A"):
    return mod.CadEnt("ARC", layer, [], False, (cx, cy), r, a0, a1)


def elevation_island(x0, y0, w=2400.0, h=2400.0, doors=4, layer=u"TU"):
    """Mặt đứng tủ: khung + vách chia đều + đường chéo ký hiệu cánh."""
    ents = [E_rect(x0, y0, x0 + w, y0 + h, layer)]
    step = w / float(doors)
    for i in range(1, doors):
        ents.append(E_line(x0 + i * step, y0, x0 + i * step, y0 + h, layer))
    for i in range(doors):
        a, b = x0 + i * step, x0 + (i + 1) * step
        ents.append(E_line(a, y0, b, y0 + h, layer))
        ents.append(E_line(a, y0 + h, b, y0, layer))
    il = mod.Island(ents)
    return il


def plan_island(x0, y0, w=2400.0, d=600.0, doors=4, layer=u"TU"):
    """Mặt bằng tủ: khung + cung quét cánh vẽ thòi ra ngoài."""
    ents = [E_rect(x0, y0, x0 + w, y0 + d, layer)]
    step = w / float(doors)
    for i in range(doors):
        hx = x0 + i * step
        ents.append(E_line(hx, y0, hx, y0 - step, layer))
        ents.append(E_arc(hx, y0, step, 270.0, 360.0, layer))
    return mod.Island(ents)


def D_line(layer, x0, y0, x1, y1):
    return [(0, "LINE"), (8, layer), (10, x0), (20, y0), (11, x1), (21, y1)]


def D_arc(layer, cx, cy, r, a0, a1):
    return [(0, "ARC"), (8, layer), (10, cx), (20, cy), (40, r), (50, a0), (51, a1)]


def D_elevation(layer, x0, y0, w, h, doors):
    """Mặt đứng tủ trong DXF: khung + vách chia + đường chéo ký hiệu cánh."""
    out = rect(layer, x0, y0, x0 + w, y0 + h)
    step = w / float(doors)
    for k in range(1, doors):
        out += D_line(layer, x0 + k * step, y0, x0 + k * step, y0 + h)
    for k in range(doors):
        a, b = x0 + k * step, x0 + (k + 1) * step
        out += D_line(layer, a, y0, b, y0 + h)
        out += D_line(layer, a, y0 + h, b, y0)
    return out


def D_plan(layer, x0, y0, w, d, doors):
    """Mặt bằng tủ trong DXF: khung + cung quét cánh vẽ thòi ra ngoài."""
    out = rect(layer, x0, y0, x0 + w, y0 + d)
    step = w / float(doors)
    for k in range(doors):
        hx = x0 + k * step
        out += D_line(layer, hx, y0, hx, y0 - step)
        out += D_arc(layer, hx, y0, step, 270.0, 360.0)
    return out


def make_wardrobe_row_dxf(n=2, w=1200.0, h=2400.0, d=600.0, doors=2, pitch=3000.0):
    """File CAD kiểu "BOX 2.dxf" trong ảnh hướng dẫn: một DÃY tủ, mỗi tủ có
    mặt đứng ở trên và mặt bằng (có cung quét cánh) ngay bên dưới."""
    head = [(0, "SECTION"), (2, "HEADER"), (9, "$INSUNITS"), (70, 4), (0, "ENDSEC")]
    ents = [(0, "SECTION"), (2, "ENTITIES")]
    for i in range(n):
        x0 = i * pitch
        ents += D_elevation("TU", x0, 1000.0, w, h, doors)
        ents += D_plan("TU", x0, 0.0, w, d, doors)
    ents += [(0, "ENDSEC"), (0, "EOF")]
    return dxf(*(head + ents))


def make_kitchen_dxf():
    """File CAD kiểu "K.dxf": CHỈ CÓ mặt đứng — mặt đứng chính ở giữa, 2
    mặt bên 2 đầu, KHÔNG có mặt bằng."""
    head = [(0, "SECTION"), (2, "HEADER"), (9, "$INSUNITS"), (70, 4), (0, "ENDSEC")]
    ents = [(0, "SECTION"), (2, "ENTITIES")]
    ents += D_elevation("BEP", 1000.0, 0.0, 2400.0, 2400.0, 4)
    ents += D_elevation("BEP", 200.0, 0.0, 600.0, 2400.0, 1)
    ents += D_elevation("BEP", 3600.0, 0.0, 600.0, 2400.0, 1)
    ents += [(0, "ENDSEC"), (0, "EOF")]
    return dxf(*(head + ents))


class TestScanProductsMultiple(unittest.TestCase):
    def test_row_of_wardrobes_becomes_many_families(self):
        """1 file CAD chứa 3 cái tủ -> phải ra 3 family riêng, mỗi cái đúng
        kích thước của nó, không gộp cả dãy làm một."""
        path = write_tmp(make_wardrobe_row_dxf(3), name=u"TỦ ÁO.dxf")
        seed = mod.group_files_into_plans([path], True)[0]
        plans = mod.scan_products(seed, mod.dxf_reader, True, True, True)
        self.assertEqual(len(plans), 3)
        names = set()
        for p in plans:
            self.assertEqual(p.category, "Casework")
            self.assertAlmostEqual(p.length, 1200.0, delta=5.0)
            self.assertAlmostEqual(p.width, 600.0, delta=5.0,
                                   msg=u"cung quét cánh không được tính vào chiều sâu tủ")
            self.assertAlmostEqual(p.height, 2400.0, delta=5.0)
            self.assertIn("PLAN", p.views)
            self.assertIn("FRONT", p.views)
            self.assertFalse(p.views["PLAN"].synthetic)
            self.assertEqual(len(p.parts), 2, u"tủ 2 cánh -> 2 khoang -> 2 family con")
            self.assertTrue(p.parts_equal)
            names.add(p.family_name)
        self.assertEqual(len(names), 3, u"tên family phải khác nhau")

    def test_side_view_is_synthesized_for_wardrobe(self):
        path = write_tmp(make_wardrobe_row_dxf(1), name=u"TỦ ÁO.dxf")
        seed = mod.group_files_into_plans([path], True)[0]
        p = mod.scan_products(seed, mod.dxf_reader, True, True, True)[0]
        self.assertIn("LEFT", p.views)
        self.assertTrue(p.views["LEFT"].synthetic)
        self.assertEqual(p.synth, ["LEFT"])
        self.assertIn(u"Trái*", p.views_display())

    def test_kitchen_elevations_only_get_synthetic_plan(self):
        """Bản vẽ chỉ có mặt đứng + mặt bên -> phải TỰ SUY RA mặt bằng."""
        path = write_tmp(make_kitchen_dxf(), name=u"BẾP.dxf")
        seed = mod.group_files_into_plans([path], True)[0]
        plans = mod.scan_products(seed, mod.dxf_reader, True, True, True)
        self.assertEqual(len(plans), 1, u"mặt đứng chính + 2 mặt bên = 1 sản phẩm")
        p = plans[0]
        self.assertIn("FRONT", p.views)
        self.assertFalse(p.views["FRONT"].synthetic)
        self.assertIn("PLAN", p.views)
        self.assertTrue(p.views["PLAN"].synthetic)
        self.assertAlmostEqual(p.length, 2400.0, delta=5.0)
        self.assertAlmostEqual(p.width, 600.0, delta=5.0,
                               msg=u"chiều sâu phải lấy từ BỀ NGANG mặt bên")
        self.assertAlmostEqual(p.height, 2400.0, delta=5.0)
        self.assertEqual(len(p.parts), 4, u"mặt đứng bếp 4 module -> 4 khoang")

    def test_multi_off_gives_single_plan(self):
        path = write_tmp(make_wardrobe_row_dxf(3), name=u"TỦ ÁO.dxf")
        seed = mod.group_files_into_plans([path], True)[0]
        plans = mod.scan_products(seed, mod.dxf_reader, False, True, True)
        self.assertEqual(len(plans), 1)

    def test_cad_origin_recorded_for_placement(self):
        """Toạ độ thật trên CAD phải được ghi lại để đặt family đúng vị trí."""
        path = write_tmp(make_wardrobe_row_dxf(2, pitch=5000.0), name=u"TỦ ÁO.dxf")
        seed = mod.group_files_into_plans([path], True)[0]
        plans = mod.scan_products(seed, mod.dxf_reader, True, True, True)
        xs = sorted(p.cad_origin[0] for p in plans)
        self.assertAlmostEqual(xs[0], 600.0, delta=5.0)
        self.assertAlmostEqual(xs[1], 5600.0, delta=5.0)


class TestIslandFrame(unittest.TestCase):
    def test_frame_ignores_door_swing(self):
        """Cung quét cánh vẽ thòi ra ngoài KHÔNG được tính vào kích thước tủ."""
        il = plan_island(0.0, 0.0, 2400.0, 600.0, 4)
        self.assertGreater(il.bbox[3] - il.bbox[1], 600.0)      # bbox bị phồng
        self.assertAlmostEqual(il.size()[0], 2400.0, places=3)  # frame thì đúng
        self.assertAlmostEqual(il.size()[1], 600.0, places=3)


class TestGridLines(unittest.TestCase):
    def test_extract_vertical_dividers(self):
        il = elevation_island(0.0, 0.0, 2400.0, 2400.0, 4)
        xs, ys, span = mod.extract_grid_lines(il)
        self.assertEqual(span, (2400.0, 2400.0))
        inner = sorted(mod.interior_values(xs, span[0]))
        self.assertEqual(len(inner), 3)
        for got, want in zip(inner, [600.0, 1200.0, 1800.0]):
            self.assertAlmostEqual(got, want, delta=30.0)
        self.assertEqual(mod.interior_values(ys, span[1]), [])

    def test_detect_bays(self):
        il = elevation_island(0.0, 0.0, 2400.0, 2400.0, 4)
        bays, span = mod.detect_bays(il)
        self.assertEqual(len(bays), 4)
        for (a, b) in bays:
            self.assertAlmostEqual(b - a, 600.0, delta=30.0)

    def test_subparts_dedupe(self):
        il = elevation_island(0.0, 0.0, 2400.0, 2400.0, 4)
        parts, equal = mod.build_subparts(il, 2400.0, 600.0, 2400.0)
        self.assertEqual(len(parts), 4)
        self.assertTrue(equal, u"4 cánh đều nhau phải nhận ra là đều")
        self.assertEqual(len(set(p.key for p in parts)), 1,
                         u"4 khoang giống hệt nhau chỉ cần 1 family con")
        self.assertAlmostEqual(parts[0].width, 600.0, delta=30.0)
        self.assertAlmostEqual(parts[0].depth, 600.0, places=3)

    def test_subparts_unequal(self):
        ents = [E_rect(0, 0, 2000, 2000)]
        ents.append(E_line(500, 0, 500, 2000))     # 500 | 1500
        il = mod.Island(ents)
        parts, equal = mod.build_subparts(il, 2000.0, 600.0, 2000.0)
        self.assertEqual(len(parts), 2)
        self.assertFalse(equal)
        self.assertEqual(len(set(p.key for p in parts)), 2)


class TestPlanLikeness(unittest.TestCase):
    def test_swing_arcs_mean_plan(self):
        pl = plan_island(0.0, 0.0)
        self.assertGreater(mod.count_swing_arcs(pl), 0)
        self.assertGreater(mod.plan_likeness(pl), 0)

    def test_leaf_diagonals_mean_elevation(self):
        el = elevation_island(0.0, 0.0)
        self.assertGreater(mod.count_leaf_diagonals(el), 0)
        self.assertLess(mod.plan_likeness(el), 0)


class TestSynthesizeViews(unittest.TestCase):
    def test_plan_and_side_from_front_only(self):
        """Bản vẽ CHỈ CÓ mặt đứng -> phải tự dựng ra mặt bằng và mặt bên."""
        front = elevation_island(0.0, 0.0, 2400.0, 2400.0, 4)
        front.kind = "FRONT"
        views = {"FRONT": front}
        views, made = mod.synthesize_views(views, 2400.0, 600.0, 2400.0, "Casework")
        self.assertEqual(sorted(made), ["LEFT", "PLAN"])
        pl = views["PLAN"]
        self.assertTrue(pl.synthetic)
        self.assertAlmostEqual(pl.size()[0], 2400.0, places=3)
        self.assertAlmostEqual(pl.size()[1], 600.0, places=3)
        # vách đứng của mặt đứng phải chiếu xuống thành vách trên mặt bằng
        xs, _ys, span = mod.extract_grid_lines(pl)
        self.assertEqual(len(mod.interior_values(xs, span[0])), 3)
        # và phải có ký hiệu cánh mở
        self.assertEqual(mod.count_swing_arcs(pl), 4)
        sd = views["LEFT"]
        self.assertAlmostEqual(sd.size()[0], 600.0, places=3)
        self.assertAlmostEqual(sd.size()[1], 2400.0, places=3)

    def test_front_and_side_from_plan_only(self):
        pl = plan_island(0.0, 0.0, 1800.0, 500.0, 3)
        pl.kind = "PLAN"
        views, made = mod.synthesize_views({"PLAN": pl}, 1800.0, 500.0, 900.0, "Casework")
        self.assertEqual(sorted(made), ["FRONT", "LEFT"])
        fr = views["FRONT"]
        self.assertAlmostEqual(fr.size()[0], 1800.0, places=3)
        self.assertAlmostEqual(fr.size()[1], 900.0, places=3)

    def test_shelf_heights_project_into_side_view(self):
        """Mặt kệ (đường ngang) trên mặt đứng phải xuất hiện đúng cao độ đó
        trên mặt bên — đúng nguyên tắc hình chiếu vuông góc."""
        ents = [E_rect(0, 0, 2000, 2000), E_line(0, 800, 2000, 800),
                E_line(0, 1400, 2000, 1400)]
        front = mod.Island(ents)
        front.kind = "FRONT"
        views, made = mod.synthesize_views({"FRONT": front}, 2000.0, 600.0, 2000.0,
                                           "Casework", door_swing=False)
        side = views["LEFT"]
        _xs, ys, span = mod.extract_grid_lines(side)
        inner = sorted(mod.interior_values(ys, span[1]))
        self.assertEqual(len(inner), 2)
        self.assertAlmostEqual(inner[0], 800.0, delta=30.0)
        self.assertAlmostEqual(inner[1], 1400.0, delta=30.0)

    def test_no_synth_when_all_present(self):
        views = {"PLAN": plan_island(0, 0), "FRONT": elevation_island(0, 5000),
                 "LEFT": elevation_island(5000, 5000, 600.0)}
        views, made = mod.synthesize_views(views, 2400.0, 600.0, 2400.0)
        self.assertEqual(made, [])


class TestGroupProducts(unittest.TestCase):
    def test_two_wardrobes_each_with_own_plan(self):
        """Dãy tủ: mỗi tủ có mặt đứng ở trên và mặt bằng ngay dưới nó →
        phải ra 2 sản phẩm, KHÔNG được gộp cả dãy làm một."""
        islands = [
            elevation_island(0.0, 1000.0, 1200.0, 2400.0, 2),
            plan_island(0.0, 0.0, 1200.0, 600.0, 2),
            elevation_island(2000.0, 1000.0, 1800.0, 2400.0, 3),
            plan_island(2000.0, 0.0, 1800.0, 600.0, 3),
        ]
        groups = mod.group_products(islands)
        self.assertEqual(len(groups), 2)
        for g in groups:
            self.assertEqual(len(g), 2)
            kinds = set()
            for il in g:
                kinds.add("PLAN" if mod.plan_likeness(il) > 0 else "ELEV")
            self.assertEqual(kinds, {"PLAN", "ELEV"})

    def test_kitchen_row_front_plus_two_sides(self):
        """Bản vẽ bếp chỉ có mặt đứng: mặt đứng chính ở giữa, 2 mặt bên 2
        đầu → gom thành 1 sản phẩm."""
        front = elevation_island(1000.0, 0.0, 2400.0, 2400.0, 4)
        left = elevation_island(200.0, 0.0, 600.0, 2400.0, 1)
        right = elevation_island(3600.0, 0.0, 600.0, 2400.0, 1)
        groups = mod.group_products([front, left, right])
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 3)

    def test_row_of_plans_not_merged(self):
        """Cả trang ký hiệu đồ đạc trên mặt bằng: mỗi ký hiệu là 1 sản phẩm."""
        islands = [plan_island(i * 3000.0, 0.0, 1200.0, 600.0, 2) for i in range(4)]
        groups = mod.group_products(islands)
        self.assertEqual(len(groups), 4)

    def test_disabled_returns_single_group(self):
        islands = [plan_island(0, 0), elevation_island(0, 5000)]
        self.assertEqual(len(mod.group_products(islands, False)), 1)


class TestClassifyWithoutPlan(unittest.TestCase):
    def test_front_left_right_when_no_plan(self):
        front = elevation_island(1000.0, 0.0, 2400.0, 2400.0, 4)
        left = elevation_island(200.0, 0.0, 600.0, 2400.0, 1)
        right = elevation_island(3600.0, 0.0, 600.0, 2400.0, 1)
        mod.classify_islands([front, left, right], u"BEP.dxf")
        self.assertEqual(front.kind, "FRONT")
        self.assertEqual(left.kind, "LEFT")
        self.assertEqual(right.kind, "RIGHT")

    def test_dimensions_ignore_synthetic_views(self):
        front = elevation_island(0.0, 0.0, 2400.0, 2400.0, 4)
        front.kind = "FRONT"
        views, _made = mod.synthesize_views({"FRONT": front}, 2400.0, 600.0, 2400.0, "Casework")
        L, W, H, _note = mod.infer_dimensions(list(views.values()), "Casework")
        self.assertAlmostEqual(H, 2400.0, places=3)


class TestCropIsland(unittest.TestCase):
    def test_crop_keeps_only_bay_content(self):
        il = elevation_island(0.0, 0.0, 2400.0, 2400.0, 4)
        bays, _span = mod.detect_bays(il)
        sub = mod.crop_island(il, bays[0][0], bays[0][1])
        self.assertIsNotNone(sub)
        self.assertLess(len(sub.ents), len(il.ents))
        for e in sub.drawable():
            b = mod.ent_bbox(e)
            self.assertLessEqual((b[0] + b[2]) / 2.0, 700.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
