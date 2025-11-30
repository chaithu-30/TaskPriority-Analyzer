from datetime import date, datetime, timedelta
import calendar


def is_weekend(check_date):
    return check_date.weekday() >= 5


def get_common_holidays(year):
    holidays = [
        date(year, 1, 1),
        date(year, 7, 4),
        date(year, 12, 25)
    ]
    
    nov_calendar = calendar.monthcalendar(year, 11)
    thanksgiving_week = nov_calendar[3]
    if thanksgiving_week[3] == 0:
        thanksgiving_week = nov_calendar[4]
    holidays.append(date(year, 11, thanksgiving_week[3]))
    
    return holidays


def is_working_day(check_date, holidays=None):
    if holidays is None:
        holidays = get_common_holidays(check_date.year)
    
    if check_date.year not in [h.year for h in holidays]:
        holidays = get_common_holidays(check_date.year)
    
    return not is_weekend(check_date) and check_date not in holidays


def get_working_days_remaining(due_date, start_date=None):
    if start_date is None:
        start_date = date.today()
    
    if due_date < start_date:
        return 0
    
    working_days = 0
    current = start_date
    
    holidays = get_common_holidays(start_date.year)
    if due_date.year > start_date.year:
        holidays.extend(get_common_holidays(due_date.year))
    
    while current < due_date:
        if is_working_day(current, holidays):
            working_days += 1
        current += timedelta(days=1)
    
    return working_days


def detect_cycles(tasks):
    graph = {}
    for t in tasks:
        task_id = t.get('id')
        if task_id is None:
            continue
        graph[task_id] = t.get('dependencies', [])
    
    visited = set()
    rec_stack = set()
    cycles = set()

    def dfs(node):
        if node not in graph:
            return False
            
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor_id in graph.get(node, []):
            if neighbor_id in graph:
                if neighbor_id not in visited:
                    if dfs(neighbor_id):
                        cycles.add(node)
                        return True
                elif neighbor_id in rec_stack:
                    cycles.add(node)
                    cycles.add(neighbor_id)
                    return True
        
        rec_stack.remove(node)
        return False

    for task_id in graph:
        if task_id not in visited:
            dfs(task_id)
            
    return cycles


