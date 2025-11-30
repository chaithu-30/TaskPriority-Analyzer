from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import date, datetime
from .scoring import analyze_all_tasks, detect_cycles, detect_circular_dependencies
from .serializers import TaskAnalysisInputSerializer


def build_dependency_graph(tasks, circular_ids):
    task_lookup = {t['id']: t for t in tasks}
    nodes = []
    edges = []
    
    for task in tasks:
        task_id = task['id']
        in_cycle = task_id in circular_ids
        
        nodes.append({
            'id': task_id,
            'title': task.get('title', f'Task {task_id}'),
            'score': task.get('priority_score', 0),
            'is_circular': in_cycle
        })
        
        for dep_id in task.get('dependencies', []):
            if dep_id in task_lookup:
                edge_in_cycle = task_id in circular_ids and dep_id in circular_ids
                edges.append({
                    'from': dep_id,
                    'to': task_id,
                    'is_circular': edge_in_cycle
                })
    
    return {'nodes': nodes, 'edges': edges}


@api_view(['POST'])
def analyze_tasks(request):
    tasks = request.data.get('tasks', [])
    strategy = request.data.get('strategy', 'smart_balance')
    
    if not tasks:
        return Response({'error': 'No tasks provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = TaskAnalysisInputSerializer(data=tasks, many=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    validated_tasks = serializer.validated_data
    
    analyzed = analyze_all_tasks(validated_tasks, strategy)
    
    cycle_ids = detect_cycles(analyzed)
    cycle_names = [
        t.get('title', f"Task {t.get('id')}") 
        for t in analyzed 
        if t.get('id') in cycle_ids
    ]
    
    analyzed.sort(key=lambda x: x['priority_score'], reverse=True)
    
    for task in analyzed:
        if isinstance(task.get('due_date'), date):
            task['due_date'] = task['due_date'].isoformat()
            
    graph = build_dependency_graph(analyzed, cycle_ids)
    
    strategy_names = {
        'smart_balance': 'Smart Balance',
        'fastest_wins': 'Fastest Wins',
        'high_impact': 'High Impact',
        'deadline_driven': 'Deadline Driven'
    }
    
    return Response({
        'tasks': analyzed,
        'strategy_used': strategy_names.get(strategy, 'Smart Balance'),
        'circular_dependencies': list(cycle_names),
        'total_tasks': len(analyzed),
        'dependency_graph': graph
    })


@api_view(['GET', 'POST'])
def suggest_tasks(request):
    if request.method == 'POST':
        tasks = request.data.get('tasks', [])
        strategy = request.data.get('strategy', 'smart_balance')
        
        if not tasks:
            return Response({'error': 'No tasks provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = TaskAnalysisInputSerializer(data=tasks, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated = serializer.validated_data
        analyzed = analyze_all_tasks(validated, strategy)
        
        today = date.today()
        due_today = []
        
        for task in analyzed:
            task_due = task.get('due_date')
            
            if isinstance(task_due, str):
                try:
                    task_due = datetime.strptime(task_due, '%Y-%m-%d').date()
                except ValueError:
                    continue
            elif not isinstance(task_due, date):
                continue
            
            if task_due == today:
                due_today.append(task)
        
        due_today.sort(key=lambda x: x['priority_score'], reverse=True)
        suggestions = due_today[:3]
        
        for task in suggestions:
            if isinstance(task.get('due_date'), date):
                task['due_date'] = task['due_date'].isoformat()
        
        strategy_names = {
            'smart_balance': 'Smart Balance',
            'fastest_wins': 'Fastest Wins',
            'high_impact': 'High Impact',
            'deadline_driven': 'Deadline Driven'
        }
        
        return Response({
            'suggestions': suggestions,
            'strategy_used': strategy_names.get(strategy, 'Smart Balance'),
            'total_tasks_due_today': len(due_today),
            'message': f'Found {len(due_today)} task(s) due today, showing top {len(suggestions)}'
        })
    
    return Response({'message': 'Send POST request with tasks data'})


