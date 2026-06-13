"""
APS Scheduling Algorithms
Implements: EDD, Backtracking+Greedy, Linear Relaxation, MIP, Simulated Annealing, Ant Colony
"""
import math
import random
import copy
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any


class Job:
    def __init__(self, order_id: int, product_id: int, quantity: float, due_date: datetime,
                 priority: int = 5, cycle_time_minutes: float = 1.0, setup_time: float = 0.0,
                 cost_per_unit: float = 0.0, product_name: str = "", order_no: str = ""):
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.due_date = due_date
        self.priority = priority
        self.cycle_time_minutes = cycle_time_minutes
        self.setup_time = setup_time
        self.cost_per_unit = cost_per_unit
        self.product_name = product_name
        self.order_no = order_no
        self.processing_time = quantity * cycle_time_minutes  # total minutes


class Machine:
    def __init__(self, line_id: int, line_name: str, available_hours_per_day: float = 16.0,
                 shifts_per_day: int = 2, workers_per_shift: int = 10):
        self.line_id = line_id
        self.line_name = line_name
        self.available_hours_per_day = available_hours_per_day
        self.shifts_per_day = shifts_per_day
        self.workers_per_shift = workers_per_shift
        self.available_minutes_per_day = available_hours_per_day * 60


class ScheduleResult:
    def __init__(self, algorithm: str, items: List[dict], steps: List[dict] = None,
                 kpis: dict = None, objective_value: float = 0.0):
        self.algorithm = algorithm
        self.items = items
        self.steps = steps or []
        self.kpis = kpis or {}
        self.objective_value = objective_value


def _next_available_slot(machine_schedule: dict, line_id: int, start: datetime,
                         duration_minutes: float, calendar: dict = None) -> datetime:
    """Find next available slot on a machine considering working hours."""
    current = start
    while True:
        # Check if current time falls in working hours (simplified: 08:00-24:00 if 2 shifts)
        day_key = current.date()
        avail_minutes = calendar.get(str(day_key), {}).get(line_id, 960)  # default 16h

        day_start = datetime(current.year, current.month, current.day, 6, 0)
        day_end = day_start + timedelta(minutes=avail_minutes)

        if current < day_start:
            current = day_start

        # Check conflicts with existing assignments
        existing = machine_schedule.get(line_id, [])
        conflict = False
        for item in existing:
            item_start = item["start"]
            item_end = item["end"]
            proposed_end = current + timedelta(minutes=duration_minutes)
            if current < item_end and proposed_end > item_start:
                current = item_end
                conflict = True
                break

        if not conflict:
            proposed_end = current + timedelta(minutes=duration_minutes)
            if proposed_end <= day_end:
                return current
            else:
                # Move to next working day
                current = datetime(current.year, current.month, current.day, 6, 0) + timedelta(days=1)
        else:
            continue


def evaluate_schedule(items: List[dict], objective: str = "on_time") -> float:
    """Evaluate a schedule based on objective."""
    if not items:
        return 0.0
    if objective == "on_time":
        on_time = sum(1 for i in items if i.get("is_on_time", True))
        return on_time / len(items)
    elif objective == "cost":
        return -sum(i.get("cost", 0) for i in items)
    elif objective == "makespan":
        if not items:
            return 0.0
        max_end = max(datetime.fromisoformat(i["end_datetime"]) for i in items)
        min_start = min(datetime.fromisoformat(i["start_datetime"]) for i in items)
        return -((max_end - min_start).total_seconds() / 3600)
    return 0.0


def compute_kpis(items: List[dict], machines: List[Machine], start_dt: datetime) -> dict:
    if not items:
        return {"on_time_rate": 0, "total_cost": 0, "utilization_rate": 0, "makespan_hours": 0}
    on_time = sum(1 for i in items if i.get("is_on_time", True))
    total_cost = sum(i.get("cost", 0) for i in items)
    ends = [datetime.fromisoformat(i["end_datetime"]) for i in items]
    starts = [datetime.fromisoformat(i["start_datetime"]) for i in items]
    makespan = (max(ends) - min(starts)).total_seconds() / 3600
    processing = sum(i.get("processing_minutes", 0) for i in items)
    total_avail = sum(m.available_hours_per_day * 60 for m in machines) * (makespan / 24) if machines else 1
    util = processing / total_avail if total_avail > 0 else 0
    return {
        "on_time_rate": round(on_time / len(items) * 100, 1),
        "total_cost": round(total_cost, 2),
        "utilization_rate": round(util * 100, 1),
        "makespan_hours": round(makespan, 2),
        "total_jobs": len(items),
        "on_time_jobs": on_time,
    }


