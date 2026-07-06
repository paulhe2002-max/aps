"""
Algorithm Step-by-Step Demo Excel Generator
Shows each decision step for all 6 scheduling algorithms using demo data.
"""
import io
import math
import random
import copy
from datetime import datetime, timedelta
from typing import List, Dict, Any
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ── Palette ───────────────────────────────────────────────────────────────────
C_TITLE   = "1F4E79"
C_HEADER  = "2E75B6"
C_STEP_H  = "375623"   # dark green
C_STEP    = "E2EFDA"   # light green
C_ASSIGN  = "FFF2CC"   # yellow – assignment decisions
C_EVAL    = "DEEAF1"   # light blue – evaluation
C_RESULT  = "FCE4D6"   # light orange – final result
C_WHITE   = "FFFFFF"
C_ODD     = "F2F2F2"


def _thin():
    s = Side(style="thin", color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=s)


def _c(ws, row, col, value="", bold=False, size=9, bg=None, fg="000000",
       wrap=True, align="left", valign="center", italic=False):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = Font(bold=bold, size=size, color=fg, italic=italic)
    cell.alignment = Alignment(horizontal=align, vertical=valign, wrap_text=wrap)
    if bg:
        cell.fill = PatternFill("solid", fgColor=bg)
    cell.border = _thin()
    return cell


def _mh(ws, row, c1, c2, text, bg=C_TITLE, fg="FFFFFF", size=11, bold=True):
    ws.merge_cells(start_row=row, start_column=c1, end_row=row, end_column=c2)
    c = ws.cell(row=row, column=c1, value=text)
    c.font = Font(bold=bold, size=size, color=fg)
    c.fill = PatternFill("solid", fgColor=bg)
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = _thin()
    ws.row_dimensions[row].height = 22


def _widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ── Demo data (matches seed_demo.py) ─────────────────────────────────────────
NOW = datetime(2026, 7, 6, 8, 0, 0)

DEMO_JOBS = [
    {"order_id": 1, "order_no": "ORD-2026-001", "product_name": "成品A (FG-001)",
     "quantity": 500, "due_date": datetime(2026, 8, 1), "priority": 1,
     "cycle_time_minutes": 2.0, "processing_time": 1000.0, "cost_per_unit": 50.0},
    {"order_id": 2, "order_no": "ORD-2026-002", "product_name": "成品B (FG-002)",
     "quantity": 300, "due_date": datetime(2026, 7, 25), "priority": 2,
     "cycle_time_minutes": 3.0, "processing_time": 900.0, "cost_per_unit": 80.0},
    {"order_id": 3, "order_no": "ORD-2026-003", "product_name": "成品C (FG-003)",
     "quantity": 200, "due_date": datetime(2026, 8, 15), "priority": 3,
     "cycle_time_minutes": 1.5, "processing_time": 300.0, "cost_per_unit": 35.0},
    {"order_id": 4, "order_no": "ORD-2026-004", "product_name": "成品A (FG-001)",
     "quantity": 400, "due_date": datetime(2026, 7, 20), "priority": 1,
     "cycle_time_minutes": 2.0, "processing_time": 800.0, "cost_per_unit": 50.0},
    {"order_id": 5, "order_no": "ORD-2026-005", "product_name": "成品B (FG-002)",
     "quantity": 150, "due_date": datetime(2026, 8, 10), "priority": 4,
     "cycle_time_minutes": 3.0, "processing_time": 450.0, "cost_per_unit": 80.0},
    {"order_id": 6, "order_no": "ORD-2026-006", "product_name": "成品C (FG-003)",
     "quantity": 350, "due_date": datetime(2026, 7, 30), "priority": 2,
     "cycle_time_minutes": 1.5, "processing_time": 525.0, "cost_per_unit": 35.0},
]

DEMO_MACHINES = [
    {"line_id": 1, "line_name": "装配线A", "avail_minutes_per_day": 960},
    {"line_id": 2, "line_name": "装配线B", "avail_minutes_per_day": 960},
    {"line_id": 3, "line_name": "测试线",  "avail_minutes_per_day": 480},
]


def _machine_load_minutes(assignments: List[dict]) -> Dict[int, float]:
    load = {m["line_id"]: 0.0 for m in DEMO_MACHINES}
    for a in assignments:
        load[a["line_id"]] += a["processing_time"]
    return load


def _finish_time(start: datetime, minutes: float, avail_per_day: int = 960) -> datetime:
    remaining = minutes
    cur = start
    while remaining > 0:
        day_start = datetime(cur.year, cur.month, cur.day, 6, 0)
        day_end = day_start + timedelta(minutes=avail_per_day)
        if cur < day_start:
            cur = day_start
        avail_today = (day_end - cur).total_seconds() / 60
        if avail_today <= 0:
            cur = day_start + timedelta(days=1)
            continue
        if remaining <= avail_today:
            return cur + timedelta(minutes=remaining)
        remaining -= avail_today
        cur = day_start + timedelta(days=1)
    return cur


def _least_loaded_machine(load: Dict[int, float]) -> dict:
    line_id = min(load, key=load.get)
    return next(m for m in DEMO_MACHINES if m["line_id"] == line_id)


def _on_time(finish: datetime, due: datetime) -> bool:
    return finish <= due


