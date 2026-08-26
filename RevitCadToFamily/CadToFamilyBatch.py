# -*- coding: utf-8 -*-
"""
================================================================================
 CAD → REVIT FAMILY BATCH  —  Dynamo Python Script (CPython3 engine)
 Tự tạo HÀNG LOẠT Family Revit (.rfa) từ file CAD (DWG/DXF)
================================================================================
CHỨC NĂNG (đúng những gì bạn yêu cầu trong 2 ảnh hướng dẫn):

  1. NHẬN ĐẦU VÀO theo 3 cách, trộn lẫn thoải mái:
       a) DÁN ĐƯỜNG DẪN 1 FILE CAD  (vd D:\\OUT\\REVIT\\FAMILY\\260825.dwg)
       b) DÁN ĐƯỜNG DẪN 1 THƯ MỤC chứa nhiều file CAD  → quét toàn bộ
          *.dwg / *.dxf trong đó (tuỳ chọn quét cả thư mục con)
       c) CHỌN SẴN CAD Link / CAD Import đang có trong Revit (IN[0]) →
          lấy thẳng hình học đang hiển thị, không cần import lại.

  2. "TƯ DUY" ĐỌC HIỂU BẢN VẼ CAD (không cần bạn khai báo gì):
       - Bóc toàn bộ nét (LINE / LWPOLYLINE / POLYLINE / ARC / CIRCLE /
         INSERT-block lồng nhau / TEXT / MTEXT) kèm TÊN LAYER.
       - Tự gom nét thành các "cụm bản vẽ" (island) tách rời nhau trên
         model space — chính là các hình chiếu bạn vẽ cạnh nhau.
       - Tự nhận diện từng cụm là hình chiếu nào: MẶT BẰNG (PLAN), MẶT
         ĐỨNG CHÍNH (FRONT), MẶT SAU (BACK), MẶT BÊN TRÁI (LEFT), MẶT BÊN
         PHẢI (RIGHT), MẶT CẮT (SECTION) — dựa trên: chữ ghi chú tiếng
         Việt/Anh trong bản vẽ ("MẶT BẰNG", "MĐ CHÍNH", "ELEVATION"...),
         tên layer, tên file, rồi mới tới suy luận hình học (vị trí tương
         đối, tỉ lệ khung, số vòng kín).
       - Tự đoán ĐƠN VỊ CAD (mm / cm / m / inch / feet) từ $INSUNITS hoặc
         từ độ lớn khung bao, rồi quy hết về mm.
       - Tự suy ra KÍCH THƯỚC THẬT: Dài (từ mặt bằng), Rộng (từ mặt
         bằng), Cao (từ mặt đứng) → điền sẵn vào GUI cho bạn sửa.
       - Tự đoán DANH MỤC REVIT từ tên file/layer: CỬA→Doors, CỬA SỔ→
         Windows, LAVABO/CHẬU RỬA/WC→Plumbing Fixtures, TỦ/KỆ/BÀN ĐÁ→
         Casework, BÀN/GHẾ/GIƯỜNG→Furniture, ĐÈN→Lighting Fixtures...

  3. TẠO FAMILY .rfa CHUẨN, ĐẦY ĐỦ CÁC MẶT:
       - Khối 3D (Extrusion) dựng từ biên dạng kín của MẶT BẰNG (lỗ bên
         trong tự thành lỗ rỗng), cao đúng theo mặt đứng.
       - NÉT VẼ LẠI ĐÚNG THEO CAD trên TỪNG HÌNH CHIẾU bằng Symbolic
         Curve: mặt bằng (Ref. Level), mặt đứng Front / Back / Left /
         Right — mở family ra là thấy đủ 5 mặt y như bản CAD gốc.
       - THAM SỐ (Parameter) KÉO DÃN ĐƯỢC: "Dài", "Rộng", "Cao" gắn nhãn
         (FamilyLabel) vào Dimension giữa các Reference Plane, và các mặt
         khối được Align + Lock vào Reference Plane → kéo tham số là khối
         co giãn thật, không phải tham số chết.
       - THAM SỐ THUẬT TOÁN (công thức): "Diện tích mặt bàn" = Dài*Rộng,
         "Nửa Dài" = Dài/2, "Cao lắp đặt" = Cao - Dày mặt... (bảng công
         thức khai báo ở CONFIG, bạn thêm bớt thoải mái).
       - Tham số nhận dạng: "Mã hiệu", "Nguồn CAD", "Người tạo", "Ngày tạo".

  4. GIAO DIỆN GUI SANG TRỌNG (WinForms, theme tối – vàng đồng), dạng
     bảng Excel: mỗi dòng là 1 file CAD → 1 family. Bạn được sửa TRỰC
     TIẾP trên lưới: bật/tắt từng dòng, đổi Tên family, Danh mục, Dài /
     Rộng / Cao, Chế độ dựng khối. Có nút chọn thư mục CAD, chọn nhiều
     file, chọn thư mục xuất .rfa, áp dụng nhanh cho các dòng đang chọn.

  5. TỐC ĐỘ: chạy hàng loạt, mỗi family gói gọn trong ĐÚNG 1 Transaction,
     có chế độ TURBO (giản lược nét thừa, bỏ quét sâu) và ĐO TỐC ĐỘ THẬT
     rồi báo lại (family/giây) — không tuyên bố suông.

--------------------------------------------------------------------------------
CÁCH DÙNG TRONG DYNAMO (nối IN[1] = Boolean True là chạy được ngay):
  - IN[0] (tuỳ chọn): danh sách CAD Link / CAD Import đã chọn sẵn trong
    Revit (node "Select Model Elements"). Để trống nếu bạn muốn nhập
    đường dẫn file/thư mục trên GUI.
  - IN[1] (khuyên dùng): Boolean True/False — công tắc bảo vệ.
    False = KHÔNG làm gì cả (an toàn tuyệt đối). True/không nối = chạy.
  - IN[2] (tuỳ chọn): String — đường dẫn FILE CAD hoặc THƯ MỤC chứa CAD.
    Điền sẵn vào ô đường dẫn của GUI (bạn vẫn sửa được trên GUI).
  - IN[3] (tuỳ chọn): String — thư mục xuất file .rfa. Để trống = tạo
    thư mục "REVIT_FAMILY_OUT" ngay cạnh thư mục CAD nguồn.
  - IN[4] (tuỳ chọn): String — thư mục chứa Family Template (.rft).
    Để trống = tự dò trong C:\\ProgramData\\Autodesk\\RVT xxxx\\Family Templates.
  - IN[5] (tuỳ chọn): Boolean — True = nạp luôn family vừa tạo vào project
    đang mở. Mặc định False (chỉ xuất ra file .rfa).
  - IN[6] (nâng cao): Boolean — True = chạy thẳng KHÔNG mở GUI (dùng toàn
    bộ giá trị tự dò). Mặc định False (luôn mở GUI để bạn duyệt/sửa).

  Nhớ đổi ENGINE của node Python Script sang "CPython3"
  (chuột phải vào node → Change Engine → CPython3).

OUT: Dictionary gồm
  "Status"          : "Done" / "Cancelled" / "Idle" / "NoInput" / "Error"
  "Created"         : số family đã tạo thành công
  "Failed"          : số family lỗi
  "Files"           : danh sách file .rfa đã xuất
  "Report"          : bảng tóm tắt từng dòng (list các list)
  "Warnings"        : cảnh báo / lỗi chi tiết
  "BuildMs"         : thời gian THỰC ghi/tạo family (không tính lúc bạn
                      đang thao tác trên GUI)
  "FamiliesPerSec"  : tốc độ thật đo được = Created / (BuildMs/1000)
  "ElapsedMs"       : tổng thời gian kể cả thời gian mở GUI

--------------------------------------------------------------------------------
LƯU Ý TRUNG THỰC (đọc kỹ trước khi chạy hàng loạt):
  Script viết đúng chuẩn Revit API (Application.NewFamilyDocument,
  FamilyManager.AddParameter, FamilyCreate.NewExtrusion / NewAlignment /
  NewDimension / NewSymbolicCurve, Document.Import, SaveAs...) nhưng môi
  trường tạo mã này KHÔNG có Revit/Dynamo để chạy thử thật. Phần LOGIC
  THUẦN PYTHON (đọc DXF, gom cụm, nhận diện hình chiếu, suy kích thước,
  ghép vòng kín, đặt tên, chọn template) ĐÃ được kiểm thử tự động bằng
  tests/test_cad_family_core.py. Phần gọi Revit API thì mỗi bước đều được
  bọc try/except riêng và ghi cảnh báo, để 1 bước lỗi không làm hỏng cả
  family/cả lô. Lần đầu dùng: hãy chạy thử 1–2 file CAD, mở .rfa ra kiểm
  tra, rồi mới chạy cả thư mục.
================================================================================
"""

import os
import re
import time
import math
import glob
import traceback
import unicodedata

# ------------------------------------------------------------------------
# 1. IMPORTS & MÔI TRƯỜNG REVIT / DYNAMO
#    Toàn bộ import Revit gói trong 1 try/except: chạy ngoài Revit (vd khi
#    chạy unit test) thì REVIT_API = False và mọi hàm đụng Revit sẽ báo lỗi
#    có kiểm soát thay vì làm vỡ cả file lúc import.
# ------------------------------------------------------------------------
REVIT_API = False
REVIT_IMPORT_ERROR = ""
try:
    import clr

    clr.AddReference('RevitAPI')
    clr.AddReference('RevitAPIUI')
    from Autodesk.Revit.DB import (
        XYZ, Line, Arc, Plane, SketchPlane, Transaction, SaveAsOptions,
        Options, ViewDetailLevel, Curve, CurveArray, CurveArrArray,
        FilteredElementCollector, BuiltInCategory, BuiltInParameter, Category,
        View, ViewType, ReferenceArray, Level,
        ImportInstance, GeometryInstance, PolyLine, Solid, PlanarFace,
        DWGImportOptions, ImportPlacement, ImportUnit, ImportColorMode,
        FamilyElementVisibility, FamilyElementVisibilityType, GraphicsStyleType,
    )
    REVIT_API = True
except Exception as _revit_exc:      # ngoài Revit (unit test / máy không có Revit)
    REVIT_IMPORT_ERROR = str(_revit_exc)

# ForgeTypeId (Revit >= 2021/2022) vs API cũ (ParameterType/BuiltInParameterGroup).
# Giữ CẢ HAI để script chạy được trên nhiều đời Revit.
FORGE_API = False
try:
    from Autodesk.Revit.DB import SpecTypeId, GroupTypeId
    FORGE_API = True
except Exception:
    SpecTypeId = None
    GroupTypeId = None
try:
    from Autodesk.Revit.DB import ParameterType, BuiltInParameterGroup
except Exception:
    ParameterType = None
    BuiltInParameterGroup = None

# RevitServices chỉ tồn tại khi chạy trong Dynamo.
DYNAMO_ENV = False
TransactionManager = None
try:
    clr.AddReference('RevitServices')
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    DYNAMO_ENV = True
except Exception:
    DYNAMO_ENV = False

# --------------------------------------------------------------------
# GUI: WinForms "EVENTLESS" — KHÔNG WPF/XAML, KHÔNG event, KHÔNG subclass.
#
# Lý do (đã gặp thật ở dự án này trên Dynamo 2.19 / Revit 2024 + CPython3):
# PythonNet phải phát assembly động (System.Reflection.Emit.TypeBuilder) khi
# Python đăng ký callback vào delegate .NET hoặc kế thừa class .NET, và việc
# đó bị chặn trong tiến trình Revit → ném lỗi
#   "Constructor on type 'System.Reflection.Emit.TypeBuilder' not found".
# Cách né tuyệt đối:
#   1) KHÔNG subclass bất kỳ kiểu .NET nào (kể cả IFamilyLoadOptions — vì
#      vậy script nạp family bằng Document.LoadFamily(path) bản string,
#      không cần interface);
#   2) KHÔNG đăng ký sự kiện .NET từ Python;
#   3) Mọi tương tác đi qua Button.DialogResult + Form.ShowDialog() (100%
#      xử lý bên trong .NET), Python dựng lại cửa sổ ở mỗi bước — "wizard
#      eventless".
# --------------------------------------------------------------------
GUI_AVAILABLE = False
GUI_IMPORT_ERROR = ""
try:
    clr.AddReference('System.Windows.Forms')
    clr.AddReference('System.Drawing')
    from System.Windows.Forms import (
        Form, Label, TextBox, Button, ComboBox, ComboBoxStyle, Panel, DockStyle,
        CheckBox, DataGridView, DataGridViewTextBoxColumn, DataGridViewCheckBoxColumn,
        DataGridViewSelectionMode, DataGridViewColumnHeadersHeightSizeMode,
        DataGridViewAutoSizeColumnsMode, DataGridViewColumnSortMode,
        DialogResult, FormStartPosition, FormBorderStyle, FlatStyle,
        MessageBox, MessageBoxButtons, MessageBoxIcon, Application,
        FolderBrowserDialog, OpenFileDialog, AnchorStyles, BorderStyle, Screen,
    )
    from System.Drawing import (
        Color, Font, FontStyle, Point, Size, GraphicsUnit, SystemFonts,
        ContentAlignment,
    )
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
    try:
        app = doc.Application
    except Exception:
        app = None
else:
    doc = None
    uiapp = None
    app = None


# ------------------------------------------------------------------------
# 2. CẤU HÌNH (CONFIG) — mọi thứ cần chỉnh tay đều nằm gọn ở đây
# ------------------------------------------------------------------------
MM_PER_FT = 304.8            # 1 foot = 304.8 mm (đơn vị nội bộ Revit là feet)

CAD_EXTENSIONS = (".dwg", ".dxf")

# Dung sai (mm) khi ghép các nét rời thành 1 vòng kín.
LOOP_JOIN_TOL_MM = 0.8
# Nét ngắn hơn mức này coi như rác, bỏ qua (mm).
MIN_SEG_LEN_MM = 0.2
# Số đoạn thẳng dùng để chia nhỏ 1 cung tròn 90° (càng lớn càng mượt/càng chậm).
ARC_SEG_PER_QUARTER = 6
# Dung sai giản lược nét (Douglas–Peucker, mm) ở chế độ TURBO.
TURBO_SIMPLIFY_TOL_MM = 1.5
# Giới hạn số nét vẽ lại trên MỖI hình chiếu (chống treo Revit với file CAD
# khổng lồ). 0 = không giới hạn.
MAX_CURVES_PER_VIEW = 4000
MAX_CURVES_PER_VIEW_TURBO = 900
# Số vòng lỗ (inner loop) tối đa đưa vào 1 khối extrusion.
MAX_INNER_LOOPS = 40

# Khoảng hở (tính theo % cạnh lớn nhất của toàn bản vẽ) để tách 2 cụm bản vẽ
# rời nhau. 4% là mức thực nghiệm hợp lý cho bản vẽ nội thất/cửa.
ISLAND_GAP_RATIO = 0.04
# Cụm nhỏ hơn tỉ lệ này so với cụm lớn nhất bị coi là ghi chú/khung tên, bỏ qua.
ISLAND_MIN_AREA_RATIO = 0.012

# Kích thước mặc định (mm) khi bản vẽ không đủ dữ liệu để suy ra.
DEFAULT_DIMS = {
    "Doors":            (900.0, 200.0, 2200.0),
    "Windows":          (1200.0, 200.0, 1500.0),
    "PlumbingFixtures": (600.0, 500.0, 850.0),
    "Casework":         (1200.0, 600.0, 850.0),
    "Furniture":        (1200.0, 600.0, 750.0),
    "LightingFixtures": (300.0, 300.0, 200.0),
    "SpecialityEquipment": (800.0, 600.0, 900.0),
    "GenericModel":     (1000.0, 500.0, 800.0),
}

# Từ khoá tên file / layer → danh mục Revit. Không dấu, viết HOA, so khớp
# theo kiểu "chứa chuỗi con". Thứ tự trong list = thứ tự ưu tiên xét.
CATEGORY_KEYWORDS = [
    # Windows đứng TRƯỚC Doors: "CỬA SỔ" phải khớp Windows chứ không được
    # rơi vào từ khoá chung " CUA " của Doors.
    ("Windows", [" CUA SO", " CUASO", " WINDOW", " CSO ", " VACH KINH "]),
    ("Doors", [" CUA DI", " CUADI", " DOOR", " CDI ", " CUA D", " CUA "]),
    ("PlumbingFixtures", [" LAVABO", " CHAU RUA", " CHAURUA", " BON RUA",
                          " BONRUA", " XI BET", " XIBET", " BON CAU", " BONCAU",
                          " TIEU NAM", " TIEUNAM", " TIEU TREO", " WC ", " TOILET",
                          " BASIN", " SINK", " URINAL", " CLOSET", " SEN VOI",
                          " VOI SEN", " BON TAM", " BATHTUB", " SANITARY",
                          " THIET BI VE SINH", " VE SINH "]),
    ("Casework", [" TU BEP", " TUBEP", " TU AO", " TU QUAN AO", " CABINET",
                  " CASEWORK", " KE ", " KE SACH", " QUAY ", " COUNTER",
                  " BAN DA", " BANDA", " VANITY", " TU "]),
    ("Furniture", [" BAN LAM VIEC", " BANLAMVIEC", " GHE", " CHAIR", " TABLE",
                   " DESK", " SOFA", " GIUONG", " BED ", " FURNITURE",
                   " NOI THAT", " BAN "]),
    ("LightingFixtures", [" DEN ", " DEN LED", " DENLED", " LIGHT", " LAMP",
                          " CHIEU SANG"]),
    ("SpecialityEquipment", [" THIET BI", " THIETBI", " EQUIPMENT", " MAY "]),
]

# Danh mục → BuiltInCategory (đặt bằng tên chuỗi để tra bằng getattr, tránh
# lỗi import trên các đời Revit thiếu 1 vài enum).
CATEGORY_BIC = {
    "Doors": "OST_Doors",
    "Windows": "OST_Windows",
    "PlumbingFixtures": "OST_PlumbingFixtures",
    "Casework": "OST_Casework",
    "Furniture": "OST_Furniture",
    "LightingFixtures": "OST_LightingFixtures",
    "SpecialityEquipment": "OST_SpecialityEquipment",
    "GenericModel": "OST_GenericModel",
}

# Danh mục → từ khoá tìm file template .rft. Bao gồm cả bản cài tiếng Anh,
# tiếng Việt và tiếng Trung (bản cài hay gặp ở VN).
TEMPLATE_KEYWORDS = {
    "Doors":            ["metric door", "door", "公制门", "门", "cua di"],
    "Windows":          ["metric window", "window", "公制窗", "窗", "cua so"],
    "PlumbingFixtures": ["metric plumbing fixture", "plumbing fixture", "公制卫浴装置",
                         "卫浴", "thiet bi ve sinh"],
    "Casework":         ["metric casework", "casework", "公制橱柜", "橱柜", "tu"],
    "Furniture":        ["metric furniture", "furniture", "公制家具", "家具", "noi that"],
    "LightingFixtures": ["metric lighting fixture", "lighting fixture", "公制照明设备",
                         "照明", "den"],
    "SpecialityEquipment": ["metric specialty equipment", "specialty equipment",
                            "speciality equipment", "公制专用设备", "专用设备"],
    "GenericModel":     ["metric generic model", "generic model", "公制常规模型",
                         "常规模型", "mo hinh khoi"],
}

# Danh mục mà Revit KHÔNG cho đổi category từ template khác (phải dùng đúng
# template gốc vì có host là tường + có Opening dựng sẵn).
HOST_BOUND_CATEGORIES = ("Doors", "Windows")

# Tên tham số (tiếng Việt, đúng gu bản vẽ VN). Đổi ở đây là đổi toàn bộ.
P_LEN = u"Dài"
P_WID = u"Rộng"
P_HGT = u"Cao"

# Tham số công thức ("thuật toán") tự thêm vào mỗi family.
#   (tên, loại spec, công thức, là tham số Instance?)
# Loại spec: "LENGTH" | "AREA" | "VOLUME" | "NUMBER" | "TEXT" | "YESNO"
FORMULA_PARAMS = [
    (u"Nửa Dài",         "LENGTH", u"%s / 2" % P_LEN,           False),
    (u"Nửa Rộng",        "LENGTH", u"%s / 2" % P_WID,           False),
    (u"Diện tích chiếm chỗ", "AREA", u"%s * %s" % (P_LEN, P_WID), False),
    (u"Thể tích bao",    "VOLUME", u"%s * %s * %s" % (P_LEN, P_WID, P_HGT), False),
    (u"Tỉ lệ Dài/Rộng",  "NUMBER", u"%s / %s" % (P_LEN, P_WID), False),
]

# Tham số nhận dạng (điền giá trị, không có công thức).
IDENTITY_PARAMS = [
    (u"Mã hiệu",    "TEXT"),
    (u"Nguồn CAD",  "TEXT"),
    (u"Ngày tạo",   "TEXT"),
]

