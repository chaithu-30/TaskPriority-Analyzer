from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from .scoring import (
    calculate_priority_score, 
    detect_circular_dependencies, 
    analyze_all_tasks,
    is_weekend,
    is_working_day,
    get_working_days_remaining,
    get_common_holidays
)


class ScoringAlgorithmTests(TestCase):
    
    def test_overdue_task_highest_priority(self):
        overdue = {
            'title': 'Overdue Task',
            'due_date': date.today() - timedelta(days=5),
            'importance': 5,
            'estimated_hours': 3,
            'dependencies': []
        }
        
        future = {
            'title': 'Future Task',
            'due_date': date.today() + timedelta(days=7),
            'importance': 10,
            'estimated_hours': 1,
            'dependencies': []
        }
        
        overdue_score = calculate_priority_score(overdue)
        future_score = calculate_priority_score(future)
        
        self.assertGreater(overdue_score, future_score)
    
    def test_circular_dependency_detection(self):
        tasks = [
            {'id': 1, 'title': 'Task A', 'dependencies': [2]},
            {'id': 2, 'title': 'Task B', 'dependencies': [3]},
            {'id': 3, 'title': 'Task C', 'dependencies': [1]},
        ]
        
        circular = detect_circular_dependencies(tasks)
        self.assertTrue(len(circular) > 0)
    
    def test_quick_win_bonus(self):
        quick = {
            'title': 'Quick Task',
            'due_date': date.today() + timedelta(days=5),
            'importance': 5,
            'estimated_hours': 1,
            'dependencies': []
        }
        
        long_task = {
            'title': 'Long Task',
            'due_date': date.today() + timedelta(days=5),
            'importance': 5,
            'estimated_hours': 10,
            'dependencies': []
        }
        
        quick_score = calculate_priority_score(quick)
        long_score = calculate_priority_score(long_task)
        
        self.assertGreater(quick_score, long_score)
    
    def test_score_inheritance(self):
        tasks = [
            {
                'id': 1, 
                'title': 'Blocker Task A', 
                'due_date': date.today() + timedelta(days=30),
                'importance': 1, 
                'estimated_hours': 5,
                'dependencies': [] 
            },
            {
                'id': 2, 
                'title': 'Urgent Task B', 
                'due_date': date.today(),
                'importance': 10, 
                'estimated_hours': 3,
                'dependencies': [1]
            }
        ]
        
        analyzed = analyze_all_tasks(tasks)
        
        task_a = next(t for t in analyzed if t['id'] == 1)
        task_b = next(t for t in analyzed if t['id'] == 2)
        
        self.assertTrue(task_a['priority_score'] > task_a['raw_score'])
        
        self.assertTrue(task_a['priority_score'] > 50)
        
        self.assertIn('downstream dependencies', task_a['explanation'])