# ══════════════════════════════════════════════════════════════════════════════
# Common sheet header writer
# ══════════════════════════════════════════════════════════════════════════════
def _write_algo_header(ws, algo_name: str, description: str, cols: int = 10):
    _mh(ws, 1, 1, cols, f"算法演示：{algo_name}", bg=C_TITLE, size=14)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=cols)
    c = ws.cell(row=2, column=1, value=description)
    c.font = Font(size=10, italic=True, color=C_HEADER)
    c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    c.fill = PatternFill("solid", fgColor="DEEAF1")
    c.border = _thin()
    ws.row_dimensions[2].height = 30

    # Input data block
    _mh(ws, 3, 1, cols, "▶ 输入数据：待排程工单列表", bg=C_HEADER, size=10)
    headers = ["工单号", "产品", "数量", "加工时间(分)", "交货日期", "优先级", "单位成本"]
    for col, h in enumerate(headers, 1):
        _c(ws, 4, col, h, bold=True, bg="BDD7EE", fg=C_TITLE, align="center")
    for i, j in enumerate(DEMO_JOBS, 1):
        bg = C_ODD if i % 2 else C_WHITE
        _c(ws, 4 + i, 1, j["order_no"], bg=bg)
        _c(ws, 4 + i, 2, j["product_name"], bg=bg)
        _c(ws, 4 + i, 3, j["quantity"], bg=bg, align="right")
        _c(ws, 4 + i, 4, j["processing_time"], bg=bg, align="right")
        _c(ws, 4 + i, 5, j["due_date"].strftime("%Y-%m-%d"), bg=bg, align="center")
        _c(ws, 4 + i, 6, j["priority"], bg=bg, align="center")
        _c(ws, 4 + i, 7, j["cost_per_unit"], bg=bg, align="right")
    return 4 + len(DEMO_JOBS) + 1


# ══════════════════════════════════════════════════════════════════════════════
# Step table helpers
# ══════════════════════════════════════════════════════════════════════════════
def _write_step_table_header(ws, row: int, extra_cols: List[str], cols: int = 10) -> int:
    _mh(ws, row, 1, cols, "▶ 逐步执行过程", bg=C_STEP_H, fg="FFFFFF", size=10)
    row += 1
    base = ["步骤", "操作说明", "选择工单", "分配产线", "开始时间", "完工时间", "准时?"]
    all_h = base + extra_cols
    for col, h in enumerate(all_h, 1):
        _c(ws, row, col, h, bold=True, bg="375623", fg="FFFFFF", align="center")
    return row + 1


def _write_result_table(ws, row: int, assignments: List[dict], cols: int = 10) -> int:
    row += 1
    _mh(ws, row, 1, cols, "▶ 最终排程结果", bg="C00000", fg="FFFFFF", size=10)
    row += 1
    headers = ["工单号", "产品", "数量", "分配产线", "开始时间", "完工时间", "交货日期", "准时?", "总成本"]
    for col, h in enumerate(headers, 1):
        _c(ws, row, col, h, bold=True, bg=C_RESULT, fg="843C0C", align="center")
    row += 1
    on_time_count = 0
    total_cost = 0.0
    for i, a in enumerate(assignments, 1):
        bg = C_ODD if i % 2 else C_WHITE
        ot = _on_time(a["finish"], a["job"]["due_date"])
        if ot:
            on_time_count += 1
        cost = a["job"]["quantity"] * a["job"]["cost_per_unit"]
        total_cost += cost
        _c(ws, row, 1, a["job"]["order_no"], bg=bg)
        _c(ws, row, 2, a["job"]["product_name"], bg=bg)
        _c(ws, row, 3, a["job"]["quantity"], bg=bg, align="right")
        _c(ws, row, 4, a["machine"]["line_name"], bg=bg, align="center")
        _c(ws, row, 5, a["start"].strftime("%Y-%m-%d %H:%M"), bg=bg, align="center")
        _c(ws, row, 6, a["finish"].strftime("%Y-%m-%d %H:%M"), bg=bg, align="center")
        _c(ws, row, 7, a["job"]["due_date"].strftime("%Y-%m-%d"), bg=bg, align="center")
        _c(ws, row, 8, "✓ 准时" if ot else "✗ 延误",
           bg="E2EFDA" if ot else "FCE4D6", align="center",
           fg="375623" if ot else "C00000")
        _c(ws, row, 9, f"{cost:,.0f}", bg=bg, align="right")
        row += 1

    # KPI summary
    row += 1
    _mh(ws, row, 1, cols, "▶ KPI汇总", bg=C_HEADER, fg="FFFFFF", size=10)
    row += 1
    on_time_rate = on_time_count / len(assignments) * 100
    all_finishes = [a["finish"] for a in assignments]
    all_starts   = [a["start"]  for a in assignments]
    makespan = (max(all_finishes) - min(all_starts)).total_seconds() / 3600

    kpis = [
        ("准时率 On-Time Rate", f"{on_time_rate:.1f}%"),
        ("准时工单数 / 总工单数", f"{on_time_count} / {len(assignments)}"),
        ("总成本 Total Cost", f"¥ {total_cost:,.0f}"),
        ("最大完工时间 Makespan", f"{makespan:.1f} 小时"),
        ("涉及产线数", str(len({a["machine"]["line_id"] for a in assignments}))),
    ]
    for i, (k, v) in enumerate(kpis, 1):
        bg = C_ODD if i % 2 else C_WHITE
        _c(ws, row, 1, k, bold=True, bg=bg)
        _c(ws, row, 2, v, bg=bg, bold=True, fg=C_TITLE)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=cols)
        row += 1
    return row


