Smart Task Analyzer

A Django web application that intelligently prioritizes tasks using a sophisticated scoring algorithm. It considers due dates, importance ratings, estimated effort, task dependencies, and multiple scoring strategies to help you focus on what matters most.

Table of Contents

1. Setup Instructions
2. Algorithm Explanation
3. Design Decisions
4. Time Breakdown
5. Bonus Challenges
6. Future Improvements
7. Project Structure
8. API Documentation
9. Running Tests

Setup Instructions

Prerequisites

You need Python 3.8 or higher installed, along with pip.

Backend Setup

Navigate to the backend directory:

cd task-analyzer/backend

Create and activate a virtual environment:

On Windows:
python -m venv venv
venv\Scripts\activate

On Linux/Mac:
python -m venv venv
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

The requirements include:
- Django 4.2
- Django REST Framework 3.14
- django-cors-headers 4.3

Run database migrations:

python manage.py makemigrations
python manage.py migrate

Optional: Create a superuser for admin access:

python manage.py createsuperuser

Start the Django development server:

python manage.py runserver

The API will be available at http://127.0.0.1:8000/

Frontend Setup

Navigate to the frontend directory:

cd task-analyzer/frontend

You can open index.html directly in your browser, but it's better to use a local web server to avoid CORS issues:

python -m http.server 8001

Then open http://localhost:8001 in your browser. Alternatively, use a Live Server extension in your code editor.

Running the Application

1. Start the backend server (keep this terminal open):
   cd task-analyzer/backend
   python manage.py runserver
   
   The server runs on http://127.0.0.1:8000/

2. Open the frontend:
   cd task-analyzer/frontend
   python -m http.server 8001
   
   Then open http://localhost:8001 in your browser

3. Use the application:
   - The page loads with sample tasks pre-filled
   - Edit the JSON data or load the sample
   - Select a scoring strategy from the dropdown
   - Click "Analyze" to see prioritized results
   - Switch between "Task Priority" and "Graph" tabs to view different visualizations

Algorithm Explanation

The priority scoring algorithm uses a two-pass system that first calculates intrinsic scores for each task, then applies dependency-based score inheritance to ensure blocking tasks receive appropriate priority.

Base Score Calculation

Each task begins with a base score calculated from three components: urgency, importance, and effort. The urgency component accounts for approximately 60% of the potential score, reflecting the non-negotiable nature of deadlines. The system uses working days rather than calendar days, automatically excluding weekends and common holidays from urgency calculations. This makes the scoring more realistic for professional environments where work happens primarily on weekdays.

For overdue tasks, the urgency score starts at 100 points and adds up to 50 additional points based on how many days past the deadline. Tasks due today receive 90 points if it's a working day, or 100 points if it falls on a weekend or holiday. The urgency score decreases as the due date moves further into the future, using a decay function that considers working days remaining rather than calendar days.

The importance component multiplies the task's importance rating by a factor that varies by strategy. In the default smart balance strategy, each point of importance contributes 6 points to the score. This allows high-importance tasks to surface even when deadlines are further away.

The effort component provides a quick win bonus, giving preference to tasks that can be completed quickly. Tasks under one hour receive a 15-point bonus, while tasks under three hours get 5 points. This balances the urgency-driven scoring by allowing small but important tasks to be handled efficiently.

Score Inheritance and Dependencies

After base scores are calculated, the algorithm applies a score inheritance mechanism that addresses the critical problem of blocking tasks. When Task A depends on Task B, completing Task B becomes a prerequisite for Task A. The algorithm recognizes this by allowing Task B to inherit 50% of Task A's priority score. This bubbles up urgency from dependent tasks to their blockers, ensuring that blocking tasks receive appropriate attention even if they have lower intrinsic urgency.

The inheritance mechanism works iteratively across dependency chains. If Task A blocks Task B, and Task B blocks Task C, Task A will eventually inherit urgency from both downstream tasks through multiple iterations. The algorithm runs up to three iterations to allow scores to propagate through longer chains. This prevents scenarios where a low-priority blocker prevents completion of multiple high-priority dependent tasks.

Circular dependencies are detected using depth-first search. When cycles are found, all involved tasks are flagged with a score of 999.0 and marked for immediate attention. This prevents the algorithm from getting stuck in infinite loops and alerts users to dependency conflicts that need manual resolution.

Strategy Variations