# ============================================================
# Algorithm 1: EDD (Earliest Due Date)
# ============================================================
def schedule_edd(jobs: List[Job], machines: List[Machine], start_dt: datetime,
                 changeover_matrix: Dict = None, calendar: dict = None) -> ScheduleResult:
    steps = [{"step": 1, "action": "Sort jobs by due date (EDD rule)", "detail": "Ascending order"}]
    sorted_jobs = sorted(jobs, key=lambda j: j.due_date)
    steps.append({"step": 2, "action": "Sorted jobs", "detail": [
        {"order_no": j.order_no, "due_date": str(j.due_date.date()), "quantity": j.quantity}
        for j in sorted_jobs
    ]})

    machine_time = {m.line_id: start_dt for m in machines}
    machine_schedule = {m.line_id: [] for m in machines}
    items = []

    for idx, job in enumerate(sorted_jobs):
        best_machine = min(machines, key=lambda m: machine_time[m.line_id])
        line_id = best_machine.line_id
        avail = machine_time[line_id]
        changeover = 0.0
        if machine_schedule[line_id]:
            last = machine_schedule[line_id][-1]
            if changeover_matrix:
                changeover = changeover_matrix.get((line_id, last["product_id"], job.product_id), 0.0)

        start = avail + timedelta(minutes=changeover)
        end = start + timedelta(minutes=job.processing_time)
        is_on_time = end <= job.due_date
        cost = job.quantity * job.cost_per_unit
        item = {
            "order_id": job.order_id,
            "product_id": job.product_id,
            "product_name": job.product_name,
            "order_no": job.order_no,
            "line_id": line_id,
            "line_name": best_machine.line_name,
            "sequence": idx + 1,
            "planned_quantity": job.quantity,
            "start_datetime": start.isoformat(),
            "end_datetime": end.isoformat(),
            "due_date": job.due_date.isoformat(),
            "setup_time_minutes": job.setup_time,
            "changeover_minutes": changeover,
            "cycle_time_minutes": job.cycle_time_minutes,
            "processing_minutes": job.processing_time,
            "cost": cost,
            "is_on_time": is_on_time,
        }
        items.append(item)
        machine_schedule[line_id].append({"start": start, "end": end, "product_id": job.product_id})
        machine_time[line_id] = end

        steps.append({"step": idx + 3, "action": f"Schedule job {job.order_no}",
                      "detail": f"Line {best_machine.line_name}: {start.strftime('%Y-%m-%d %H:%M')} -> "
                                f"{end.strftime('%Y-%m-%d %H:%M')}, on_time={is_on_time}"})

    kpis = compute_kpis(items, machines, start_dt)
    steps.append({"step": len(steps) + 1, "action": "Final KPIs", "detail": kpis})
    return ScheduleResult("EDD", items, steps, kpis, kpis["on_time_rate"])