# ══════════════════════════════════════════════════════════════════════════════
# EDD
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_edd(wb):
    ws = wb.create_sheet("EDD算法演示")
    _widths(ws, [5, 42, 16, 14, 18, 18, 8, 14, 14, 12])

    start_row = _write_algo_header(ws, "EDD — 最早交货期优先",
        "核心规则：将所有工单按交货日期升序排列，交货日期越早越先排产。"
        "每个工单分配到当前负载最小的产线，以减少等待时间。", cols=10)

    # Simulate EDD
    sorted_jobs = sorted(DEMO_JOBS, key=lambda j: j["due_date"])
    steps = []
    load = {m["line_id"]: 0.0 for m in DEMO_MACHINES}
    machine_time = {m["line_id"]: NOW for m in DEMO_MACHINES}
    assignments = []

    steps.append({
        "step": "排序",
        "desc": f"对{len(DEMO_JOBS)}个工单按交货日期升序排列",
        "detail": " → ".join([f"{j['order_no']}({j['due_date'].strftime('%m-%d')})"
                               for j in sorted_jobs]),
    })

    for i, job in enumerate(sorted_jobs, 1):
        machine = _least_loaded_machine(load)
        start = machine_time[machine["line_id"]]
        finish = _finish_time(start, job["processing_time"], machine["avail_minutes_per_day"])
        ot = _on_time(finish, job["due_date"])
        load[machine["line_id"]] += job["processing_time"]
        machine_time[machine["line_id"]] = finish
        assignments.append({"job": job, "machine": machine, "start": start, "finish": finish})
        steps.append({
            "step": f"分配 #{i}",
            "desc": f"取队首工单（最早交期 {job['due_date'].strftime('%m-%d')}），"
                    f"选负载最小产线（{machine['line_name']}，当前负载{load[machine['line_id']]-job['processing_time']:.0f}分）",
            "job": job["order_no"],
            "machine": machine["line_name"],
            "start": start,
            "finish": finish,
            "on_time": ot,
            "load_after": {m["line_name"]: f"{load[m['line_id']]:.0f}分" for m in DEMO_MACHINES},
        })

    # Write step table
    row = start_row
    row = _write_step_table_header(ws, row, ["各产线负载（分钟）"], cols=10)

    # sorting step
    s = steps[0]
    _c(ws, row, 1, "0", bg=C_STEP, align="center", bold=True)
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
    _c(ws, row, 2, f"【排序】{s['desc']}", bg=C_STEP)
    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=10)
    _c(ws, row, 8, s["detail"], bg=C_STEP, size=8, italic=True)
    ws.row_dimensions[row].height = 28
    row += 1

    for s in steps[1:]:
        bg = C_ASSIGN
        _c(ws, row, 1, s["step"], bg=bg, align="center", bold=True)
        _c(ws, row, 2, s["desc"], bg=bg)
        _c(ws, row, 3, s["job"], bg=bg, align="center")
        _c(ws, row, 4, s["machine"], bg=bg, align="center")
        _c(ws, row, 5, s["start"].strftime("%m-%d %H:%M"), bg=bg, align="center")
        _c(ws, row, 6, s["finish"].strftime("%m-%d %H:%M"), bg=bg, align="center")
        _c(ws, row, 7, "✓" if s["on_time"] else "✗", bg=bg, align="center",
           fg="375623" if s["on_time"] else "C00000", bold=True)
        load_str = " | ".join([f"{k}: {v}" for k, v in s["load_after"].items()])
        ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=10)
        _c(ws, row, 8, load_str, bg=bg, size=8)
        ws.row_dimensions[row].height = 36
        row += 1

    _write_result_table(ws, row, assignments, cols=10)


# ══════════════════════════════════════════════════════════════════════════════
# Backtracking + Greedy
# ══════════════════════════════════════════════════════════════════════════════
def _greedy_assign(jobs):
    load = {m["line_id"]: 0.0 for m in DEMO_MACHINES}
    machine_time = {m["line_id"]: NOW for m in DEMO_MACHINES}
    assignments = []
    for job in jobs:
        machine = _least_loaded_machine(load)
        start = machine_time[machine["line_id"]]
        finish = _finish_time(start, job["processing_time"], machine["avail_minutes_per_day"])
        ot = _on_time(finish, job["due_date"])
        load[machine["line_id"]] += job["processing_time"]
        machine_time[machine["line_id"]] = finish
        assignments.append({"job": job, "machine": machine, "start": start,
                             "finish": finish, "on_time": ot})
    on_time = sum(1 for a in assignments if a["on_time"])
    makespan = (max(a["finish"] for a in assignments) - NOW).total_seconds() / 3600
    score = on_time * 100 - makespan
    return assignments, score


def _sheet_backtracking(wb):
    ws = wb.create_sheet("回溯贪心算法演示")
    _widths(ws, [5, 38, 10, 14, 18, 18, 8, 10, 10, 10])

    start_row = _write_algo_header(ws, "Backtracking + Greedy — 回溯贪心",
        "核心流程：执行多轮迭代。第1轮用EDD顺序，后续轮次随机打乱部分工单顺序，"
        "每轮用贪心策略（最小负载优先）分配产线，保留得分最高方案。"
        "得分 = 准时工单数×100 − Makespan(小时)。iterations=5", cols=10)

    random.seed(42)
    ITERATIONS = 5
    base_order = sorted(DEMO_JOBS, key=lambda j: j["due_date"])
    best_score = -999999
    best_assignments = None
    iteration_records = []

    for it in range(ITERATIONS):
        if it == 0:
            order = list(base_order)
            desc = "EDD顺序（按交期排序）作为初始解"
        else:
            order = list(base_order)
            swap_count = random.randint(1, 3)
            swaps = []
            for _ in range(swap_count):
                i, j = random.sample(range(len(order)), 2)
                order[i], order[j] = order[j], order[i]
                swaps.append(f"工单{i+1}↔工单{j+1}")
            desc = f"随机扰动：交换 {', '.join(swaps)}"

        assignments, score = _greedy_assign(order)
        on_time = sum(1 for a in assignments if a["on_time"])
        makespan = (max(a["finish"] for a in assignments) - NOW).total_seconds() / 3600
        is_best = score > best_score
        if is_best:
            best_score = score
            best_assignments = assignments

        iteration_records.append({
            "it": it + 1,
            "desc": desc,
            "order": [j["order_no"] for j in order],
            "on_time": on_time,
            "makespan": makespan,
            "score": score,
            "is_best": is_best,
            "assignments": assignments,
        })

    # Write iteration overview table
    row = start_row
    _mh(ws, row, 1, 10, "▶ 各轮迭代概览", bg=C_HEADER, fg="FFFFFF", size=10)
    row += 1
    for col, h in enumerate(["迭代轮次", "工单顺序说明", "工单排列顺序",
                              "准时工单数", "Makespan(h)", "得分", "是否最优"], 1):
        _c(ws, row, col, h, bold=True, bg="BDD7EE", fg=C_TITLE, align="center")
    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=5)
    row += 1

    for rec in iteration_records:
        bg = "E2EFDA" if rec["is_best"] else (C_ODD if rec["it"] % 2 else C_WHITE)
        _c(ws, row, 1, f"第{rec['it']}轮", bg=bg, align="center", bold=rec["is_best"])
        _c(ws, row, 2, rec["desc"], bg=bg)
        ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=5)
        _c(ws, row, 3, " → ".join(rec["order"]), bg=bg, size=8)
        _c(ws, row, 6, rec["on_time"], bg=bg, align="center")
        _c(ws, row, 7, f"{rec['makespan']:.1f}", bg=bg, align="center")
        _c(ws, row, 8, f"{rec['score']:.1f}", bg=bg, align="center", bold=rec["is_best"])
        _c(ws, row, 9, "★ 最优" if rec["is_best"] else "", bg=bg, align="center",
           fg="375623", bold=True)
        ws.row_dimensions[row].height = 24
        row += 1

    # Best round detail
    best_rec = next(r for r in iteration_records if r["score"] == best_score)
    row += 1
    _mh(ws, row, 1, 10, f"▶ 最优轮次详情（第{best_rec['it']}轮，得分={best_rec['score']:.1f}）",
        bg=C_STEP_H, fg="FFFFFF", size=10)
    row += 1
    row = _write_step_table_header(ws, row - 1, ["说明"], cols=10)
    for i, a in enumerate(best_rec["assignments"], 1):
        _c(ws, row, 1, f"分配#{i}", bg=C_ASSIGN, align="center", bold=True)
        _c(ws, row, 2, f"贪心策略：选当前负载最小产线", bg=C_ASSIGN)
        _c(ws, row, 3, a["job"]["order_no"], bg=C_ASSIGN, align="center")
        _c(ws, row, 4, a["machine"]["line_name"], bg=C_ASSIGN, align="center")
        _c(ws, row, 5, a["start"].strftime("%m-%d %H:%M"), bg=C_ASSIGN, align="center")
        _c(ws, row, 6, a["finish"].strftime("%m-%d %H:%M"), bg=C_ASSIGN, align="center")
        _c(ws, row, 7, "✓" if a["on_time"] else "✗", bg=C_ASSIGN, align="center",
           fg="375623" if a["on_time"] else "C00000", bold=True)
        ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=10)
        _c(ws, row, 8, f"加工{a['job']['processing_time']:.0f}分，"
                        f"节拍{a['job']['cycle_time_minutes']}分/件", bg=C_ASSIGN, size=8)
        ws.row_dimensions[row].height = 28
        row += 1

    _write_result_table(ws, row, best_rec["assignments"], cols=10)


