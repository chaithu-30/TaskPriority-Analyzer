const API_BASE = 'http://127.0.0.1:8000/api/tasks';

async function analyzeTasks() {
    const inputEl = document.getElementById('taskInput');
    const strategyEl = document.getElementById('strategySelect');
    const resultsEl = document.getElementById('resultsContainer');
    const errorEl = document.getElementById('errorDisplay');
    const loadingEl = document.getElementById('loadingSpinner');
    
    resultsEl.innerHTML = '';
    errorEl.classList.add('hidden');
    
    let tasks;
    try {
        tasks = JSON.parse(inputEl.value);
        if (!Array.isArray(tasks)) {
            throw new Error('Input must be an array of tasks');
        }
        if (tasks.length === 0) {
            throw new Error('Please provide at least one task');
        }
    } catch (e) {
        showError(`Invalid JSON: ${e.message}`);
        return;
    }
    
    loadingEl.classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/analyze/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                tasks: tasks,
                strategy: strategyEl.value
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `API error: ${response.status}`);
        }
        
        const data = await response.json();
        displayResults(data);
        
    } catch (error) {
        showError(`Error: ${error.message}. Make sure Django server is running on port 8000.`);
    } finally {
        loadingEl.classList.add('hidden');
    }
}

function displayResults(data) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';
    
    if (data.circular_dependencies && data.circular_dependencies.length > 0) {
        const warningDiv = document.createElement('div');
        warningDiv.className = 'warning';
        warningDiv.innerHTML = `Warning: Circular dependencies detected: ${data.circular_dependencies.join(', ')}`;
        container.appendChild(warningDiv);
    }
    
    const infoDiv = document.createElement('div');
    infoDiv.className = 'info';
    infoDiv.innerHTML = `Strategy: ${data.strategy_used} | Total tasks: ${data.total_tasks}`;
    container.appendChild(infoDiv);
    
    data.tasks.forEach((task, idx) => {
        const card = createTaskCard(task, idx + 1);
        container.appendChild(card);
    });
    
    if (data.dependency_graph) {
        renderDependencyGraph(data.dependency_graph, data.circular_dependencies || []);
    }
}

function switchTab(tabName) {
    const priorityTab = document.getElementById('priorityTab');
    const graphTab = document.getElementById('graphTab');
    const priorityBtn = document.querySelector('.tab-btn[onclick*="priority"]');
    const graphBtn = document.querySelector('.tab-btn[onclick*="graph"]');
    
    if (tabName === 'priority') {
        priorityTab.classList.add('active');
        graphTab.classList.remove('active');
        priorityBtn.classList.add('active');
        graphBtn.classList.remove('active');
    } else {
        priorityTab.classList.remove('active');
        graphTab.classList.add('active');
        priorityBtn.classList.remove('active');
        graphBtn.classList.add('active');
    }
}

function createTaskCard(task, rank) {
    const card = document.createElement('div');
    card.className = 'task-card';
    
    if (task.priority_score >= 80) {
        card.classList.add('high');
    } else if (task.priority_score >= 50) {
        card.classList.add('medium');
    } else {
        card.classList.add('low');
    }
    
    const dueDate = new Date(task.due_date);
    const today = new Date();
    const daysLeft = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
    
    let dueText = task.due_date;
    if (daysLeft < 0) {
        dueText += ` (Overdue by ${Math.abs(daysLeft)} days)`;
    } else if (daysLeft === 0) {
        dueText += ' (Due today)';
    } else if (daysLeft <= 2) {
        dueText += ` (${daysLeft} days)`;
    }
    
    card.innerHTML = `
        <div class="task-rank">#${rank}</div>
        <h3>${task.title}</h3>
        <div class="task-score">Score: ${task.priority_score}</div>
        <div class="task-details">
            <span>Due: ${dueText}</span>
            <span>Hours: ${task.estimated_hours}</span>
            <span>Importance: ${task.importance}/10</span>
        </div>
        ${task.explanation ? `<div class="explanation">${task.explanation}</div>` : ''}
    `;
    
    return card;
}

