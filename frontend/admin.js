// frontend/admin.js
const API_URL = 'http://localhost:8000/api/v1';
let accessToken = localStorage.getItem('accessToken');

const adminDashboard = {
    charts: {},

    async init() {
        // Get token from localStorage (set by main app)
        if (!accessToken) {
            alert('Please login first');
            window.close();
            return;
        }

        await this.loadAllData();
        
        // Refresh every 30 seconds
        setInterval(() => this.loadAllData(), 30000);
    },

    async loadAllData() {
        await Promise.all([
            this.loadOverallStats(),
            this.loadSentimentOverview(),
            this.loadNegativeAlerts(),
            this.loadUserSentiments()
        ]);
    },

    async loadOverallStats() {
        try {
            const response = await fetch(`${API_URL}/analytics/stats/overall`, {
                headers: {'Authorization': `Bearer ${accessToken}`}
            });

            if (response.ok) {
                const data = await response.json();
                document.getElementById('totalUsers').textContent = data.total_users;
                document.getElementById('totalMessages').textContent = data.total_messages;
                document.getElementById('messagesToday').textContent = data.messages_today;
                document.getElementById('totalRooms').textContent = data.total_chat_rooms;
            }
        } catch (error) {
            console.error('Failed to load overall stats:', error);
        }
    },

    async loadSentimentOverview() {
        try {
            const response = await fetch(`${API_URL}/analytics/sentiment/overview?days=7`, {
                headers: {'Authorization': `Bearer ${accessToken}`}
            });

            if (response.ok) {
                const data = await response.json();
                this.renderSentimentPieChart(data.sentiment_distribution);
                this.renderSentimentLineChart(data.daily_trends);
            }
        } catch (error) {
            console.error('Failed to load sentiment overview:', error);
        }
    },

    renderSentimentPieChart(distribution) {
        const ctx = document.getElementById('sentimentPieChart').getContext('2d');
        
        if (this.charts.pie) {
            this.charts.pie.destroy();
        }

        const data = {
            labels: Object.keys(distribution).map(s => s.charAt(0).toUpperCase() + s.slice(1)),
            datasets: [{
                data: Object.values(distribution),
                backgroundColor: [
                    '#28a745',  // positive
                    '#dc3545',  // negative
                    '#6c757d'   // neutral
                ],
                borderWidth: 0
            }]
        };

        this.charts.pie = new Chart(ctx, {
            type: 'doughnut',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    },

    renderSentimentLineChart(trends) {
        const ctx = document.getElementById('sentimentLineChart').getContext('2d');
        
        if (this.charts.line) {
            this.charts.line.destroy();
        }

        const labels = trends.map(t => new Date(t.date).toLocaleDateString('en-US', {month: 'short', day: 'numeric'}));
        
        const data = {
            labels: labels,
            datasets: [
                {
                    label: 'Positive',
                    data: trends.map(t => t.positive || 0),
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Negative',
                    data: trends.map(t => t.negative || 0),
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Neutral',
                    data: trends.map(t => t.neutral || 0),
                    borderColor: '#6c757d',
                    backgroundColor: 'rgba(108, 117, 125, 0.1)',
                    tension: 0.4
                }
            ]
        };

        this.charts.line = new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    },

    async loadNegativeAlerts() {
        try {
            const response = await fetch(`${API_URL}/analytics/sentiment/negative-alerts?limit=10`, {
                headers: {'Authorization': `Bearer ${accessToken}`}
            });

            if (response.ok) {
                const data = await response.json();
                this.renderNegativeAlerts(data.negative_messages);
            }
        } catch (error) {
            console.error('Failed to load negative alerts:', error);
        }
    },

    renderNegativeAlerts(alerts) {
        const container = document.getElementById('negativeAlerts');
        
        if (alerts.length === 0) {
            container.innerHTML = '<div class="no-data">No negative messages found 🎉</div>';
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="alert-item">
                <div class="alert-header">
                    <span class="alert-user">@${alert.sender}</span>
                    <span class="alert-time">${new Date(alert.timestamp).toLocaleString()}</span>
                </div>
                <div class="alert-room">💬 ${alert.chat_room}</div>
                <div class="alert-content">${this.escapeHtml(alert.content)}</div>
            </div>
        `).join('');
    },

    async loadUserSentiments() {
        try {
            const response = await fetch(`${API_URL}/analytics/sentiment/by-user?days=7`, {
                headers: {'Authorization': `Bearer ${accessToken}`}
            });

            if (response.ok) {
                const data = await response.json();
                this.renderUserSentimentTable(data.user_sentiments);
            }
        } catch (error) {
            console.error('Failed to load user sentiments:', error);
        }
    },

    renderUserSentimentTable(users) {
        const tbody = document.querySelector('#userSentimentTable tbody');
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">No data available</td></tr>';
            return;
        }

        tbody.innerHTML = users.map(user => {
            const scoreClass = user.sentiment_score > 20 ? 'score-positive' : 
                              user.sentiment_score < -20 ? 'score-negative' : 'score-neutral';
            
            return `
                <tr>
                    <td><strong>${user.username}</strong></td>
                    <td>${user.total_messages}</td>
                    <td style="color: #28a745">${user.positive_count} (${user.positive_percent}%)</td>
                    <td style="color: #dc3545">${user.negative_count} (${user.negative_percent}%)</td>
                    <td style="color: #6c757d">${user.neutral_count}</td>
                    <td class="${scoreClass}">${user.sentiment_score > 0 ? '+' : ''}${user.sentiment_score}</td>
                </tr>
            `;
        }).join('');
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Store token in localStorage from main app
window.addEventListener('message', (event) => {
    if (event.data.type === 'AUTH_TOKEN') {
        accessToken = event.data.token;
        localStorage.setItem('accessToken', accessToken);
    }
});

// Initialize dashboard
adminDashboard.init();