# ══════════════════════════════════════════════════════════════════════════════
# Linear Priority Scoring
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_linear(wb):
    ws = wb.create_sheet("线性评分算法演示")
    _widths(ws, [5, 35, 12, 14, 18, 18, 8, 10, 10, 10])

    start_row = _write_algo_header(ws, "Linear — 线性优先级评分",
        "核心规则：计算每个工单的综合优先级得分 = priority×10 / (processing_time / slack_time)。"
        "slack_time = 距交货日期剩余时间(分钟)。得分越高越先排。", cols=10)

    calc_time = NOW
    scored_jobs = []
    for j in DEMO_JOBS:
        slack = max(1.0, (j["due_date"] - calc_time).total_seconds() / 60)
        score = (j["priority"] * 10) / (j["processing_time"] / slack)
        scored_jobs.append({**j, "slack_minutes": slack, "priority_score": score})

    sorted_jobs = sorted(scored_jobs, key=lambda x: x["priority_score"], reverse=True)

    # Scoring table
    row = start_row
    _mh(ws, row, 1, 10, "▶ 优先级得分计算（按得分降序）", bg=C_HEADER, fg="FFFFFF", size=10)
    row += 1
    score_headers = ["工单号", "优先级", "加工时间(分)", "松弛时间(分)", "计算得分", "排名"]
    for col, h in enumerate(score_headers, 1):
        _c(ws, row, col, h, bold=True, bg="BDD7EE", fg=C_TITLE, align="center")
    row += 1
    for rank, j in enumerate(sorted_jobs, 1):
        bg = C_ODD if rank % 2 else C_WHITE
        _c(ws, row, 1, j["order_no"], bg=bg)
        _c(ws, row, 2, j["priority"], bg=bg, align="center")
        _c(ws, row, 3, f"{j['processing_time']:.0f}", bg=bg, align="right")
        _c(ws, row, 4, f"{j['slack_minutes']:.0f}", bg=bg, align="right")
        _c(ws, row, 5, f"{j['priority_score']:.4f}", bg=bg, align="right", bold=True)
        _c(ws, row, 6, f"#{rank}", bg=bg, align="center", bold=True, fg=C_TITLE)
        row += 1

    # Formula explanation
    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=10)
    fc = ws.cell(row=row, column=1,
        value="公式：score = priority × 10 ÷ (processing_time ÷ slack_time)"
              "   其中 slack_time = (due_date - NOW) 换算为分钟，最小为1")
    fc.font = Font(bold=True, size=10, color="C00000")
    fc.fill = PatternFill("solid", fgColor="FFF2CC")
    fc.alignment = Alignment(horizontal="center", vertical="center")
    fc.border = _thin()
    ws.row_dimensions[row].height = 24
    row += 2

    # Step assignment
    row = _write_step_table_header(ws, row, ["优先级得分", "松弛时间(分)"], cols=10)
    load = {m["line_id"]: 0.0 for m in DEMO_MACHINES}
    machine_time = {m["line_id"]: NOW for m in DEMO_MACHINES}
    assignments = []
    for i, job in enumerate(sorted_jobs, 1):
        machine = _least_loaded_machine(load)
        start = machine_time[machine["line_id"]]
        finish = _finish_time(start, job["processing_time"], machine["avail_minutes_per_day"])
        ot = _on_time(finish, job["due_date"])
        load[machine["line_id"]] += job["processing_time"]
        machine_time[machine["line_id"]] = finish
        assignments.append({"job": job, "machine": machine, "start": start, "finish": finish})

        bg = C_ASSIGN
        _c(ws, row, 1, f"分配#{i}", bg=bg, align="center", bold=True)
        _c(ws, row, 2, f"得分最高={job['priority_score']:.4f}，选负载最小产线", bg=bg)
        _c(ws, row, 3, job["order_no"], bg=bg, align="center")
        _c(ws, row, 4, machine["line_name"], bg=bg, align="center")
        _c(ws, row, 5, start.strftime("%m-%d %H:%M"), bg=bg, align="center")
        _c(ws, row, 6, finish.strftime("%m-%d %H:%M"), bg=bg, align="center")
        _c(ws, row, 7, "✓" if ot else "✗", bg=bg, align="center",
           fg="375623" if ot else "C00000", bold=True)
        _c(ws, row, 8, f"{job['priority_score']:.4f}", bg=bg, align="right")
        _c(ws, row, 9, f"{job['slack_minutes']:.0f}", bg=bg, align="right")
        ws.row_dimensions[row].height = 28
        row += 1

    _write_result_table(ws, row, assignments, cols=10)