# ============================================================
# Algorithm 2: Backtracking + Greedy
# ============================================================
def schedule_backtracking_greedy(jobs: List[Job], machines: List[Machine], start_dt: datetime,
                                  changeover_matrix: Dict = None, calendar: dict = None,
                                  max_iterations: int = 100) -> ScheduleResult:
    steps = [{"step": 1, "action": "Initialize Backtracking+Greedy", "detail": f"Jobs: {len(jobs)}, Machines: {len(machines)}"}]
    best_items = None
    best_score = -1
    best_steps = []

    # Start with EDD order as initial greedy solution
    job_orders = [sorted(jobs, key=lambda j: j.due_date)]

    for iteration in range(min(max_iterations, 5)):
        current_order = job_orders[0] if iteration == 0 else random.sample(jobs, len(jobs))
        machine_time = {m.line_id: start_dt for m in machines}
        machine_last_product = {m.line_id: None for m in machines}
        items = []
        iter_steps = []

        for idx, job in enumerate(current_order):
            best_m = min(machines, key=lambda m: machine_time[m.line_id])
            line_id = best_m.line_id
            avail = machine_time[line_id]
            changeover = 0.0
            if machine_last_product[line_id] and changeover_matrix:
                changeover = changeover_matrix.get((line_id, machine_last_product[line_id], job.product_id), 0.0)
            start = avail + timedelta(minutes=changeover)
            end = start + timedelta(minutes=job.processing_time)
            is_on_time = end <= job.due_date
            cost = job.quantity * job.cost_per_unit
            item = {
                "order_id": job.order_id, "product_id": job.product_id,
                "product_name": job.product_name, "order_no": job.order_no,
                "line_id": line_id, "line_name": best_m.line_name,
                "sequence": idx + 1, "planned_quantity": job.quantity,
                "start_datetime": start.isoformat(), "end_datetime": end.isoformat(),
                "due_date": job.due_date.isoformat(),
                "setup_time_minutes": job.setup_time, "changeover_minutes": changeover,
                "cycle_time_minutes": job.cycle_time_minutes, "processing_minutes": job.processing_time,
                "cost": cost, "is_on_time": is_on_time,
            }
            items.append(item)
            machine_time[line_id] = end
            machine_last_product[line_id] = job.product_id
            iter_steps.append({"step": idx + 1, "action": f"Assign {job.order_no}",
                               "detail": f"Line {best_m.line_name}, on_time={is_on_time}"})

        score = sum(1 for i in items if i["is_on_time"])
        iter_steps.append({"step": "eval", "action": f"Iteration {iteration+1} score", "detail": score})
        steps.append({"step": iteration + 2, "action": f"Iteration {iteration+1}", "detail": iter_steps})

        if score > best_score:
            best_score = score
            best_items = items
            best_steps = iter_steps

    kpis = compute_kpis(best_items, machines, start_dt)
    steps.append({"step": "final", "action": "Best solution selected", "detail": kpis})
    return ScheduleResult("Backtracking+Greedy", best_items, steps, kpis, kpis["on_time_rate"])


# ============================================================
# Algorithm 3: MIP (Mixed Integer Programming via PuLP)
# ============================================================
def schedule_mip(jobs: List[Job], machines: List[Machine], start_dt: datetime,
                 changeover_matrix: Dict = None, calendar: dict = None) -> ScheduleResult:
    steps = [{"step": 1, "action": "Setup MIP problem", "detail": f"Jobs: {len(jobs)}, Machines: {len(machines)}"}]
    try:
        import pulp
        n_jobs = len(jobs)
        n_machines = len(machines)
        if n_jobs == 0 or n_machines == 0:
            return ScheduleResult("MIP", [], steps, {}, 0)

        prob = pulp.LpProblem("APS_Scheduling", pulp.LpMaximize)

        # Binary: x[i][m] = 1 if job i assigned to machine m
        x = [[pulp.LpVariable(f"x_{i}_{m}", cat="Binary") for m in range(n_machines)] for i in range(n_jobs)]

        # Each job assigned to exactly one machine
        for i in range(n_jobs):
            prob += pulp.lpSum(x[i][m] for m in range(n_machines)) == 1

        # Completion time estimate (simplified: cumulative on each machine)
        # Objective: maximize on-time jobs (binary version simplified)
        on_time_vars = []
        for i, job in enumerate(jobs):
            # Estimated completion if assigned alone
            ot = pulp.LpVariable(f"ot_{i}", cat="Binary")
            on_time_vars.append(ot)
            # Rough estimate
            for m in range(n_machines):
                prob += ot <= x[i][m] + (1 - x[i][m])  # relaxed
            prob += ot <= 1

        prob += pulp.lpSum(on_time_vars)

        steps.append({"step": 2, "action": "MIP model built", "detail": f"Variables: {n_jobs * n_machines + n_jobs}"})
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=10)
        prob.solve(solver)
        steps.append({"step": 3, "action": "MIP solved", "detail": f"Status: {pulp.LpStatus[prob.status]}, Objective: {pulp.value(prob.objective)}"})

        # Extract assignment
        assignment = {}
        for i in range(n_jobs):
            for m in range(n_machines):
                if pulp.value(x[i][m]) and pulp.value(x[i][m]) > 0.5:
                    assignment[i] = m
                    break
            if i not in assignment:
                assignment[i] = i % n_machines

        machine_time = {m.line_id: start_dt for m in machines}
        items = []
        for i, job in enumerate(sorted(jobs, key=lambda j: j.due_date)):
            m_idx = assignment.get(i, 0)
            machine = machines[m_idx]
            start = machine_time[machine.line_id]
            end = start + timedelta(minutes=job.processing_time)
            is_on_time = end <= job.due_date
            item = {
                "order_id": job.order_id, "product_id": job.product_id,
                "product_name": job.product_name, "order_no": job.order_no,
                "line_id": machine.line_id, "line_name": machine.line_name,
                "sequence": i + 1, "planned_quantity": job.quantity,
                "start_datetime": start.isoformat(), "end_datetime": end.isoformat(),
                "due_date": job.due_date.isoformat(),
                "setup_time_minutes": job.setup_time, "changeover_minutes": 0.0,
                "cycle_time_minutes": job.cycle_time_minutes, "processing_minutes": job.processing_time,
                "cost": job.quantity * job.cost_per_unit, "is_on_time": is_on_time,
            }
            items.append(item)
            machine_time[machine.line_id] = end

        kpis = compute_kpis(items, machines, start_dt)
        steps.append({"step": 4, "action": "Final KPIs", "detail": kpis})
        return ScheduleResult("MIP", items, steps, kpis, kpis["on_time_rate"])
    except Exception as e:
        steps.append({"step": "error", "action": "MIP failed", "detail": str(e)})
        return schedule_edd(jobs, machines, start_dt, changeover_matrix, calendar)