def calculate_base_score(task, strategy='smart_balance'):
    score = 0.0
    today = date.today()
    
    due_date = task.get('due_date')
    if isinstance(due_date, str):
        try:
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        except ValueError:
            due_date = today + timedelta(days=30)
    elif due_date is None:
        due_date = today + timedelta(days=30)
    
    days_until_due = (due_date - today).days
    working_days_left = get_working_days_remaining(due_date, today)
    importance = max(1, min(10, task.get('importance', 5)))
    hours = task.get('estimated_hours', 1)
    
    if strategy == 'deadline_driven':
        if days_until_due < 0:
            score += 150 + min(50, abs(days_until_due) * 5)
        elif days_until_due == 0:
            if is_working_day(today):
                score += 120
            else:
                score += 130
        elif working_days_left <= 1:
            score += 100
        elif working_days_left <= 3:
            score += 80
        elif working_days_left <= 7:
            score += 60
        else:
            score += max(0, 40 - (working_days_left // 3))
        
        if is_weekend(due_date) and days_until_due > 0:
            score += 5
            
        score += importance * 3
        
        if hours <= 1:
            score += 10
        elif hours <= 3:
            score += 5
    
    elif strategy == 'fastest_wins':
        if days_until_due < 0:
            score += 80 + min(40, abs(days_until_due) * 3)
        elif days_until_due == 0:
            score += 70
        elif working_days_left <= 1:
            score += 60
        elif working_days_left <= 3:
            score += 40
        elif working_days_left <= 7:
            score += 25
        else:
            score += max(0, 15 - (working_days_left // 7))
        
        score += importance * 4
        
        if hours <= 1:
            score += 40
        elif hours <= 2:
            score += 25
        elif hours <= 3:
            score += 15
        elif hours <= 5:
            score += 5
    
    elif strategy == 'high_impact':
        if days_until_due < 0:
            score += 90 + min(40, abs(days_until_due) * 4)
        elif days_until_due == 0:
            if is_working_day(today):
                score += 80
            else:
                score += 85
        elif working_days_left <= 1:
            score += 70
        elif working_days_left <= 3:
            score += 50
        elif working_days_left <= 7:
            score += 30
        else:
            score += max(0, 20 - (working_days_left // 5))
        
        if is_weekend(due_date) and days_until_due > 0:
            score += 5
        
        score += importance * 10
        
        if hours <= 1:
            score += 10
        elif hours <= 3:
            score += 5
    
    else:
        if days_until_due < 0:
            score += 100 + min(50, abs(days_until_due) * 5)
        elif days_until_due == 0:
            if is_working_day(today):
                score += 90
            else:
                score += 100
        elif working_days_left <= 1:
            score += 80
        elif working_days_left <= 3:
            score += 60
        elif working_days_left <= 7:
            score += 40
        else:
            score += max(0, 25 - (working_days_left // 5))
        
        if is_weekend(due_date) and days_until_due > 0:
            score += 5
            
        score += importance * 6
        
        if hours <= 1:
            score += 15
        elif hours <= 3:
            score += 5
        
    return round(score, 2)


def calculate_priority_score(task, all_tasks=None, strategy='smart_balance'):
    return calculate_base_score(task, strategy)


def analyze_all_tasks(tasks, strategy='smart_balance'):
    if not tasks:
        return []
    
    for i, task in enumerate(tasks):
        if 'id' not in task:
            task['id'] = i
        
        deps = task.get('dependencies')
        if deps is None:
            task['dependencies'] = []
        elif not isinstance(deps, list):
            task['dependencies'] = []
        else:
            task['dependencies'] = [d for d in deps if d is not None]
    
    for task in tasks:
        task['raw_score'] = calculate_base_score(task, strategy)
        task['priority_score'] = task['raw_score']
        task['explanation'] = _generate_base_explanation(task, strategy)

    cycle_ids = detect_cycles(tasks)
    
    for iteration in range(3):
        changed = False
        current_scores = {t['id']: t['priority_score'] for t in tasks}
        
        for task in tasks:
            task_id = task['id']
            blocking_for = [t for t in tasks if task_id in t.get('dependencies', [])]
            
            inherited = 0
            for dependent in blocking_for:
                dep_score = current_scores.get(dependent['id'], 0)
                inherited += dep_score * 0.5
            
            if inherited > 0:
                new_score = task['raw_score'] + inherited
                if new_score > task['priority_score'] and new_score < 1000:
                    task['priority_score'] = round(new_score, 2)
                    changed = True
        
        if not changed:
            break

    task_map = {t['id']: t for t in tasks}
    
    for task in tasks:
        if task['id'] in cycle_ids:
            task['priority_score'] = 999.0
            task['explanation'] = "CIRCULAR DEPENDENCY DETECTED - Resolve Immediately"
            continue
            
        deps = task.get('dependencies', [])
        blockers = [d for d in deps if d is not None and d in task_map]
        
        if blockers:
            task['explanation'] = f"Blocked by {len(blockers)} task(s). " + task['explanation']
            
        if task['priority_score'] > task['raw_score'] + 1:
            boost = int(task['priority_score'] - task['raw_score'])
            task['explanation'] += f" (Includes +{boost}pts from downstream dependencies)"
            
    return tasks


def _generate_base_explanation(task, strategy='smart_balance'):
    due = task.get('due_date')
    due_date_obj = None
    
    if isinstance(due, str):
        try:
            due_date_obj = datetime.strptime(due, '%Y-%m-%d').date()
        except:
            pass
    elif isinstance(due, date):
        due_date_obj = due
        
    if not due_date_obj:
        return f"Due date unknown (Imp: {task.get('importance', 5)})"
        
    days_remaining = (due_date_obj - date.today()).days
    working_days_remaining = get_working_days_remaining(due_date_obj)
    importance = task.get('importance', 5)
    
    strategy_names = {
        'smart_balance': 'Smart Balance',
        'fastest_wins': 'Fastest Wins',
        'high_impact': 'High Impact',
        'deadline_driven': 'Deadline Driven'
    }
    strategy_name = strategy_names.get(strategy, 'Smart Balance')
    
    if days_remaining < 0:
        msg = f"Overdue by {abs(days_remaining)} days"
    elif days_remaining == 0:
        if is_working_day(date.today()):
            msg = "Due today"
        else:
            msg = "Due today (weekend/holiday)"
    elif working_days_remaining <= 1:
        if is_weekend(due_date_obj):
            msg = f"Due in {working_days_remaining} working day (falls on weekend)"
        else:
            msg = f"Due in {working_days_remaining} working day"
    elif working_days_remaining <= 3:
        msg = f"Due in {working_days_remaining} working days"
    else:
        msg = f"Due {due_date_obj.isoformat()} ({working_days_remaining} working days)"
    
    return f"{msg} (Imp: {importance}, {strategy_name})"


def detect_circular_dependencies(tasks):
    cycle_ids = detect_cycles(tasks)
    task_map = {t.get('id'): t for t in tasks}
    result = []
    for task_id in cycle_ids:
        task = task_map.get(task_id)
        if task:
            result.append(task.get('title', f"Task {task_id}"))
    return result


def generate_explanation(task, score, strategy):
    reasons = []
    
    due_date = task.get('due_date')
    if isinstance(due_date, str):
        try:
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        except ValueError:
            due_date = date.today() + timedelta(days=30)
    
    days_left = (due_date - date.today()).days if isinstance(due_date, date) else 0
    
    if days_left < 0:
        reasons.append(f"Overdue by {abs(days_left)} days")
    elif days_left == 0:
        reasons.append("Due today")
    elif days_left <= 2:
        reasons.append("Due very soon")
    
    if task.get('importance', 5) >= 8:
        reasons.append("High importance rating")
    
    if task.get('estimated_hours', 1) <= 2:
        reasons.append("Quick win opportunity")
    
    if not reasons:
        reasons.append(f"Balanced priority using {strategy} strategy")
    
    return " • ".join(reasons)