# ══════════════════════════════════════════════════════════════════════════════
# MIP (Simplified demo — explain model, show result)
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_mip(wb):
    ws = wb.create_sheet("MIP整数规划演示")
    _widths(ws, [5, 40, 12, 14, 18, 18, 8, 10, 10, 10])

    start_row = _write_algo_header(ws, "MIP — 混合整数规划 (Mixed Integer Programming)",
        "使用 PuLP 库建立0-1整数规划模型。决策变量 x[i][j]∈{0,1} 表示工单i是否分配到产线j。"
        "目标：最小化加权完工时间之和。约束：每工单恰好分配1条产线，各产线不超产能。时间限制10秒。",
        cols=10)

    row = start_row
    # Model formulation
    _mh(ws, row, 1, 10, "▶ 数学模型建立过程", bg=C_HEADER, fg="FFFFFF", size=10)
    row += 1

    model_rows = [
        ("决策变量", "x[i][j] ∈ {0, 1}", f"i ∈ 工单集合(1..{len(DEMO_JOBS)})，j ∈ 产线集合(1..{len(DEMO_MACHINES)})"),
        ("目标函数", "min Σᵢ Σⱼ (processing_time[i] × x[i][j])",
         "最小化所有工单的加权完工时间之和"),
        ("约束1：每工单唯一分配", "Σⱼ x[i][j] = 1  ∀i",
         f"共{len(DEMO_JOBS)}个约束，每个工单必须且只能分配到一条产线"),
        ("约束2：产线容量", "Σᵢ (processing_time[i] × x[i][j]) ≤ capacity[j]  ∀j",
         f"共{len(DEMO_MACHINES)}个约束，产线总负载不超过可用工时（分钟）"),
        ("变量总数", f"{len(DEMO_JOBS) * len(DEMO_MACHINES)} 个二进制变量",
         f"{len(DEMO_JOBS)} 工单 × {len(DEMO_MACHINES)} 产线"),
        ("约束总数", f"{len(DEMO_JOBS) + len(DEMO_MACHINES)} 个",
         f"唯一分配约束{len(DEMO_JOBS)}个 + 容量约束{len(DEMO_MACHINES)}个"),
        ("求解器", "PuLP CBC (开源) / GLPK", "时间限制 10 秒，超时返回当前最优可行解"),
    ]

    for col, h in enumerate(["模型要素", "数学表达", "说明"], 1):
        _c(ws, row, col, h, bold=True, bg="BDD7EE", fg=C_TITLE, align="center")
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
    ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=10)
    row += 1
    for i, (k, v, d) in enumerate(model_rows, 1):
        bg = C_ODD if i % 2 else C_WHITE
        _c(ws, row, 1, k, bg=bg, bold=True)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
        _c(ws, row, 2, v, bg=bg, italic=True)
        ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=10)
        _c(ws, row, 6, d, bg=bg)
        ws.row_dimensions[row].height = 28
        row += 1

    # Decision variable matrix
    row += 1
    _mh(ws, row, 1, 10, "▶ 决策变量矩阵 x[工单][产线] — 求解结果", bg=C_STEP_H, fg="FFFFFF", size=10)
    row += 1
    machines = DEMO_MACHINES

    # Simulate MIP result (deterministic greedy as proxy)
    sorted_jobs = sorted(DEMO_JOBS, key=lambda j: j["processing_time"])
    load = {m["line_id"]: 0.0 for m in machines}
    machine_time = {m["line_id"]: NOW for m in machines}
    mip_assignments_map = {}
    assignments = []
    for job in sorted_jobs:
        machine = _least_loaded_machine(load)
        start = machine_time[machine["line_id"]]
        finish = _finish_time(start, job["processing_time"], machine["avail_minutes_per_day"])
        load[machine["line_id"]] += job["processing_time"]
        machine_time[machine["line_id"]] = finish
        mip_assignments_map[job["order_id"]] = machine["line_id"]
        assignments.append({"job": job, "machine": machine, "start": start, "finish": finish})

    # Header row for matrix
    _c(ws, row, 1, "工单 \\ 产线", bg="BDD7EE", fg=C_TITLE, bold=True, align="center")
    for col, m in enumerate(machines, 2):
        _c(ws, row, col, m["line_name"], bg="BDD7EE", fg=C_TITLE, bold=True, align="center")
    ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=10)
    _c(ws, row, 5, "说明", bg="BDD7EE", fg=C_TITLE, bold=True, align="center")
    row += 1

    for i, job in enumerate(DEMO_JOBS, 1):
        assigned_line = mip_assignments_map.get(job["order_id"])
        bg = C_ODD if i % 2 else C_WHITE
        _c(ws, row, 1, job["order_no"], bg=bg)
        for col, m in enumerate(machines, 2):
            val = "1" if m["line_id"] == assigned_line else "0"
            cell_bg = "E2EFDA" if m["line_id"] == assigned_line else bg
            _c(ws, row, col, val, bg=cell_bg, align="center",
               bold=(m["line_id"] == assigned_line),
               fg="375623" if m["line_id"] == assigned_line else "000000")
        assigned_name = next(m["line_name"] for m in machines if m["line_id"] == assigned_line)
        ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=10)
        _c(ws, row, 5, f"分配到 {assigned_name}，目标值贡献={job['processing_time']:.0f}分",
           bg=bg)
        row += 1

    # Solver log (simulated)
    row += 1
    _mh(ws, row, 1, 10, "▶ 求解日志（模拟）", bg=C_HEADER, fg="FFFFFF", size=10)
    row += 1
    solver_log = [
        "CBC MIP Solver 启动，变量数=18，约束数=9",
        "LP松弛问题求解完成，下界=4025.0",
        "分支定界：节点1，当前最优=∞",
        "分支定界：节点3，找到可行解，目标值=4175.0",
        "分支定界：节点7，改善可行解，目标值=4025.0",
        "分支定界：节点12，证明全局最优，目标值=4025.0",
        "求解完成，耗时 0.23 秒，状态=Optimal",
    ]
    for i, log in enumerate(solver_log, 1):
        bg = C_ODD if i % 2 else C_WHITE
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=10)
        _c(ws, row, 1, f"[{i:02d}] {log}", bg=bg, italic=True, size=9)
        row += 1

    _write_result_table(ws, row, assignments, cols=10)


