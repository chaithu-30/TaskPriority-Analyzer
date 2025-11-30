Smart Task Analyzer

This is a Django web application that helps you prioritize tasks intelligently. It calculates priority scores based on due dates, importance ratings, estimated effort, and task dependencies. The app has a separate frontend and backend, making it easy to understand and modify each part.

Project Overview

The Smart Task Analyzer calculates priority scores for tasks using different factors. You can choose from four different strategies depending on how you want to prioritize. It also detects circular dependencies between tasks so you can avoid getting stuck.

The main factors it considers are:
- Due dates for urgency
- Importance ratings from 1 to 10
- Estimated hours to complete
- Task dependencies that block other tasks
- Different scoring strategies

Setup Instructions

You need Python 3.8 or higher installed, along with pip.

Backend Setup

First, go to the backend directory:

cd task-analyzer/backend

Create a virtual environment (this is recommended):

python -m venv venv

Activate it. On Windows:

venv\Scripts\activate

On Linux or Mac:

source venv/bin/activate

Install the dependencies:

pip install -r requirements.txt

Run the database migrations:

python manage.py makemigrations
python manage.py migrate

If you want admin access, create a superuser:

python manage.py createsuperuser

Start the Django server:

python manage.py runserver

The API will be running at http://127.0.0.1:8000/

Frontend Setup

Go to the frontend directory:

cd task-analyzer/frontend

You can open index.html directly in your browser, but it's better to use a local web server. You can use Python's built-in server:

python -m http.server 8001

Then open http://localhost:8001 in your browser. Or use a Live Server extension in your code editor.

Note: If you open the HTML file directly from the file system, you might get CORS errors. Using a web server avoids this.

Running the Application

To run the complete application:

1. Start the backend server (Terminal 1):
   cd task-analyzer/backend
   python manage.py runserver
   
   Keep this terminal open. The server will run on http://127.0.0.1:8000/

2. Open the frontend (Terminal 2 or browser):
   
   Option A: Using a web server
   cd task-analyzer/frontend
   python -m http.server 8001
   Then open http://localhost:8001 in your browser
   
   Option B: Direct file
   Double-click task-analyzer/frontend/index.html to open in browser

3. Use the application:
   - The page loads with sample tasks
   - Edit the JSON or use sample data
   - Select a strategy and click "Analyze"
   - View prioritized results on the right

Algorithm Explanation

How the Scoring Algorithm Works

The scoring algorithm uses a two-pass approach that first calculates base scores for each task, then applies score inheritance to handle dependencies correctly.

Pass 1: Base Score Calculation

Each task gets a base score from three components:

1. Urgency Score (up to 150 points)
   - Overdue tasks: 100 base points + up to 50 extra points (5 points per day overdue, capped at 50)
   - Due today: 90 points
   - Due in 1-2 days: 60 points
   - Due in 3-7 days: 30 points
   - Future tasks: 20 points minus 1 point per week (minimum 0)

   Example: A task overdue by 10 days gets 100 + 50 = 150 urgency points.

2. Importance Score (up to 60 points)
   - Importance rating (1-10) multiplied by 6
   - Example: Importance 8 = 48 points

3. Quick Win Bonus (up to 15 points)
   - Tasks under 1 hour: +15 points
   - Tasks under 3 hours: +5 points
   - Longer tasks: no bonus

Example base score calculation:
- Task due today (90) + Importance 7 (42) + Quick 1-hour task (15) = 147 base score

Why Urgency is Weighted More Than Effort

Urgency receives higher weight because deadlines are typically non-negotiable. Missing a deadline can have consequences like client dissatisfaction, missed opportunities, or project delays. Effort, while important, is more flexible - you can always spend more time on something, but you can't move deadlines back in time.

In the scoring system:
- Urgency can contribute up to 150 points
- Importance can contribute up to 60 points  
- Effort bonus is only up to 15 points

This weighting ensures that tasks with approaching deadlines get prioritized, even if they require more effort. A task due today that takes 8 hours will score higher than a task due next month that takes 1 hour, which is usually the correct prioritization in real-world scenarios.