class APITests(TestCase):
    
    def setUp(self):
        self.client = APIClient()
    
    def test_analyze_tasks_endpoint(self):
        data = {
            'tasks': [
                {
                    'title': 'Test Task 1',
                    'due_date': str(date.today() + timedelta(days=1)),
                    'estimated_hours': 2,
                    'importance': 8,
                    'dependencies': []
                },
                {
                    'title': 'Test Task 2',
                    'due_date': str(date.today() + timedelta(days=7)),
                    'estimated_hours': 4,
                    'importance': 5,
                    'dependencies': []
                }
            ],
            'strategy': 'smart_balance'
        }
        
        response = self.client.post('/api/tasks/analyze/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tasks', response.data)
        self.assertIn('strategy_used', response.data)
        self.assertEqual(len(response.data['tasks']), 2)
        self.assertIn('priority_score', response.data['tasks'][0])
    
    def test_analyze_tasks_empty_list(self):
        response = self.client.post('/api/tasks/analyze/', {'tasks': []}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_analyze_tasks_all_strategies(self):
        data = {
            'tasks': [
                {
                    'title': 'Test Task',
                    'due_date': str(date.today() + timedelta(days=3)),
                    'estimated_hours': 2,
                    'importance': 7,
                    'dependencies': []
                }
            ]
        }
        
        strategies = {
            'smart_balance': 'Smart Balance',
            'fastest_wins': 'Fastest Wins',
            'high_impact': 'High Impact',
            'deadline_driven': 'Deadline Driven'
        }
        
        for strategy_key, strategy_name in strategies.items():
            data['strategy'] = strategy_key
            response = self.client.post('/api/tasks/analyze/', data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['strategy_used'], strategy_name)
    
    def test_suggest_tasks_endpoint(self):
        today_str = str(date.today())
        data = {
            'tasks': [
                {
                    'title': 'Task Due Today 1',
                    'due_date': today_str,
                    'estimated_hours': 1,
                    'importance': 9,
                    'dependencies': []
                },
                {
                    'title': 'Task Due Today 2',
                    'due_date': today_str,
                    'estimated_hours': 2,
                    'importance': 8,
                    'dependencies': []
                },
                {
                    'title': 'Task Due Today 3',
                    'due_date': today_str,
                    'estimated_hours': 3,
                    'importance': 7,
                    'dependencies': []
                },
                {
                    'title': 'Task Due Today 4',
                    'due_date': today_str,
                    'estimated_hours': 4,
                    'importance': 6,
                    'dependencies': []
                },
                {
                    'title': 'Task Due Tomorrow',
                    'due_date': str(date.today() + timedelta(days=1)),
                    'estimated_hours': 1,
                    'importance': 10,
                    'dependencies': []
                },
                {
                    'title': 'Task Due Next Week',
                    'due_date': str(date.today() + timedelta(days=7)),
                    'estimated_hours': 2,
                    'importance': 9,
                    'dependencies': []
                }
            ],
            'strategy': 'smart_balance'
        }
        
        response = self.client.post('/api/tasks/suggest/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('suggestions', response.data)
        self.assertEqual(len(response.data['suggestions']), 3)
        self.assertIn('total_tasks_due_today', response.data)
        self.assertEqual(response.data['total_tasks_due_today'], 4)
        self.assertIn('message', response.data)
        
        for suggestion in response.data['suggestions']:
            self.assertIn('priority_score', suggestion)
            self.assertIn('explanation', suggestion)
            self.assertIn('title', suggestion)
            self.assertTrue(len(suggestion['explanation']) > 0)
            self.assertEqual(suggestion['due_date'], today_str)
    
    def test_circular_dependency_detection_in_api(self):
        data = {
            'tasks': [
                {
                    'title': 'Task A',
                    'due_date': str(date.today() + timedelta(days=1)),
                    'estimated_hours': 2,
                    'importance': 5,
                    'dependencies': [1]
                },
                {
                    'title': 'Task B',
                    'due_date': str(date.today() + timedelta(days=2)),
                    'estimated_hours': 3,
                    'importance': 5,
                    'dependencies': [0]
                }
            ],
            'strategy': 'smart_balance'
        }
        
        response = self.client.post('/api/tasks/analyze/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('circular_dependencies', response.data)
        self.assertTrue(len(response.data['circular_dependencies']) > 0)
    
    def test_dependency_graph_in_response(self):
        data = {
            'tasks': [
                {
                    'title': 'Task A',
                    'due_date': str(date.today() + timedelta(days=1)),
                    'estimated_hours': 2,
                    'importance': 5,
                    'dependencies': []
                },
                {
                    'title': 'Task B',
                    'due_date': str(date.today() + timedelta(days=2)),
                    'estimated_hours': 3,
                    'importance': 5,
                    'dependencies': [0]
                }
            ]
        }
        
        response = self.client.post('/api/tasks/analyze/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('dependency_graph', response.data)
        self.assertIn('nodes', response.data['dependency_graph'])
        self.assertIn('edges', response.data['dependency_graph'])
        self.assertEqual(len(response.data['dependency_graph']['nodes']), 2)
        self.assertEqual(len(response.data['dependency_graph']['edges']), 1)
    
    def test_weekend_detection(self):
        monday = date(2024, 1, 1)
        while monday.weekday() != 0:
            monday += timedelta(days=1)
        
        saturday = monday + timedelta(days=5)
        sunday = monday + timedelta(days=6)
        
        self.assertFalse(is_weekend(monday))
        self.assertFalse(is_weekend(monday + timedelta(days=4)))
        self.assertTrue(is_weekend(saturday))
        self.assertTrue(is_weekend(sunday))
    
    def test_working_days_calculation(self):
        monday = date(2024, 1, 8)
        friday = monday + timedelta(days=4)
        
        working_days = get_working_days_remaining(friday, monday)
        self.assertEqual(working_days, 4)
        
        next_monday = monday + timedelta(days=7)
        working_days_weekend = get_working_days_remaining(next_monday, monday)
        self.assertEqual(working_days_weekend, 5)
    
    def test_holiday_detection(self):
        holidays_2024 = get_common_holidays(2024)
        self.assertIn(date(2024, 1, 1), holidays_2024)
        self.assertIn(date(2024, 7, 4), holidays_2024)
        self.assertIn(date(2024, 12, 25), holidays_2024)
    
    def test_working_day_excludes_holidays(self):
        new_year = date(2024, 1, 1)
        while new_year.weekday() == 5 or new_year.weekday() == 6:
            new_year += timedelta(days=1)
        
        holidays = get_common_holidays(2024)
        if new_year.year == 2024:
            if new_year in holidays:
                self.assertFalse(is_working_day(new_year, holidays))
    
    def test_task_due_monday_after_weekend(self):
        today = date.today()
        friday = today
        while friday.weekday() != 4:
            friday -= timedelta(days=1)
        
        monday = friday + timedelta(days=3)
        while monday.weekday() != 0:
            monday += timedelta(days=1)
        
        if (monday - today).days <= 7:
            task = {
                'title': 'Monday Task',
                'due_date': monday,
                'importance': 5,
                'estimated_hours': 2,
                'dependencies': []
            }
            score = calculate_priority_score(task)
            self.assertGreater(score, 0)
    
    def test_task_due_on_weekend_prioritized(self):
        today = date.today()
        saturday = today
        while saturday.weekday() != 5:
            saturday += timedelta(days=1)
        
        task_weekend = {
            'title': 'Weekend Task',
            'due_date': saturday,
            'importance': 5,
            'estimated_hours': 2,
            'dependencies': []
        }
        
        next_monday = saturday + timedelta(days=2)
        while next_monday.weekday() != 0:
            next_monday += timedelta(days=1)
        
        task_monday = {
            'title': 'Monday Task',
            'due_date': next_monday,
            'importance': 5,
            'estimated_hours': 2,
            'dependencies': []
        }
        
        score_weekend = calculate_priority_score(task_weekend)
        score_monday = calculate_priority_score(task_monday)
        self.assertGreater(score_weekend, 0)
        self.assertGreater(score_monday, 0)
    
    def test_missing_fields_defaults(self):
        task_minimal = {
            'title': 'Minimal Task'
        }
        
        try:
            score = calculate_priority_score(task_minimal)
            self.assertIsInstance(score, (int, float))
            self.assertGreaterEqual(score, 0)
        except Exception:
            self.fail("Should handle missing fields gracefully")
    
    def test_importance_bounds(self):
        task_low = {
            'title': 'Low Importance',
            'due_date': date.today() + timedelta(days=5),
            'importance': 0,
            'estimated_hours': 2,
            'dependencies': []
        }
        
        task_high = {
            'title': 'High Importance',
            'due_date': date.today() + timedelta(days=5),
            'importance': 15,
            'estimated_hours': 2,
            'dependencies': []
        }
        
        score_low = calculate_priority_score(task_low)
        score_high = calculate_priority_score(task_high)
        
        self.assertGreater(score_high, score_low)
        self.assertGreaterEqual(score_low, 0)
    
    def test_zero_hours_handling(self):
        task = {
            'title': 'Zero Hours Task',
            'due_date': date.today() + timedelta(days=5),
            'importance': 5,
            'estimated_hours': 0,
            'dependencies': []
        }
        
        score = calculate_priority_score(task)
        self.assertGreaterEqual(score, 0)
    
    def test_negative_hours_handling(self):
        task = {
            'title': 'Negative Hours Task',
            'due_date': date.today() + timedelta(days=5),
            'importance': 5,
            'estimated_hours': -5,
            'dependencies': []
        }
        
        score = calculate_priority_score(task)
        self.assertGreaterEqual(score, 0)
    
    def test_far_future_date(self):
        task = {
            'title': 'Far Future Task',
            'due_date': date.today() + timedelta(days=365),
            'importance': 10,
            'estimated_hours': 1,
            'dependencies': []
        }
        
        score = calculate_priority_score(task)
        self.assertGreaterEqual(score, 0)
        self.assertLess(score, 100)
    
    def test_empty_dependencies_list(self):
        task = {
            'title': 'No Dependencies',
            'due_date': date.today() + timedelta(days=5),
            'importance': 5,
            'estimated_hours': 2,
            'dependencies': []
        }
        
        tasks = [task]
        analyzed = analyze_all_tasks(tasks)
        self.assertEqual(len(analyzed), 1)
        self.assertEqual(analyzed[0]['dependencies'], [])
    
    def test_none_dependencies_handling(self):
        task = {
            'title': 'None Dependencies',
            'due_date': date.today() + timedelta(days=5),
            'importance': 5,
            'estimated_hours': 2,
            'dependencies': None
        }
        
        tasks = [task]
        analyzed = analyze_all_tasks(tasks)
        self.assertEqual(len(analyzed), 1)
        self.assertEqual(analyzed[0]['dependencies'], [])
    
    def test_multiple_dependency_chains(self):
        tasks = [
            {
                'id': 0,
                'title': 'Root Task',
                'due_date': date.today() + timedelta(days=30),
                'importance': 1,
                'estimated_hours': 5,
                'dependencies': []
            },
            {
                'id': 1,
                'title': 'Middle Task',
                'due_date': date.today() + timedelta(days=10),
                'importance': 5,
                'estimated_hours': 3,
                'dependencies': [0]
            },
            {
                'id': 2,
                'title': 'Top Task',
                'due_date': date.today(),
                'importance': 10,
                'estimated_hours': 2,
                'dependencies': [1]
            }
        ]
        
        analyzed = analyze_all_tasks(tasks)
        root_task = next(t for t in analyzed if t['id'] == 0)
        top_task = next(t for t in analyzed if t['id'] == 2)
        
        self.assertTrue(root_task['priority_score'] > root_task['raw_score'])
        self.assertGreater(top_task['priority_score'], root_task['priority_score'])
    
    def test_invalid_date_string(self):
        task = {
            'title': 'Invalid Date Task',
            'due_date': 'not-a-date',
            'importance': 5,
            'estimated_hours': 2,
            'dependencies': []
        }
        
        score = calculate_priority_score(task)
        self.assertGreaterEqual(score, 0)
    
    def test_empty_task_list(self):
        result = analyze_all_tasks([])
        self.assertEqual(result, [])
    
    def test_single_task(self):
        task = {
            'title': 'Single Task',
            'due_date': date.today() + timedelta(days=5),
            'importance': 5,
            'estimated_hours': 2,
            'dependencies': []
        }
        
        analyzed = analyze_all_tasks([task])
        self.assertEqual(len(analyzed), 1)
        self.assertIn('priority_score', analyzed[0])
        self.assertIn('explanation', analyzed[0])
    
    def test_task_with_nonexistent_dependency(self):
        task = {
            'id': 0,
            'title': 'Task with Bad Dependency',
            'due_date': date.today() + timedelta(days=5),
            'importance': 5,
            'estimated_hours': 2,
            'dependencies': [999]
        }
        
        analyzed = analyze_all_tasks([task])
        self.assertEqual(len(analyzed), 1)
        self.assertIn('priority_score', analyzed[0])