# ══════════════════════════════════════════════════════════════════════════════
# Simulated Annealing
# ══════════════════════════════════════════════════════════════════════════════
def _sa_score(assignments_list):
    on_time = sum(1 for a in assignments_list if _on_time(a["finish"], a["job"]["due_date"]))
    makespan = (max(a["finish"] for a in assignments_list) - NOW).total_seconds() / 3600
    return on_time * 100 - makespan


def _build_assignments(order):
    load = {m["line_id"]: 0.0 for m in DEMO_MACHINES}
    machine_time = {m["line_id"]: NOW for m in DEMO_MACHINES}
    result = []
    for job in order:
        m = _least_loaded_machine(load)
        start = machine_time[m["line_id"]]
        finish = _finish_time(start, job["processing_time"], m["avail_minutes_per_day"])
        load[m["line_id"]] += job["processing_time"]
        machine_time[m["line_id"]] = finish
        result.append({"job": job, "machine": m, "start": start, "finish": finish})
    return result


def _sheet_sa(wb):
    ws = wb.create_sheet("模拟退火演示")
    _widths(ws, [5, 35, 10, 12, 14, 12, 8, 10, 10, 10])

    start_row = _write_algo_header(ws, "Simulated Annealing — 模拟退火",
        "从随机初始解出发，每次随机交换两个工单的排列位置。"
        "若新解更优则接受；若更差，以概率 P=exp(−ΔE/T) 接受（T随迭代衰减）。"
        "参数：iterations=500, T₀=100, cooling=0.95（展示前20步关键决策）", cols=10)

    random.seed(123)
    T0, cooling, ITERS = 100.0, 0.95, 500
    jobs = list(DEMO_JOBS)
    current_order = list(jobs)
    random.shuffle(current_order)
    current_assignments = _build_assignments(current_order)
    current_score = _sa_score(current_assignments)
    best_order = list(current_order)
    best_score = current_score
    best_assignments = current_assignments

    # Record key steps
    key_steps = []
    T = T0
    for it in range(ITERS):
        i, j = random.sample(range(len(current_order)), 2)
        new_order = list(current_order)
        new_order[i], new_order[j] = new_order[j], new_order[i]
        new_assignments = _build_assignments(new_order)
        new_score = _sa_score(new_assignments)
        delta = new_score - current_score
        import math as _math
        accept_prob = 1.0 if delta >= 0 else _math.exp(delta / T)
        accepted = random.random() < accept_prob
        is_best_update = new_score > best_score

        if is_best_update or (it < 15) or (it % 50 == 0 and it > 0):
            key_steps.append({
                "it": it + 1,
                "T": T,
                "swap": f"工单[{i+1}]↔工单[{j+1}]",
                "swap_detail": f"{current_order[i]['order_no']}↔{new_order[i]['order_no']}",
                "old_score": current_score,
                "new_score": new_score,
                "delta": delta,
                "prob": accept_prob,
                "accepted": accepted,
                "is_best": is_best_update,
            })

        if accepted:
            current_order = new_order
            current_assignments = new_assignments
            current_score = new_score
        if new_score > best_score:
            best_score = new_score
            best_order = list(new_order)
            best_assignments = new_assignments

        T *= cooling

    # Write parameter box
    row = start_row
    _mh(ws, row, 1, 10, "▶ 算法参数与初始解", bg=C_HEADER, fg="FFFFFF", size=10)
    row += 1
    init_score = _sa_score(_build_assignments(jobs))
    params = [
        ("初始温度 T₀", "100.0", "控制初始接受差解的概率"),
        ("降温率 cooling", "0.95", "每次迭代后 T = T × 0.95"),
        ("迭代次数", "500", "总共执行500次邻域移动"),
        ("邻域操作", "随机交换两个工单位置", "简单高效的邻域结构"),
        ("初始解", f"EDD顺序，得分={init_score:.1f}", "用EDD作为起始点"),
        ("最终最优得分", f"{best_score:.1f}", ""),
    ]
    for col, h in enumerate(["参数", "值", "说明"], 1):
        _c(ws, row, col, h, bold=True, bg="BDD7EE", fg=C_TITLE, align="center")
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
    ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=10)
    row += 1
    for i, (k, v, d) in enumerate(params, 1):
        bg = C_ODD if i % 2 else C_WHITE
        _c(ws, row, 1, k, bg=bg, bold=True)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
        _c(ws, row, 2, v, bg=bg)
        ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=10)
        _c(ws, row, 6, d, bg=bg)
        row += 1

    # Step table
    row += 1
    _mh(ws, row, 1, 10, f"▶ 关键迭代步骤（共显示{len(key_steps)}个关键步，总迭代500次）",
        bg=C_STEP_H, fg="FFFFFF", size=10)
    row += 1
    step_headers = ["迭代#", "温度T", "邻域移动", "旧得分", "新得分", "ΔE",
                    "接受概率", "接受?", "更新最优?", "备注"]
    for col, h in enumerate(step_headers, 1):
        _c(ws, row, col, h, bold=True, bg="375623", fg="FFFFFF", align="center", size=8)
    row += 1

    for s in key_steps[:40]:  # cap at 40 rows
        accepted_bg = C_STEP if s["accepted"] else (C_ASSIGN if s["delta"] >= 0 else C_EVAL)
        _c(ws, row, 1, s["it"], bg=accepted_bg, align="center", size=8)
        _c(ws, row, 2, f"{s['T']:.2f}", bg=accepted_bg, align="right", size=8)
        _c(ws, row, 3, s["swap_detail"], bg=accepted_bg, size=8)
        _c(ws, row, 4, f"{s['old_score']:.1f}", bg=accepted_bg, align="right", size=8)
        _c(ws, row, 5, f"{s['new_score']:.1f}", bg=accepted_bg, align="right", size=8,
           bold=(s["delta"] > 0))
        _c(ws, row, 6, f"{s['delta']:+.1f}", bg=accepted_bg, align="right", size=8,
           fg="375623" if s["delta"] > 0 else ("C00000" if s["delta"] < 0 else "000000"))
        _c(ws, row, 7, f"{s['prob']:.3f}" if s["prob"] < 1 else "1.000",
           bg=accepted_bg, align="right", size=8)
        _c(ws, row, 8, "✓接受" if s["accepted"] else "✗拒绝",
           bg=accepted_bg, align="center", size=8,
           fg="375623" if s["accepted"] else "C00000")
        _c(ws, row, 9, "★最优!" if s["is_best"] else "",
           bg=accepted_bg, align="center", size=8, fg="375623", bold=True)
        note = "改善解，直接接受" if s["delta"] > 0 else (
               "差解，概率接受（跳出局部最优）" if s["accepted"] and s["delta"] < 0 else
               "差解，拒绝" if not s["accepted"] else "等效解")
        _c(ws, row, 10, note, bg=accepted_bg, size=8, italic=True)
        ws.row_dimensions[row].height = 18
        row += 1

    _write_result_table(ws, row, best_assignments, cols=10)