# Từ khoá nhận diện hình chiếu trong CHỮ của bản vẽ và trong TÊN LAYER/FILE.
# Đã bỏ dấu + viết HOA trước khi so khớp.
VIEW_KEYWORDS = [
    ("PLAN",    ["MAT BANG", "MATBANG", "MB ", " MB", "-MB", "_MB", "PLAN",
                 "TOP VIEW", "TOPVIEW", "BANG VE MAT BANG", "HINH CHIEU BANG"]),
    ("FRONT",   ["MAT DUNG CHINH", "MATDUNGCHINH", "MAT TRUOC", "MATTRUOC",
                 "MD CHINH", "FRONT", "ELEVATION FRONT", "HINH CHIEU DUNG",
                 "MAT DUNG TRUOC", "TRUOC"]),
    ("BACK",    ["MAT SAU", "MATSAU", "MD SAU", "BACK", "REAR", "PHIA SAU"]),
    ("LEFT",    ["MAT BEN TRAI", "MAT TRAI", "MATTRAI", "MD TRAI", "BEN TRAI",
                 "LEFT", "SIDE LEFT"]),
    ("RIGHT",   ["MAT BEN PHAI", "MAT PHAI", "MATPHAI", "MD PHAI", "BEN PHAI",
                 "RIGHT", "SIDE RIGHT"]),
    ("SECTION", ["MAT CAT", "MATCAT", "SECTION", "CAT A", "CAT B"]),
    # Đặt "MAT DUNG"/"MD" chung cuối cùng: nếu không rõ trái/phải/sau thì coi
    # là mặt đứng chính (FRONT).
    ("FRONT",   ["MAT DUNG", "MATDUNG", "MD ", " MD", "-MD", "_MD",
                 "ELEVATION", "ELEV"]),
]

# Thứ tự gán mặc định cho các cụm mặt đứng khi bản vẽ KHÔNG ghi chú gì:
# xếp từ trái sang phải trên model space.
ELEVATION_FALLBACK_ORDER = ["FRONT", "LEFT", "RIGHT", "BACK"]

# Layer thường là ghi chú/kích thước/khung tên → KHÔNG vẽ lại vào family.
# Layer thường là ghi chú/kích thước/khung tên → KHÔNG vẽ lại vào family.
# Quy ước: khoảng trắng ở đầu/cuối = bắt buộc đúng ranh giới từ (xem
# kw_pattern). CỐ Ý không đưa từ đơn "CHU" vào đây: nó trùng với "CHỮ NHẬT",
# "CHÚ THÍCH"... nên sẽ loại oan layer vật liệu; đã có "GHI CHU"/"CHU THICH"/
# "TEXT"/"NOTE" phủ các trường hợp thật.
NOISE_LAYER_KEYWORDS = [
    " DIM", " KICH THUOC", " KICHTHUOC", " TEXT", " GHI CHU", " GHICHU",
    " CHU THICH", " NOTE", " HATCH", " TITLE", " KHUNG TEN", " KHUNGTEN",
    " AXIS", " TRUC ", " DEFPOINTS", " VIEWPORT", " GRID", " LEADER",
    " TAG ", " SCALE", " ANNOTATION",
]

# Chế độ dựng khối 3D.
MODE_HYBRID = "HYBRID"    # khối hộp tham số + nét CAD đủ 5 mặt   (MẶC ĐỊNH)
MODE_PROFILE = "PROFILE"  # đùn đúng biên dạng CAD (hình chuẩn, ít co giãn)
MODE_LINES = "LINES"      # chỉ nét CAD, không khối 3D
MODE_BOX = "BOX"          # chỉ khối hộp tham số, không nét CAD
BUILD_MODES = [MODE_HYBRID, MODE_PROFILE, MODE_BOX, MODE_LINES]
BUILD_MODE_LABEL = {
    MODE_HYBRID:  u"HYBRID – hộp tham số + nét CAD 5 mặt (khuyên dùng)",
    MODE_PROFILE: u"PROFILE – đùn đúng biên dạng CAD",
    MODE_BOX:     u"BOX – chỉ khối hộp tham số",
    MODE_LINES:   u"LINES – chỉ nét CAD, không khối",
}

THEME = {
    "bg":        "#0F1115",
    "panel":     "#171A21",
    "panel2":    "#1E2028",
    "gold":      "#E8C37A",
    "gold_dark": "#C9A227",
    "text":      "#E6E6E6",
    "text_dim":  "#9AA0A6",
    "grid_line": "#2A2E37",
    "row_alt":   "#14161C",
    "ok":        "#7CD992",
    "err":       "#FF7A7A",
}


# ------------------------------------------------------------------------
# 3. TIỆN ÍCH CHUNG (thuần Python — có unit test)
# ------------------------------------------------------------------------
_VN_EXTRA = {u"đ": u"d", u"Đ": u"D"}


def strip_accents(s):
    """Bỏ dấu tiếng Việt: "MẶT ĐỨNG" -> "MAT DUNG". Dùng để so khớp từ khoá
    mà không phụ thuộc người vẽ gõ có dấu hay không dấu."""
    if s is None:
        return u""
    try:
        s = u"%s" % s
    except Exception:
        return u""
    for k, v in _VN_EXTRA.items():
        s = s.replace(k, v)
    try:
        nfd = unicodedata.normalize("NFD", s)
        return u"".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    except Exception:
        return s


def norm_key(s):
    """Chuẩn hoá về dạng so khớp: bỏ dấu, viết HOA, gộp mọi ký tự phân cách
    ( _ - . ) thành 1 khoảng trắng. "cua_di-P1.dwg" -> "CUA DI P1 DWG"."""
    s = strip_accents(s).upper()
    s = re.sub(r"[\s_\-\.\+/\\\(\)\[\]#]+", u" ", s)
    return re.sub(r"\s+", u" ", s).strip()


def mm_to_ft(v):
    return float(v) / MM_PER_FT


def ft_to_mm(v):
    return float(v) * MM_PER_FT


def fmt_mm(v):
    """Hiển thị mm gọn gàng: 900.0 -> "900", 899.75 -> "899.8"."""
    try:
        v = float(v)
    except Exception:
        return u""
    if abs(v - round(v)) < 0.05:
        return u"%d" % int(round(v))
    return u"%.1f" % v


def parse_number(s, default=None):
    """Đọc số từ ô người dùng gõ trên GUI: chấp nhận "1.200,5", "1200.5",
    "1200 mm", " 1200 "."""
    if s is None:
        return default
    if isinstance(s, (int, float)):
        return float(s)
    t = u"%s" % s
    t = t.strip()
    if not t:
        return default
    t = re.sub(r"[^\d,\.\-]", u"", t)
    if not t:
        return default
    # Phân biệt dấu phẩy THẬP PHÂN (kiểu VN) với dấu phẩy NGÌN (kiểu Anh):
    #   "1.200,5" và "1200,5" -> 1200.5   (sau dấu phẩy không phải đúng 3 số)
    #   "1,200"               -> 1200     (sau dấu phẩy đúng 3 số = phân nhóm nghìn)
    if t.count(",") == 1 and t.count(".") >= 1 and t.rfind(",") > t.rfind("."):
        t = t.replace(".", "").replace(",", ".")
    elif t.count(",") == 1 and t.count(".") == 0 and len(t.split(",")[1]) != 3:
        t = t.replace(",", ".")
    else:
        t = t.replace(",", "")
    try:
        return float(t)
    except Exception:
        return default


def sanitize_family_name(name, fallback=u"FAMILY"):
    """Tên family hợp lệ cho Windows/Revit: bỏ ký tự cấm \\ / : * ? " < > | { }
    và cắt bớt độ dài. Giữ nguyên dấu tiếng Việt (Revit hỗ trợ tốt)."""
    if name is None:
        name = u""
    n = u"%s" % name
    n = re.sub(r'[\\/:\*\?"<>\|\{\}]+', u"-", n)
    n = re.sub(r"\s+", u" ", n).strip(" .-_")
    if not n:
        n = fallback
    return n[:180]


def unique_name(name, used):
    """Tránh trùng tên family trong cùng 1 lô: THEM hậu tố _2, _3..."""
    base = name
    i = 2
    while name.lower() in used:
        name = u"%s_%d" % (base, i)
        i += 1
    used.add(name.lower())
    return name


def list_cad_files(path, recursive=False):
    """Nhận 1 chuỗi đường dẫn (file HOẶC thư mục) và trả về danh sách file
    CAD. Chấp nhận nhiều đường dẫn cách nhau bằng dấu ; hoặc xuống dòng —
    đúng kiểu bạn copy nhiều dòng từ Explorer dán vào."""
    out = []
    if not path:
        return out
    if isinstance(path, (list, tuple)):
        parts = list(path)
    else:
        parts = re.split(r"[;\r\n]+", u"%s" % path)
    for raw in parts:
        p = (raw or u"").strip().strip('"').strip("'")
        if not p:
            continue
        try:
            if os.path.isdir(p):
                pattern = "**/*" if recursive else "*"
                for f in sorted(glob.glob(os.path.join(p, pattern), recursive=recursive)):
                    if os.path.isfile(f) and f.lower().endswith(CAD_EXTENSIONS):
                        out.append(os.path.abspath(f))
            elif os.path.isfile(p) and p.lower().endswith(CAD_EXTENSIONS):
                out.append(os.path.abspath(p))
        except Exception:
            continue
    # bỏ trùng, giữ thứ tự
    seen = set()
    uniq = []
    for f in out:
        k = f.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    return uniq


def default_output_dir(cad_files, explicit=None):
    """Thư mục xuất .rfa: ưu tiên đường dẫn bạn chỉ định; nếu không thì tạo
    "REVIT_FAMILY_OUT" ngay cạnh file CAD đầu tiên."""
    if explicit:
        return u"%s" % explicit
    if cad_files:
        return os.path.join(os.path.dirname(cad_files[0]), "REVIT_FAMILY_OUT")
    return os.path.join(os.path.expanduser("~"), "REVIT_FAMILY_OUT")


def ensure_dir(path):
    try:
        if path and not os.path.isdir(path):
            os.makedirs(path)
        return True
    except Exception:
        return False


def kw_pattern(k):
    """Chuẩn hoá 1 từ khoá NHƯNG GIỮ khoảng trắng ở biên — khoảng trắng biên
    chính là dấu hiệu "phải đúng ranh giới từ". Vd " TU " chỉ khớp từ TU đứng
    riêng, không khớp "TUONG"; còn " DOOR" khớp cả "DOOR" lẫn "DOORS"."""
    if not k:
        return u""
    lead = u" " if k[:1] == u" " else u""
    trail = u" " if k[-1:] == u" " else u""
    core = norm_key(k)
    if not core:
        return u""
    return lead + core + trail


def contains_keyword(text, keyword):
    """So khớp từ khoá (không dấu, không phân biệt hoa thường, tôn trọng ranh
    giới từ nếu keyword có khoảng trắng ở biên)."""
    pat = kw_pattern(keyword)
    if not pat:
        return False
    return (u" %s " % norm_key(text)).find(pat) >= 0


def guess_category(*texts):
    """Đoán danh mục Revit từ tên file / tên layer / chữ trong bản vẽ.
    Trả về khoá trong CATEGORY_BIC. Không đoán được -> "GenericModel"."""
    blob = u" %s " % norm_key(u" ".join(u"%s" % t for t in texts if t))
    for cat, keys in CATEGORY_KEYWORDS:
        for k in keys:
            pat = kw_pattern(k)
            if pat and blob.find(pat) >= 0:
                return cat
    return "GenericModel"


# ------------------------------------------------------------------------
# 4. ĐỌC FILE CAD
#    4a. Bộ đọc DXF thuần Python (không cần Revit) — dùng cho: quét nhanh
#        danh sách file trên GUI, và dựng family từ .dxf mà KHÔNG cần
#        import vào Revit (nhanh hơn hẳn).
#    4b. File .dwg là định dạng nhị phân độc quyền, Python không đọc trực
#        tiếp được → dùng chính Revit để Import rồi bóc hình học (mục 8).
# ------------------------------------------------------------------------
class CadEnt(object):
    """1 đối tượng CAD đã chuẩn hoá về đơn vị mm, mặt phẳng XY.
      kind  : "POLY" | "ARC" | "CIRCLE" | "TEXT"
      layer : tên layer (chuỗi)
      pts   : list [(x, y), ...] — POLY: các đỉnh; TEXT: 1 điểm neo
      closed: POLY có khép kín không
      center/radius/a0/a1: dùng cho ARC (a0, a1 tính bằng ĐỘ, ngược kim đồng hồ)
      text  : nội dung chữ (TEXT/MTEXT)"""

    __slots__ = ("kind", "layer", "pts", "closed", "center", "radius",
                 "a0", "a1", "text")

    def __init__(self, kind, layer=u"0", pts=None, closed=False, center=None,
                 radius=0.0, a0=0.0, a1=360.0, text=u""):
        self.kind = kind
        self.layer = layer or u"0"
        self.pts = pts or []
        self.closed = bool(closed)
        self.center = center
        self.radius = float(radius or 0.0)
        self.a0 = float(a0)
        self.a1 = float(a1)
        self.text = text or u""

    def points(self):
        """Trả về đường gấp khúc xấp xỉ của đối tượng (dùng để tính khung
        bao, gom cụm, ghép vòng kín)."""
        if self.kind == "POLY":
            pts = list(self.pts)
            if self.closed and len(pts) > 2 and pts[0] != pts[-1]:
                pts.append(pts[0])
            return pts
        if self.kind == "CIRCLE":
            return arc_points(self.center, self.radius, 0.0, 360.0)
        if self.kind == "ARC":
            return arc_points(self.center, self.radius, self.a0, self.a1)
        return list(self.pts)

    def scaled(self, k):
        """Nhân toàn bộ toạ độ với k (đổi đơn vị CAD -> mm)."""
        if k == 1.0:
            return self
        pts = [(x * k, y * k) for (x, y) in self.pts]
        ctr = (self.center[0] * k, self.center[1] * k) if self.center else None
        return CadEnt(self.kind, self.layer, pts, self.closed, ctr,
                      self.radius * k, self.a0, self.a1, self.text)

    def moved(self, dx, dy):
        pts = [(x + dx, y + dy) for (x, y) in self.pts]
        ctr = (self.center[0] + dx, self.center[1] + dy) if self.center else None
        return CadEnt(self.kind, self.layer, pts, self.closed, ctr,
                      self.radius, self.a0, self.a1, self.text)

    def is_drawable(self):
        return self.kind in ("POLY", "ARC", "CIRCLE")


def arc_points(center, radius, a0_deg, a1_deg, seg_per_quarter=None):
    """Chia nhỏ cung tròn thành đường gấp khúc. Góc theo ĐỘ, ngược chiều kim
    đồng hồ, đúng quy ước DXF."""
    if not center or radius <= 0:
        return []
    n_q = seg_per_quarter or ARC_SEG_PER_QUARTER
    a0 = float(a0_deg)
    a1 = float(a1_deg)
    sweep = a1 - a0
    while sweep <= 0:
        sweep += 360.0
    while sweep > 360.0:
        sweep -= 360.0
    n = max(2, int(math.ceil(abs(sweep) / 90.0 * n_q)))
    cx, cy = center
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + sweep * i / float(n))
        out.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return out


def bulge_points(p1, p2, bulge, seg_per_quarter=None):
    """Đổi 1 đoạn LWPOLYLINE có "bulge" (độ phình) thành đường gấp khúc.
    bulge = tan(góc mở / 4) — quy ước DXF."""
    if not bulge:
        return [p1, p2]
    x1, y1 = p1
    x2, y2 = p2
    chord = math.hypot(x2 - x1, y2 - y1)
    if chord < 1e-9:
        return [p1, p2]
    theta = 4.0 * math.atan(abs(bulge))          # góc mở (radian)
    radius = chord / (2.0 * math.sin(theta / 2.0))
    # tâm nằm trên trung trực của dây cung
    mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    h = math.sqrt(max(radius * radius - (chord / 2.0) ** 2, 0.0))
    ux, uy = (x2 - x1) / chord, (y2 - y1) / chord
    nx, ny = -uy, ux
    sign = 1.0 if bulge > 0 else -1.0
    cx, cy = mx - nx * h * sign, my - ny * h * sign
    a0 = math.degrees(math.atan2(y1 - cy, x1 - cx))
    a1 = math.degrees(math.atan2(y2 - cy, x2 - cx))
    if bulge < 0:
        a0, a1 = a1, a0
    pts = arc_points((cx, cy), radius, a0, a1, seg_per_quarter)
    if bulge < 0:
        pts.reverse()
    if pts:
        pts[0] = p1
        pts[-1] = p2
        return pts
    return [p1, p2]


# --- Bảng đơn vị $INSUNITS của DXF -> hệ số quy đổi ra mm --------------
INSUNITS_TO_MM = {
    0: None,        # không xác định
    1: 25.4,        # inch
    2: 304.8,       # feet
    4: 1.0,         # mm
    5: 10.0,        # cm
    6: 1000.0,      # m
    8: 0.0254,      # micro-inch
    9: 0.0254 * 1000,   # mil
    10: 914.4,      # yard
    13: 0.000001,   # micromet
    14: 100.0,      # decimet
    15: 10000.0,    # decamet
}


def dxf_read_text(path):
    """Đọc file DXF dạng text với nhiều bảng mã (CAD ở VN hay lưu cp1258 /
    cp1252). Trả về (nội dung, lỗi)."""
    if not os.path.isfile(path):
        return None, u"Không tìm thấy file: %s" % path
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except Exception as ex:
        return None, u"Không đọc được file: %s" % ex
    if raw[:18] == b"AutoCAD Binary DXF":
        return None, u"DXF nhị phân (Binary DXF) — hãy Save As sang DXF dạng ASCII."
    for enc in ("utf-8-sig", "utf-8", "cp1258", "cp1252", "latin-1"):
        try:
            return raw.decode(enc), None
        except Exception:
            continue
    return raw.decode("latin-1", "ignore"), None


def dxf_pairs(text):
    """Tách nội dung DXF thành các cặp (mã nhóm, giá trị). DXF là định dạng
    2 dòng/1 cặp: dòng lẻ là mã nhóm (số), dòng chẵn là giá trị."""
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i + 1 < n:
        code_raw = lines[i].strip()
        val = lines[i + 1].rstrip("\r\n")
        i += 2
        if not code_raw:
            continue
        try:
            code = int(code_raw)
        except ValueError:
            # Lệch nhịp (file hỏng/ghi chú lạ) -> lùi 1 dòng để bắt lại nhịp.
            i -= 1
            continue
        out.append((code, val.strip() if code != 1 and code != 3 else val))
    return out


def dxf_sections(pairs):
    """Cắt danh sách cặp thành từng SECTION: {"HEADER": [...], "ENTITIES":
    [...], "BLOCKS": [...]}."""
    sections = {}
    i = 0
    n = len(pairs)
    while i < n:
        code, val = pairs[i]
        if code == 0 and val == "SECTION":
            name = None
            j = i + 1
            if j < n and pairs[j][0] == 2:
                name = pairs[j][1]
                j += 1
            body = []
            while j < n and not (pairs[j][0] == 0 and pairs[j][1] == "ENDSEC"):
                body.append(pairs[j])
                j += 1
            if name:
                sections[name] = body
            i = j + 1
        else:
            i += 1
    return sections


def dxf_chunks(pairs):
    """Gom các cặp thành từng "chunk" đối tượng: mỗi chunk bắt đầu ở mã 0.
    Trả về list [(tên_đối_tượng, [(mã, giá trị), ...]), ...]."""
    chunks = []
    cur_name = None
    cur = []
    for code, val in pairs:
        if code == 0:
            if cur_name is not None:
                chunks.append((cur_name, cur))
            cur_name = val
            cur = []
        elif cur_name is not None:
            cur.append((code, val))
    if cur_name is not None:
        chunks.append((cur_name, cur))
    return chunks


def _g(data, code, default=None, cast=float):
    for c, v in data:
        if c == code:
            try:
                return cast(v)
            except Exception:
                return default
    return default


def _gs(data, code, default=u""):
    for c, v in data:
        if c == code:
            return v
    return default


def _vertices(data):
    """Đọc chuỗi đỉnh (10/20) kèm bulge (42) từ 1 chunk LWPOLYLINE/POLYLINE."""
    pts = []
    bulges = []
    x = None
    for c, v in data:
        if c == 10:
            try:
                x = float(v)
            except Exception:
                x = None
        elif c == 20 and x is not None:
            try:
                pts.append((x, float(v)))
                bulges.append(0.0)
            except Exception:
                pass
            x = None
        elif c == 42 and bulges:
            try:
                bulges[-1] = float(v)
            except Exception:
                pass
    return pts, bulges


def _expand_bulges(pts, bulges, closed):
    """Biến chuỗi đỉnh + bulge thành đường gấp khúc thuần (đã bung cung)."""
    if not pts:
        return []
    if not any(bulges):
        return list(pts)
    out = [pts[0]]
    n = len(pts)
    last = n if closed else n - 1
    for i in range(last):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        b = bulges[i] if i < len(bulges) else 0.0
        seg = bulge_points(p1, p2, b)
        out.extend(seg[1:])
    return out


MAX_DXF_ENTITIES = 200000     # trần an toàn, chống file CAD "bom" làm treo máy
MAX_INSERT_DEPTH = 6          # độ sâu tối đa khi bung block lồng block