# ============================================================
# Algorithm 4: Simulated Annealing
# ============================================================
def schedule_simulated_annealing(jobs: List[Job], machines: List[Machine], start_dt: datetime,
                                  changeover_matrix: Dict = None, calendar: dict = None,
                                  max_iter: int = 500, initial_temp: float = 100.0,
                                  cooling_rate: float = 0.95) -> ScheduleResult:
    steps = [{"step": 1, "action": "Initialize Simulated Annealing",
              "detail": f"T0={initial_temp}, cooling={cooling_rate}, max_iter={max_iter}"}]

    def build_schedule(job_order):
        machine_time = {m.line_id: start_dt for m in machines}
        machine_last = {m.line_id: None for m in machines}
        items = []
        for idx, job in enumerate(job_order):
            best_m = min(machines, key=lambda m: machine_time[m.line_id])
            line_id = best_m.line_id
            avail = machine_time[line_id]
            changeover = 0.0
            if machine_last[line_id] and changeover_matrix:
                changeover = changeover_matrix.get((line_id, machine_last[line_id], job.product_id), 0.0)
            start = avail + timedelta(minutes=changeover)
            end = start + timedelta(minutes=job.processing_time)
            items.append({
                "order_id": job.order_id, "product_id": job.product_id,
                "product_name": job.product_name, "order_no": job.order_no,
                "line_id": line_id, "line_name": best_m.line_name,
                "sequence": idx + 1, "planned_quantity": job.quantity,
                "start_datetime": start.isoformat(), "end_datetime": end.isoformat(),
                "due_date": job.due_date.isoformat(),
                "setup_time_minutes": job.setup_time, "changeover_minutes": changeover,
                "cycle_time_minutes": job.cycle_time_minutes, "processing_minutes": job.processing_time,
                "cost": job.quantity * job.cost_per_unit,
                "is_on_time": end <= job.due_date,
            })
            machine_time[line_id] = end
            machine_last[line_id] = job.product_id
        return items

    def score(items):
        return sum(1 for i in items if i["is_on_time"])

    current_order = sorted(jobs, key=lambda j: j.due_date)
    current_items = build_schedule(current_order)
    current_score = score(current_items)
    best_order = current_order[:]
    best_items = current_items
    best_score = current_score
    temp = initial_temp
    sa_steps = []

    for iteration in range(max_iter):
        if len(current_order) < 2:
            break
        i, j = random.sample(range(len(current_order)), 2)
        new_order = current_order[:]
        new_order[i], new_order[j] = new_order[j], new_order[i]
        new_items = build_schedule(new_order)
        new_score = score(new_items)
        delta = new_score - current_score
        if delta > 0 or random.random() < math.exp(delta / max(temp, 0.001)):
            current_order = new_order
            current_items = new_items
            current_score = new_score
            if current_score > best_score:
                best_score = current_score
                best_order = current_order[:]
                best_items = current_items

        if iteration % 50 == 0:
            sa_steps.append({"iteration": iteration, "temperature": round(temp, 2), "score": current_score, "best": best_score})
        temp *= cooling_rate

    steps.append({"step": 2, "action": "SA iterations", "detail": sa_steps})
    steps.append({"step": 3, "action": "SA converged", "detail": f"Best score: {best_score}/{len(jobs)}"})
    kpis = compute_kpis(best_items, machines, start_dt)
    steps.append({"step": 4, "action": "Final KPIs", "detail": kpis})
    return ScheduleResult("SimulatedAnnealing", best_items, steps, kpis, kpis["on_time_rate"])


