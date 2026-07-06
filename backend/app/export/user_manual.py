"""
User Operations Manual Excel Generator
Generates a comprehensive user manual for the APS system.
"""
import io
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, GradientFill
)
from openpyxl.utils import get_column_letter


# ── Color palette ─────────────────────────────────────────────────────────────
C_HEADER_BG   = "1F4E79"   # dark blue
C_HEADER_FG   = "FFFFFF"
C_SECTION_BG  = "2E75B6"   # medium blue
C_SECTION_FG  = "FFFFFF"
C_SUB_BG      = "BDD7EE"   # light blue
C_SUB_FG      = "1F4E79"
C_ROW_ODD     = "DEEAF1"
C_ROW_EVEN    = "FFFFFF"
C_TITLE_BG    = "0070C0"
C_WARN_BG     = "FFF2CC"
C_STEP_BG     = "E2EFDA"   # light green for steps


def _thin_border():
    s = Side(style="thin", color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=s)


def _cell(ws, row, col, value, bold=False, size=10, bg=None, fg="000000",
          wrap=True, align="left", valign="top", border=True, italic=False, num_format=None):
    c = ws.cell(row=row, column=col, value=value)
    c.font = Font(bold=bold, size=size, color=fg, italic=italic)
    c.alignment = Alignment(horizontal=align, vertical=valign, wrap_text=wrap)
    if bg:
        c.fill = PatternFill("solid", fgColor=bg)
    if border:
        c.border = _thin_border()
    if num_format:
        c.number_format = num_format
    return c


def _merge_header(ws, row, col_start, col_end, text, bg=C_HEADER_BG, fg=C_HEADER_FG,
                  size=11, bold=True):
    ws.merge_cells(start_row=row, start_column=col_start,
                   end_row=row, end_column=col_end)
    c = ws.cell(row=row, column=col_start, value=text)
    c.font = Font(bold=bold, size=size, color=fg)
    c.fill = PatternFill("solid", fgColor=bg)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = _thin_border()
    return c


def _section(ws, row, text):
    """Write a full-width section header across columns 1-5."""
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(bold=True, size=11, color=C_SECTION_FG)
    c.fill = PatternFill("solid", fgColor=C_SECTION_BG)
    c.alignment = Alignment(horizontal="left", vertical="center")
    c.border = _thin_border()
    ws.row_dimensions[row].height = 22
    return row + 1


def _row(ws, row, cells, odd=True):
    bg = C_ROW_ODD if odd else C_ROW_EVEN
    for col, (val, width_hint) in enumerate(cells, 1):
        _cell(ws, row, col, val, bg=bg)
    return row + 1