def clean_mtext(s):
    """Bỏ mã định dạng của MTEXT: {\\f Arial|b0;...}, \\P (xuống dòng),
    \\pxq;, \\H2.5x; ... để lấy phần chữ thuần."""
    if not s:
        return u""
    t = u"%s" % s
    t = t.replace(u"\\P", u" ").replace(u"\\~", u" ")
    t = re.sub(r"\\[A-Za-z][^;\\]*;", u"", t)
    t = re.sub(r"[{}]", u"", t)
    t = t.replace(u"\\\\", u"\\")
    return re.sub(r"\s+", u" ", t).strip()


def _tf_point(tf, p):
    """Áp phép biến đổi của INSERT lên 1 điểm: dời gốc block -> co giãn ->
    xoay -> tịnh tiến tới điểm chèn."""
    dx, dy, sx, sy, rot, bx, by = tf
    x = (p[0] - bx) * sx
    y = (p[1] - by) * sy
    if rot:
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)
        x, y = x * ca - y * sa, x * sa + y * ca
    return (x + dx, y + dy)


def transform_ent(ent, tf):
    """Biến đổi 1 CadEnt theo tf. Cung tròn giữ nguyên dạng ARC nếu phép co
    giãn là ĐỀU và không lật gương; ngược lại bung thành đường gấp khúc để
    tuyệt đối không sai hình."""
    if tf is None:
        return ent
    dx, dy, sx, sy, rot, bx, by = tf
    uniform = abs(abs(sx) - abs(sy)) < 1e-9 and sx > 0 and sy > 0
    if ent.kind in ("ARC", "CIRCLE"):
        if uniform:
            c = _tf_point(tf, ent.center) if ent.center else None
            return CadEnt(ent.kind, ent.layer, [], False, c, ent.radius * sx,
                          ent.a0 + rot, ent.a1 + rot, ent.text)
        pts = [_tf_point(tf, p) for p in ent.points()]
        return CadEnt("POLY", ent.layer, pts, ent.kind == "CIRCLE")
    pts = [_tf_point(tf, p) for p in ent.pts]
    return CadEnt(ent.kind, ent.layer, pts, ent.closed, None, 0.0, 0.0, 0.0, ent.text)


def chunk_to_entities(name, data):
    """Đổi 1 chunk DXF đơn lẻ thành list CadEnt (0, 1 hoặc nhiều)."""
    layer = _gs(data, 8, u"0")
    if name == "LINE":
        x1, y1 = _g(data, 10, 0.0), _g(data, 20, 0.0)
        x2, y2 = _g(data, 11, 0.0), _g(data, 21, 0.0)
        if x1 is None or x2 is None:
            return []
        return [CadEnt("POLY", layer, [(x1, y1), (x2, y2)], False)]
    if name == "LWPOLYLINE":
        pts, bulges = _vertices(data)
        if len(pts) < 2:
            return []
        closed = bool(int(_g(data, 70, 0, int) or 0) & 1)
        return [CadEnt("POLY", layer, _expand_bulges(pts, bulges, closed), closed)]
    if name == "ARC":
        c = (_g(data, 10, 0.0), _g(data, 20, 0.0))
        return [CadEnt("ARC", layer, [], False, c, _g(data, 40, 0.0),
                       _g(data, 50, 0.0), _g(data, 51, 360.0))]
    if name == "CIRCLE":
        c = (_g(data, 10, 0.0), _g(data, 20, 0.0))
        return [CadEnt("CIRCLE", layer, [], True, c, _g(data, 40, 0.0), 0.0, 360.0)]
    if name == "ELLIPSE":
        cx, cy = _g(data, 10, 0.0), _g(data, 20, 0.0)
        mx, my = _g(data, 11, 0.0), _g(data, 21, 0.0)   # nửa trục lớn (tương đối)
        ratio = _g(data, 40, 1.0) or 1.0
        p0 = _g(data, 41, 0.0) or 0.0
        p1 = _g(data, 42, 2 * math.pi)
        if p1 is None:
            p1 = 2 * math.pi
        a = math.hypot(mx, my)
        b = a * ratio
        rot = math.atan2(my, mx)
        n = max(8, int(ARC_SEG_PER_QUARTER * 4))
        pts = []
        for i in range(n + 1):
            t = p0 + (p1 - p0) * i / float(n)
            ex, ey = a * math.cos(t), b * math.sin(t)
            pts.append((cx + ex * math.cos(rot) - ey * math.sin(rot),
                        cy + ex * math.sin(rot) + ey * math.cos(rot)))
        return [CadEnt("POLY", layer, pts, abs((p1 - p0) - 2 * math.pi) < 1e-6)]
    if name == "SPLINE":
        # Xấp xỉ spline bằng chính các điểm điều khiển / điểm khớp — đủ tốt
        # cho nét trang trí, và không bao giờ làm hỏng cả file vì 1 spline.
        fit = []
        x = None
        for c, v in data:
            if c == 11:
                try:
                    x = float(v)
                except Exception:
                    x = None
            elif c == 21 and x is not None:
                fit.append((x, float(v)))
                x = None
        if len(fit) < 2:
            fit, _b = _vertices(data)
        if len(fit) < 2:
            return []
        closed = bool(int(_g(data, 70, 0, int) or 0) & 1)
        return [CadEnt("POLY", layer, fit, closed)]
    if name in ("TEXT", "MTEXT"):
        txt = clean_mtext(_gs(data, 1, u""))
        if name == "MTEXT":
            extra = u"".join(v for c, v in data if c == 3)
            txt = clean_mtext(extra + _gs(data, 1, u""))
        px, py = _g(data, 10, 0.0), _g(data, 20, 0.0)
        if not txt:
            return []
        return [CadEnt("TEXT", layer, [(px, py)], False, None, 0.0, 0.0, 0.0, txt)]
    if name == "SOLID":
        pts = []
        for code_x, code_y in ((10, 20), (11, 21), (12, 22), (13, 23)):
            vx, vy = _g(data, code_x), _g(data, code_y)
            if vx is not None and vy is not None:
                pts.append((vx, vy))
        if len(pts) >= 3:
            return [CadEnt("POLY", layer, pts, True)]
        return []
    return []


def chunks_to_entities(chunks, blocks, depth=0, budget=None):
    """Đổi cả danh sách chunk thành CadEnt, tự bung POLYLINE/VERTEX và
    INSERT (block, kể cả block lồng nhau và mảng block hàng/cột)."""
    if budget is None:
        budget = [MAX_DXF_ENTITIES]
    out = []
    i = 0
    n = len(chunks)
    while i < n:
        if budget[0] <= 0:
            break
        name, data = chunks[i]

        if name == "POLYLINE":
            layer = _gs(data, 8, u"0")
            closed = bool(int(_g(data, 70, 0, int) or 0) & 1)
            pts = []
            bulges = []
            j = i + 1
            while j < n and chunks[j][0] == "VERTEX":
                vp, vb = _vertices(chunks[j][1])
                if vp:
                    pts.append(vp[0])
                    bulges.append(vb[0] if vb else 0.0)
                j += 1
            if j < n and chunks[j][0] == "SEQEND":
                j += 1
            if len(pts) >= 2:
                out.append(CadEnt("POLY", layer, _expand_bulges(pts, bulges, closed), closed))
                budget[0] -= 1
            i = j
            continue

        if name == "INSERT":
            bname = _gs(data, 2, u"")
            blk = blocks.get(bname)
            if blk is not None and depth < MAX_INSERT_DEPTH:
                ix, iy = _g(data, 10, 0.0), _g(data, 20, 0.0)
                sx = _g(data, 41, 1.0)
                sy = _g(data, 42, 1.0)
                rot = _g(data, 50, 0.0) or 0.0
                sx = 1.0 if not sx else sx
                sy = 1.0 if not sy else sy
                cols = int(_g(data, 70, 1, int) or 1)
                rows = int(_g(data, 71, 1, int) or 1)
                csp = _g(data, 44, 0.0) or 0.0
                rsp = _g(data, 45, 0.0) or 0.0
                cols = max(1, min(cols, 200))
                rows = max(1, min(rows, 200))
                base = blk["base"]
                sub = chunks_to_entities(blk["chunks"], blocks, depth + 1, budget)
                for rr in range(rows):
                    for cc in range(cols):
                        tf = (ix + cc * csp, iy + rr * rsp, sx, sy, rot, base[0], base[1])
                        for e in sub:
                            out.append(transform_ent(e, tf))
                            budget[0] -= 1
                            if budget[0] <= 0:
                                break
            i += 1
            continue

        for e in chunk_to_entities(name, data):
            out.append(e)
            budget[0] -= 1
        i += 1
    return out


def parse_dxf_blocks(section_pairs):
    """Đọc SECTION BLOCKS -> {tên block: {"base": (x, y), "chunks": [...]}}."""
    blocks = {}
    cur = None
    for name, data in dxf_chunks(section_pairs):
        if name == "BLOCK":
            bname = _gs(data, 2, u"") or _gs(data, 3, u"")
            cur = {"name": bname,
                   "base": (_g(data, 10, 0.0) or 0.0, _g(data, 20, 0.0) or 0.0),
                   "chunks": []}
            if bname:
                blocks[bname] = cur
        elif name == "ENDBLK":
            cur = None
        elif cur is not None:
            cur["chunks"].append((name, data))
    return blocks


def infer_units_scale(insunits, max_dim_raw):
    """Đoán đơn vị bản vẽ -> hệ số nhân ra mm.
    Ưu tiên $INSUNITS; nếu file không khai báo thì suy từ độ lớn khung bao
    (đồ nội thất/cửa thực tế nằm trong khoảng 100 mm ... 100 m).
    Trả về (hệ_số, tên_đơn_vị, chắc_chắn?)."""
    if insunits in INSUNITS_TO_MM and INSUNITS_TO_MM.get(insunits):
        k = INSUNITS_TO_MM[insunits]
        names = {25.4: u"inch", 304.8: u"feet", 1.0: u"mm", 10.0: u"cm", 1000.0: u"m"}
        return k, names.get(k, u"đvị #%s" % insunits), True
    d = float(max_dim_raw or 0.0)
    if d <= 0:
        return 1.0, u"mm (mặc định)", False
    if d < 50.0:
        return 1000.0, u"m (suy đoán)", False
    if d < 500.0:
        return 10.0, u"cm (suy đoán)", False
    return 1.0, u"mm (suy đoán)", False


class CadDoc(object):
    """Toàn bộ nội dung 1 file CAD sau khi đã chuẩn hoá: hình học tính bằng
    MILIMET, mặt phẳng XY, kèm thông tin đơn vị gốc và cảnh báo."""

    def __init__(self, path, entities, unit_scale=1.0, unit_name=u"mm",
                 unit_ok=True, warnings=None, reader=u"DXF"):
        self.path = path
        self.name = os.path.splitext(os.path.basename(path))[0] if path else u""
        self.entities = entities or []
        self.unit_scale = unit_scale
        self.unit_name = unit_name
        self.unit_ok = unit_ok
        self.warnings = warnings or []
        self.reader = reader

    def layers(self):
        return sorted(set(e.layer for e in self.entities))

    def texts(self):
        return [e.text for e in self.entities if e.kind == "TEXT" and e.text]

    def drawable(self):
        return [e for e in self.entities if e.is_drawable()]


def read_dxf(path):
    """Đọc 1 file .dxf ASCII -> CadDoc (đơn vị mm). Trả về (CadDoc, lỗi)."""
    text, err = dxf_read_text(path)
    if err:
        return None, err
    warnings = []
    pairs = dxf_pairs(text)
    if not pairs:
        return None, u"File DXF rỗng hoặc sai định dạng."
    sections = dxf_sections(pairs)
    blocks = parse_dxf_blocks(sections.get("BLOCKS", []))
    ent_chunks = dxf_chunks(sections.get("ENTITIES", []))
    if not ent_chunks:
        return None, u"Không tìm thấy SECTION ENTITIES trong file DXF."
    raw = chunks_to_entities(ent_chunks, blocks)
    if not raw:
        return None, u"File DXF không có đối tượng nào đọc được."

    # $INSUNITS nằm trong HEADER dưới dạng cặp (9, "$INSUNITS") + (70, giá trị)
    insunits = 0
    header = sections.get("HEADER", [])
    for idx in range(len(header) - 1):
        if header[idx][0] == 9 and header[idx][1].strip().upper() == "$INSUNITS":
            try:
                insunits = int(header[idx + 1][1])
            except Exception:
                insunits = 0
            break

    bb = entities_bbox(raw)
    max_dim_raw = max(bb[2] - bb[0], bb[3] - bb[1]) if bb else 0.0
    scale, uname, unit_ok = infer_units_scale(insunits, max_dim_raw)
    if not unit_ok:
        warnings.append(u"File không khai báo $INSUNITS — script tự suy đơn vị là %s. "
                        u"Nếu sai, hãy sửa lại Dài/Rộng/Cao trên GUI." % uname)
    ents = [e.scaled(scale) for e in raw] if scale != 1.0 else raw
    if len(raw) >= MAX_DXF_ENTITIES:
        warnings.append(u"File quá lớn — chỉ đọc %d đối tượng đầu tiên." % MAX_DXF_ENTITIES)
    return CadDoc(path, ents, scale, uname, unit_ok, warnings, u"DXF"), None