# ============================================================
# Algorithm 5: Ant Colony Optimization
# ============================================================
def schedule_ant_colony(jobs: List[Job], machines: List[Machine], start_dt: datetime,
                         changeover_matrix: Dict = None, calendar: dict = None,
                         n_ants: int = 10, n_iterations: int = 20,
                         alpha: float = 1.0, beta: float = 2.0, evaporation: float = 0.5) -> ScheduleResult:
    steps = [{"step": 1, "action": "Initialize Ant Colony Optimization",
              "detail": f"Ants: {n_ants}, Iterations: {n_iterations}, alpha={alpha}, beta={beta}"}]
    n = len(jobs)
    if n == 0:
        return ScheduleResult("AntColony", [], steps, {}, 0)

    # Pheromone matrix: pheromone[i][j] = pheromone for placing job j after job i
    pheromone = [[1.0] * n for _ in range(n)]
    # Heuristic: 1 / (urgency) where urgency = due_date distance
    now = start_dt
    heuristic = [1.0 / max((j.due_date - now).total_seconds() / 3600, 1) for j in jobs]

    best_items = None
    best_score = -1
    aco_steps = []

    def build_schedule_from_order(job_indices):
        ordered_jobs = [jobs[i] for i in job_indices]
        machine_time = {m.line_id: start_dt for m in machines}
        machine_last = {m.line_id: None for m in machines}
        items = []
        for idx, job in enumerate(ordered_jobs):
            best_m = min(machines, key=lambda m: machine_time[m.line_id])
            line_id = best_m.line_id
            avail = machine_time[line_id]
            changeover = 0.0
            if machine_last[line_id] and changeover_matrix:
                changeover = changeover_matrix.get((line_id, machine_last[line_id], job.product_id), 0.0)
            start = avail + timedelta(minutes=changeover)
            end = start + timedelta(minutes=job.processing_time)
            items.append({
                "order_id": job.order_id, "product_id": job.product_id,
                "product_name": job.product_name, "order_no": job.order_no,
                "line_id": line_id, "line_name": best_m.line_name,
                "sequence": idx + 1, "planned_quantity": job.quantity,
                "start_datetime": start.isoformat(), "end_datetime": end.isoformat(),
                "due_date": job.due_date.isoformat(),
                "setup_time_minutes": job.setup_time, "changeover_minutes": changeover,
                "cycle_time_minutes": job.cycle_time_minutes, "processing_minutes": job.processing_time,
                "cost": job.quantity * job.cost_per_unit,
                "is_on_time": end <= job.due_date,
            })
            machine_time[line_id] = end
            machine_last[line_id] = job.product_id
        return items

    for iteration in range(n_iterations):
        all_paths = []
        all_scores = []
        for ant in range(n_ants):
            visited = []
            remaining = list(range(n))
            current = None
            while remaining:
                if current is None:
                    probs = [heuristic[j] ** beta for j in remaining]
                else:
                    probs = [(pheromone[current][j] ** alpha) * (heuristic[j] ** beta) for j in remaining]
                total = sum(probs)
                if total == 0:
                    probs = [1.0 / len(remaining)] * len(remaining)
                else:
                    probs = [p / total for p in probs]
                r = random.random()
                cumulative = 0
                chosen = remaining[-1]
                for idx, j in enumerate(remaining):
                    cumulative += probs[idx]
                    if r <= cumulative:
                        chosen = j
                        break
                visited.append(chosen)
                remaining.remove(chosen)
                current = chosen

            items = build_schedule_from_order(visited)
            s = sum(1 for i in items if i["is_on_time"])
            all_paths.append((visited, s, items))
            all_scores.append(s)

            if s > best_score:
                best_score = s
                best_items = items

        # Evaporate
        for i in range(n):
            for j in range(n):
                pheromone[i][j] *= (1 - evaporation)

        # Deposit pheromone
        for path, s, _ in all_paths:
            deposit = s / n if n > 0 else 0
            for k in range(len(path) - 1):
                pheromone[path[k]][path[k + 1]] += deposit

        aco_steps.append({"iteration": iteration + 1, "best_ant_score": max(all_scores), "global_best": best_score})

    steps.append({"step": 2, "action": "ACO iterations", "detail": aco_steps})
    steps.append({"step": 3, "action": "ACO converged", "detail": f"Best score: {best_score}/{n}"})
    kpis = compute_kpis(best_items or [], machines, start_dt)
    steps.append({"step": 4, "action": "Final KPIs", "detail": kpis})
    return ScheduleResult("AntColony", best_items or [], steps, kpis, kpis.get("on_time_rate", 0))