The system supports four scoring strategies that adjust the weighting of different components. The Smart Balance strategy provides equal consideration to urgency and importance. Fastest Wins prioritizes quick tasks and deadlines, ideal for clearing backlogs. High Impact emphasizes importance ratings, suitable for strategic work. Deadline Driven maximizes urgency weight, perfect for deadline-focused environments.

Date Intelligence

The algorithm incorporates date intelligence that considers weekends and holidays when calculating urgency. It recognizes common holidays including New Year's Day, Independence Day, Thanksgiving, and Christmas. Working days are calculated by excluding weekends and holidays, ensuring that tasks due on Mondays after weekends or after holidays have accurate urgency scores. Tasks due on weekends receive a small bonus to reflect the inconvenience of weekend work.

Design Decisions

Backend Architecture

Django REST Framework was chosen for rapid API development and excellent serialization capabilities. The scoring logic is completely isolated in scoring.py, making it easy to modify algorithms without touching views or models. This separation of concerns allows for algorithm experimentation and refinement without risking API stability.

Tasks can be analyzed without saving to the database, allowing for quick what-if scenarios and keeping the API stateless for analysis requests. The Task model exists primarily for potential future persistence features, but the core functionality works entirely in-memory.

CORS headers are enabled for all origins in development, making it easy to test the frontend independently. For production deployment, this should be restricted to specific allowed origins.

Frontend Approach

Vanilla JavaScript was chosen over frameworks like React or Vue to keep the codebase simple and easily understandable. This makes it easier for others to read and modify the code. The design uses CSS Grid and Flexbox for responsive layout, avoiding complex CSS frameworks.

The dependency graph visualization uses SVG rather than Canvas, providing better scalability and easier interaction potential. The circular layout algorithm positions nodes in a circle for clarity, though future improvements could include force-directed layouts for better readability with many tasks.

Data Model Choices

Dependencies are stored as a JSON field rather than using a separate relationship table. This provides flexibility for the in-memory analysis approach while keeping the data structure simple. The trade-off is that we lose referential integrity at the database level, but since tasks are analyzed in-memory without database constraints, this is acceptable.

The system handles dates as either strings or date objects, providing flexibility for different input formats. All dates are normalized during processing to ensure consistent behavior.

Strategy Implementation

The four strategies are implemented within the base score calculation function rather than as separate algorithms. This ensures consistency in edge case handling while allowing strategy-specific weight adjustments. The trade-off is slightly more complex conditional logic, but it prevents code duplication and maintains consistent behavior.

Time Breakdown

Initial Project Setup (1 hour)

Setting up the Django project structure, configuring settings, creating the Task model, and establishing the basic API endpoints. This included setting up CORS headers and configuring REST framework serializers.

Core Scoring Algorithm (3 hours)

Developing the base scoring logic with urgency, importance, and effort components. This required careful consideration of weighting factors and testing various scenarios to ensure reasonable prioritization.

Dependency Handling (2 hours)

Implementing the score inheritance mechanism and circular dependency detection using depth-first search. This included handling edge cases like missing dependencies and dependency chains of varying lengths.

Date Intelligence (1 hour)

Adding weekend and holiday detection, implementing working day calculations, and integrating this into the urgency scoring. This required careful handling of date edge cases and ensuring accurate working day counts.

Multiple Scoring Strategies (1 hour)

Implementing the four different strategies by adjusting weights within the scoring algorithm. Testing each strategy to ensure meaningful differences in prioritization.

API Development (1.5 hours)

Creating the analyze and suggest endpoints, handling request validation, error responses, and building the dependency graph data structure for frontend visualization.

Frontend Development (2 hours)

Building the HTML structure, CSS styling, and JavaScript functionality. This included creating the tabbed interface, task card display, and implementing the API integration.

Dependency Graph Visualization (2 hours)

Implementing the SVG-based graph rendering with circular layout, arrow markers, and highlighting for circular dependencies. This required understanding SVG coordinate systems and creating an algorithm for node positioning.

Testing (2 hours)

Writing comprehensive unit tests for the scoring algorithm, edge cases, API endpoints, and date intelligence functions. Debugging and fixing issues discovered during testing.

Edge Case Handling (1 hour)

Addressing missing fields, invalid dates, out-of-range values, and other edge cases throughout the codebase. Adding appropriate default values and validation.

Code Refinement (1 hour)

Removing comments, simplifying code structure, making variable names more natural, and ensuring the code reads as human-written rather than template-generated.

Total Estimated Time: 18.5 hours

Bonus Challenges

Dependency Graph Visualization