def sniff_dwg(path):
    """Đọc 6 byte đầu file .dwg để biết phiên bản AutoCAD (AC1015 = 2000,
    AC1032 = 2018...). Không bóc được hình học (DWG là định dạng nhị phân
    độc quyền) — phần hình học sẽ do chính Revit Import đảm nhiệm."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(6).decode("ascii", "ignore")
    except Exception as ex:
        return None, u"Không đọc được file: %s" % ex
    versions = {
        "AC1009": "R11/R12", "AC1012": "R13", "AC1014": "R14",
        "AC1015": "2000", "AC1018": "2004", "AC1021": "2007",
        "AC1024": "2010", "AC1027": "2013", "AC1032": "2018+",
    }
    if head[:2] != "AC":
        return None, u"Không phải file DWG hợp lệ."
    return versions.get(head, head), None


# ------------------------------------------------------------------------
# 5. HÌNH HỌC & "TƯ DUY" ĐỌC BẢN VẼ (thuần Python — có unit test)
# ------------------------------------------------------------------------
def bbox_of(points):
    """Khung bao của 1 danh sách điểm -> (minx, miny, maxx, maxy)."""
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def ent_bbox(ent):
    if ent.kind in ("ARC", "CIRCLE") and ent.center:
        return bbox_of(ent.points())
    return bbox_of(ent.pts)


def entities_bbox(ents):
    boxes = [b for b in (ent_bbox(e) for e in ents) if b]
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def bbox_size(bb):
    if not bb:
        return (0.0, 0.0)
    return (bb[2] - bb[0], bb[3] - bb[1])


def bbox_area(bb):
    w, h = bbox_size(bb)
    return max(w, 0.0) * max(h, 0.0)


def bbox_center(bb):
    return ((bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0) if bb else (0.0, 0.0)


def is_noise_layer(layer):
    """Layer ghi chú / kích thước / khung tên -> không vẽ lại vào family.
    So khớp có tôn trọng ranh giới từ (xem kw_pattern), nếu không thì layer
    vật liệu như "BAN CHU NHAT" sẽ bị loại oan vì chứa chuỗi con "CHU"."""
    key = u" %s " % norm_key(layer)
    for k in NOISE_LAYER_KEYWORDS:
        pat = kw_pattern(k)
        if pat and key.find(pat) >= 0:
            return True
    return False


class Island(object):
    """1 "cụm bản vẽ" rời rạc trên model space — ứng với 1 hình chiếu."""

    def __init__(self, ents):
        self.ents = ents
        self.bbox = entities_bbox([e for e in ents if e.is_drawable()]) or entities_bbox(ents)
        self.kind = None          # PLAN / FRONT / BACK / LEFT / RIGHT / SECTION / EXTRA
        self.reason = u""         # vì sao lại nhận diện như vậy (hiện trên GUI)
        self.labels = []          # chữ trong/gần cụm

    def size(self):
        return bbox_size(self.bbox)

    def area(self):
        return bbox_area(self.bbox)

    def text_blob(self):
        return u" ".join([e.text for e in self.ents if e.kind == "TEXT" and e.text] + self.labels)

    def closed_count(self):
        n = 0
        for e in self.ents:
            if e.kind == "CIRCLE":
                n += 1
            elif e.kind == "POLY" and e.closed and len(e.pts) >= 3:
                n += 1
        return n

    def drawable(self):
        return [e for e in self.ents if e.is_drawable()]


def cluster_islands(ents, gap=None, max_cells=200000):
    """Gom các đối tượng thành từng cụm rời nhau bằng lưới ô vuông + loang
    vùng (flood fill) — nhanh cả với bản vẽ hàng chục nghìn nét (không so
    từng cặp đối tượng, tránh O(n²) làm treo máy).

    gap = khoảng hở tối thiểu giữa 2 cụm (mm). Để None -> tự tính bằng
    ISLAND_GAP_RATIO × cạnh lớn nhất của toàn bản vẽ."""
    ents = [e for e in ents if ent_bbox(e)]
    if not ents:
        return []
    full = entities_bbox(ents)
    W, H = bbox_size(full)
    span = max(W, H, 1e-6)
    if gap is None:
        gap = span * ISLAND_GAP_RATIO
    gap = max(gap, span / 400.0, 1e-6)

    nx = int(W / gap) + 2
    ny = int(H / gap) + 2
    while nx * ny > max_cells:
        gap *= 1.5
        nx = int(W / gap) + 2
        ny = int(H / gap) + 2

    occupied = {}
    ent_cells = []
    for idx, e in enumerate(ents):
        bb = ent_bbox(e)
        i0 = int((bb[0] - full[0]) / gap)
        i1 = int((bb[2] - full[0]) / gap)
        j0 = int((bb[1] - full[1]) / gap)
        j1 = int((bb[3] - full[1]) / gap)
        cells = []
        # Trần ô cho 1 đối tượng: nét dài xuyên bản vẽ (trục, khung) không
        # được phép "dính" mọi cụm lại thành một.
        if (i1 - i0 + 1) * (j1 - j0 + 1) > 40000:
            i1 = min(i1, i0 + 200)
            j1 = min(j1, j0 + 200)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                occupied[(i, j)] = -1
                cells.append((i, j))
        ent_cells.append(cells)

    # loang vùng 8 hướng trên các ô có nét
    comp_id = 0
    for cell in list(occupied.keys()):
        if occupied[cell] != -1:
            continue
        stack = [cell]
        occupied[cell] = comp_id
        while stack:
            ci, cj = stack.pop()
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    nb = (ci + di, cj + dj)
                    if occupied.get(nb, None) == -1:
                        occupied[nb] = comp_id
                        stack.append(nb)
        comp_id += 1

    groups = {}
    for idx, cells in enumerate(ent_cells):
        cid = occupied.get(cells[0], 0) if cells else 0
        groups.setdefault(cid, []).append(ents[idx])
    islands = [Island(v) for v in groups.values() if v]
    islands.sort(key=lambda il: -il.area())
    return islands


def attach_labels(islands):
    """Ghi chú ("MẶT BẰNG", "MĐ CHÍNH"...) thường nằm TÁCH RỜI bên dưới hình
    vẽ nên bị tách thành 1 cụm riêng chỉ toàn chữ. Hàm này gán các cụm chữ
    đó về cụm hình gần nhất, và trả về danh sách cụm hình thật."""
    real = []
    text_only = []
    for il in islands:
        if il.drawable():
            real.append(il)
        else:
            text_only.append(il)
    for tl in text_only:
        txt = tl.text_blob().strip()
        if not txt or not real:
            continue
        tc = bbox_center(tl.bbox)
        best = None
        best_d = None
        for il in real:
            c = bbox_center(il.bbox)
            # ưu tiên cụm nằm NGAY TRÊN chữ (ghi chú luôn đặt dưới hình):
            # phạt khoảng cách ngang gấp đôi khoảng cách dọc.
            d = math.hypot((c[0] - tc[0]) * 2.0, c[1] - tc[1])
            if best_d is None or d < best_d:
                best_d = d
                best = il
        if best is not None:
            best.labels.append(txt)
    return real


def drop_noise_islands(islands):
    """Bỏ các cụm quá nhỏ so với cụm lớn nhất (khung tên, ghi chú, logo)."""
    if not islands:
        return []
    amax = max(il.area() for il in islands) or 1.0
    keep = [il for il in islands if il.area() >= amax * ISLAND_MIN_AREA_RATIO]
    return keep or islands[:1]


def match_view_keyword(text):
    """Dò xem chuỗi chữ nói tới hình chiếu nào. Trả về (kind, từ_khoá) hoặc
    (None, None)."""
    if not text:
        return None, None
    blob = u" %s " % norm_key(text)
    for kind, keys in VIEW_KEYWORDS:
        for k in keys:
            pat = kw_pattern(k)
            if pat and blob.find(pat) >= 0:
                return kind, k.strip()
    return None, None


def classify_islands(islands, file_name=u""):
    """"TƯ DUY" nhận diện từng cụm là hình chiếu nào. Thứ tự ưu tiên:
      1) Chữ ghi chú trong/gần cụm ("MẶT BẰNG", "MĐ BÊN TRÁI", "FRONT"...)
      2) Tên layer của các nét trong cụm
      3) Tên file (khi cả bản vẽ chỉ có 1 cụm)
      4) Suy luận hình học:
           - Cụm nhiều vòng kín nhất (hoặc lớn nhất) = MẶT BẰNG.
           - Cụm còn lại có BỀ NGANG ≈ Dài của mặt bằng  -> FRONT rồi BACK.
           - Cụm còn lại có BỀ NGANG ≈ Rộng của mặt bằng -> LEFT rồi RIGHT.
           - Còn dư thì gán theo thứ tự trái→phải: FRONT, LEFT, RIGHT, BACK.
    Trả về chính list islands đã gán .kind và .reason."""
    if not islands:
        return []

    used = set()

    # --- (1) + (2): theo chữ ghi chú và tên layer -----------------------
    for il in islands:
        kind, kw = match_view_keyword(il.text_blob())
        if kind is None:
            layers = u" ".join(sorted(set(e.layer for e in il.ents)))
            kind, kw = match_view_keyword(layers)
            if kind:
                il.reason = u"layer chứa '%s'" % kw
        else:
            il.reason = u"chữ trong bản vẽ: '%s'" % kw
        if kind and kind not in used:
            il.kind = kind
            used.add(kind)
        elif kind:
            il.kind = None      # trùng loại -> để bước hình học xử lý tiếp
            il.reason = u""

    # --- (3): chỉ có 1 cụm -> dựa vào tên file ---------------------------
    if len(islands) == 1 and islands[0].kind is None:
        kind, kw = match_view_keyword(file_name)
        islands[0].kind = kind or "PLAN"
        islands[0].reason = (u"tên file chứa '%s'" % kw) if kind else u"bản vẽ chỉ có 1 hình → coi là mặt bằng"
        return islands

    # --- (4): suy luận hình học -----------------------------------------
    rest = [il for il in islands if il.kind is None]
    plan = next((il for il in islands if il.kind == "PLAN"), None)
    if plan is None and rest:
        # nhiều vòng kín nhất; hoà thì lấy cụm có diện tích lớn nhất
        rest.sort(key=lambda il: (-il.closed_count(), -il.area()))
        plan = rest[0]
        plan.kind = "PLAN"
        plan.reason = (u"nhiều biên dạng kín nhất (%d) → mặt bằng" % plan.closed_count()
                       if plan.closed_count() else u"cụm lớn nhất → mặt bằng")
        used.add("PLAN")
        rest = rest[1:]

    if plan is not None and rest:
        pl, pw = plan.size()
        fronts, sides, others = [], [], []
        for il in rest:
            w, _h = il.size()
            d_len = abs(w - pl) / pl if pl > 0 else 9.0
            d_wid = abs(w - pw) / pw if pw > 0 else 9.0
            if d_len <= 0.12 and d_len <= d_wid:
                fronts.append(il)
            elif d_wid <= 0.12:
                sides.append(il)
            else:
                others.append(il)
        fronts.sort(key=lambda il: bbox_center(il.bbox)[0])
        sides.sort(key=lambda il: bbox_center(il.bbox)[0])
        for il, kind in zip(fronts, [k for k in ("FRONT", "BACK") if k not in used]):
            il.kind = kind
            il.reason = u"bề ngang ≈ Dài mặt bằng → mặt đứng %s" % kind
            used.add(kind)
        for il, kind in zip(sides, [k for k in ("LEFT", "RIGHT") if k not in used]):
            il.kind = kind
            il.reason = u"bề ngang ≈ Rộng mặt bằng → mặt bên %s" % kind
            used.add(kind)
        rest = [il for il in rest if il.kind is None]

    leftover = [k for k in ELEVATION_FALLBACK_ORDER if k not in used]
    rest.sort(key=lambda il: bbox_center(il.bbox)[0])
    for il in rest:
        if leftover:
            il.kind = leftover.pop(0)
            il.reason = u"gán theo thứ tự trái→phải"
        else:
            il.kind = "EXTRA"
            il.reason = u"dư — không đưa vào family"
    return islands


def infer_dimensions(islands, category="GenericModel"):
    """Suy Dài / Rộng / Cao (mm) từ các cụm đã nhận diện.
      - Mặt bằng  -> Dài (theo X) và Rộng (theo Y)
      - Mặt đứng  -> Cao (theo Y); ưu tiên FRONT, rồi BACK/LEFT/RIGHT
      - Thiếu dữ liệu -> lấy mặc định theo danh mục (DEFAULT_DIMS)
    Trả về (dài, rộng, cao, ghi_chú_nguồn)."""
    dl, dw, dh = DEFAULT_DIMS.get(category, DEFAULT_DIMS["GenericModel"])
    notes = []
    by_kind = {}
    for il in islands:
        if il.kind and il.kind not in by_kind:
            by_kind[il.kind] = il

    plan = by_kind.get("PLAN")
    if plan is not None:
        w, h = plan.size()
        if w > 1.0 and h > 1.0:
            dl, dw = w, h
            notes.append(u"Dài×Rộng lấy từ mặt bằng")
    for k in ("FRONT", "BACK", "LEFT", "RIGHT", "SECTION"):
        il = by_kind.get(k)
        if il is not None:
            _w, h = il.size()
            if h > 1.0:
                dh = h
                notes.append(u"Cao lấy từ mặt đứng %s" % k)
                break
    if plan is None:
        # Không có mặt bằng: lấy cụm lớn nhất làm bề ngang, giữ Rộng mặc định.
        for il in islands:
            w, h = il.size()
            if w > 1.0:
                dl = w
                dh = h if h > 1.0 else dh
                notes.append(u"Không thấy mặt bằng — Dài/Cao lấy từ hình chiếu %s" % (il.kind or u"?"))
                break
    if not notes:
        notes.append(u"Dùng kích thước mặc định của danh mục")
    return dl, dw, dh, u"; ".join(notes)


# --- Vòng kín & biên dạng đùn khối --------------------------------------
def polygon_area(pts):
    """Diện tích đại số (shoelace). Dương = ngược chiều kim đồng hồ."""
    n = len(pts)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def point_in_polygon(pt, poly):
    """Kiểm tra điểm nằm trong đa giác (ray casting)."""
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1
            if x < xin:
                inside = not inside
    return inside


def dedupe_points(pts, tol=1e-6):
    out = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > tol:
            out.append(p)
    if len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= tol:
        out.pop()
    return out


def simplify_polyline(pts, tol):
    """Giản lược đường gấp khúc (Douglas–Peucker) — dùng ở chế độ TURBO để
    giảm số nét phải vẽ trong Revit mà mắt thường không thấy khác."""
    if tol <= 0 or len(pts) < 3:
        return list(pts)
    first, last = 0, len(pts) - 1
    keep = [False] * len(pts)
    keep[first] = keep[last] = True
    stack = [(first, last)]
    while stack:
        i0, i1 = stack.pop()
        if i1 <= i0 + 1:
            continue
        x1, y1 = pts[i0]
        x2, y2 = pts[i1]
        dx, dy = x2 - x1, y2 - y1
        seg = math.hypot(dx, dy)
        best_i, best_d = -1, -1.0
        for i in range(i0 + 1, i1):
            px, py = pts[i]
            if seg < 1e-12:
                d = math.hypot(px - x1, py - y1)
            else:
                d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / seg
            if d > best_d:
                best_d, best_i = d, i
        if best_d > tol and best_i > 0:
            keep[best_i] = True
            stack.append((i0, best_i))
            stack.append((best_i, i1))
    return [p for p, k in zip(pts, keep) if k]


def chain_loops(segments, tol=None):
    """Ghép các đoạn thẳng rời rạc thành vòng kín. segments = list các cặp
    ((x1, y1), (x2, y2)). Trả về list các vòng (list điểm, KHÔNG lặp lại
    điểm đầu ở cuối)."""
    tol = LOOP_JOIN_TOL_MM if tol is None else tol
    q = max(tol, 1e-9)

    def key(p):
        return (int(round(p[0] / q)), int(round(p[1] / q)))

    adj = {}
    segs = []
    for (p1, p2) in segments:
        if math.hypot(p2[0] - p1[0], p2[1] - p1[1]) < MIN_SEG_LEN_MM:
            continue
        idx = len(segs)
        segs.append((p1, p2))
        adj.setdefault(key(p1), []).append(idx)
        adj.setdefault(key(p2), []).append(idx)

    used = [False] * len(segs)
    loops = []
    for start in range(len(segs)):
        if used[start]:
            continue
        used[start] = True
        p_start, p_cur = segs[start]
        chain = [p_start, p_cur]
        while True:
            nxt = None
            for idx in adj.get(key(p_cur), []):
                if used[idx]:
                    continue
                a, b = segs[idx]
                if key(a) == key(p_cur):
                    nxt, p_new = idx, b
                    break
                if key(b) == key(p_cur):
                    nxt, p_new = idx, a
                    break
            if nxt is None:
                break
            used[nxt] = True
            p_cur = p_new
            chain.append(p_cur)
            if key(p_cur) == key(p_start):
                break
        if len(chain) >= 4 and key(chain[-1]) == key(chain[0]):
            loop = dedupe_points(chain, tol * 0.5)
            if len(loop) >= 3 and abs(polygon_area(loop)) > tol * tol:
                loops.append(loop)
    return loops


def collect_loops(ents, tol=None):
    """Lấy TẤT CẢ vòng kín của 1 cụm bản vẽ:
      - Ưu tiên các đối tượng vốn đã kín (LWPOLYLINE closed, CIRCLE) — đây
        là 99% trường hợp biên dạng thật do người vẽ vẽ liền nét.
      - Các nét hở còn lại được ghép lại với nhau (chain_loops) để cứu
        những biên dạng vẽ bằng nhiều đoạn rời."""
    tol = LOOP_JOIN_TOL_MM if tol is None else tol
    loops = []
    open_segs = []
    for e in ents:
        if not e.is_drawable() or is_noise_layer(e.layer):
            continue
        pts = e.points()
        if len(pts) < 2:
            continue
        closed_ent = e.closed or e.kind == "CIRCLE"
        if closed_ent:
            loop = dedupe_points(pts, tol * 0.5)
            if len(loop) >= 3 and abs(polygon_area(loop)) > tol * tol:
                loops.append(loop)
        else:
            for i in range(len(pts) - 1):
                open_segs.append((pts[i], pts[i + 1]))
    if open_segs:
        loops.extend(chain_loops(open_segs, tol))
    return loops


def pick_profile_loops(loops, min_area_ratio=0.0008):
    """Chọn biên dạng để đùn khối: vòng lớn nhất làm BIÊN NGOÀI, các vòng
    nằm trọn bên trong nó làm LỖ RỖNG (bỏ vòng quá nhỏ = chi tiết trang trí,
    không nên đục thủng khối)."""
    if not loops:
        return None, []
    ranked = sorted(loops, key=lambda lp: -abs(polygon_area(lp)))
    outer = ranked[0]
    outer_area = abs(polygon_area(outer)) or 1.0
    inner = []
    for lp in ranked[1:]:
        a = abs(polygon_area(lp))
        if a < outer_area * min_area_ratio:
            continue
        cx = sum(p[0] for p in lp) / len(lp)
        cy = sum(p[1] for p in lp) / len(lp)
        if point_in_polygon((cx, cy), outer):
            inner.append(lp)
        if len(inner) >= MAX_INNER_LOOPS:
            break
    return outer, inner


def is_rectangleish(loop, angle_tol_deg=8.0, area_tol=0.06):
    """Biên dạng có phải (gần như) hình chữ nhật không? Dùng để quyết định
    có gán ràng buộc Align+Lock 4 mặt vào Reference Plane hay không — chỉ
    hình chữ nhật mới co giãn theo Dài/Rộng một cách chắc chắn."""
    pts = dedupe_points(list(loop))
    if len(pts) < 4:
        return False
    bb = bbox_of(pts)
    ba = bbox_area(bb)
    if ba <= 0:
        return False
    if abs(abs(polygon_area(pts)) - ba) / ba > area_tol:
        return False
    if len(pts) > 12:
        return False
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        ang = abs(math.degrees(math.atan2(y2 - y1, x2 - x1))) % 180.0
        if min(abs(ang - 0.0), abs(ang - 90.0), abs(ang - 180.0)) > angle_tol_deg:
            return False
    return True


# ------------------------------------------------------------------------
# 6. GOM FILE THÀNH "KẾ HOẠCH TẠO FAMILY" (FamilyPlan)
#    Hỗ trợ cả 2 kiểu tổ chức file mà bạn hay dùng:
#      A) 1 file CAD chứa ĐỦ mặt bằng + các mặt đứng  → 1 family
#      B) mỗi hình chiếu 1 file, đặt tên có hậu tố:
#         LAVABO_MB.dwg + LAVABO_MD.dwg + LAVABO_MB TRAI.dwg → gộp 1 family
# ------------------------------------------------------------------------
VIEW_FILE_SUFFIX = [
    ("PLAN",    ["MB", "MAT BANG", "PLAN", "TOP", "BANG"]),
    ("FRONT",   ["MD", "MAT DUNG", "MDC", "MD CHINH", "FRONT", "ELEVATION", "TRUOC"]),
    ("BACK",    ["MS", "MAT SAU", "MD SAU", "BACK", "REAR", "SAU"]),
    ("LEFT",    ["MT", "MAT TRAI", "MD TRAI", "LEFT", "TRAI"]),
    ("RIGHT",   ["MP", "MAT PHAI", "MD PHAI", "RIGHT", "PHAI"]),
    ("SECTION", ["MC", "MAT CAT", "SECTION", "CAT"]),
]


def split_view_suffix(file_base_name):
    """Tách hậu tố hình chiếu khỏi tên file.
      "LAVABO BO 3_MD TRAI" -> ("LAVABO BO 3", "LEFT")
      "CUA DI P1"           -> ("CUA DI P1", None)"""
    tokens = norm_key(file_base_name).split()
    if not tokens:
        return norm_key(file_base_name), None
    for take in (3, 2, 1):
        if len(tokens) <= take:
            continue
        tail = u" ".join(tokens[-take:])
        for kind, keys in VIEW_FILE_SUFFIX:
            for k in keys:
                if tail == norm_key(k):
                    return u" ".join(tokens[:-take]), kind
    return u" ".join(tokens), None


class FamilySource(object):
    """1 file CAD nguồn của 1 family."""

    def __init__(self, path, forced_kind=None):
        self.path = path
        self.forced_kind = forced_kind
        self.caddoc = None
        self.islands = []
        self.error = None

    @property
    def ext(self):
        return os.path.splitext(self.path)[1].lower()

    @property
    def needs_revit(self):
        return self.ext == ".dwg"


class FamilyPlan(object):
    """Kế hoạch tạo 1 family: nguồn CAD, tên, danh mục, kích thước, chế độ.
    Đây chính là 1 DÒNG trên bảng GUI — bạn sửa gì trên lưới là sửa vào đây."""

    def __init__(self, name, sources):
        self.sources = sources
        self.family_name = sanitize_family_name(name)
        self.category = "GenericModel"
        self.mode = MODE_HYBRID
        self.length = DEFAULT_DIMS["GenericModel"][0]
        self.width = DEFAULT_DIMS["GenericModel"][1]
        self.height = DEFAULT_DIMS["GenericModel"][2]
        self.enabled = True
        self.scanned = False
        self.status = u"Chờ quét"
        self.detect_note = u""
        self.views = {}          # kind -> Island (toạ độ mm, gốc CAD)
        self.out_path = u""
        self.template_path = u""
        self.warnings = []
        self.unit_name = u""
        self.elapsed_ms = 0

    @property
    def src_paths(self):
        return [s.path for s in self.sources]

    @property
    def src_display(self):
        if len(self.sources) == 1:
            return os.path.basename(self.sources[0].path)
        return u"%s (+%d file)" % (os.path.basename(self.sources[0].path), len(self.sources) - 1)

    def views_display(self):
        order = ["PLAN", "FRONT", "BACK", "LEFT", "RIGHT", "SECTION"]
        vn = {"PLAN": u"MB", "FRONT": u"MĐ", "BACK": u"Sau", "LEFT": u"Trái",
              "RIGHT": u"Phải", "SECTION": u"Cắt"}
        got = [vn[k] for k in order if k in self.views]
        return u"+".join(got) if got else u"—"


def group_files_into_plans(paths, group_by_name=True):
    """Nhóm danh sách file CAD thành các FamilyPlan. Chỉ gộp khi các file có
    CÙNG tên gốc và hậu tố hình chiếu KHÁC NHAU — tránh gộp nhầm 2 sản phẩm
    khác nhau vào 1 family."""
    plans = []
    if not group_by_name:
        for p in paths:
            base = os.path.splitext(os.path.basename(p))[0]
            plans.append(FamilyPlan(base, [FamilySource(p, None)]))
        return plans

    buckets = {}
    order = []
    for p in paths:
        base_raw = os.path.splitext(os.path.basename(p))[0]
        base_key, kind = split_view_suffix(base_raw)
        buckets.setdefault(base_key, []).append((p, kind, base_raw))
        if base_key not in order:
            order.append(base_key)

    for key in order:
        items = buckets[key]
        kinds = [k for (_p, k, _b) in items if k]
        can_group = (len(items) > 1 and len(kinds) == len(items)
                     and len(set(kinds)) == len(kinds))
        if can_group:
            display = items[0][2]
            b, _k = split_view_suffix(items[0][2])
            # lấy lại tên gốc có dấu: cắt đúng số ký tự của phần base đã chuẩn hoá
            display = _restore_base_name(items[0][2], b)
            plans.append(FamilyPlan(display, [FamilySource(p, k) for (p, k, _b) in items]))
        else:
            for (p, k, base_raw) in items:
                plans.append(FamilyPlan(base_raw, [FamilySource(p, k)]))
    return plans


def _restore_base_name(original, base_key_norm):
    """Lấy lại phần tên gốc (CÒN DẤU) tương ứng với base đã chuẩn hoá — để
    tên family giữ được tiếng Việt có dấu như bạn đặt trong CAD."""
    n_tokens = len(base_key_norm.split())
    if n_tokens <= 0:
        return original
    parts = re.split(r"([\s_\-\.]+)", original)
    words = [p for p in parts if p.strip(" _-.")]
    if n_tokens >= len(words):
        return original
    kept = words[:n_tokens]
    out = original
    try:
        idx = 0
        pos = 0
        for w in kept:
            pos = original.index(w, pos) + len(w)
            idx += 1
        out = original[:pos]
    except Exception:
        out = u" ".join(kept)
    return out.strip(" _-.")


# ------------------------------------------------------------------------
# 7. PHÂN TÍCH 1 KẾ HOẠCH: đọc CAD -> gom cụm -> nhận diện hình chiếu ->
#    suy danh mục & kích thước. Dùng chung cho cả DXF (đọc thẳng) lẫn DWG
#    (do Revit bóc hình học) nhờ tham số read_func.
# ------------------------------------------------------------------------
def filter_for_analysis(ents):
    """Giữ nét trên layer "thật" + GIỮ LẠI TẤT CẢ chữ (chữ nằm trên layer
    TEXT/GHI CHU chính là ghi chú tên hình chiếu mà ta cần đọc)."""
    out = []
    for e in ents:
        if e.kind == "TEXT":
            out.append(e)
        elif e.is_drawable() and not is_noise_layer(e.layer):
            out.append(e)
    return out


def scan_plan(plan, read_func):
    """Đọc và phân tích toàn bộ file nguồn của 1 FamilyPlan. Không ném lỗi:
    mọi sự cố đều ghi vào plan.warnings / plan.status."""
    t0 = time.time()
    plan.views = {}
    plan.warnings = []
    all_layers = []
    all_texts = []
    ok_any = False

    for src in plan.sources:
        caddoc, err = read_func(src.path)
        src.caddoc = caddoc
        src.error = err
        if err or caddoc is None:
            plan.warnings.append(u"%s: %s" % (os.path.basename(src.path), err or u"không đọc được"))
            continue
        ok_any = True
        plan.unit_name = caddoc.unit_name
        plan.warnings.extend([u"%s: %s" % (os.path.basename(src.path), w) for w in caddoc.warnings])
        all_layers.extend(caddoc.layers())
        all_texts.extend(caddoc.texts())

        ents = filter_for_analysis(caddoc.entities)
        if not ents:
            plan.warnings.append(u"%s: không có nét nào dùng được (toàn layer ghi chú?)."
                                 % os.path.basename(src.path))
            continue
        islands = drop_noise_islands(attach_labels(cluster_islands(ents)))
        src.islands = islands

        if src.forced_kind and islands:
            main = max(islands, key=lambda il: il.area())
            main.kind = src.forced_kind
            main.reason = u"hậu tố tên file"
            for il in islands:
                if il is not main and il.kind is None:
                    il.kind = "EXTRA"
        else:
            classify_islands(islands, os.path.basename(src.path))

        for il in islands:
            if il.kind and il.kind != "EXTRA" and il.kind not in plan.views:
                plan.views[il.kind] = il

    if not ok_any:
        plan.status = u"✖ Lỗi đọc CAD"
        plan.scanned = True
        plan.elapsed_ms = int((time.time() - t0) * 1000)
        return plan

    plan.category = guess_category(plan.family_name,
                                   u" ".join(os.path.basename(p) for p in plan.src_paths),
                                   u" ".join(all_layers[:400]),
                                   u" ".join(all_texts[:200]))
    dl, dw, dh, note = infer_dimensions(list(plan.views.values()), plan.category)
    plan.length, plan.width, plan.height = dl, dw, dh
    reasons = [u"%s: %s" % (k, plan.views[k].reason) for k in
               ("PLAN", "FRONT", "BACK", "LEFT", "RIGHT") if k in plan.views and plan.views[k].reason]
    plan.detect_note = u" | ".join([note] + reasons[:3])
    plan.status = u"✔ Sẵn sàng" if plan.views else u"⚠ Không nhận ra hình chiếu"
    plan.scanned = True
    plan.elapsed_ms = int((time.time() - t0) * 1000)
    return plan


def dxf_reader(path):
    """read_func cho file .dxf — đọc thẳng bằng Python, không đụng Revit."""
    if os.path.splitext(path)[1].lower() != ".dxf":
        return None, u"Không phải file DXF."
    try:
        return read_dxf(path)
    except Exception as ex:
        return None, u"Lỗi đọc DXF: %s" % ex


# ------------------------------------------------------------------------
# 8. PHÍA REVIT — TEMPLATE, IMPORT DWG, DỰNG FAMILY
# ------------------------------------------------------------------------
def revit_ready():
    return REVIT_API and app is not None


def discover_template_root(explicit=None):
    """Tìm thư mục Family Template (.rft). Ưu tiên đường dẫn bạn khai báo;
    nếu không có thì dò C:\\ProgramData\\Autodesk\\RVT xxxx\\Family Templates
    (bản cài mặc định của Revit), lấy bản Revit MỚI NHẤT."""
    cands = []
    if explicit:
        for part in re.split(r"[;\r\n]+", u"%s" % explicit):
            part = part.strip().strip('"')
            if part and os.path.isdir(part):
                cands.append(part)
    if cands:
        return cands[0]
    roots = []
    for base in (r"C:\ProgramData\Autodesk", r"D:\ProgramData\Autodesk"):
        try:
            if not os.path.isdir(base):
                continue
            for d in sorted(os.listdir(base), reverse=True):
                if not d.upper().startswith("RVT"):
                    continue
                ft = os.path.join(base, d, "Family Templates")
                if os.path.isdir(ft):
                    roots.append(ft)
        except Exception:
            continue
    return roots[0] if roots else None


_TEMPLATE_CACHE = {}


def list_templates(root):
    """Liệt kê toàn bộ .rft trong thư mục template (có cache theo phiên)."""
    if not root:
        return []
    if root in _TEMPLATE_CACHE:
        return _TEMPLATE_CACHE[root]
    files = []
    try:
        for dirpath, _dirs, names in os.walk(root):
            for n in names:
                if n.lower().endswith(".rft"):
                    files.append(os.path.join(dirpath, n))
    except Exception:
        files = []
    _TEMPLATE_CACHE[root] = files
    return files


def pick_template(category, root, explicit_map=None):
    """Chọn file .rft hợp nhất cho 1 danh mục: chấm điểm theo từ khoá, ưu
    tiên bản "Metric"/"公制" và tránh các template biến thể (wall based,
    ceiling based, line based...) trừ khi không còn lựa chọn nào khác."""
    if explicit_map and category in explicit_map and os.path.isfile(explicit_map[category]):
        return explicit_map[category]
    files = list_templates(root)
    if not files:
        return None
    keys = TEMPLATE_KEYWORDS.get(category, TEMPLATE_KEYWORDS["GenericModel"])
    best, best_score = None, -1
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        low = name.lower()
        nkey = norm_key(name)
        score = 0
        for i, k in enumerate(keys):
            kk = k.lower()
            if kk in low or norm_key(k) in nkey:
                score += 100 - i * 10
                break
        if score <= 0:
            continue
        if "metric" in low or u"公制" in name:
            score += 25
        for bad in ("wall based", "ceiling based", "floor based", "line based",
                    "face based", "roof based", "two level", "curtain",
                    "based on", "pattern"):
            if bad in low:
                score -= 40
        score -= min(len(name), 60) * 0.1        # tên càng ngắn càng "chuẩn gốc"
        if score > best_score:
            best, best_score = f, score
    if best is None:
        # không tìm được template đúng danh mục -> lùi về Generic Model
        for f in files:
            low = os.path.basename(f).lower()
            if "generic model" in low or u"常规模型" in os.path.basename(f):
                return f
    return best


def _graphics_layer_name(rdoc, gobj):
    """Tên layer CAD của 1 GeometryObject sau khi import (Revit ánh xạ mỗi
    layer CAD thành 1 GraphicsStyle/Subcategory)."""
    try:
        gs = rdoc.GetElement(gobj.GraphicsStyleId)
        if gs is not None:
            cat = gs.GraphicsStyleCategory
            return cat.Name if cat is not None else gs.Name
    except Exception:
        pass
    return u"0"


def _revit_curve_to_ent(cur, layer):
    """Đổi 1 Curve của Revit (đơn vị feet) thành CadEnt (đơn vị mm)."""
    try:
        if isinstance(cur, Line):
            p0, p1 = cur.GetEndPoint(0), cur.GetEndPoint(1)
            return CadEnt("POLY", layer,
                          [(ft_to_mm(p0.X), ft_to_mm(p0.Y)),
                           (ft_to_mm(p1.X), ft_to_mm(p1.Y))], False)
        if isinstance(cur, Arc):
            c = cur.Center
            nz = 1.0
            try:
                nz = cur.Normal.Z
            except Exception:
                nz = 1.0
            if abs(abs(nz) - 1.0) < 1e-6:
                r = ft_to_mm(cur.Radius)
                ctr = (ft_to_mm(c.X), ft_to_mm(c.Y))
                if not cur.IsBound:
                    return CadEnt("CIRCLE", layer, [], True, ctr, r, 0.0, 360.0)
                p0, p1 = cur.GetEndPoint(0), cur.GetEndPoint(1)
                a0 = math.degrees(math.atan2(p0.Y - c.Y, p0.X - c.X))
                a1 = math.degrees(math.atan2(p1.Y - c.Y, p1.X - c.X))
                if nz < 0:
                    a0, a1 = a1, a0
                return CadEnt("ARC", layer, [], False, ctr, r, a0, a1)
        pts = [(ft_to_mm(p.X), ft_to_mm(p.Y)) for p in cur.Tessellate()]
        if len(pts) >= 2:
            return CadEnt("POLY", layer, pts, False)
    except Exception:
        return None
    return None


def entities_from_geometry(rdoc, geo, layer_hint=u"0", depth=0, out=None, budget=None):
    """Duyệt đệ quy GeometryElement của 1 CAD Import và bóc ra CadEnt (mm).
    Xử lý được: Curve, PolyLine, GeometryInstance (block CAD) và Solid (bản
    vẽ CAD 3D — lấy cạnh của khối)."""
    if out is None:
        out = []
    if budget is None:
        budget = [MAX_DXF_ENTITIES]
    if geo is None or depth > MAX_INSERT_DEPTH or budget[0] <= 0:
        return out
    for gobj in geo:
        if budget[0] <= 0:
            break
        try:
            layer = _graphics_layer_name(rdoc, gobj) or layer_hint
        except Exception:
            layer = layer_hint
        try:
            if isinstance(gobj, GeometryInstance):
                entities_from_geometry(rdoc, gobj.GetInstanceGeometry(), layer,
                                       depth + 1, out, budget)
                continue
            if isinstance(gobj, PolyLine):
                pts = [(ft_to_mm(p.X), ft_to_mm(p.Y)) for p in gobj.GetCoordinates()]
                if len(pts) >= 2:
                    closed = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-6
                    out.append(CadEnt("POLY", layer, pts[:-1] if closed else pts, closed))
                    budget[0] -= 1
                continue
            if isinstance(gobj, Curve):
                e = _revit_curve_to_ent(gobj, layer)
                if e is not None:
                    out.append(e)
                    budget[0] -= 1
                continue
            if isinstance(gobj, Solid):
                # CAD 3D: lấy cạnh của khối (giới hạn số cạnh để không treo máy)
                try:
                    edges = gobj.Edges
                    if edges.Size == 0 or edges.Size > 6000:
                        continue
                    for ed in edges:
                        e = _revit_curve_to_ent(ed.AsCurve(), layer)
                        if e is not None:
                            out.append(e)
                            budget[0] -= 1
                except Exception:
                    continue
        except Exception:
            continue
    return out


def sanity_fix_scale(ents, warnings):
    """Chốt chặn cuối về đơn vị: sau khi Revit import, kích thước phải nằm
    trong khoảng hợp lý của đồ nội thất/cấu kiện (3 cm … 500 m). Nếu lệch
    hẳn 1000 lần thì gần như chắc chắn file CAD khai sai đơn vị -> tự sửa
    và báo lại, thay vì tạo ra family to/nhỏ vô lý."""
    bb = entities_bbox(ents)
    if not bb:
        return ents
    d = max(bbox_size(bb))
    if d <= 0:
        return ents
    if d < 30.0:
        warnings.append(u"Kích thước đọc được quá nhỏ (%.2f mm) — tự nhân 1000 "
                        u"(file CAD nhiều khả năng vẽ bằng mét)." % d)
        return [e.scaled(1000.0) for e in ents]
    if d > 500000.0:
        warnings.append(u"Kích thước đọc được quá lớn (%.0f mm) — tự chia 1000." % d)
        return [e.scaled(0.001) for e in ents]
    return ents


def import_cad_geometry(target_doc, path, view, warnings):
    """Import 1 file CAD vào tài liệu Revit rồi trả về (ImportInstance, ids
    trước đó) — GỌI TRONG 1 TRANSACTION ĐANG MỞ.

    Không dùng tham số 'out ElementId' của Document.Import (cách gọi out-
    param khác nhau giữa các phiên bản pythonnet, rất dễ vỡ); thay vào đó
    so sánh danh sách ImportInstance trước/sau — cách này đúng với mọi
    phiên bản."""
    before = set()
    try:
        for e in FilteredElementCollector(target_doc).OfClass(ImportInstance):
            before.add(e.Id.IntegerValue)
    except Exception:
        pass

    opts = DWGImportOptions()
    try:
        opts.Placement = ImportPlacement.Origin
        opts.ThisViewOnly = False
        opts.OrientToView = False
        opts.ColorMode = ImportColorMode.BlackAndWhite
        opts.Unit = ImportUnit.Default
        opts.VisibleLayersOnly = False
    except Exception as ex:
        warnings.append(u"Không đặt được đầy đủ tuỳ chọn import: %s" % ex)

    ok = False
    try:
        res = target_doc.Import(path, opts, view)
        # pythonnet trả về bool hoặc tuple (bool, ElementId) tuỳ phiên bản
        if isinstance(res, tuple):
            ok = bool(res[0])
        else:
            ok = bool(res) if res is not None else True
    except Exception as ex:
        warnings.append(u"Import CAD lỗi: %s" % ex)
        return None

    found = None
    try:
        for e in FilteredElementCollector(target_doc).OfClass(ImportInstance):
            if e.Id.IntegerValue not in before:
                found = e
                break
    except Exception:
        pass
    if found is None and not ok:
        warnings.append(u"Revit không import được file: %s" % os.path.basename(path))
    return found


def entities_from_import_instance(rdoc, imp):
    """Bóc hình học từ 1 ImportInstance (CAD Link/Import) -> list CadEnt mm.
    Dùng cho CẢ 2 trường hợp: CAD vừa import vào family, và CAD Link bạn
    chọn sẵn trong project (IN[0])."""
    gopts = Options()
    try:
        gopts.ComputeReferences = False
        gopts.IncludeNonVisibleObjects = True
        gopts.DetailLevel = ViewDetailLevel.Fine
    except Exception:
        pass
    geo = imp.get_Geometry(gopts)
    ents = entities_from_geometry(rdoc, geo)
    # CAD Link có thể được đặt lệch/xoay trong project -> đưa về hệ toạ độ
    # của chính phần tử đã đặt (GetInstanceGeometry ở trên đã áp transform).
    return ents


_DWG_CACHE = {}


def make_revit_dwg_reader(scratch_doc, scratch_view, warnings):
    """Tạo read_func đọc .dwg BẰNG CHÍNH REVIT: import vào 1 family "nháp",
    bóc hình học, rồi ROLLBACK transaction — tài liệu nháp sạch nguyên như
    cũ, cực nhanh, không để lại rác. Có cache theo (đường dẫn + thời điểm
    sửa file) nên quét lại lần 2 gần như tức thì."""

    def _read(path):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".dxf":
            return read_dxf(path)
        try:
            key = (os.path.abspath(path).lower(), os.path.getmtime(path))
        except Exception:
            key = (os.path.abspath(path).lower(), 0)
        if key in _DWG_CACHE:
            return _DWG_CACHE[key], None
        if scratch_doc is None:
            return None, u"Cần Revit để đọc file DWG (hãy chạy trong Dynamo/Revit)."

        ver, verr = sniff_dwg(path)
        local_warn = []
        if verr:
            return None, verr
        ents = []
        t = Transaction(scratch_doc, u"Quét CAD")
        try:
            t.Start()
            imp = import_cad_geometry(scratch_doc, path, scratch_view, local_warn)
            if imp is not None:
                scratch_doc.Regenerate()
                ents = entities_from_import_instance(scratch_doc, imp)
        except Exception as ex:
            local_warn.append(u"Lỗi khi quét CAD: %s" % ex)
        finally:
            try:
                t.RollBack()
            except Exception:
                pass
        if not ents:
            return None, u"Không bóc được nét nào từ DWG (%s). %s" % (
                ver or u"?", u" ".join(local_warn))
        ents = sanity_fix_scale(ents, local_warn)
        cad = CadDoc(path, ents, 1.0, u"mm (Revit tự quy đổi)", True,
                     local_warn, u"REVIT-IMPORT")
        _DWG_CACHE[key] = cad
        return cad, None

    return _read


# --- Tham số family (an toàn cho nhiều đời Revit) ------------------------
def _spec_id(kind):
    """Trả về "kiểu dữ liệu" của tham số: Revit >= 2022 dùng ForgeTypeId
    (SpecTypeId), đời cũ dùng ParameterType."""
    if FORGE_API:
        table = {
            "LENGTH": lambda: SpecTypeId.Length,
            "AREA": lambda: SpecTypeId.Area,
            "VOLUME": lambda: SpecTypeId.Volume,
            "NUMBER": lambda: SpecTypeId.Number,
            "TEXT": lambda: SpecTypeId.String.Text,
            "YESNO": lambda: SpecTypeId.Boolean.YesNo,
            "MATERIAL": lambda: SpecTypeId.Reference.Material,
        }
    else:
        table = {
            "LENGTH": lambda: ParameterType.Length,
            "AREA": lambda: ParameterType.Area,
            "VOLUME": lambda: ParameterType.Volume,
            "NUMBER": lambda: ParameterType.Number,
            "TEXT": lambda: ParameterType.Text,
            "YESNO": lambda: ParameterType.YesNo,
            "MATERIAL": lambda: ParameterType.Material,
        }
    fn = table.get(kind)
    return fn() if fn else None


def _group_id(kind):
    if FORGE_API:
        table = {"GEOM": "Geometry", "ID": "IdentityData",
                 "MAT": "Materials", "CONS": "Constraints"}
        return getattr(GroupTypeId, table.get(kind, "Geometry"), None)
    table = {"GEOM": "PG_GEOMETRY", "ID": "PG_IDENTITY_DATA",
             "MAT": "PG_MATERIALS", "CONS": "PG_CONSTRAINTS"}
    return getattr(BuiltInParameterGroup, table.get(kind, "PG_GEOMETRY"), None)


def ensure_type(fm, type_name=u"Chuẩn"):
    """Family phải có ít nhất 1 Type thì mới Set được giá trị tham số."""
    try:
        if fm.Types.Size == 0:
            fm.NewType(type_name)
        else:
            for ft in fm.Types:
                fm.CurrentType = ft
                break
    except Exception:
        try:
            fm.NewType(type_name)
        except Exception:
            pass


def add_param(fm, name, kind, group, is_instance, warnings):
    """Thêm 1 tham số family. Nếu tham số đã có sẵn trong template thì dùng
    lại chính nó (không tạo trùng)."""
    try:
        for p in fm.Parameters:
            try:
                if p.Definition.Name == name:
                    return p
            except Exception:
                continue
        return fm.AddParameter(name, _group_id(group), _spec_id(kind), bool(is_instance))
    except Exception as ex:
        warnings.append(u"Không tạo được tham số '%s': %s" % (name, ex))
        return None


def set_param_value(fm, fparam, value, warnings):
    if fparam is None:
        return
    try:
        fm.Set(fparam, value)
    except Exception as ex:
        warnings.append(u"Không đặt được giá trị cho '%s': %s"
                        % (getattr(fparam.Definition, "Name", u"?"), ex))


def set_param_formula(fm, fparam, formula, warnings):
    if fparam is None:
        return
    try:
        fm.SetFormula(fparam, formula)
    except Exception as ex:
        warnings.append(u"Không đặt được công thức '%s' cho '%s': %s"
                        % (formula, getattr(fparam.Definition, "Name", u"?"), ex))


# --- View, mặt phẳng, ánh xạ toạ độ -------------------------------------
def get_family_views(fdoc):
    """Lấy các view có sẵn trong family template: mặt bằng + 4 mặt đứng.
    Nhận diện mặt đứng bằng VECTƠ HƯỚNG NHÌN (chuẩn xác với mọi ngôn ngữ
    cài đặt), tên view chỉ dùng để dự phòng."""
    out = {}
    try:
        for v in FilteredElementCollector(fdoc).OfClass(View):
            try:
                if v.IsTemplate:
                    continue
                vt = v.ViewType
            except Exception:
                continue
            if vt == ViewType.FloorPlan and "PLAN" not in out:
                out["PLAN"] = v
            elif vt == ViewType.Elevation:
                try:
                    d = v.ViewDirection
                    if abs(d.Y + 1.0) < 0.1:
                        out.setdefault("FRONT", v)
                    elif abs(d.Y - 1.0) < 0.1:
                        out.setdefault("BACK", v)
                    elif abs(d.X + 1.0) < 0.1:
                        out.setdefault("LEFT", v)
                    elif abs(d.X - 1.0) < 0.1:
                        out.setdefault("RIGHT", v)
                except Exception:
                    continue
            elif vt == ViewType.ThreeD and "3D" not in out:
                out["3D"] = v
    except Exception:
        pass
    return out


# Hướng nhìn của từng mặt đứng trong family:
#   u = vectơ "sang phải trên màn hình", v = vectơ "lên trên" (luôn là +Z),
#   n = pháp tuyến mặt phẳng đặt nét vẽ, off = vị trí mặt phẳng.
# Suy ra từ công thức r = d × up với d là hướng nhìn của từng view.
VIEW_FRAME = {
    "PLAN":  {"u": (1.0, 0.0, 0.0), "v": (0.0, 1.0, 0.0), "n": (0.0, 0.0, 1.0)},
    "FRONT": {"u": (1.0, 0.0, 0.0), "v": (0.0, 0.0, 1.0), "n": (0.0, 1.0, 0.0)},
    "BACK":  {"u": (-1.0, 0.0, 0.0), "v": (0.0, 0.0, 1.0), "n": (0.0, 1.0, 0.0)},
    "LEFT":  {"u": (0.0, -1.0, 0.0), "v": (0.0, 0.0, 1.0), "n": (1.0, 0.0, 0.0)},
    "RIGHT": {"u": (0.0, 1.0, 0.0), "v": (0.0, 0.0, 1.0), "n": (1.0, 0.0, 0.0)},
    "SECTION": {"u": (1.0, 0.0, 0.0), "v": (0.0, 0.0, 1.0), "n": (0.0, 1.0, 0.0)},
}


class PlaneMap(object):
    """Ánh xạ 1 điểm CAD (mm, hệ 2D của bản vẽ) sang toạ độ 3D của family
    (feet), kèm co giãn để hình vẽ khớp ĐÚNG kích thước Dài/Rộng/Cao mà bạn
    đặt trên GUI (FIT_CAD_TO_PARAMS).

    Toàn bộ phép tính viết bằng số thực rồi mới dựng XYZ — KHÔNG dùng toán
    tử +/- trên đối tượng XYZ, vì trên CPython3/pythonnet trong Revit các
    toán tử này từng gây crash (đã gặp ở dự án này)."""

    def __init__(self, origin_ft, u_vec, v_vec, ox_mm, oy_mm, sx=1.0, sy=1.0):
        self.o = origin_ft
        self.u = u_vec
        self.v = v_vec
        self.ox = ox_mm
        self.oy = oy_mm
        self.sx = sx
        self.sy = sy

    def pt(self, x_mm, y_mm):
        du = mm_to_ft((x_mm - self.ox) * self.sx)
        dv = mm_to_ft((y_mm - self.oy) * self.sy)
        return XYZ(self.o[0] + self.u[0] * du + self.v[0] * dv,
                   self.o[1] + self.u[1] * du + self.v[1] * dv,
                   self.o[2] + self.u[2] * du + self.v[2] * dv)

    def uniform(self, tol=0.02):
        """Co giãn 2 phương có bằng nhau không — nếu không thì cung tròn sẽ
        biến thành elip, lúc đó phải bung cung thành đường gấp khúc."""
        return abs(self.sx - self.sy) <= tol * max(abs(self.sx), abs(self.sy), 1e-9)

    def axis_u(self):
        return XYZ(self.u[0], self.u[1], self.u[2])

    def axis_v(self):
        return XYZ(self.v[0], self.v[1], self.v[2])

    def origin_xyz(self):
        return XYZ(self.o[0], self.o[1], self.o[2])


def make_view_map(kind, island, length_mm, width_mm, height_mm, fit=True):
    """Dựng PlaneMap cho 1 hình chiếu: căn giữa theo phương ngang, đặt đáy
    mặt đứng đúng cao độ 0, và co giãn cho khớp Dài/Rộng/Cao."""
    frame = VIEW_FRAME.get(kind, VIEW_FRAME["FRONT"])
    bb = island.bbox
    if not bb:
        return None
    bw, bh = bbox_size(bb)
    bw = bw if bw > 1e-6 else 1.0
    bh = bh if bh > 1e-6 else 1.0
    cx = (bb[0] + bb[2]) / 2.0
    cy = (bb[1] + bb[3]) / 2.0

    L_ft, W_ft = mm_to_ft(length_mm), mm_to_ft(width_mm)
    if kind == "PLAN":
        sx = (length_mm / bw) if fit else 1.0
        sy = (width_mm / bh) if fit else 1.0
        return PlaneMap((0.0, 0.0, 0.0), frame["u"], frame["v"], cx, cy, sx, sy)

    # Mặt đứng: gốc chiều cao đặt ở đáy hình vẽ (y nhỏ nhất) -> cao độ 0.
    oy = bb[1]
    sy = (height_mm / bh) if fit else 1.0
    if kind in ("FRONT", "BACK", "SECTION"):
        sx = (length_mm / bw) if fit else 1.0
        oz = 0.0
        origin = (0.0, -W_ft / 2.0 if kind == "FRONT" else W_ft / 2.0, oz)
        if kind == "SECTION":
            origin = (0.0, 0.0, oz)
        return PlaneMap(origin, frame["u"], frame["v"], cx, oy, sx, sy)
    # LEFT/RIGHT: bề ngang của mặt bên chính là chiều RỘNG của vật
    sx = (width_mm / bw) if fit else 1.0
    origin = (-L_ft / 2.0 if kind == "LEFT" else L_ft / 2.0, 0.0, 0.0)
    return PlaneMap(origin, frame["u"], frame["v"], cx, oy, sx, sy)


MIN_CURVE_LEN_FT = 1.2 / MM_PER_FT      # Revit từ chối đường < ~0.8 mm


def ent_to_revit_curves(ent, pmap, simplify_tol=0.0):
    """Đổi 1 CadEnt thành list Curve của Revit theo phép ánh xạ pmap."""
    curves = []
    try:
        if ent.kind == "CIRCLE" and ent.center and pmap.uniform():
            c = pmap.pt(ent.center[0], ent.center[1])
            r = mm_to_ft(ent.radius * pmap.sx)
            if r > MIN_CURVE_LEN_FT:
                # Revit không nhận 1 cung 360° -> tách làm 2 nửa
                curves.append(Arc.Create(c, r, 0.0, math.pi, pmap.axis_u(), pmap.axis_v()))
                curves.append(Arc.Create(c, r, math.pi, 2.0 * math.pi, pmap.axis_u(), pmap.axis_v()))
            return curves
        if ent.kind == "ARC" and ent.center and pmap.uniform():
            c = pmap.pt(ent.center[0], ent.center[1])
            r = mm_to_ft(ent.radius * pmap.sx)
            a0 = math.radians(ent.a0)
            a1 = math.radians(ent.a1)
            while a1 <= a0:
                a1 += 2.0 * math.pi
            if r > MIN_CURVE_LEN_FT and (a1 - a0) > 1e-4:
                if (a1 - a0) > 2.0 * math.pi - 1e-6:
                    a1 = a0 + math.pi
                    curves.append(Arc.Create(c, r, a0, a1, pmap.axis_u(), pmap.axis_v()))
                    curves.append(Arc.Create(c, r, a1, a1 + math.pi, pmap.axis_u(), pmap.axis_v()))
                else:
                    curves.append(Arc.Create(c, r, a0, a1, pmap.axis_u(), pmap.axis_v()))
            return curves
        pts = ent.points()
        if simplify_tol > 0 and len(pts) > 3:
            pts = simplify_polyline(pts, simplify_tol)
        for i in range(len(pts) - 1):
            p1 = pmap.pt(pts[i][0], pts[i][1])
            p2 = pmap.pt(pts[i + 1][0], pts[i + 1][1])
            if p1.DistanceTo(p2) > MIN_CURVE_LEN_FT:
                curves.append(Line.CreateBound(p1, p2))
    except Exception:
        return curves
    return curves


def loop_to_curve_array(loop, pmap):
    """Đổi 1 vòng kín (list điểm mm) thành CurveArray khép kín của Revit."""
    pts = dedupe_points(list(loop), 0.05)
    if len(pts) < 3:
        return None
    xyz = [pmap.pt(p[0], p[1]) for p in pts]
    ca = CurveArray()
    n = len(xyz)
    made = 0
    for i in range(n):
        p1 = xyz[i]
        p2 = xyz[(i + 1) % n]
        if p1.DistanceTo(p2) <= MIN_CURVE_LEN_FT:
            continue
        ca.Append(Line.CreateBound(p1, p2))
        made += 1
    return ca if made >= 3 else None


def rect_curve_array(length_ft, width_ft, z=0.0):
    """CurveArray hình chữ nhật L×W tâm tại gốc — biên dạng dự phòng khi
    không lấy được biên dạng CAD."""
    hl, hw = length_ft / 2.0, width_ft / 2.0
    p = [XYZ(-hl, -hw, z), XYZ(hl, -hw, z), XYZ(hl, hw, z), XYZ(-hl, hw, z)]
    ca = CurveArray()
    for i in range(4):
        ca.Append(Line.CreateBound(p[i], p[(i + 1) % 4]))
    return ca


# --- Dựng family --------------------------------------------------------
def set_family_category(fdoc, category, warnings):
    """Đặt danh mục cho family. Với Cửa/Cửa sổ thì KHÔNG đổi (phải dùng
    đúng template gốc vì có tường chủ + lỗ mở dựng sẵn)."""
    if category in HOST_BOUND_CATEGORIES:
        return
    bic_name = CATEGORY_BIC.get(category)
    if not bic_name:
        return
    try:
        bic = getattr(BuiltInCategory, bic_name)
        cat = Category.GetCategory(fdoc, bic)
        if cat is not None:
            fdoc.OwnerFamily.FamilyCategory = cat
    except Exception as ex:
        warnings.append(u"Không đổi được danh mục sang %s: %s" % (category, ex))


def new_subcategory(fdoc, name, warnings):
    """Tạo Subcategory (lớp con) để bạn bật/tắt nét CAD trong 1 nốt nhạc."""
    try:
        parent = fdoc.OwnerFamily.FamilyCategory
        cats = fdoc.Settings.Categories
        for c in parent.SubCategories:
            if c.Name == name:
                return c
        return cats.NewSubcategory(parent, name)
    except Exception as ex:
        warnings.append(u"Không tạo được subcategory '%s': %s" % (name, ex))
        return None


def _set_line_style(elem, subcat, warnings):
    if subcat is None or elem is None:
        return
    try:
        gs = subcat.GetGraphicsStyle(GraphicsStyleType.Projection)
        if gs is not None:
            elem.LineStyle = gs
    except Exception:
        pass


def create_ref_plane(fdoc, view, p1, p2, cut, name, warnings):
    try:
        rp = fdoc.FamilyCreate.NewReferencePlane(p1, p2, cut, view)
        try:
            rp.Name = name
        except Exception:
            pass          # trùng tên với plane có sẵn của template -> bỏ qua
        return rp
    except Exception as ex:
        warnings.append(u"Không tạo được Reference Plane '%s': %s" % (name, ex))
        return None


def label_dimension(fdoc, view, ref_a, ref_b, line, fparam, warnings, tag=u""):
    """Tạo Dimension giữa 2 Reference rồi GẮN NHÃN tham số vào — đây chính
    là thứ làm family "kéo ra kéo vào" được."""
    if ref_a is None or ref_b is None or fparam is None or view is None:
        return None
    try:
        ra = ReferenceArray()
        ra.Append(ref_a)
        ra.Append(ref_b)
        dim = fdoc.FamilyCreate.NewDimension(view, line, ra)
        try:
            dim.FamilyLabel = fparam
        except Exception as ex:
            warnings.append(u"Không gắn được nhãn tham số %s: %s" % (tag, ex))
        return dim
    except Exception as ex:
        warnings.append(u"Không tạo được Dimension %s: %s" % (tag, ex))
        return None


def planar_face_ref(elem, direction, warnings):
    """Lấy Reference của mặt phẳng NGOÀI CÙNG theo 1 hướng (vd hướng +X =
    mặt bên phải của khối). Cần cho NewAlignment để khoá khối vào Reference
    Plane -> khối co giãn theo tham số."""
    try:
        gopts = Options()
        gopts.ComputeReferences = True
        gopts.IncludeNonVisibleObjects = False
        gopts.DetailLevel = ViewDetailLevel.Fine
        geo = elem.get_Geometry(gopts)
        if geo is None:
            return None
        best, best_d = None, None
        d = XYZ(direction[0], direction[1], direction[2])
        for gobj in geo:
            solids = []
            if isinstance(gobj, Solid):
                solids = [gobj]
            elif isinstance(gobj, GeometryInstance):
                solids = [g for g in gobj.GetInstanceGeometry() if isinstance(g, Solid)]
            for sol in solids:
                for f in sol.Faces:
                    if not isinstance(f, PlanarFace):
                        continue
                    n = f.FaceNormal
                    if (n.X * d.X + n.Y * d.Y + n.Z * d.Z) < 0.999:
                        continue
                    o = f.Origin
                    dist = o.X * d.X + o.Y * d.Y + o.Z * d.Z
                    if best_d is None or dist > best_d:
                        best_d, best = dist, f
        return best.Reference if best is not None else None
    except Exception as ex:
        warnings.append(u"Không lấy được mặt phẳng của khối: %s" % ex)
        return None


def align_face(fdoc, view, rp, elem, direction, warnings, tag=u""):
    """Align + Lock 1 mặt của khối vào 1 Reference Plane."""
    if rp is None or view is None:
        return False
    fref = planar_face_ref(elem, direction, warnings)
    if fref is None:
        return False
    try:
        al = fdoc.FamilyCreate.NewAlignment(view, rp.GetReference(), fref)
        try:
            al.IsLocked = True
        except Exception:
            pass
        return True
    except Exception as ex:
        warnings.append(u"Không khoá được mặt %s vào Reference Plane: %s" % (tag, ex))
        return False


def level_plane_ref(fdoc):
    """Reference của cao độ Ref. Level (đáy family)."""
    try:
        for lv in FilteredElementCollector(fdoc).OfClass(Level):
            try:
                return lv.GetPlaneReference()
            except Exception:
                continue
    except Exception:
        pass
    return None


def build_extrusion(fdoc, plan, ctx, warnings):
    """Dựng khối 3D. Thứ tự thử (rơi xuống mức sau nếu mức trước lỗi):
        1) Biên dạng CAD (biên ngoài + các lỗ rỗng)
        2) Biên dạng CAD (chỉ biên ngoài)
        3) Hình chữ nhật Dài × Rộng
    Nhờ vậy 1 bản vẽ CAD "bẩn" (nét chồng, hở) vẫn ra được family dùng
    được, thay vì báo lỗi rồi bỏ trắng."""
    L_ft = mm_to_ft(plan.length)
    W_ft = mm_to_ft(plan.width)
    H_ft = mm_to_ft(plan.height)
    if H_ft <= MIN_CURVE_LEN_FT:
        H_ft = mm_to_ft(DEFAULT_DIMS.get(plan.category, DEFAULT_DIMS["GenericModel"])[2])

    sp = None
    try:
        sp = SketchPlane.Create(fdoc, Plane.CreateByNormalAndOrigin(XYZ(0, 0, 1), XYZ(0, 0, 0)))
    except Exception as ex:
        warnings.append(u"Không tạo được mặt phẳng vẽ khối: %s" % ex)
        return None, False

    attempts = []
    island = plan.views.get("PLAN")
    use_profile = plan.mode in (MODE_HYBRID, MODE_PROFILE) and island is not None
    rect_like = True
    if use_profile:
        pmap = make_view_map("PLAN", island, plan.length, plan.width, plan.height,
                             ctx.get("fit_to_params", True))
        loops = collect_loops(island.drawable())
        outer, inner = pick_profile_loops(loops)
        if outer:
            rect_like = is_rectangleish(outer)
            ca_out = loop_to_curve_array(outer, pmap)
            if ca_out is not None:
                arr_full = CurveArrArray()
                arr_full.Append(ca_out)
                n_holes = 0
                for lp in inner:
                    ca_in = loop_to_curve_array(lp, pmap)
                    if ca_in is not None:
                        arr_full.Append(ca_in)
                        n_holes += 1
                if n_holes:
                    attempts.append((arr_full, u"biên dạng CAD + %d lỗ" % n_holes))
                arr_solo = CurveArrArray()
                arr_solo.Append(loop_to_curve_array(outer, pmap))
                attempts.append((arr_solo, u"biên dạng CAD"))
        else:
            warnings.append(u"Không tìm thấy biên dạng kín trên mặt bằng — dùng khối hộp.")

    arr_rect = CurveArrArray()
    arr_rect.Append(rect_curve_array(L_ft, W_ft))
    attempts.append((arr_rect, u"hộp Dài×Rộng"))

    for arr, label in attempts:
        try:
            ext = fdoc.FamilyCreate.NewExtrusion(True, arr, sp, H_ft)
            warnings.append(u"Khối 3D dựng theo %s." % label)
            is_rect = rect_like or label == u"hộp Dài×Rộng"
            return ext, is_rect
        except Exception as ex:
            warnings.append(u"Đùn khối theo %s không thành (%s) — thử cách khác." % (label, ex))
            continue
    return None, False


def draw_linework(fdoc, plan, ctx, warnings):
    """Vẽ lại nét CAD lên các hình chiếu của family.

    GIỚI HẠN CÓ THẬT CỦA REVIT (nói rõ để bạn không bất ngờ): Symbolic Line
    chỉ bật/tắt được theo CẶP "Front/Back" và "Left/Right" — Revit KHÔNG cho
    tách riêng Front với Back. Vì vậy:
      • Mặt bằng            -> Symbolic Line (chỉ hiện ở mặt bằng)
      • Mặt đứng chính      -> Symbolic Line (hiện ở Front + Back)
      • Mặt bên trái        -> Symbolic Line (hiện ở Left + Right)
      • Mặt sau / mặt phải  -> Model Line đặt đúng vị trí thật (mặt sau ở
        y = +Rộng/2, mặt phải ở x = +Dài/2), nằm trong subcategory riêng
        "CAD - Mặt sau & phải" để bạn tắt trong 1 nốt nhạc nếu thấy rối.
    Nhờ vậy family vẫn có ĐỦ dữ liệu của cả 4 mặt đứng + mặt bằng."""
    if plan.mode == MODE_BOX:
        return 0
    turbo = ctx.get("turbo", False)
    simp = TURBO_SIMPLIFY_TOL_MM if turbo else 0.0
    cap = MAX_CURVES_PER_VIEW_TURBO if turbo else MAX_CURVES_PER_VIEW

    sym_kinds = []
    if "PLAN" in plan.views:
        sym_kinds.append("PLAN")
    sym_kinds.append("FRONT" if "FRONT" in plan.views else ("BACK" if "BACK" in plan.views else None))
    sym_kinds.append("LEFT" if "LEFT" in plan.views else ("RIGHT" if "RIGHT" in plan.views else None))
    sym_kinds = [k for k in sym_kinds if k]

    model_kinds = []
    if ctx.get("draw_back_right", True):
        if "BACK" in plan.views and "FRONT" in plan.views:
            model_kinds.append("BACK")
        if "RIGHT" in plan.views and "LEFT" in plan.views:
            model_kinds.append("RIGHT")

    sub_names = {
        "PLAN": u"CAD - Mặt bằng",
        "FRONT": u"CAD - Mặt đứng",
        "BACK": u"CAD - Mặt sau & phải",
        "LEFT": u"CAD - Mặt bên",
        "RIGHT": u"CAD - Mặt sau & phải",
    }
    subcats = {}
    total = 0

    for kind in sym_kinds + model_kinds:
        island = plan.views.get(kind)
        if island is None:
            continue
        pmap = make_view_map(kind, island, plan.length, plan.width, plan.height,
                             ctx.get("fit_to_params", True))
        if pmap is None:
            continue
        frame = VIEW_FRAME.get(kind, VIEW_FRAME["FRONT"])
        try:
            sp = SketchPlane.Create(fdoc, Plane.CreateByNormalAndOrigin(
                XYZ(frame["n"][0], frame["n"][1], frame["n"][2]), pmap.origin_xyz()))
        except Exception as ex:
            warnings.append(u"Không tạo được mặt phẳng vẽ cho %s: %s" % (kind, ex))
            continue

        sname = sub_names.get(kind, u"CAD")
        if sname not in subcats:
            subcats[sname] = new_subcategory(fdoc, sname, warnings)
        subcat = subcats[sname]

        is_model = kind in model_kinds
        count = 0
        for ent in island.drawable():
            if is_noise_layer(ent.layer):
                continue
            if count >= cap:
                warnings.append(u"Hình chiếu %s có quá nhiều nét — chỉ vẽ %d nét đầu "
                                u"(bật/tắt giới hạn ở MAX_CURVES_PER_VIEW)." % (kind, cap))
                break
            for cur in ent_to_revit_curves(ent, pmap, simp):
                if count >= cap:
                    break
                try:
                    if is_model:
                        el = fdoc.FamilyCreate.NewModelCurve(cur, sp)
                    else:
                        el = fdoc.FamilyCreate.NewSymbolicCurve(cur, sp)
                        _apply_symbolic_visibility(el, kind, warnings)
                    _set_line_style(el, subcat, warnings)
                    count += 1
                except Exception:
                    continue
        total += count
    return total


def _apply_symbolic_visibility(sym, kind, warnings):
    """Đặt Symbolic Line hiện đúng ở nhóm view của nó."""
    try:
        vis = FamilyElementVisibility(FamilyElementVisibilityType.ViewSpecific)
        vis.IsShownInPlanRCPCut = (kind == "PLAN")
        vis.IsShownInFrontBack = kind in ("FRONT", "BACK", "SECTION")
        vis.IsShownInLeftRight = kind in ("LEFT", "RIGHT")
        sym.SetVisibility(vis)
    except Exception:
        pass


def build_family(plan, ctx):
    """Tạo 1 file .rfa hoàn chỉnh từ 1 FamilyPlan. Trả về (đường_dẫn, ok).
    Mọi bước đều bọc try/except riêng: 1 bước hỏng (vd không khoá được ràng
    buộc) vẫn cho ra family dùng được, chỉ ghi cảnh báo."""
    warnings = plan.warnings
    tpl = plan.template_path
    if not tpl or not os.path.isfile(tpl):
        plan.status = u"✖ Thiếu template .rft"
        return None, False

    try:
        fdoc = ctx["app"].NewFamilyDocument(tpl)
    except Exception as ex:
        warnings.append(u"Không mở được template '%s': %s" % (tpl, ex))
        plan.status = u"✖ Lỗi template"
        return None, False

    out_path = None
    try:
        L_ft = mm_to_ft(plan.length)
        W_ft = mm_to_ft(plan.width)
        H_ft = mm_to_ft(plan.height)

        t = Transaction(fdoc, u"Dựng family từ CAD")
        t.Start()
        try:
            set_family_category(fdoc, plan.category, warnings)

            fm = fdoc.FamilyManager
            ensure_type(fm, ctx.get("type_name", u"Chuẩn"))
            inst = ctx.get("instance_params", True) and plan.category not in HOST_BOUND_CATEGORIES
            p_len = add_param(fm, P_LEN, "LENGTH", "GEOM", inst, warnings)
            p_wid = add_param(fm, P_WID, "LENGTH", "GEOM", inst, warnings)
            p_hgt = add_param(fm, P_HGT, "LENGTH", "GEOM", inst, warnings)
            set_param_value(fm, p_len, L_ft, warnings)
            set_param_value(fm, p_wid, W_ft, warnings)
            set_param_value(fm, p_hgt, H_ft, warnings)

            views = get_family_views(fdoc)
            v_plan = views.get("PLAN")
            v_front = views.get("FRONT") or views.get("BACK")
            if v_plan is None:
                warnings.append(u"Template không có view mặt bằng — bỏ qua ràng buộc Dài/Rộng.")
            if v_front is None:
                warnings.append(u"Template không có view mặt đứng — bỏ qua ràng buộc Cao.")

            # --- Reference Plane: khung xương co giãn của family ---------
            rp = {}
            if v_plan is not None:
                cut = XYZ(0, 0, 1)
                span = max(L_ft, W_ft)
                rp["L"] = create_ref_plane(fdoc, v_plan, XYZ(-L_ft / 2.0, -span, 0),
                                           XYZ(-L_ft / 2.0, span, 0), cut, u"Cạnh Trái", warnings)
                rp["R"] = create_ref_plane(fdoc, v_plan, XYZ(L_ft / 2.0, -span, 0),
                                           XYZ(L_ft / 2.0, span, 0), cut, u"Cạnh Phải", warnings)
                rp["F"] = create_ref_plane(fdoc, v_plan, XYZ(-span, -W_ft / 2.0, 0),
                                           XYZ(span, -W_ft / 2.0, 0), cut, u"Cạnh Trước", warnings)
                rp["B"] = create_ref_plane(fdoc, v_plan, XYZ(-span, W_ft / 2.0, 0),
                                           XYZ(span, W_ft / 2.0, 0), cut, u"Cạnh Sau", warnings)
            if v_front is not None:
                rp["T"] = create_ref_plane(fdoc, v_front, XYZ(-L_ft, 0, H_ft),
                                           XYZ(L_ft, 0, H_ft), XYZ(0, 1, 0), u"Đỉnh", warnings)

            # --- Dimension + gắn nhãn tham số ---------------------------
            if v_plan is not None and rp.get("L") and rp.get("R"):
                label_dimension(fdoc, v_plan, rp["L"].GetReference(), rp["R"].GetReference(),
                                Line.CreateBound(XYZ(-L_ft / 2.0, W_ft * 0.8, 0),
                                                 XYZ(L_ft / 2.0, W_ft * 0.8, 0)),
                                p_len, warnings, P_LEN)
            if v_plan is not None and rp.get("F") and rp.get("B"):
                label_dimension(fdoc, v_plan, rp["F"].GetReference(), rp["B"].GetReference(),
                                Line.CreateBound(XYZ(L_ft * 0.8, -W_ft / 2.0, 0),
                                                 XYZ(L_ft * 0.8, W_ft / 2.0, 0)),
                                p_wid, warnings, P_WID)
            base_ref = level_plane_ref(fdoc)
            if v_front is not None and rp.get("T") and base_ref is not None:
                label_dimension(fdoc, v_front, base_ref, rp["T"].GetReference(),
                                Line.CreateBound(XYZ(L_ft * 0.8, 0, 0), XYZ(L_ft * 0.8, 0, H_ft)),
                                p_hgt, warnings, P_HGT)

            # --- Khối 3D ------------------------------------------------
            ext, rect_like = build_extrusion(fdoc, plan, ctx, warnings)

            if ext is not None:
                try:
                    fdoc.Regenerate()      # phải Regenerate thì mới lấy được mặt của khối
                except Exception:
                    pass
                locked = 0
                if v_front is not None and rp.get("T"):
                    locked += 1 if align_face(fdoc, v_front, rp["T"], ext, (0, 0, 1), warnings, P_HGT) else 0
                if rect_like and v_plan is not None:
                    if rp.get("R"):
                        locked += 1 if align_face(fdoc, v_plan, rp["R"], ext, (1, 0, 0), warnings, u"phải") else 0
                    if rp.get("L"):
                        locked += 1 if align_face(fdoc, v_plan, rp["L"], ext, (-1, 0, 0), warnings, u"trái") else 0
                    if rp.get("B"):
                        locked += 1 if align_face(fdoc, v_plan, rp["B"], ext, (0, 1, 0), warnings, u"sau") else 0
                    if rp.get("F"):
                        locked += 1 if align_face(fdoc, v_plan, rp["F"], ext, (0, -1, 0), warnings, u"trước") else 0
                elif not rect_like:
                    warnings.append(u"Biên dạng CAD không phải hình chữ nhật nên chỉ khoá được "
                                    u"chiều CAO vào tham số; Dài/Rộng vẫn có nhưng không kéo "
                                    u"giãn được biên dạng (chọn chế độ BOX nếu cần co giãn 100%).")
                plan.warnings.append(u"Đã khoá %d mặt khối vào Reference Plane." % locked)

                # tham số Vật liệu, liên kết thẳng vào khối
                try:
                    p_mat = add_param(fm, u"Vật liệu", "MATERIAL", "MAT", False, warnings)
                    mp = ext.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)
                    if p_mat is not None and mp is not None:
                        fm.AssociateElementParameterToFamilyParameter(mp, p_mat)
                except Exception:
                    pass

            # --- Vẽ lại nét CAD lên các hình chiếu ----------------------
            n_curves = draw_linework(fdoc, plan, ctx, warnings)
            plan.warnings.append(u"Đã vẽ lại %d nét CAD lên các hình chiếu." % n_curves)

            # --- Tham số công thức ("thuật toán") -----------------------
            if ctx.get("formula_params", True):
                for name, kind, formula, is_inst in FORMULA_PARAMS:
                    fp = add_param(fm, name, kind, "GEOM", is_inst, warnings)
                    set_param_formula(fm, fp, formula, warnings)

            # --- Tham số nhận dạng --------------------------------------
            ident = {
                u"Mã hiệu": plan.family_name,
                u"Nguồn CAD": u"; ".join(os.path.basename(p) for p in plan.src_paths)[:250],
                u"Ngày tạo": time.strftime("%d/%m/%Y %H:%M"),
            }
            for name, kind in IDENTITY_PARAMS:
                fp = add_param(fm, name, kind, "ID", False, warnings)
                set_param_value(fm, fp, ident.get(name, u""), warnings)

            t.Commit()
        except Exception:
            try:
                t.RollBack()
            except Exception:
                pass
            raise

        # --- Lưu file .rfa ----------------------------------------------
        ensure_dir(ctx["out_dir"])
        out_path = os.path.join(ctx["out_dir"], u"%s.rfa" % plan.family_name)
        so = SaveAsOptions()
        try:
            so.OverwriteExistingFile = True
            so.MaximumBackups = 1
        except Exception:
            pass
        fdoc.SaveAs(out_path, so)
        plan.out_path = out_path
        plan.status = u"✔ Đã tạo"
        return out_path, True
    except Exception as ex:
        warnings.append(u"Lỗi dựng family '%s': %s" % (plan.family_name, ex))
        warnings.append(traceback.format_exc())
        plan.status = u"✖ Lỗi dựng"
        return None, False
    finally:
        try:
            fdoc.Close(False)
        except Exception:
            pass


def load_families_into_project(project_doc, paths, warnings):
    """Nạp các .rfa vừa tạo vào project đang mở, trong ĐÚNG 1 Transaction.
    Dùng Document.LoadFamily(string) — bản KHÔNG cần IFamilyLoadOptions, vì
    hiện thực 1 interface .NET từ Python sẽ kích hoạt TypeBuilder và làm
    crash CPython3 trong Revit (xem ghi chú GUI ở đầu file)."""
    if not paths or project_doc is None:
        return 0
    if DYNAMO_ENV and TransactionManager is not None:
        try:
            TransactionManager.Instance.ForceCloseTransaction()
        except Exception:
            pass
    n = 0
    t = Transaction(project_doc, u"Nạp family từ CAD")
    t.Start()
    try:
        for p in paths:
            try:
                if project_doc.LoadFamily(p):
                    n += 1
                else:
                    warnings.append(u"Family '%s' đã có sẵn trong project — bỏ qua nạp lại."
                                    % os.path.basename(p))
            except Exception as ex:
                warnings.append(u"Không nạp được '%s': %s" % (os.path.basename(p), ex))
        t.Commit()
    except Exception:
        try:
            t.RollBack()
        except Exception:
            pass
    return n


# ------------------------------------------------------------------------
# 9. GIAO DIỆN GUI — WINFORMS "EVENTLESS", THEME TỐI SANG TRỌNG VÀNG ĐỒNG
# ------------------------------------------------------------------------
def hexcolor(h):
    h = h.lstrip("#")
    return Color.FromArgb(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


CAT_CHOICES = [u"Tự động", u"Doors – Cửa đi", u"Windows – Cửa sổ",
               u"PlumbingFixtures – Thiết bị vệ sinh", u"Casework – Tủ/kệ",
               u"Furniture – Nội thất", u"LightingFixtures – Đèn",
               u"SpecialityEquipment – Thiết bị", u"GenericModel – Mô hình khối"]
CAT_CODES = [None, "Doors", "Windows", "PlumbingFixtures", "Casework",
             "Furniture", "LightingFixtures", "SpecialityEquipment", "GenericModel"]
CAT_SHORT = {"Doors": u"Cửa đi", "Windows": u"Cửa sổ",
             "PlumbingFixtures": u"TB vệ sinh", "Casework": u"Tủ/kệ",
             "Furniture": u"Nội thất", "LightingFixtures": u"Đèn",
             "SpecialityEquipment": u"Thiết bị", "GenericModel": u"Khối chung"}
SHORT_TO_CAT = dict((norm_key(v), k) for k, v in CAT_SHORT.items())

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
    C_OK = hexcolor(THEME["ok"])
    C_ERR = hexcolor(THEME["err"])
    C_INK = Color.FromArgb(20, 20, 20)

    def safe_font(size=9.5, bold=False, family="Segoe UI"):
        """Font .NET an toàn: nếu family/size gây lỗi (đã gặp trên CPython3:
        ArgumentException 'Parameter is not valid') thì lùi về font hệ thống
        thay vì làm sập cả cửa sổ."""
        style = FontStyle.Bold if bold else FontStyle.Regular
        try:
            em = Single(float(size))
        except Exception:
            em = float(size)
        try:
            return Font(family, em, style, GraphicsUnit.Point)
        except Exception:
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

    A_TL = AnchorStyles.Top | AnchorStyles.Left
    A_TR = AnchorStyles.Top | AnchorStyles.Right
    A_TLR = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
    A_BR = AnchorStyles.Bottom | AnchorStyles.Right
    A_BLR = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right

    def anchor(ctrl, a):
        try:
            ctrl.Anchor = a
        except Exception:
            pass
        return ctrl

    def add_button(parent, text, x, y, w, h, result, primary=False, a=None):
        b = Button()
        b.Text = text
        b.Location = Point(x, y)
        b.Size = Size(w, h)
        b.DialogResult = result
        style_button(b, primary)
        parent.Controls.Add(b)
        if a is not None:
            anchor(b, a)
        return b

    def mk_form(title, width, height):
        """Cửa sổ luôn nằm gọn trong màn hình: laptop 1366×768 vẫn dùng
        được, không bị tràn nút bấm ra ngoài."""
        f = Form()
        f.Text = title
        try:
            wa = Screen.PrimaryScreen.WorkingArea
            width = min(width, wa.Width - 40)
            height = min(height, wa.Height - 40)
        except Exception:
            pass
        width = max(width, 1080)
        height = max(height, 640)
        f.Size = Size(width, height)
        f.MinimumSize = Size(min(width, 1080), min(height, 640))
        f.StartPosition = FormStartPosition.CenterScreen
        f.BackColor = C_BG
        f.ForeColor = C_TEXT
        f.FormBorderStyle = FormBorderStyle.Sizable
        set_font(f, 9.5, False)
        return f

    def add_label(parent, text, x, y, w, h, color=None, bold=False, size=9.5, a=None):
        l = Label()
        l.Text = text
        l.Location = Point(x, y)
        l.Size = Size(w, h)
        l.ForeColor = color or C_TEXT
        l.BackColor = Color.Transparent
        set_font(l, size, bold)
        parent.Controls.Add(l)
        if a is not None:
            anchor(l, a)
        return l

    def add_textbox(parent, text, x, y, w, h=26, a=None):
        tb = TextBox()
        tb.Text = text or u""
        tb.Location = Point(x, y)
        tb.Size = Size(w, h)
        tb.BackColor = Color.White
        tb.ForeColor = Color.Black
        set_font(tb, 9.5, False)
        parent.Controls.Add(tb)
        if a is not None:
            anchor(tb, a)
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

    def add_check(parent, text, x, y, w, checked=False):
        cb = CheckBox()
        cb.Text = text
        cb.Location = Point(x, y)
        cb.Size = Size(w, 24)
        cb.Checked = bool(checked)
        cb.ForeColor = C_TEXT
        cb.BackColor = Color.Transparent
        set_font(cb, 9.0, False)
        parent.Controls.Add(cb)
        return cb

    # Cột lưới: (tiêu đề, rộng, chỉ đọc)
    GRID_COLS = [
        (u"✔", 34, False), (u"TÊN FAMILY", 230, False), (u"DANH MỤC", 110, False),
        (u"CHẾ ĐỘ", 90, False), (u"DÀI (mm)", 80, False), (u"RỘNG (mm)", 80, False),
        (u"CAO (mm)", 80, False), (u"HÌNH CHIẾU", 110, True), (u"FILE CAD", 200, True),
        (u"TRẠNG THÁI / NHẬN DIỆN", 380, True),
    ]

    def build_plan_grid(x, y, w, h):
        grid = DataGridView()
        grid.Location = Point(x, y)
        grid.Size = Size(w, h)
        grid.AllowUserToAddRows = False
        grid.AllowUserToDeleteRows = False
        grid.AllowUserToResizeRows = False
        grid.RowHeadersVisible = False
        grid.SelectionMode = DataGridViewSelectionMode.CellSelect
        grid.MultiSelect = True
        grid.BackgroundColor = C_BG
        grid.GridColor = C_GRID_LINE
        grid.BorderStyle = getattr(BorderStyle, "None")
        grid.EnableHeadersVisualStyles = False
        grid.ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.DisableResizing
        grid.ColumnHeadersHeight = 34
        grid.RowTemplate.Height = 26
        grid.AutoSizeColumnsMode = getattr(DataGridViewAutoSizeColumnsMode, "None")
        grid.ColumnHeadersDefaultCellStyle.BackColor = C_PANEL2
        grid.ColumnHeadersDefaultCellStyle.ForeColor = C_GOLD
        grid.ColumnHeadersDefaultCellStyle.Font = safe_font(9.0, True)
        grid.DefaultCellStyle.BackColor = C_BG
        grid.DefaultCellStyle.ForeColor = C_TEXT
        grid.DefaultCellStyle.SelectionBackColor = C_GOLD_DARK
        grid.DefaultCellStyle.SelectionForeColor = C_INK
        grid.AlternatingRowsDefaultCellStyle.BackColor = C_ROW_ALT
        grid.AlternatingRowsDefaultCellStyle.ForeColor = C_TEXT
        set_font(grid, 9.0, False)

        chk = DataGridViewCheckBoxColumn()
        chk.HeaderText = GRID_COLS[0][0]
        chk.Width = GRID_COLS[0][1]
        chk.SortMode = DataGridViewColumnSortMode.NotSortable
        grid.Columns.Add(chk)
        for title, wid, ro in GRID_COLS[1:]:
            c = DataGridViewTextBoxColumn()
            c.HeaderText = title
            c.Width = wid
            c.ReadOnly = ro
            # Cấm sort: nếu WinForms sắp xếp lại hàng thì ánh xạ hàng <-> plan
            # sẽ lệch hoàn toàn.
            c.SortMode = DataGridViewColumnSortMode.NotSortable
            grid.Columns.Add(c)
        return grid

    def fill_grid(grid, plans):
        grid.Rows.Clear()
        for p in plans:
            i = grid.Rows.Add()
            r = grid.Rows[i]
            r.Cells[0].Value = bool(p.enabled)
            r.Cells[1].Value = p.family_name
            r.Cells[2].Value = CAT_SHORT.get(p.category, p.category)
            r.Cells[3].Value = p.mode
            r.Cells[4].Value = fmt_mm(p.length)
            r.Cells[5].Value = fmt_mm(p.width)
            r.Cells[6].Value = fmt_mm(p.height)
            r.Cells[7].Value = p.views_display()
            r.Cells[8].Value = p.src_display
            r.Cells[9].Value = u"%s — %s" % (p.status, p.detect_note or u"")
            try:
                if p.status.startswith(u"✖"):
                    r.Cells[9].Style.ForeColor = C_ERR
                elif p.status.startswith(u"✔"):
                    r.Cells[9].Style.ForeColor = C_OK
            except Exception:
                pass

    def read_grid(grid, plans, used_names):
        """Đọc ngược những gì bạn đã sửa trên lưới về lại các FamilyPlan."""
        n = min(grid.Rows.Count, len(plans))
        used_names.clear()
        for i in range(n):
            r = grid.Rows[i]
            p = plans[i]
            try:
                p.enabled = bool(r.Cells[0].Value)
            except Exception:
                p.enabled = True
            name = r.Cells[1].Value
            p.family_name = unique_name(sanitize_family_name(name or p.family_name), used_names)
            cat_txt = norm_key(r.Cells[2].Value or u"")
            p.category = SHORT_TO_CAT.get(cat_txt, p.category)
            mode_txt = (u"%s" % (r.Cells[3].Value or p.mode)).strip().upper()
            p.mode = mode_txt if mode_txt in BUILD_MODES else p.mode
            p.length = parse_number(r.Cells[4].Value, p.length) or p.length
            p.width = parse_number(r.Cells[5].Value, p.width) or p.width
            p.height = parse_number(r.Cells[6].Value, p.height) or p.height


def run_gui(state, ctx):
    """Vòng lặp GUI "eventless": mỗi lần bấm nút, cửa sổ tự đóng (nhờ
    Button.DialogResult — xử lý 100% trong .NET, không cần callback Python),
    Python đọc lại toàn bộ control + lưới, xử lý, rồi dựng LẠI cửa sổ mới với
    dữ liệu đã cập nhật. Lặp tới khi bạn bấm "TẠO FAMILY" hoặc "Đóng"."""
    try:
        Application.EnableVisualStyles()
    except Exception:
        pass

    NONE_RESULT = getattr(DialogResult, "None")
    used_names = set()
    status_msg = u"Dán đường dẫn file/thư mục CAD rồi bấm \"🔍 QUÉT\" — hoặc bấm nút chọn thư mục."
    result = {"status": "Cancelled", "created": 0, "failed": 0, "files": [], "build_ms": 0}
    bulk_cat = 0
    bulk_mode = 0

    while True:
        plans = state["plans"]
        f = mk_form(u"CAD → REVIT FAMILY — TẠO FAMILY HÀNG LOẠT TỪ FILE CAD", 1560, 900)
        cw = f.ClientSize.Width
        ch = f.ClientSize.Height

        header = Panel()
        header.Dock = DockStyle.Top
        header.Height = 56
        header.BackColor = C_PANEL
        f.Controls.Add(header)
        add_label(header, u"⬛ CAD → REVIT FAMILY  |  TỰ TẠO FAMILY HÀNG LOẠT",
                  16, 6, 720, 26, C_GOLD, True, 14.0)
        add_label(header, u"Mặt bằng + 4 mặt đứng • Tham số Dài/Rộng/Cao co giãn • Công thức tự động",
                  16, 32, 820, 20, C_TEXT_DIM, False, 9.0)
        badge = Label()
        badge.Text = u"⚡ %d dòng • 1 TRANSACTION / FAMILY" % len(plans)
        badge.Size = Size(280, 30)
        badge.Location = Point(cw - 12 - 280, 13)
        badge.TextAlign = ContentAlignment.MiddleCenter
        badge.BackColor = C_GOLD_DARK
        badge.ForeColor = C_INK
        set_font(badge, 9.0, True)
        header.Controls.Add(badge)
        anchor(badge, A_TR)

        # --- hàng 1: đường dẫn CAD --------------------------------------
        y1 = 66
        add_label(f, u"Đường dẫn CAD (file hoặc thư mục):", 12, y1 + 4, 216, 22,
                  C_TEXT_DIM, False, 9.0)
        bx = cw - 12 - 322
        txt_path = add_textbox(f, state["paths_text"], 232, y1, max(180, bx - 244), 26, A_TLR)
        add_button(f, u"📂 Thư mục…", bx, y1 - 1, 104, 28, DialogResult.Ignore, False, A_TR)
        add_button(f, u"📄 File CAD…", bx + 108, y1 - 1, 104, 28, DialogResult.Yes, False, A_TR)
        add_button(f, u"🔍 QUÉT", bx + 216, y1 - 1, 106, 28, DialogResult.Retry, True, A_TR)

        # --- hàng 2: thư mục xuất ---------------------------------------
        y2 = y1 + 34
        add_label(f, u"Thư mục xuất .rfa:", 12, y2 + 4, 216, 22, C_TEXT_DIM, False, 9.0)
        txt_out = add_textbox(f, state["out_dir"], 232, y2, max(180, bx - 244), 26, A_TLR)
        add_button(f, u"📁 Chọn thư mục xuất…", bx, y2 - 1, 214, 28, DialogResult.Abort, False, A_TR)

        # --- hàng 3: tuỳ chọn + nút áp dụng nhanh -----------------------
        y3 = y2 + 34
        chk_rec = add_check(f, u"Thư mục con", 12, y3, 100, state["recursive"])
        chk_grp = add_check(f, u"Gộp file cùng tên", 116, y3, 140, state["group"])
        chk_turbo = add_check(f, u"TURBO", 260, y3, 75, state["turbo"])
        chk_inst = add_check(f, u"Tham số Instance", 339, y3, 125, state["instance_params"])
        chk_back = add_check(f, u"Vẽ mặt sau/phải", 468, y3, 132, state["draw_back_right"])
        chk_load = add_check(f, u"Nạp vào project", 604, y3, 128, state["load_project"])
        anchor(add_button(f, u"⚙ Áp dụng cho dòng đang chọn", cw - 12 - 230, y3 - 2, 230, 28,
                          DialogResult.No), A_TR)

        # --- hàng 4: thanh áp dụng nhanh --------------------------------
        y4 = y3 + 32
        add_label(f, u"Áp dụng nhanh cho các dòng đang bôi chọn →", 12, y4 + 4, 250, 22,
                  C_GOLD, True, 9.0)
        cmb_cat = add_combo(f, CAT_CHOICES, 266, y4, 215, 26, bulk_cat)
        cmb_mode = add_combo(f, [BUILD_MODE_LABEL[m] for m in BUILD_MODES], 486, y4, 300, 26, bulk_mode)
        add_label(f, u"Cao (mm):", 792, y4 + 4, 62, 22, C_TEXT_DIM, False, 9.0)
        txt_bulk_h = add_textbox(f, u"", 856, y4, 80, 26)

        # --- lưới dữ liệu ------------------------------------------------
        gy = y4 + 36
        gh = max(180, ch - gy - 104)
        grid = build_plan_grid(12, gy, cw - 24, gh)
        fill_grid(grid, plans)
        f.Controls.Add(grid)
        anchor(grid, AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom)

        add_label(f, status_msg, 12, gy + gh + 6, cw - 24, 20, C_GOLD, True, 9.0, A_BLR)
        add_label(f, u"Mẹo: sửa trực tiếp Tên family / Dài / Rộng / Cao ngay trên lưới. "
                     u"Bỏ tick cột ✔ để KHÔNG tạo dòng đó.",
                  12, gy + gh + 26, cw - 24, 20, C_TEXT_DIM, False, 8.5, A_BLR)

        by = ch - 46
        btn_cancel = add_button(f, u"✖ Đóng", cw - 12 - 110, by, 110, 32,
                                DialogResult.Cancel, False, A_BR)
        f.CancelButton = btn_cancel
        btn_run = add_button(f, u"▶ TẠO FAMILY HÀNG LOẠT", cw - 12 - 110 - 12 - 260, by - 1,
                             260, 34, DialogResult.OK, True, A_BR)
        f.AcceptButton = btn_run

        dr = f.ShowDialog()

        # ---- đọc lại toàn bộ trạng thái NGAY sau khi cửa sổ đóng --------
        state["paths_text"] = txt_path.Text.strip()
        state["out_dir"] = txt_out.Text.strip()
        state["recursive"] = bool(chk_rec.Checked)
        state["group"] = bool(chk_grp.Checked)
        state["turbo"] = bool(chk_turbo.Checked)
        state["instance_params"] = bool(chk_inst.Checked)
        state["draw_back_right"] = bool(chk_back.Checked)
        state["load_project"] = bool(chk_load.Checked)
        bulk_cat = cmb_cat.SelectedIndex if cmb_cat.SelectedIndex >= 0 else 0
        bulk_mode = cmb_mode.SelectedIndex if cmb_mode.SelectedIndex >= 0 else 0
        bulk_h = parse_number(txt_bulk_h.Text, None)
        sel_rows = sorted(set(c.RowIndex for c in grid.SelectedCells))
        read_grid(grid, plans, used_names)
        ctx["turbo"] = state["turbo"]
        ctx["instance_params"] = state["instance_params"]
        ctx["draw_back_right"] = state["draw_back_right"]

        if dr == DialogResult.Ignore:          # chọn thư mục CAD
            try:
                fbd = FolderBrowserDialog()
                fbd.Description = u"Chọn thư mục chứa các file CAD (.dwg/.dxf)"
                if fbd.ShowDialog() == DialogResult.OK and fbd.SelectedPath:
                    state["paths_text"] = fbd.SelectedPath
                    status_msg = u"Đã chọn thư mục: %s — bấm \"🔍 QUÉT\" để nạp danh sách." % fbd.SelectedPath
            except Exception as ex:
                status_msg = u"⚠ Không mở được hộp thoại chọn thư mục: %s" % ex
            continue

        if dr == DialogResult.Yes:             # chọn nhiều file CAD
            try:
                ofd = OpenFileDialog()
                ofd.Multiselect = True
                ofd.Title = u"Chọn 1 hoặc nhiều file CAD"
                ofd.Filter = u"File CAD (*.dwg;*.dxf)|*.dwg;*.dxf|Tất cả (*.*)|*.*"
                if ofd.ShowDialog() == DialogResult.OK:
                    names = list(ofd.FileNames)
                    if names:
                        state["paths_text"] = u";".join(names)
                        status_msg = u"Đã chọn %d file — bấm \"🔍 QUÉT\" để nạp danh sách." % len(names)
            except Exception as ex:
                status_msg = u"⚠ Không mở được hộp thoại chọn file: %s" % ex
            continue

        if dr == DialogResult.Abort:           # chọn thư mục xuất
            try:
                fbd = FolderBrowserDialog()
                fbd.Description = u"Chọn thư mục để xuất file .rfa"
                if fbd.ShowDialog() == DialogResult.OK and fbd.SelectedPath:
                    state["out_dir"] = fbd.SelectedPath
                    status_msg = u"Thư mục xuất: %s" % fbd.SelectedPath
            except Exception as ex:
                status_msg = u"⚠ Không mở được hộp thoại chọn thư mục: %s" % ex
            continue

        if dr == DialogResult.Retry:           # QUÉT
            t_scan = time.time()
            files = list_cad_files(state["paths_text"], state["recursive"])
            if not files:
                status_msg = u"⚠ Không tìm thấy file .dwg/.dxf nào ở đường dẫn đã nhập."
                continue
            new_plans = group_files_into_plans(files, state["group"])
            names = set()
            for p in new_plans:
                p.family_name = unique_name(p.family_name, names)
                scan_plan(p, ctx["read_func"])
                p.template_path = pick_template(p.category, ctx["template_root"], ctx.get("template_map"))
                if not p.template_path:
                    p.status = u"✖ Không thấy template .rft"
            state["plans"] = new_plans
            if not state["out_dir"]:
                state["out_dir"] = default_output_dir(files)
            ms = int((time.time() - t_scan) * 1000)
            ok = sum(1 for p in new_plans if p.status.startswith(u"✔"))
            status_msg = (u"Đã quét %d file → %d family, %d dòng sẵn sàng, mất %d ms "
                          u"(%.1f file/giây)." % (len(files), len(new_plans), ok, ms,
                                                  (len(files) / (ms / 1000.0)) if ms > 0 else 0.0))
            continue

        if dr == DialogResult.No:              # áp dụng nhanh
            if not sel_rows:
                status_msg = u"⚠ Hãy bôi chọn ít nhất 1 dòng trong bảng trước khi áp dụng."
                continue
            cat = CAT_CODES[bulk_cat] if 0 <= bulk_cat < len(CAT_CODES) else None
            mode = BUILD_MODES[bulk_mode] if 0 <= bulk_mode < len(BUILD_MODES) else MODE_HYBRID
            n = 0
            for i in sel_rows:
                if 0 <= i < len(plans):
                    p = plans[i]
                    if cat:
                        p.category = cat
                        p.template_path = pick_template(cat, ctx["template_root"], ctx.get("template_map"))
                    p.mode = mode
                    if bulk_h:
                        p.height = bulk_h
                    n += 1
            status_msg = u"Đã áp dụng cho %d dòng." % n
            continue

        if dr == DialogResult.OK:              # CHẠY
            todo = [p for p in plans if p.enabled and not p.status.startswith(u"✖")]
            if not todo:
                status_msg = u"⚠ Chưa có dòng nào hợp lệ để tạo. Hãy bấm \"🔍 QUÉT\" trước."
                continue
            if not state["out_dir"]:
                state["out_dir"] = default_output_dir([p.src_paths[0] for p in todo])
            ctx["out_dir"] = state["out_dir"]
            confirm = MessageBox.Show(
                u"Sẽ tạo %d file family (.rfa) vào thư mục:\n%s\n\nTiếp tục?"
                % (len(todo), state["out_dir"]),
                u"Xác nhận tạo family", MessageBoxButtons.YesNo, MessageBoxIcon.Question)
            if confirm != DialogResult.Yes:
                status_msg = u"Đã huỷ thao tác tạo family."
                continue
            res = run_batch(todo, ctx)
            result.update(res)
            result["status"] = "Done"
            rate = res["families_per_sec"]
            MessageBox.Show(
                u"Hoàn tất!\n\n"
                u"• Tạo thành công : %d family\n"
                u"• Lỗi            : %d\n"
                u"• Thời gian dựng : %d ms\n"
                u"• Tốc độ thực đo : %.2f family/giây\n"
                u"• Thư mục xuất   : %s%s"
                % (res["created"], res["failed"], res["build_ms"], rate, state["out_dir"],
                   (u"\n• Đã nạp vào project: %d family" % res["loaded"]) if res["loaded"] else u""),
                u"CAD → REVIT FAMILY", MessageBoxButtons.OK, MessageBoxIcon.Information)
            status_msg = (u"✔ Xong: %d thành công / %d lỗi — %.2f family/giây."
                          % (res["created"], res["failed"], rate))
            if res["failed"] == 0:
                break
            continue

        if dr == DialogResult.Cancel or dr == NONE_RESULT:
            break

    return result


# ------------------------------------------------------------------------
# 10. CHẠY HÀNG LOẠT & ĐO TỐC ĐỘ THẬT
# ------------------------------------------------------------------------
def run_batch(plans, ctx):
    """Dựng lần lượt từng family. Mỗi family = 1 tài liệu + 1 Transaction
    duy nhất (Revit chỉ regenerate 1 lần cho cả family thay vì mỗi nét 1
    lần) — đây là điểm quyết định tốc độ."""
    t0 = time.time()
    created, failed, files = 0, 0, []
    for p in plans:
        t_one = time.time()
        if not p.template_path:
            p.template_path = pick_template(p.category, ctx["template_root"], ctx.get("template_map"))
        try:
            path, ok = build_family(p, ctx)
        except Exception as ex:
            p.warnings.append(u"Lỗi không lường trước: %s" % ex)
            p.warnings.append(traceback.format_exc())
            p.status = u"✖ Lỗi"
            path, ok = None, False
        p.elapsed_ms = int((time.time() - t_one) * 1000)
        if ok and path:
            created += 1
            files.append(path)
        else:
            failed += 1
    build_ms = int((time.time() - t0) * 1000)

    loaded = 0
    if ctx.get("load_project") and files and ctx.get("project_doc") is not None:
        loaded = load_families_into_project(ctx["project_doc"], files, ctx.setdefault("warnings", []))

    return {
        "created": created,
        "failed": failed,
        "files": files,
        "build_ms": build_ms,
        "loaded": loaded,
        "families_per_sec": round(created / (build_ms / 1000.0), 2) if build_ms > 0 and created else 0.0,
    }


def plans_from_cad_links(elements, project_doc, cache, warnings):
    """Tạo FamilyPlan từ các CAD Link/Import đang được chọn sẵn trong Revit
    (IN[0]) — không cần đường dẫn file, lấy thẳng nét đang hiển thị."""
    plans = []
    for e in elements or []:
        try:
            if not isinstance(e, ImportInstance):
                continue
        except Exception:
            continue
        name = u"CAD_%s" % e.Id
        try:
            sym = project_doc.GetElement(e.GetTypeId())
            if sym is not None and sym.Name:
                name = os.path.splitext(u"%s" % sym.Name)[0]
        except Exception:
            pass
        try:
            ents = entities_from_import_instance(project_doc, e)
        except Exception as ex:
            warnings.append(u"Không bóc được hình học từ CAD Link Id=%s: %s" % (e.Id, ex))
            continue
        if not ents:
            warnings.append(u"CAD Link Id=%s không có nét nào đọc được." % e.Id)
            continue
        local = []
        ents = sanity_fix_scale(ents, local)
        pseudo = u"<CAD LINK> %s.dwg" % name
        cache[pseudo] = CadDoc(pseudo, ents, 1.0, u"mm (từ CAD Link)", True, local, u"CAD-LINK")
        plans.append(FamilyPlan(name, [FamilySource(pseudo, None)]))
    return plans


def make_scratch_doc(ctx, warnings):
    """Tạo 1 family "nháp" dùng chung để import & bóc hình học DWG. Chỉ tạo
    khi thật sự cần (có file .dwg), và đóng lại ở cuối phiên."""
    tpl = pick_template("GenericModel", ctx["template_root"], ctx.get("template_map"))
    if not tpl:
        warnings.append(u"Không tìm thấy template Generic Model để quét DWG. "
                        u"Hãy khai báo thư mục Family Template ở IN[4].")
        return None, None
    try:
        sdoc = ctx["app"].NewFamilyDocument(tpl)
        views = get_family_views(sdoc)
        return sdoc, (views.get("PLAN") or views.get("3D"))
    except Exception as ex:
        warnings.append(u"Không tạo được tài liệu nháp để quét DWG: %s" % ex)
        return None, None


def make_reader(cache, scratch_doc, scratch_view, warnings):
    """read_func tổng: ưu tiên cache (CAD Link / DWG đã quét), .dxf đọc
    thẳng bằng Python, .dwg nhờ Revit import."""
    revit_reader = make_revit_dwg_reader(scratch_doc, scratch_view, warnings)

    def _read(path):
        if path in cache:
            return cache[path], None
        ext = os.path.splitext(path)[1].lower()
        if ext == ".dxf":
            try:
                return read_dxf(path)
            except Exception as ex:
                return None, u"Lỗi đọc DXF: %s" % ex
        if not REVIT_API:
            return None, u"Cần chạy trong Revit/Dynamo để đọc file DWG."
        return revit_reader(path)

    return _read


def run(elements, path_text, out_dir, template_dir, load_project, show_gui):
    """Điều phối toàn bộ: chuẩn bị môi trường → quét → GUI → dựng hàng loạt."""
    t_all = time.time()
    warnings = []

    if not REVIT_API or app is None:
        return {
            "Status": "Error", "Created": 0, "Failed": 0, "Files": [], "Report": [],
            "Warnings": [u"Không thấy Revit API (%s). Script này phải chạy trong "
                         u"node Python Script của Dynamo, engine CPython3."
                         % (REVIT_IMPORT_ERROR or u"app = None")],
            "BuildMs": 0, "FamiliesPerSec": 0.0, "ElapsedMs": 0,
        }

    template_root = discover_template_root(template_dir)
    if not template_root:
        warnings.append(u"Không tự dò được thư mục Family Template (.rft). "
                        u"Hãy nối 1 String vào IN[4] trỏ tới thư mục chứa .rft.")

    ctx = {
        "app": app,
        "project_doc": doc,
        "template_root": template_root,
        "template_map": None,
        "out_dir": out_dir or u"",
        "turbo": False,
        "instance_params": True,
        "draw_back_right": True,
        "fit_to_params": True,
        "formula_params": True,
        "load_project": bool(load_project),
        "type_name": u"Chuẩn",
        "warnings": warnings,
    }

    cache = {}
    link_plans = plans_from_cad_links(elements, doc, cache, warnings)

    files = list_cad_files(path_text)
    # Tài liệu "nháp" chỉ cần cho file .dwg (Python không đọc được DWG). Khi
    # mở GUI thì vẫn tạo sẵn, vì lát nữa bạn có thể chọn thêm thư mục DWG
    # ngay trên giao diện — tạo trước 1 lần rẻ hơn tạo lại mỗi lần quét.
    need_scratch = show_gui or any(p.lower().endswith(".dwg") for p in files)
    scratch_doc, scratch_view = (None, None)
    if need_scratch:
        scratch_doc, scratch_view = make_scratch_doc(ctx, warnings)
    read_func = make_reader(cache, scratch_doc, scratch_view, warnings)
    ctx["read_func"] = read_func

    try:
        plans = list(link_plans)
        if files:
            plans.extend(group_files_into_plans(files, True))
        names = set()
        for p in plans:
            p.family_name = unique_name(p.family_name, names)
            scan_plan(p, read_func)
            p.template_path = pick_template(p.category, template_root, ctx.get("template_map"))
            if not p.template_path:
                p.status = u"✖ Không thấy template .rft"

        if not ctx["out_dir"]:
            src = [s.path for p in plans for s in p.sources if os.path.isfile(s.path)]
            ctx["out_dir"] = default_output_dir(src, out_dir)

        state = {
            "paths_text": path_text or u"",
            "out_dir": ctx["out_dir"],
            "plans": plans,
            "recursive": False,
            "group": True,
            "turbo": False,
            "instance_params": True,
            "draw_back_right": True,
            "load_project": bool(load_project),
        }

        if show_gui and GUI_AVAILABLE:
            res = run_gui(state, ctx)
            status = "Done" if res.get("status") == "Done" else "Cancelled"
            plans = state["plans"]
        else:
            if not GUI_AVAILABLE and show_gui:
                warnings.append(u"Không mở được GUI (%s) — chạy thẳng không giao diện."
                                % GUI_IMPORT_ERROR)
            todo = [p for p in plans if p.enabled and not p.status.startswith(u"✖")]
            if not todo:
                return {
                    "Status": "NoInput", "Created": 0, "Failed": 0, "Files": [],
                    "Report": [], "Warnings": warnings + [u"Không có file CAD hợp lệ nào."],
                    "BuildMs": 0, "FamiliesPerSec": 0.0,
                    "ElapsedMs": int((time.time() - t_all) * 1000),
                }
            res = run_batch(todo, ctx)
            res["status"] = "Done"
            status = "Done"
    finally:
        try:
            if scratch_doc is not None:
                scratch_doc.Close(False)
        except Exception:
            pass

    report = [[u"Family", u"Danh mục", u"Dài", u"Rộng", u"Cao", u"Hình chiếu",
               u"Trạng thái", u"ms", u"File .rfa"]]
    for p in plans:
        report.append([p.family_name, CAT_SHORT.get(p.category, p.category),
                       fmt_mm(p.length), fmt_mm(p.width), fmt_mm(p.height),
                       p.views_display(), p.status, p.elapsed_ms, p.out_path])
        for w in p.warnings:
            warnings.append(u"[%s] %s" % (p.family_name, w))

    return {
        "Status": status,
        "Created": res.get("created", 0),
        "Failed": res.get("failed", 0),
        "Files": res.get("files", []),
        "Loaded": res.get("loaded", 0),
        "Report": report,
        "Warnings": warnings,
        "BuildMs": res.get("build_ms", 0),
        "FamiliesPerSec": res.get("families_per_sec", 0.0),
        "ElapsedMs": int((time.time() - t_all) * 1000),
    }


# ------------------------------------------------------------------------
# 11. DYNAMO IN / OUT
# ------------------------------------------------------------------------
def _get_in(index, default=None):
    try:
        return IN[index]
    except Exception:
        return default


def _as_element_list(raw):
    """Chuẩn hoá IN[0] về list phần tử Revit thật. KHÔNG dùng
    isinstance(x, list): tuỳ phiên bản, "Select Model Elements" trả về 1
    danh sách .NET chứ không phải list Python, isinstance sẽ sai và bọc
    nhầm CẢ danh sách thành 1 phần tử."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        items = list(raw)
    else:
        try:
            items = list(raw)
        except TypeError:
            items = [raw]
    out = []
    for e in items:
        if e is None:
            continue
        out.append(e.InternalElement if hasattr(e, "InternalElement") else e)
    return out


try:
    _elements = _as_element_list(_get_in(0, []))

    _run_guard = _get_in(1, True)
    if _run_guard is None:
        _run_guard = True

    if not _run_guard:
        OUT = {
            "Status": "Idle", "Created": 0, "Failed": 0, "Files": [], "Report": [],
            "Warnings": [u"IN[1] = False — script tạm dừng, chưa xử lý gì. Đặt True để chạy."],
            "BuildMs": 0, "FamiliesPerSec": 0.0, "ElapsedMs": 0,
        }
    else:
        _path_text = _get_in(2, u"") or u""
        _out_dir = _get_in(3, u"") or u""
        _tpl_dir = _get_in(4, u"") or u""
        _load_prj = _get_in(5, False)
        _headless = _get_in(6, False)
        OUT = run(_elements, u"%s" % _path_text, u"%s" % _out_dir, u"%s" % _tpl_dir,
                  bool(_load_prj), not bool(_headless))
except Exception as _ex:
    OUT = {
        "Status": "Error", "Created": 0, "Failed": 0, "Files": [], "Report": [],
        "Warnings": [str(_ex), traceback.format_exc()],
        "BuildMs": 0, "FamiliesPerSec": 0.0, "ElapsedMs": 0,
    }