def _set_col_widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 1 – Cover / 封面
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_cover(wb):
    ws = wb.active
    ws.title = "封面"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 20

    for r in range(1, 5):
        ws.row_dimensions[r].height = 18

    ws.row_dimensions[5].height = 60
    ws.merge_cells("B5:C5")
    c = ws.cell(row=5, column=2, value="APS 高级计划与排程系统")
    c.font = Font(bold=True, size=28, color=C_HEADER_BG)
    c.alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[6].height = 30
    ws.merge_cells("B6:C6")
    c = ws.cell(row=6, column=2, value="用户操作手册  User Operations Manual")
    c.font = Font(size=16, color=C_SECTION_BG, italic=True)
    c.alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[7].height = 20
    ws.row_dimensions[8].height = 20

    info = [
        ("版本", "V1.0"),
        ("系统端口", "后端 9000 / 前端 7000"),
        ("数据库", "MySQL 8.0  |  aps_db_1"),
        ("默认管理员", "admin / admin123"),
        ("默认计划员", "planner / planner123"),
        ("文档日期", "2026-07"),
    ]
    for i, (k, v) in enumerate(info, 9):
        ws.row_dimensions[i].height = 20
        ws.cell(row=i, column=2, value=k).font = Font(bold=True, size=11, color=C_HEADER_BG)
        ws.cell(row=i, column=2).alignment = Alignment(horizontal="right")
        ws.cell(row=i, column=3, value=v).font = Font(size=11)

    # table of contents
    r = 17
    ws.row_dimensions[r].height = 24
    ws.merge_cells(f"B{r}:C{r}")
    c = ws.cell(row=r, column=2, value="目  录")
    c.font = Font(bold=True, size=13, color=C_HEADER_FG)
    c.fill = PatternFill("solid", fgColor=C_HEADER_BG)
    c.alignment = Alignment(horizontal="center", vertical="center")

    toc = [
        ("Sheet 2", "系统概览与架构"),
        ("Sheet 3", "登录与权限管理"),
        ("Sheet 4", "BOM 物料清单管理"),
        ("Sheet 5", "客户订单管理"),
        ("Sheet 6", "库存管理"),
        ("Sheet 7", "生产线与工作日历"),
        ("Sheet 8", "MRP 需求计划"),
        ("Sheet 9", "RCCP 粗产能规划"),
        ("Sheet 10", "排程算法与结果"),
        ("Sheet 11", "KPI 报表与分析"),
        ("Sheet 12", "算法原理说明"),
    ]
    for i, (sheet, title) in enumerate(toc, r + 1):
        ws.row_dimensions[i].height = 18
        c1 = ws.cell(row=i, column=2, value=sheet)
        c1.font = Font(bold=True, color=C_SECTION_BG, size=10)
        c1.alignment = Alignment(horizontal="right")
        c2 = ws.cell(row=i, column=3, value=title)
        c2.font = Font(size=10)


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 2 – 系统概览
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_overview(wb):
    ws = wb.create_sheet("系统概览")
    _set_col_widths(ws, [4, 22, 40, 22, 18])
    ws.row_dimensions[1].height = 30

    _merge_header(ws, 1, 1, 5, "系统概览与整体架构", size=14)

    modules = [
        ("模块", "功能描述", "主要操作", "角色权限"),
        ("BOM管理", "维护成品/半成品/原料的多层物料清单，支持爆炸计算",
         "新增产品 → 设置BOM层级 → 查看树状结构", "admin / planner"),
        ("订单管理", "导入/手工录入客户订单，跟踪订单状态",
         "导入Excel / 手工新增 → 查看状态 → 导出", "admin / planner"),
        ("库存管理", "维护实际库存、在途库存、WIP(在制品)",
         "录入或Excel导入库存 → 查看库存健康状态", "admin / planner"),
        ("生产线管理", "配置产线参数、排产产品、换线时间、工作日历",
         "新增产线 → 绑定产品节拍 → 生成日历", "admin"),
        ("MRP需求计划", "基于BOM爆炸计算净需求，含安全库存扣减",
         '点击[计算净需求] → 查看独立/依赖需求列表', "planner"),
        ("RCCP粗产能", "按周/月汇总产能需求与可用产能，支持手动调整",
         "选择周期 → 计算RCCP → 调整超负荷产线", "planner"),
        ("排程算法", "6种算法一键排程，支持比较与甘特图",
         "选算法 → 运行 → 对比KPI → 批准排程", "planner"),
        ("KPI报表", "仪表板、库存健康、订单履行、产能利用率、WIP分析",
         "选报表类型 → 查看图表 → 导出Excel", "admin / planner"),
        ("算法演示", "逐步演示算法决策过程，支持自动播放",
         "选择算法 → 逐步/自动播放 → 查看每步状态", "planner"),
    ]

    r = 2
    _merge_header(ws, r, 1, 5, "核心功能模块一览", bg=C_SECTION_BG)
    r += 1
    headers = ["序号", "模块名称", "功能描述", "主要操作步骤", "角色权限"]
    for col, h in enumerate(headers, 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    r += 1
    for i, row in enumerate(modules[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, i, bg=bg, align="center")
        for col, val in enumerate(row, 2):
            _cell(ws, r, col, val, bg=bg)
        ws.row_dimensions[r].height = 36
        r += 1

    r += 1
    _merge_header(ws, r, 1, 5, "技术架构", bg=C_SECTION_BG)
    r += 1
    arch = [
        ("层次", "技术栈", "说明"),
        ("前端", "Vue 3 + Vite + Element Plus + Pinia", "端口 7000，SPA 单页应用"),
        ("后端", "Python 3.11 + FastAPI + SQLAlchemy", "端口 9000，RESTful API"),
        ("数据库", "MySQL 8.0", "库名 aps_db_1"),
        ("认证", "JWT (python-jose + passlib/bcrypt)", "Token 有效期 24 小时"),
        ("算法库", "PuLP(MIP) + NumPy + SciPy", "内置6种排程算法"),
        ("容器化", "Docker Compose", "一键启动 mysql/backend/frontend"),
    ]
    for col, h in enumerate(["层次", "技术栈", "说明"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
    r += 1
    for i, row in enumerate(arch[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        for col, val in enumerate(row, 1):
            _cell(ws, r, col, val, bg=bg)
        if len(row) == 3:
            ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
        r += 1


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 3 – 登录与权限
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_auth(wb):
    ws = wb.create_sheet("登录与权限")
    _set_col_widths(ws, [4, 20, 30, 30, 20])
    _merge_header(ws, 1, 1, 5, "登录与权限管理", size=14)

    r = 2
    r = _section(ws, r, "▶ 1. 登录步骤")
    steps = [
        ("步骤", "操作", "说明"),
        ("1", "打开浏览器，访问 http://localhost:7000", "Chrome / Edge 推荐"),
        ("2", "输入用户名和密码", "默认账号见封面页"),
        ("3", '点击[登录]按钮', "登录成功后跳转至仪表板"),
        ("4", "系统自动保存 JWT Token", "Token 存于浏览器 localStorage，24小时有效"),
        ("5", "退出：点击右上角用户名 → 退出登录", "清除本地 Token"),
    ]
    for col, h in enumerate(["序号", "操作", "详细说明"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
    r += 1
    for i, row in enumerate(steps[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, row[0], bg=bg, align="center")
        _cell(ws, r, 2, row[1], bg=bg)
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
        _cell(ws, r, 3, row[2], bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 2. 角色权限说明")
    roles = [
        ("角色", "可访问模块", "限制"),
        ("admin (管理员)", "所有模块，含用户管理", "无限制"),
        ("planner (计划员)", "BOM/订单/库存/规划/排程/报表", "不可管理用户"),
    ]
    for col, h in enumerate(["角色", "可访问模块", "限制"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    r += 1
    for i, row in enumerate(roles[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, row[0], bg=bg)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
        _cell(ws, r, 2, row[1], bg=bg)
        _cell(ws, r, 5, row[2], bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 3. 注册新用户（管理员操作）")
    steps2 = [
        "POST /api/auth/register  或在系统用户管理页面操作",
        "填写 username / email / password / role（admin 或 planner）",
        "提交后新用户即可使用指定账号密码登录",
    ]
    for i, s in enumerate(steps2, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, i, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 4 – BOM管理
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_bom(wb):
    ws = wb.create_sheet("BOM管理")
    _set_col_widths(ws, [4, 22, 14, 14, 40])
    _merge_header(ws, 1, 1, 5, "BOM 物料清单管理", size=14)

    r = 2
    r = _section(ws, r, "▶ 产品类型说明")
    types = [
        ("类型代码", "中文名", "说明"),
        ("FG", "成品 Finished Goods", "直接面向客户订单的最终产品"),
        ("SFG", "半成品 Semi-Finished Goods", "生产过程中的中间品，有BOM子项"),
        ("RM", "原料 Raw Material", "最底层物料，无BOM子项"),
    ]
    for col, h in enumerate(["类型代码", "中文名", "说明"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
    r += 1
    for i, row in enumerate(types[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        for col, val in enumerate(row, 1):
            _cell(ws, r, col, val, bg=bg)
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 新增产品操作步骤")
    steps = [
        (1, "菜单 → BOM管理 → 产品列表 → 点击「新增产品」"),
        (2, "填写：产品编码（唯一）、产品名称、类型(FG/SFG/RM)、单位"),
        (3, "填写提前期(天) Lead Time Days：从开始生产到完工所需天数"),
        (4, "填写安全库存 Safety Stock：触发补货的最低库存量"),
        (5, "点击「保存」"),
    ]
    for i, (no, s) in enumerate(steps, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 新增BOM子项操作步骤")
    steps2 = [
        (1, "在产品列表中，选择一个 FG 或 SFG 产品 → 点击「BOM」"),
        (2, "点击「添加子项」"),
        (3, "选择子产品（下拉搜索产品编码/名称）"),
        (4, "填写用量 Quantity：生产1个父产品需要多少个子产品"),
        (5, "填写报废率 Scrap Rate（%）：如5表示5%报废，系统自动放大需求"),
        (6, "点击「保存」，可重复添加多个子项，形成多层BOM"),
    ]
    for i, (no, s) in enumerate(steps2, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 字段说明")
    fields = [
        ("字段", "含义", "示例"),
        ("product_code", "产品唯一编码", "FG-001"),
        ("product_name", "产品名称", "成品A"),
        ("product_type", "类型：FG/SFG/RM", "FG"),
        ("unit", "计量单位", "PCS / KG"),
        ("lead_time_days", "提前期（天）", "5"),
        ("safety_stock", "安全库存量", "100"),
        ("quantity (BOM子项)", "每单位父产品所需子产品数量", "2.0"),
        ("scrap_rate (BOM子项)", "报废率（%）", "5.0"),
    ]
    for col, h in enumerate(["字段名", "含义", "示例"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    r += 1
    for i, row in enumerate(fields[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        for col, val in enumerate(row, 1):
            _cell(ws, r, col, val, bg=bg)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
        r += 1


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 5 – 订单管理
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_orders(wb):
    ws = wb.create_sheet("订单管理")
    _set_col_widths(ws, [4, 22, 14, 14, 40])
    _merge_header(ws, 1, 1, 5, "客户订单管理", size=14)

    r = 2
    r = _section(ws, r, "▶ 手工录入订单")
    steps = [
        (1, "菜单 → 订单管理 → 点击「新增订单」"),
        (2, "填写订单号（唯一）、选择产品（从BOM产品中选FG类型）"),
        (3, "填写数量、交货日期（due_date）、优先级（1最高-10最低）、客户名称"),
        (4, "状态默认为 open（开放），点击「保存」"),
    ]
    for i, (no, s) in enumerate(steps, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ Excel批量导入订单")
    steps2 = [
        (1, "准备Excel文件（.xlsx），表头必须包含以下列："),
        (2, "order_no | product_code | quantity | due_date | priority | customer_name"),
        (3, "due_date 格式：YYYY-MM-DD（如 2026-08-15）"),
        (4, "priority 范围：1（最高优先）到 10（最低优先）"),
        (5, "菜单 → 订单管理 → 点击「导入Excel」→ 选择文件 → 确认导入"),
        (6, "系统自动匹配 product_code 到产品ID，重复 order_no 会报错提示"),
    ]
    for i, (no, s) in enumerate(steps2, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 订单状态说明")
    statuses = [
        ("状态", "含义", "操作"),
        ("open", "开放，待排程", "可编辑、可排程"),
        ("in_progress", "排程中/生产中", "已纳入排程计划"),
        ("completed", "已完成", "只读"),
        ("cancelled", "已取消", "不参与MRP/排程计算"),
    ]
    for col, h in enumerate(["状态", "含义", "操作说明"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    r += 1
    for i, row in enumerate(statuses[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        for col, val in enumerate(row, 1):
            _cell(ws, r, col, val, bg=bg)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
        r += 1

    r += 1
    r = _section(ws, r, "▶ Excel导入模板示例")
    header = ["order_no", "product_code", "quantity", "due_date", "priority", "customer_name"]
    example = [
        ["ORD-2026-001", "FG-001", 500, "2026-08-01", 1, "客户A"],
        ["ORD-2026-002", "FG-002", 300, "2026-08-15", 2, "客户B"],
        ["ORD-2026-003", "FG-001", 200, "2026-09-01", 3, "客户C"],
    ]
    for col, h in enumerate(header, 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=6)
    r += 1
    for i, row in enumerate(example, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        for col, val in enumerate(row, 1):
            _cell(ws, r, col, val, bg=bg)
        r += 1


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 6 – 库存管理
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_inventory(wb):
    ws = wb.create_sheet("库存管理")
    _set_col_widths(ws, [4, 22, 16, 16, 36])
    _merge_header(ws, 1, 1, 5, "库存管理", size=14)

    r = 2
    r = _section(ws, r, "▶ 库存字段说明")
    fields = [
        ("字段", "中文名", "说明"),
        ("actual_stock", "实际库存", "当前仓库实物数量"),
        ("in_transit", "在途库存", "已下采购单但未到货的数量"),
        ("wip", "在制品 WIP", "已投入生产但未完工的数量"),
        ("last_updated", "最后更新时间", "系统自动记录"),
    ]
    for col, h in enumerate(["字段", "中文名", "说明"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
    r += 1
    for i, row in enumerate(fields[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        for col, val in enumerate(row, 1):
            _cell(ws, r, col, val, bg=bg)
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
        r += 1

    r += 1
    r = _section(ws, r, "▶ MRP净需求计算公式")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    formula_cell = ws.cell(row=r, column=1,
        value="净需求 = max(0, 毛需求 + 安全库存 - 实际库存 - 在途库存 - 在制品WIP)")
    formula_cell.font = Font(bold=True, size=12, color="C00000")
    formula_cell.fill = PatternFill("solid", fgColor=C_WARN_BG)
    formula_cell.alignment = Alignment(horizontal="center", vertical="center")
    formula_cell.border = _thin_border()
    ws.row_dimensions[r].height = 28
    r += 1

    r += 1
    r = _section(ws, r, "▶ 手工录入库存")
    steps = [
        (1, "菜单 → 库存管理 → 选择产品 → 点击「更新库存」"),
        (2, "填写 actual_stock（实际库存）"),
        (3, "填写 in_transit（在途）/ wip（在制品），没有则填0"),
        (4, "点击「保存」，系统记录更新时间"),
    ]
    for i, (no, s) in enumerate(steps, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ Excel批量导入库存")
    steps2 = [
        (1, "准备Excel，表头：product_code | actual_stock | in_transit | wip"),
        (2, "菜单 → 库存管理 → 「导入Excel」→ 选择文件 → 确认"),
        (3, "重复导入同一产品会覆盖更新"),
    ]
    for i, (no, s) in enumerate(steps2, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 库存健康状态说明")
    health = [
        ("状态", "判断条件", "建议操作"),
        ("OK（正常）", "实际库存 > 安全库存", "正常"),
        ("LOW（偏低）", "0 < 实际库存 ≤ 安全库存", "考虑补货或加快生产"),
        ("STOCKOUT（缺货）", "实际库存 = 0", "紧急补货或调整交期"),
    ]
    for col, h in enumerate(["状态", "判断条件", "建议操作"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    r += 1
    for i, row in enumerate(health[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        for col, val in enumerate(row, 1):
            _cell(ws, r, col, val, bg=bg)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
        r += 1


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 7 – 生产线与日历
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_production(wb):
    ws = wb.create_sheet("生产线与日历")
    _set_col_widths(ws, [4, 24, 16, 16, 36])
    _merge_header(ws, 1, 1, 5, "生产线管理与工作日历", size=14)

    r = 2
    r = _section(ws, r, "▶ 生产线参数说明")
    fields = [
        ("参数", "含义", "示例"),
        ("line_name", "产线名称", "装配线A"),
        ("capacity_per_shift", "每班产能（件/班）", "500"),
        ("shifts_per_day", "每天班次数", "2（两班制）"),
        ("workers_per_shift", "每班工人数", "10"),
        ("available_hours_per_day", "每天可用工时（自动计算）", "16小时（2班×8h）"),
    ]
    for col, h in enumerate(["参数", "含义", "示例"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
    r += 1
    for i, row in enumerate(fields[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        for col, val in enumerate(row, 1):
            _cell(ws, r, col, val, bg=bg)
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 绑定产品到产线（节拍时间）")
    steps = [
        (1, "生产线列表 → 选择产线 → 「绑定产品」"),
        (2, "选择产品，填写节拍时间 cycle_time_minutes（分钟/件）"),
        (3, "填写准备时间 setup_time_minutes（换型前的设置时间）"),
        (4, "填写单位成本 cost_per_unit（元/件）"),
        (5, "一条产线可绑定多个产品，同一产品可绑多条产线"),
    ]
    for i, (no, s) in enumerate(steps, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 工作日历管理")
    steps2 = [
        (1, "生产线 → 「管理日历」→ 输入开始日期和天数 → 点击「批量生成」"),
        (2, "系统自动将周六、周日标记为休息日（is_holiday=True，available_hours=0）"),
        (3, "可手动修改某天的 shift_count（班次）和 available_hours（可用工时）"),
        (4, "特殊假期（如法定节假日）：手动设置 is_holiday=True"),
        (5, "available_hours 决定该天能排多少工时的生产任务"),
    ]
    for i, (no, s) in enumerate(steps2, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 换线时间矩阵（Changeover Matrix）")
    steps3 = [
        (1, "生产线 → 「换线时间」→ 点击「新增换线时间」"),
        (2, "选择：产线、从产品（from_product）、到产品（to_product）"),
        (3, "填写 changeover_minutes（从生产产品A切换到产品B所需分钟数）"),
        (4, "排程时系统自动在相邻不同产品任务间插入换线时间"),
    ]
    for i, (no, s) in enumerate(steps3, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 8 – MRP需求计划
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_mrp(wb):
    ws = wb.create_sheet("MRP需求计划")
    _set_col_widths(ws, [4, 24, 16, 16, 36])
    _merge_header(ws, 1, 1, 5, "MRP 物料需求计划", size=14)

    r = 2
    r = _section(ws, r, "▶ MRP计算流程")
    steps = [
        (1, "确保已完成：产品BOM设置、库存录入、订单创建（状态=open）"),
        (2, "菜单 → MRP规划 → 点击「计算净需求」"),
        (3, "系统对所有 open 状态的客户订单执行BOM爆炸"),
        (4, "对每层BOM，按公式计算净需求（见下方公式框）"),
        (5, "独立需求（is_independent=True）：直接来自客户订单的FG需求"),
        (6, "依赖需求（is_independent=False）：BOM爆炸产生的SFG/RM需求"),
        (7, "最迟开始日期 = 交货日期 - 提前期天数（向上取整）"),
        (8, "查看结果：独立需求列表 / 依赖需求列表，可按产品/日期筛选"),
    ]
    for i, (no, s) in enumerate(steps, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        ws.row_dimensions[r].height = 20
        r += 1

    r += 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r + 1, end_column=5)
    formula_cell = ws.cell(row=r, column=1,
        value="净需求公式：net_requirement = max(0, 毛需求(gross_requirement) + 安全库存(safety_stock)"
              " - 实际库存(actual_stock) - 在途(in_transit) - 在制品(wip)\n"
              "最迟开始日期：latest_start_date = due_date - ceil(lead_time_days)")
    formula_cell.font = Font(bold=True, size=11, color="C00000")
    formula_cell.fill = PatternFill("solid", fgColor=C_WARN_BG)
    formula_cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    formula_cell.border = _thin_border()
    ws.row_dimensions[r].height = 40
    r += 2

    r += 1
    r = _section(ws, r, "▶ 净需求结果字段说明")
    fields = [
        ("字段", "含义"),
        ("product_code", "产品编码"),
        ("gross_requirement", "毛需求（订单数量 × BOM用量）"),
        ("safety_stock", "产品安全库存设置值"),
        ("actual_stock", "计算时的实际库存快照"),
        ("in_transit", "在途库存快照"),
        ("wip", "在制品快照"),
        ("net_requirement", "净需求（最终参与排程的数量）"),
        ("due_date", "对应订单的交货日期"),
        ("latest_start_date", "最迟必须开始生产的日期"),
        ("is_independent", "True=独立需求(FG)，False=依赖需求(SFG/RM)"),
    ]
    for col, h in enumerate(["字段名", "含义说明"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    r += 1
    for i, row in enumerate(fields[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, row[0], bg=bg)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, row[1], bg=bg)
        r += 1


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 9 – RCCP
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_rccp(wb):
    ws = wb.create_sheet("RCCP粗产能规划")
    _set_col_widths(ws, [4, 24, 16, 16, 36])
    _merge_header(ws, 1, 1, 5, "RCCP 粗产能规划", size=14)

    r = 2
    r = _section(ws, r, "▶ RCCP操作步骤")
    steps = [
        (1, "先完成MRP净需求计算（见上一Sheet）"),
        (2, "菜单 → RCCP规划 → 选择时间颗粒度：周（Weekly）或月（Monthly）"),
        (3, "点击「计算RCCP」"),
        (4, "系统按时间桶汇总各产线的需求工时和可用工时"),
        (5, "查看表格：绿色=正常，红色=超负荷（utilization_rate > 100%）"),
        (6, "对超负荷产线，可点击「调整」输入 adjustment_hours（正=增加，负=减少）"),
        (7, "调整后系统重新计算利用率，直至无超负荷"),
    ]
    for i, (no, s) in enumerate(steps, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ RCCP字段说明")
    fields = [
        ("字段", "含义"),
        ("period_start / period_end", "时间桶的开始/结束日期"),
        ("bucket_type", "时间颗粒度：weekly 或 monthly"),
        ("line_name", "产线名称"),
        ("required_capacity_hours", "该时间桶内需要的总工时（来自净需求×节拍时间）"),
        ("available_capacity_hours", "该时间桶内工作日历可用总工时"),
        ("adjustment_hours", "手动调整量（可正可负）"),
        ("utilization_rate", "利用率 = 需求工时 / (可用工时+调整量) × 100%"),
        ("is_overloaded", "True=超负荷（利用率>100%），False=正常"),
    ]
    for col, h in enumerate(["字段名", "含义说明"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    r += 1
    for i, row in enumerate(fields[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, row[0], bg=bg)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, row[1], bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 产能平衡建议")
    tips = [
        "1. 超负荷处理方式：加班（增加 adjustment_hours）、外协、延期交货、拆分订单",
        "2. 产能利用率建议保持在 75%~90%，留有缓冲应对紧急订单",
        "3. 调整后需重新运行排程算法以生效",
        "4. 长期超负荷建议在「生产线管理」中增加班次或扩产线",
    ]
    for i, tip in enumerate(tips, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
        _cell(ws, r, 1, tip, bg=bg)
        r += 1


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 10 – 排程算法
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_scheduling(wb):
    ws = wb.create_sheet("排程算法与结果")
    _set_col_widths(ws, [4, 22, 16, 16, 38])
    _merge_header(ws, 1, 1, 5, "排程算法使用与结果分析", size=14)

    r = 2
    r = _section(ws, r, "▶ 排程操作步骤")
    steps = [
        (1, "先完成 MRP净需求计算（必须有净需求>0的独立需求）"),
        (2, "菜单 → 排程管理 → 选择算法（见下方算法说明）"),
        (3, "点击「运行排程」，等待计算完成（MIP算法约需10秒）"),
        (4, "查看排程结果：甘特图 / 列表视图"),
        (5, "查看KPI：准时率、总成本、产能利用率、最大完工时间(Makespan)"),
        (6, "可同时运行多种算法 → 点击「算法对比」比较各算法KPI"),
        (7, "选择满意的排程方案 → 点击「批准排程」→ 该方案变为 active 状态"),
        (8, "批准后订单状态自动变为 in_progress"),
    ]
    for i, (no, s) in enumerate(steps, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1

    r += 1
    r = _section(ws, r, "▶ 6种算法简介与适用场景")
    algos = [
        ("算法名称", "全称", "适用场景", "特点"),
        ("EDD", "最早交货期优先 Earliest Due Date",
         "交期紧张、需快速出排程", "最简单，速度最快，优先处理最紧急订单"),
        ("Backtracking", "回溯+贪心 Backtracking + Greedy",
         "中等规模，需改善EDD结果", "多次随机重排取最优，平衡速度与质量"),
        ("Linear", "线性优先级评分",
         "需综合考虑优先级和工时", "按 priority×10/(加工时间/松弛时间) 评分排序"),
        ("MIP", "混合整数规划 Mixed Integer Programming",
         "小规模、追求最优解", "数学最优，但计算时间长（≤10秒时间限制）"),
        ("SimulatedAnnealing", "模拟退火",
         "中大规模，可接受较长计算时间", "随机搜索，跳出局部最优，质量较高"),
        ("AntColony", "蚁群优化 Ant Colony Optimization",
         "大规模，多产线分配优化", "信息素引导，适合并行多机分配问题"),
    ]
    headers = ["算法名称", "全称", "适用场景", "特点"]
    for col, h in enumerate(headers, 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
    r += 1
    for i, row in enumerate(algos[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, row[0], bg=bg, bold=True, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
        _cell(ws, r, 2, row[1], bg=bg)
        _cell(ws, r, 4, row[2], bg=bg)
        _cell(ws, r, 5, row[3], bg=bg)
        ws.row_dimensions[r].height = 36
        r += 1

    r += 1
    r = _section(ws, r, "▶ KPI指标说明")
    kpis = [
        ("指标", "计算方式", "目标"),
        ("准时率 on_time_rate", "准时完工订单数 / 总订单数 × 100%", "越高越好，目标≥95%"),
        ("总成本 total_cost", "Σ(数量 × 单位成本)", "越低越好"),
        ("产能利用率 utilization_rate", "总加工时间 / 总可用时间 × 100%", "建议75%~90%"),
        ("最大完工时间 makespan", "所有任务中最晚完工时间 - 最早开始时间（小时）", "越小越好"),
    ]
    for col, h in enumerate(["KPI指标", "计算方式", "优化目标"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    r += 1
    for i, row in enumerate(kpis[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, row[0], bg=bg)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
        _cell(ws, r, 2, row[1], bg=bg)
        _cell(ws, r, 5, row[2], bg=bg)
        r += 1


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 11 – KPI报表
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_reports(wb):
    ws = wb.create_sheet("KPI报表与分析")
    _set_col_widths(ws, [4, 22, 20, 20, 30])
    _merge_header(ws, 1, 1, 5, "KPI 报表与数据分析", size=14)

    r = 2
    reports = [
        ("报表名称", "内容描述", "操作路径"),
        ("仪表板 Dashboard", "系统整体概览：订单数、产品数、库存产品数、活跃排程数",
         "报表 → 仪表板"),
        ("库存健康 Inventory Health", "各产品实际库存 vs 安全库存，标注OK/LOW/STOCKOUT",
         "报表 → 库存健康"),
        ("订单履行 Order Fulfillment", "排程结果与订单交期对比，统计准时率",
         "报表 → 订单履行"),
        ("产能利用率 Capacity Utilization", "各产线各时间桶的利用率，来自RCCP结果",
         "报表 → 产能利用率"),
        ("WIP分析 WIP Analysis", "在制品库存金额和数量分析",
         "报表 → WIP分析"),
    ]
    r = _section(ws, r, "▶ 报表功能一览")
    for col, h in enumerate(["报表名称", "内容描述", "操作路径"], 1):
        _cell(ws, r, col, h, bold=True, bg=C_SUB_BG, fg=C_SUB_FG, align="center")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    r += 1
    for i, row in enumerate(reports[1:], 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, row[0], bg=bg, bold=True)
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
        _cell(ws, r, 2, row[1], bg=bg)
        _cell(ws, r, 5, row[2], bg=bg)
        ws.row_dimensions[r].height = 36
        r += 1

    r += 1
    r = _section(ws, r, "▶ Excel导出功能")
    exports = [
        (1, "排程结果甘特表：GET /api/export/schedule-gantt  → 含每个任务的开始/结束时间"),
        (2, "净需求明细：GET /api/export/net-requirements  → MRP计算结果详情"),
        (3, "RCCP产能报表：GET /api/export/rccp  → 各产线各周期利用率"),
        (4, "本操作手册：GET /api/export/user-manual  → 即本文件"),
        (5, "算法演示过程：GET /api/export/algorithm-demo?algorithm=EDD  → 逐步演示"),
    ]
    for i, (no, s) in enumerate(exports, 1):
        bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
        _cell(ws, r, 1, no, bg=bg, align="center")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        _cell(ws, r, 2, s, bg=bg)
        r += 1


# ══════════════════════════════════════════════════════════════════════════════
# Sheet 12 – 算法原理
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_algo_theory(wb):
    ws = wb.create_sheet("算法原理说明")
    _set_col_widths(ws, [4, 28, 16, 16, 32])
    _merge_header(ws, 1, 1, 5, "排程算法原理详解", size=14)

    algo_details = [
        {
            "name": "EDD — 最早交货期优先",
            "principle": "将所有工单按交货日期升序排列，越早截止的工单越先排产，依次分配到负载最小的产线。",
            "complexity": "O(n log n)",
            "pros": "实现简单、速度极快、能有效降低最大延迟",
            "cons": "忽略订单优先级和产线差异，总成本可能不最优",
            "params": "无参数",
        },
        {
            "name": "Backtracking + Greedy — 回溯贪心",
            "principle": "在EDD基础上进行多轮随机扰动（随机打乱部分工单顺序），每轮按贪心策略（分配到最早可完工的产线）执行，保留得分最高的方案。",
            "complexity": "O(iterations × n log n)",
            "pros": "比纯EDD质量更高，速度仍较快",
            "cons": "结果有随机性，多次运行结果可能不同",
            "params": "iterations=5（迭代次数）",
        },
        {
            "name": "Linear — 线性优先级评分",
            "principle": "对每个工单计算优先级得分：score = priority×10 / (processing_time / slack)，slack=剩余时间。按得分降序排列后贪心分配。",
            "complexity": "O(n log n)",
            "pros": "综合考虑优先级和紧急程度",
            "cons": "slack可能为0导致除零，需特殊处理",
            "params": "无参数",
        },
        {
            "name": "MIP — 混合整数规划",
            "principle": "用PuLP建立0-1整数规划模型：决策变量x[i][j]表示工单i是否分配到产线j，目标函数最小化加权完工时间，约束：每工单恰好分配一条产线、不超产能。",
            "complexity": "NP-Hard，时间限制10秒",
            "pros": "理论上可得全局最优解",
            "cons": "大规模问题可能超时，只能返回当前最优可行解",
            "params": "time_limit=10s",
        },
        {
            "name": "SimulatedAnnealing — 模拟退火",
            "principle": "从随机初始解出发，每次随机交换两个工单的产线分配，若新解更优则接受，若更差则以概率 exp(-Δ/T) 接受（T随迭代降低）。",
            "complexity": "O(iterations × n)",
            "pros": "能跳出局部最优，质量较高",
            "cons": "参数敏感，需调T0和cooling rate",
            "params": "iterations=500, T0=100, cooling=0.95",
        },
        {
            "name": "AntColony — 蚁群优化",
            "principle": "模拟蚂蚁觅食：每只蚂蚁根据信息素τ[i][j]和启发式η[i][j]（1/处理时间）概率选择工单-产线分配，完成后根据解质量更新信息素（好解增强、蒸发衰减）。",
            "complexity": "O(ants × iterations × n²)",
            "pros": "适合大规模多产线问题，全局搜索能力强",
            "cons": "计算量大，参数较多",
            "params": "ants=10, iterations=20, α=1, β=2, evaporation=0.5",
        },
    ]

    r = 2
    for algo in algo_details:
        r = _section(ws, r, f"▶ {algo['name']}")
        details = [
            ("算法原理", algo["principle"]),
            ("时间复杂度", algo["complexity"]),
            ("优点", algo["pros"]),
            ("缺点", algo["cons"]),
            ("参数设置", algo["params"]),
        ]
        for i, (key, val) in enumerate(details, 1):
            bg = C_ROW_ODD if i % 2 else C_ROW_EVEN
            _cell(ws, r, 1, "", bg=bg)
            _cell(ws, r, 2, key, bg=bg, bold=True)
            ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
            _cell(ws, r, 3, val, bg=bg)
            ws.row_dimensions[r].height = 36 if key == "算法原理" else 20
            r += 1
        r += 1


# ══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ══════════════════════════════════════════════════════════════════════════════
def generate_user_manual() -> bytes:
    wb = Workbook()
    _sheet_cover(wb)
    _sheet_overview(wb)
    _sheet_auth(wb)
    _sheet_bom(wb)
    _sheet_orders(wb)
    _sheet_inventory(wb)
    _sheet_production(wb)
    _sheet_mrp(wb)
    _sheet_rccp(wb)
    _sheet_scheduling(wb)
    _sheet_reports(wb)
    _sheet_algo_theory(wb)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()