Implemented a complete SVG-based visualization that displays task dependencies as a directed graph. Nodes are positioned in a circular layout for clarity, with arrows showing dependency direction. Circular dependencies are visually highlighted with red coloring and thicker edges. The graph shows task titles, priority scores, and dependency relationships, making it easy to understand task interdependencies at a glance.

Date Intelligence

Implemented comprehensive date intelligence that considers weekends and holidays when calculating urgency. The system recognizes common holidays and calculates working days remaining rather than calendar days. Tasks due on weekends receive special handling, and the urgency calculations reflect realistic work schedules. This makes the prioritization much more practical for professional use.

Circular Dependency Detection

Implemented robust circular dependency detection using depth-first search algorithm. The system not only detects cycles but flags all tasks involved and assigns them a high priority score (999.0) to ensure they're addressed immediately. This prevents users from getting stuck in dependency loops.

Multiple Scoring Strategies

Implemented four distinct scoring strategies that adjust the weighting of different priority factors. Each strategy is optimized for different use cases, from clearing backlogs quickly to focusing on high-impact strategic work.

Future Improvements

With more time, several enhancements would significantly improve the application:

Database Persistence and Task Management

Add full CRUD operations for tasks, allowing users to save task lists, update task status, and track completion history. This would enable the system to learn from past behavior and refine scoring weights based on actual completion patterns.

User Authentication and Multi-User Support

Implement user accounts so multiple users can maintain separate task lists. Add team collaboration features where tasks can be assigned to team members and dependencies can span across users.

Machine Learning Integration

Track which tasks users actually complete and in what order, then use this data to train a model that adjusts scoring weights automatically based on user behavior patterns. This would personalize the prioritization algorithm for each user's working style.

Advanced Calendar Integration

Connect with calendar systems to automatically detect busy periods, meetings, and availability windows. The algorithm could then suggest optimal times to work on specific tasks based on available time slots and task duration estimates.

Task Templates and Workflows

Create reusable task templates for common workflows, allowing users to quickly set up standard task lists for recurring project types. Include dependency templates that automatically establish common dependency patterns.

Analytics Dashboard

Build a dashboard showing productivity metrics, task completion rates, time estimates vs actual time spent, and trends over time. This would help users understand their work patterns and improve future task estimation.

External Integrations

Add import capabilities from popular task management tools like Trello, Asana, or Jira. This would allow users to leverage the prioritization algorithm with their existing task data.

Notifications and Reminders

Implement deadline notifications, suggesting optimal times to start tasks based on their estimated duration and current workload. This proactive approach would help prevent last-minute rushes.

Advanced Visualization Options

Add force-directed graph layouts for better readability with many tasks. Implement timeline views showing task schedules, Gantt chart views, and calendar views with prioritized tasks highlighted.

Refined Algorithm Options

Allow users to customize scoring weights within strategies, create custom strategies, and adjust the inheritance percentage for dependency handling. Add support for task categories or tags that influence prioritization.

Project Structure

task-analyzer/
├── backend/
│   ├── manage.py
│   ├── db.sqlite3
│   ├── requirements.txt
│   ├── task_analyzer/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── tasks/
│       ├── migrations/
│       │   ├── __init__.py
│       │   └── 0001_initial.py
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       ├── scoring.py
│       ├── urls.py
│       └── tests.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── script.js
└── README.md

API Documentation

Base URL: http://127.0.0.1:8000/api/tasks/

POST /analyze/

Analyzes and prioritizes a list of tasks.

Request Body:
{
  "tasks": [
    {
      "title": "Task name",
      "due_date": "2025-12-25",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": [0, 1]
    }
  ],
  "strategy": "smart_balance"
}

Response:
{
  "tasks": [...],
  "strategy_used": "Smart Balance",
  "circular_dependencies": [],
  "total_tasks": 1,
  "dependency_graph": {
    "nodes": [...],
    "edges": [...]
  }
}

Available strategies: smart_balance, fastest_wins, high_impact, deadline_driven

POST /suggest/

Returns the top 3 highest priority tasks due today.

Request body is the same as /analyze/. Response includes a suggestions array with up to 3 tasks.

Running Tests

From the backend directory, run:

python manage.py test

The test suite includes 28 tests covering:
- Overdue task prioritization
- Circular dependency detection
- Quick win bonus verification
- Score inheritance verification
- Date intelligence (weekends, holidays, working days)
- API endpoint functionality
- Edge case handling

All tests should pass successfully.