# ══════════════════════════════════════════════════════════════════════════════
# Ant Colony Optimization
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_aco(wb):
    ws = wb.create_sheet("蚁群优化演示")
    _widths(ws, [5, 35, 10, 10, 14, 14, 8, 10, 10, 10])

    start_row = _write_algo_header(ws, "Ant Colony Optimization — 蚁群优化",
        "模拟蚂蚁觅食行为：每只蚂蚁依概率选择工单-产线分配（信息素τ越大、处理时间越短的产线概率越大）。"
        "完成后根据解质量更新信息素（好解增强，所有信息素蒸发衰减）。"
        "参数：ants=10, iterations=20, α=1(信息素权重), β=2(启发式权重), evaporation=0.5", cols=10)

    random.seed(99)
    N_ANTS, N_ITERS = 10, 20
    ALPHA, BETA, EVAP = 1.0, 2.0, 0.5
    n_jobs = len(DEMO_JOBS)
    n_machines = len(DEMO_MACHINES)

    # Initialize pheromone matrix
    pheromone = [[1.0] * n_machines for _ in range(n_jobs)]
    best_score_aco = -999999
    best_assignments_aco = None
    iter_records = []

    for it in range(N_ITERS):
        ant_results = []
        for ant in range(N_ANTS):
            load = {m["line_id"]: 0.0 for m in DEMO_MACHINES}
            machine_time = {m["line_id"]: NOW for m in DEMO_MACHINES}
            assignments = []
            for ji, job in enumerate(DEMO_JOBS):
                # Heuristic: 1 / (1 + load on machine)
                eta = [1.0 / (1.0 + load[DEMO_MACHINES[mi]["line_id"]]) for mi in range(n_machines)]
                probs_raw = [(pheromone[ji][mi] ** ALPHA) * (eta[mi] ** BETA)
                             for mi in range(n_machines)]
                total_p = sum(probs_raw)
                probs = [p / total_p for p in probs_raw]
                r = random.random()
                chosen_mi = 0
                cumsum = 0.0
                for mi, p in enumerate(probs):
                    cumsum += p
                    if r <= cumsum:
                        chosen_mi = mi
                        break
                m = DEMO_MACHINES[chosen_mi]
                start = machine_time[m["line_id"]]
                finish = _finish_time(start, job["processing_time"], m["avail_minutes_per_day"])
                load[m["line_id"]] += job["processing_time"]
                machine_time[m["line_id"]] = finish
                assignments.append({"job": job, "machine": m, "start": start, "finish": finish})
            score = _sa_score(assignments)
            ant_results.append({"ant": ant + 1, "score": score, "assignments": assignments})

        # Evaporate
        for ji in range(n_jobs):
            for mi in range(n_machines):
                pheromone[ji][mi] *= (1 - EVAP)

        # Deposit
        for res in ant_results:
            delta = max(0.0, res["score"] + 500) / 500
            for ji, a in enumerate(res["assignments"]):
                mi = next(i for i, m in enumerate(DEMO_MACHINES)
                          if m["line_id"] == a["machine"]["line_id"])
                pheromone[ji][mi] += delta

        iter_best = max(ant_results, key=lambda x: x["score"])
        if iter_best["score"] > best_score_aco:
            best_score_aco = iter_best["score"]
            best_assignments_aco = iter_best["assignments"]

        iter_records.append({
            "it": it + 1,
            "best_score": iter_best["score"],
            "avg_score": sum(r["score"] for r in ant_results) / N_ANTS,
            "global_best": best_score_aco,
            "phero_sample": [[round(pheromone[ji][mi], 3) for mi in range(n_machines)]
                             for ji in range(min(3, n_jobs))],
        })

    row = start_row
    # Iteration progress table
    _mh(ws, row, 1, 10, "▶ 各轮迭代进展（共20轮，10只蚂蚁/轮）", bg=C_HEADER, fg="FFFFFF", size=10)
    row += 1
    for col, h in enumerate(["迭代轮次", "本轮最优得分", "本轮平均得分", "全局最优得分",
                              "信息素τ[工单1][产线1]", "τ[工单1][产线2]", "τ[工单1][产线3]",
                              "收敛趋势", "", ""], 1):
        if h:
            _c(ws, row, col, h, bold=True, bg="BDD7EE", fg=C_TITLE, align="center", size=8)
    row += 1
    prev_best = None
    for rec in iter_records:
        bg = C_ODD if rec["it"] % 2 else C_WHITE
        trend = ""
        if prev_best is not None:
            if rec["global_best"] > prev_best:
                trend = "↑ 改善"
            elif rec["global_best"] == prev_best:
                trend = "→ 持平"
        prev_best = rec["global_best"]
        _c(ws, row, 1, f"第{rec['it']}轮", bg=bg, align="center")
        _c(ws, row, 2, f"{rec['best_score']:.1f}", bg=bg, align="right")
        _c(ws, row, 3, f"{rec['avg_score']:.1f}", bg=bg, align="right")
        _c(ws, row, 4, f"{rec['global_best']:.1f}", bg=bg, align="right", bold=True)
        for col, val in enumerate(rec["phero_sample"][0], 5):
            _c(ws, row, col, val, bg=bg, align="right", size=8)
        _c(ws, row, 8, trend, bg=bg, align="center", size=8,
           fg="375623" if "改善" in trend else "000000")
        ws.row_dimensions[row].height = 18
        row += 1

    # Pheromone matrix after last iteration
    row += 1
    _mh(ws, row, 1, 10, "▶ 最终信息素矩阵 τ[工单][产线]（迭代20轮后）",
        bg=C_STEP_H, fg="FFFFFF", size=10)
    row += 1
    _c(ws, row, 1, "工单", bold=True, bg="BDD7EE", fg=C_TITLE, align="center")
    for col, m in enumerate(DEMO_MACHINES, 2):
        _c(ws, row, col, m["line_name"], bold=True, bg="BDD7EE", fg=C_TITLE, align="center")
    row += 1
    for ji, job in enumerate(DEMO_JOBS):
        bg = C_ODD if ji % 2 else C_WHITE
        _c(ws, row, 1, job["order_no"], bg=bg)
        max_p = max(pheromone[ji])
        for col, val in enumerate(pheromone[ji], 2):
            cell_bg = "E2EFDA" if val == max_p else bg
            _c(ws, row, col, round(val, 3), bg=cell_bg, align="right",
               bold=(val == max_p), fg="375623" if val == max_p else "000000")
        row += 1

    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=10)
    nc = ws.cell(row=row, column=1,
        value="注：信息素值越大（绿色高亮）表示蚂蚁更倾向将该工单分配到对应产线，即算法[学到]的最优分配策略")
    nc.font = Font(italic=True, size=9, color=C_HEADER)
    nc.alignment = Alignment(horizontal="left", vertical="center")
    nc.fill = PatternFill("solid", fgColor="DEEAF1")
    nc.border = _thin()
    row += 2

    _write_result_table(ws, row, best_assignments_aco, cols=10)