function renderDependencyGraph(graphData, circularDeps) {
    const container = document.getElementById('graphContainer');
    if (!container || !graphData) {
        if (container) {
            container.innerHTML = '<p class="empty">No dependency graph data available</p>';
        }
        return;
    }
    
    const circularSet = new Set(circularDeps);
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];
    
    if (nodes.length === 0) {
        container.innerHTML = '<p class="empty">No tasks to display in graph</p>';
        return;
    }
    
    const width = Math.max(800, container.offsetWidth - 30);
    const height = 500;
    const radius = 35;
    
    container.innerHTML = '';
    
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'graph-svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    
    const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bg.setAttribute('width', '100%');
    bg.setAttribute('height', '100%');
    bg.setAttribute('fill', '#f5f7fa');
    svg.appendChild(bg);
    
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    arrow.setAttribute('id', 'arrowhead');
    arrow.setAttribute('markerWidth', '10');
    arrow.setAttribute('markerHeight', '10');
    arrow.setAttribute('refX', '9');
    arrow.setAttribute('refY', '3');
    arrow.setAttribute('orient', 'auto');
    const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    poly.setAttribute('points', '0 0, 10 3, 0 6');
    poly.setAttribute('fill', '#34495e');
    arrow.appendChild(poly);
    defs.appendChild(arrow);
    svg.appendChild(defs);
    
    const positions = {};
    const centerX = width / 2;
    const centerY = height / 2;
    const layoutRadius = Math.min(width, height) / 3;
    
    nodes.forEach((node, i) => {
        const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
        positions[node.id] = {
            x: centerX + layoutRadius * Math.cos(angle),
            y: centerY + layoutRadius * Math.sin(angle)
        };
    });
    
    edges.forEach(edge => {
        const fromPos = positions[edge.from];
        const toPos = positions[edge.to];
        if (!fromPos || !toPos) return;
        
        const dx = toPos.x - fromPos.x;
        const dy = toPos.y - fromPos.y;
        const len = Math.sqrt(dx * dx + dy * dy);
        const ux = dx / len;
        const uy = dy / len;
        
        const startX = fromPos.x + ux * radius;
        const startY = fromPos.y + uy * radius;
        const endX = toPos.x - ux * radius;
        const endY = toPos.y - uy * radius;
        
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', startX);
        line.setAttribute('y1', startY);
        line.setAttribute('x2', endX);
        line.setAttribute('y2', endY);
        line.setAttribute('class', `graph-edge ${edge.is_circular ? 'circular' : 'normal'}`);
        line.setAttribute('stroke-width', edge.is_circular ? '3' : '2');
        line.setAttribute('marker-end', 'url(#arrowhead)');
        svg.appendChild(line);
    });
    
    nodes.forEach(node => {
        const pos = positions[node.id];
        if (!pos) return;
        
        const inCycle = node.is_circular || circularSet.has(node.title);
        
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', pos.x);
        circle.setAttribute('cy', pos.y);
        circle.setAttribute('r', radius);
        circle.setAttribute('class', `graph-node ${inCycle ? 'circular' : 'normal'}`);
        svg.appendChild(circle);
        
        const titleText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        titleText.setAttribute('x', pos.x);
        titleText.setAttribute('y', pos.y + 5);
        titleText.setAttribute('text-anchor', 'middle');
        titleText.setAttribute('class', 'graph-text');
        titleText.setAttribute('font-size', '11px');
        const shortTitle = node.title.length > 15 ? node.title.substring(0, 15) + '...' : node.title;
        titleText.textContent = shortTitle;
        svg.appendChild(titleText);
        
        const scoreText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        scoreText.setAttribute('x', pos.x);
        scoreText.setAttribute('y', pos.y + radius + 15);
        scoreText.setAttribute('text-anchor', 'middle');
        scoreText.setAttribute('class', 'graph-score');
        scoreText.setAttribute('font-size', '9px');
        scoreText.textContent = `Score: ${node.score.toFixed(1)}`;
        svg.appendChild(scoreText);
    });
    
    container.appendChild(svg);
}

function showError(message) {
    const errorMsg = document.getElementById('errorDisplay');
    errorMsg.textContent = message;
    errorMsg.classList.remove('hidden');
}

function loadSampleData() {
    const samples = [
        {
            "title": "Fix critical login bug",
            "due_date": "2025-11-25",
            "estimated_hours": 2,
            "importance": 9,
            "dependencies": []
        },
        {
            "title": "Update API documentation",
            "due_date": "2025-12-05",
            "estimated_hours": 4,
            "importance": 5,
            "dependencies": []
        },
        {
            "title": "Refactor authentication module",
            "due_date": "2025-12-01",
            "estimated_hours": 6,
            "importance": 7,
            "dependencies": [0]
        },
        {
            "title": "Write unit tests",
            "due_date": "2025-12-10",
            "estimated_hours": 8,
            "importance": 6,
            "dependencies": [2]
        },
        {
            "title": "Deploy to production",
            "due_date": "2025-12-15",
            "estimated_hours": 3,
            "importance": 10,
            "dependencies": [0, 2, 3]
        }
    ];
    
    document.getElementById('taskInput').value = JSON.stringify(samples, null, 2);
}

window.addEventListener('DOMContentLoaded', () => {
    loadSampleData();
});