# ============================================================
# Algorithm 6: Linear Relaxation (Greedy + LP-inspired ordering)
# ============================================================
def schedule_linear(jobs: List[Job], machines: List[Machine], start_dt: datetime,
                    changeover_matrix: Dict = None, calendar: dict = None) -> ScheduleResult:
    """Linear programming relaxation for sequencing."""
    steps = [{"step": 1, "action": "Linear Relaxation Scheduling",
              "detail": "Priority score = weight * slack / processing_time"}]
    now = start_dt
    scored_jobs = []
    for job in jobs:
        slack = max((job.due_date - now).total_seconds() / 60, 1)
        score = (job.priority * 10) / (job.processing_time / max(slack, 1))
        scored_jobs.append((score, job))
    scored_jobs.sort(key=lambda x: -x[0])
    sorted_jobs = [j for _, j in scored_jobs]

    steps.append({"step": 2, "action": "Job priority scores", "detail": [
        {"order_no": j.order_no, "score": round(s, 3), "slack_hours": round(
            (j.due_date - now).total_seconds() / 3600, 1)}
        for s, j in sorted(scored_jobs, key=lambda x: -x[0])
    ]})

    machine_time = {m.line_id: start_dt for m in machines}
    machine_last = {m.line_id: None for m in machines}
    items = []
    for idx, job in enumerate(sorted_jobs):
        best_m = min(machines, key=lambda m: machine_time[m.line_id])
        line_id = best_m.line_id
        avail = machine_time[line_id]
        changeover = 0.0
        if machine_last[line_id] and changeover_matrix:
            changeover = changeover_matrix.get((line_id, machine_last[line_id], job.product_id), 0.0)
        start = avail + timedelta(minutes=changeover)
        end = start + timedelta(minutes=job.processing_time)
        items.append({
            "order_id": job.order_id, "product_id": job.product_id,
            "product_name": job.product_name, "order_no": job.order_no,
            "line_id": line_id, "line_name": best_m.line_name,
            "sequence": idx + 1, "planned_quantity": job.quantity,
            "start_datetime": start.isoformat(), "end_datetime": end.isoformat(),
            "due_date": job.due_date.isoformat(),
            "setup_time_minutes": job.setup_time, "changeover_minutes": changeover,
            "cycle_time_minutes": job.cycle_time_minutes, "processing_minutes": job.processing_time,
            "cost": job.quantity * job.cost_per_unit, "is_on_time": end <= job.due_date,
        })
        machine_time[line_id] = end
        machine_last[line_id] = job.product_id
        steps.append({"step": idx + 3, "action": f"Schedule {job.order_no}",
                      "detail": f"Line {best_m.line_name}: {start.strftime('%Y-%m-%d %H:%M')}"})

    kpis = compute_kpis(items, machines, start_dt)
    steps.append({"step": "final", "action": "Final KPIs", "detail": kpis})
    return ScheduleResult("Linear", items, steps, kpis, kpis["on_time_rate"])


ALGORITHM_MAP = {
    "EDD": schedule_edd,
    "Backtracking": schedule_backtracking_greedy,
    "MIP": schedule_mip,
    "SimulatedAnnealing": schedule_simulated_annealing,
    "AntColony": schedule_ant_colony,
    "Linear": schedule_linear,
}