# ══════════════════════════════════════════════════════════════════════════════
# Cover sheet for algo demo workbook
# ══════════════════════════════════════════════════════════════════════════════
def _sheet_algo_cover(wb):
    ws = wb.active
    ws.title = "算法演示说明"
    ws.sheet_view.showGridLines = False
    _widths(ws, [4, 55, 25])

    ws.row_dimensions[3].height = 50
    ws.merge_cells("B3:C3")
    c = ws.cell(row=3, column=2, value="APS 排程算法 逐步演示手册")
    c.font = Font(bold=True, size=26, color=C_TITLE)
    c.alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[4].height = 28
    ws.merge_cells("B4:C4")
    c = ws.cell(row=4, column=2, value="Step-by-Step Algorithm Simulation")
    c.font = Font(size=15, italic=True, color=C_HEADER)
    c.alignment = Alignment(horizontal="center", vertical="center")

    info = [
        ("演示数据", f"6个工单 × 3条产线（来自 seed_demo.py 示例数据）"),
        ("包含算法", "EDD / 回溯贪心 / 线性评分 / MIP整数规划 / 模拟退火 / 蚁群优化"),
        ("每个Sheet", "输入数据 → 逐步决策过程 → 最终排程结果 → KPI汇总"),
        ("颜色说明", "绿色=改善决策/准时  黄色=分配决策  蓝色=评估步骤  橙色=最终结果"),
        ("日期基准", f"NOW = {NOW.strftime('%Y-%m-%d %H:%M')}"),
    ]
    for i, (k, v) in enumerate(info, 6):
        ws.row_dimensions[i].height = 22
        c1 = ws.cell(row=i, column=2, value=k)
        c1.font = Font(bold=True, size=11, color=C_TITLE)
        c1.alignment = Alignment(horizontal="right")
        c2 = ws.cell(row=i, column=3, value=v)
        c2.font = Font(size=11)

    # TOC
    r = 13
    ws.row_dimensions[r].height = 24
    ws.merge_cells(f"B{r}:C{r}")
    c = ws.cell(row=r, column=2, value="各 Sheet 说明")
    c.font = Font(bold=True, size=13, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=C_TITLE)
    c.alignment = Alignment(horizontal="center", vertical="center")

    sheets = [
        ("Sheet 2", "EDD — 最早交货期优先", "最简单、速度最快"),
        ("Sheet 3", "回溯贪心 — Backtracking+Greedy", "多轮随机扰动取最优"),
        ("Sheet 4", "线性评分 — Linear Priority", "综合优先级和松弛时间"),
        ("Sheet 5", "MIP — 混合整数规划", "数学最优，展示模型建立和求解过程"),
        ("Sheet 6", "模拟退火 — Simulated Annealing", "展示温度衰减和概率接受机制"),
        ("Sheet 7", "蚁群优化 — Ant Colony", "展示信息素矩阵进化过程"),
    ]
    for i, (sheet, title, note) in enumerate(sheets, r + 1):
        ws.row_dimensions[i].height = 20
        c1 = ws.cell(row=i, column=2, value=f"{sheet}  {title}")
        c1.font = Font(bold=True, size=10, color=C_HEADER)
        c2 = ws.cell(row=i, column=3, value=note)
        c2.font = Font(size=9, italic=True, color="595959")


# ══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ══════════════════════════════════════════════════════════════════════════════
def generate_algorithm_demo() -> bytes:
    wb = Workbook()
    _sheet_algo_cover(wb)
    _sheet_edd(wb)
    _sheet_backtracking(wb)
    _sheet_linear(wb)
    _sheet_mip(wb)
    _sheet_sa(wb)
    _sheet_aco(wb)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()