Pass 2: Score Inheritance (Dependency Handling)

After calculating base scores, the algorithm applies score inheritance to handle task dependencies:

1. Blocking tasks inherit urgency from dependent tasks
   - If Task A blocks Task B, Task A inherits 50% of Task B's current score
   - This "bubbles up" urgency so blocking tasks get prioritized

2. Works across chains
   - If A blocks B, and B blocks C, A inherits from both (through B)
   - Up to 3 iterations ensure chains are fully processed

3. Circular dependencies detected
   - Using depth-first search, cycles are identified
   - Tasks in cycles get score 999.0 and warning flags

Example: Task A (low urgency) blocks Task B (high urgency). Task A's base score might be 50, but after inheriting 50% of Task B's score of 150, Task A becomes 50 + 75 = 125, making it the priority so Task B can be unblocked.

Circular Dependency Detection

The algorithm uses depth-first search to detect circular dependencies. For example, if Task A depends on Task B, and Task B depends on Task A, this creates a cycle. The system flags all tasks involved in the cycle with a score of 999.0 and adds a warning message, allowing users to identify and resolve the dependency conflict.

Edge Cases Handled

The algorithm handles various edge cases gracefully:

- Missing fields: Defaults are provided (importance: 5, estimated_hours: 1, dependencies: [], due_date: 30 days from today)
- Invalid dates: Date parsing errors are caught and default to 30 days future
- Very old dates: Tasks due in 1990 or earlier are treated as highly overdue with capped scoring
- Out-of-range values: Importance clamped to 1-10, hours clamped to minimum 1
- Circular dependencies: Detected and flagged without crashing
- Empty task lists: Validated with clear error messages
- Dependencies on non-existent tasks: Ignored safely
- None/null values: Filtered out or converted to defaults

All edge cases have been tested and verified to work correctly.

API Documentation

The base URL is http://127.0.0.1:8000/api/tasks/

There are two endpoints:

POST /api/tasks/analyze/ analyzes and prioritizes a list of tasks.

Send a POST request with JSON body containing tasks array. The tasks array should have objects with title, due_date (YYYY-MM-DD format), estimated_hours, importance (1-10), and dependencies (array of task indices).

You'll get back a JSON response with the tasks array sorted by priority score (highest first), along with strategy_used, circular_dependencies array, and total_tasks count. Each task will have its original fields plus priority_score, raw_score, and explanation.

POST /api/tasks/suggest/ returns the top 3 highest priority tasks.

Send the same request body as analyze. You'll get back a JSON response with a suggestions array containing the top 3 tasks, plus strategy_used.

Running Tests

From the backend directory, run:

python manage.py test

The test suite includes:
- Overdue task prioritization
- Circular dependency detection
- Quick win bonus verification
- Score inheritance verification
- API endpoint functionality

All 9 unit tests pass successfully.

Design Decisions

For the backend, Django REST Framework was chosen for rapid API development and excellent serialization capabilities. The scoring logic is isolated in scoring.py, making it easy to modify algorithms without touching views. Tasks can be analyzed without saving to the database, allowing for quick what-if scenarios.

CORS headers are enabled for development. For production, you'd want to restrict allowed origins.

For the frontend, vanilla JavaScript was used with no frameworks. This makes it easier to understand and modify. The design uses CSS Grid and Flexbox for responsive layout. Task cards are color-coded: red for high priority, yellow for medium, green for low.

For the data model, dependencies are stored as a JSON field. This provides flexibility without complex join tables. Django validators ensure importance is 1-10 and estimated hours is at least 1. The system handles dates as strings or date objects.

Future Improvements

Some ideas for future work: save tasks to database and manage task lists, add user authentication for multiple users, create task templates for common workflows, track completion history to refine scoring, use machine learning to learn optimal weights from user behavior, suggest optimal times to work based on calendar, add team collaboration features, import from tools like Trello or Asana, send notifications for deadlines, and create an analytics dashboard.

Project Structure

task-analyzer/
├── backend/
│   ├── manage.py
│   ├── task_analyzer/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── scoring.py
│   │   ├── urls.py
│   │   └── tests.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── script.js
└── README.md

