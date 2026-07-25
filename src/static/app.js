document.addEventListener('DOMContentLoaded', () => {
    // API base URL (empty string means relative to current host)
    const API_BASE = "";
    
    // Tab switching elements
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    const tabTitle = document.getElementById('current-tab-title');
    const tabSubtitle = document.getElementById('current-tab-subtitle');
    
    // Playground elements
    const reviewInput = document.getElementById('review-input');
    const predictBtn = document.getElementById('predict-btn');
    const resultCard = document.getElementById('result-card');
    const emptyState = resultCard.querySelector('.empty-state');
    const resultState = resultCard.querySelector('.result-state');
    const pills = document.querySelectorAll('.pill');
    
    const predSentiment = document.getElementById('pred-sentiment');
    const sentimentConfBar = document.getElementById('sentiment-conf-bar');
    const sentimentConfVal = document.getElementById('sentiment-conf-val');
    
    const predCategory = document.getElementById('pred-category');
    const categoryConfBar = document.getElementById('category-conf-bar');
    const categoryConfVal = document.getElementById('category-conf-val');
    
    const latencyTag = document.getElementById('latency-tag');
    
    // Feedback elements
    const correctSentiment = document.getElementById('correct-sentiment');
    const correctCategory = document.getElementById('correct-category');
    const submitFeedbackBtn = document.getElementById('submit-feedback-btn');
    const feedbackSuccessMsg = document.getElementById('feedback-success-msg');
    
    // Monitoring elements
    const refreshMetricsBtn = document.getElementById('refresh-metrics-btn');
    const kpiRequests = document.getElementById('kpi-requests');
    const kpiLatency = document.getElementById('kpi-latency');
    const kpiUptime = document.getElementById('kpi-uptime');
    const kpiErrors = document.getElementById('kpi-errors');
    const kpiFeedbacksCount = document.getElementById('kpi-feedbacks-count');
    
    const driftAlertBanner = document.getElementById('drift-alert-banner');
    const driftScoreValue = document.getElementById('drift-score-value');
    
    const feedbackTableBody = document.getElementById('feedback-table-body');
    const apiStatusText = document.getElementById('api-status-text');
    const statusIndicator = document.querySelector('.status-indicator');
    
    // Current active prediction data (saved for feedback loop)
    let currentPrediction = null;
    
    // Chart instances
    let sentimentChart = null;
    let categoryChart = null;
    
    // -------------------------------------------------------------
    // Tab Navigation Logic
    // -------------------------------------------------------------
    const tabDetails = {
        'playground-tab': {
            title: "Model Playground",
            subtitle: "Test predictions, view confidence scores and submit feedback."
        },
        'monitoring-tab': {
            title: "Real-time Monitoring",
            subtitle: "Check model latency, distribution, errors and dataset drift."
        },
        'feedback-tab': {
            title: "Human-in-the-Loop Feedback",
            subtitle: "View correction logs submitted by users to improve future runs."
        }
    };
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');
            
            // Toggle active menu item
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            
            // Toggle active tab content
            tabContents.forEach(content => {
                if (content.id === targetTab) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
            
            // Update Header Info
            tabTitle.textContent = tabDetails[targetTab].title;
            tabSubtitle.textContent = tabDetails[targetTab].subtitle;
            
            // Fetch fresh metrics if switching to Monitoring or Feedback
            if (targetTab === 'monitoring-tab' || targetTab === 'feedback-tab') {
                fetchMetrics();
            }
        });
    });
    
    // -------------------------------------------------------------
    // Playground Logic
    // -------------------------------------------------------------
    // Pill selection helper
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            reviewInput.value = pill.getAttribute('data-text');
            reviewInput.focus();
        });
    });
    
    // Predict API Call
    predictBtn.addEventListener('click', async () => {
        const text = reviewInput.value.trim();
        if (!text) return;
        
        predictBtn.disabled = true;
        predictBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        feedbackSuccessMsg.classList.add('hidden');
        
        try {
            const response = await fetch(`${API_BASE}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            
            if (!response.ok) throw new Error("Inference failed");
            
            const data = await response.json();
            currentPrediction = data;
            
            // Populate output UI
            predSentiment.textContent = data.sentiment;
            sentimentConfBar.style.width = `${Math.round(data.sentiment_confidence * 100)}%`;
            sentimentConfVal.textContent = `${Math.round(data.sentiment_confidence * 100)}% confidence`;
            
            // Color coding for sentiment
            predSentiment.style.color = getSentimentColor(data.sentiment);
            sentimentConfBar.style.backgroundColor = getSentimentColor(data.sentiment);
            
            predCategory.textContent = data.category;
            categoryConfBar.style.width = `${Math.round(data.category_confidence * 100)}%`;
            categoryConfVal.textContent = `${Math.round(data.category_confidence * 100)}% confidence`;
            
            latencyTag.innerHTML = `<i class="fa-regular fa-clock"></i> ${data.latency_ms}ms`;
            
            // Auto populate feedback selectors
            correctSentiment.value = data.sentiment;
            correctCategory.value = data.category;
            
            // Toggle view state
            resultCard.classList.remove('empty');
            emptyState.classList.add('hidden');
            resultState.classList.remove('hidden');
            
        } catch (error) {
            console.error(error);
            alert("Error invoking model prediction api. Make sure python server is running.");
        } finally {
            predictBtn.disabled = false;
            predictBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Classify Review';
        }
    });
    
    // Submit Feedback Correction
    submitFeedbackBtn.addEventListener('click', async () => {
        if (!currentPrediction) return;
        
        const feedbackPayload = {
            text: currentPrediction.text,
            predicted_sentiment: currentPrediction.sentiment,
            actual_sentiment: correctSentiment.value,
            predicted_category: currentPrediction.category,
            actual_category: correctCategory.value
        };
        
        submitFeedbackBtn.disabled = true;
        
        try {
            const response = await fetch(`${API_BASE}/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(feedbackPayload)
            });
            
            if (response.ok) {
                feedbackSuccessMsg.classList.remove('hidden');
                setTimeout(() => {
                    feedbackSuccessMsg.classList.add('hidden');
                }, 4000);
            }
        } catch (error) {
            console.error(error);
        } finally {
            submitFeedbackBtn.disabled = false;
        }
    });
    
    // Helper colors
    function getSentimentColor(sentiment) {
        if (sentiment === 'Positif') return 'var(--sentiment-pos)';
        if (sentiment === 'Neutre') return 'var(--sentiment-neu)';
        return 'var(--sentiment-neg)';
    }
    
    // -------------------------------------------------------------
    // Monitoring Dashboard & Metrics Logic
    // -------------------------------------------------------------
    async function checkApiHealth() {
        try {
            const response = await fetch(`${API_BASE}/health`);
            if (response.ok) {
                apiStatusText.textContent = "Online";
                statusIndicator.className = "status-indicator online";
            } else {
                throw new Error();
            }
        } catch (e) {
            apiStatusText.textContent = "Offline";
            statusIndicator.className = "status-indicator offline";
        }
    }
    
    function formatUptime(seconds) {
        if (seconds < 60) return `${seconds}s`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        return `${hours}h ${remainingMinutes}m`;
    }
    
    async function fetchMetrics() {
        try {
            const response = await fetch(`${API_BASE}/metrics`);
            if (!response.ok) return;
            
            const metrics = await response.json();
            
            // Update KPI Cards
            kpiRequests.textContent = metrics.total_requests;
            kpiLatency.textContent = `${metrics.average_latency_ms} ms`;
            kpiUptime.textContent = formatUptime(metrics.uptime_seconds);
            kpiErrors.textContent = metrics.total_errors;
            kpiFeedbacksCount.textContent = `${metrics.feedback_loop.total_submitted} feedbacks`;
            
            // Update Drift Alert Banner
            const driftData = metrics.model_monitoring;
            if (driftData.drift_detected) {
                driftAlertBanner.classList.remove('hidden');
                driftScoreValue.textContent = driftData.drift_score.toFixed(3);
            } else {
                driftAlertBanner.classList.add('hidden');
            }
            
            // Update Charts
            updateCharts(metrics.sentiment_distribution, metrics.category_distribution);
            
            // Update Feedbacks Table
            updateFeedbackTable(metrics.feedback_loop.recent_corrections);
            
        } catch (error) {
            console.error("Failed to fetch dashboard metrics", error);
        }
    }
    
    // Initialise and update charts
    function updateCharts(sentimentDist, categoryDist) {
        // 1. Sentiment Chart (Doughnut)
        const sentLabels = Object.keys(sentimentDist);
        const sentValues = Object.values(sentimentDist);
        
        if (sentimentChart) {
            sentimentChart.data.datasets[0].data = sentValues;
            sentimentChart.update();
        } else {
            const ctx = document.getElementById('sentiment-chart').getContext('2d');
            sentimentChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: sentLabels,
                    datasets: [{
                        data: sentValues,
                        backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                        borderWidth: 2,
                        borderColor: '#121426'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
                        }
                    }
                }
            });
        }
        
        // 2. Category Chart (Bar)
        const catLabels = Object.keys(categoryDist);
        const catValues = Object.values(categoryDist);
        
        if (categoryChart) {
            categoryChart.data.datasets[0].data = catValues;
            categoryChart.update();
        } else {
            const ctx = document.getElementById('category-chart').getContext('2d');
            categoryChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: catLabels,
                    datasets: [{
                        label: 'Requests',
                        data: catValues,
                        backgroundColor: '#6366f1',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                        y: { 
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }, 
                            ticks: { color: '#94a3b8', precision: 0 } 
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    }
    
    // Populate Feedback loop corrections logs table
    function updateFeedbackTable(recentCorrections) {
        if (!recentCorrections || recentCorrections.length === 0) {
            feedbackTableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-table-cell">No feedback submitted yet. Run 'simulate_traffic.py' or submit corrections in the playground.</td>
                </tr>
            `;
            return;
        }
        
        feedbackTableBody.innerHTML = "";
        
        recentCorrections.forEach(item => {
            const dateStr = new Date(item.timestamp).toLocaleTimeString();
            const textTrunc = item.text.length > 60 ? item.text.substring(0, 60) + "..." : item.text;
            
            // Format labels
            const predSentClass = item.predicted_sentiment === 'Positif' ? 'pos' : (item.predicted_sentiment === 'Neutre' ? 'neu' : 'neg');
            const actualSentClass = item.actual_sentiment === 'Positif' ? 'pos' : (item.actual_sentiment === 'Neutre' ? 'neu' : 'neg');
            
            const isDifferent = item.is_different === true || item.is_different === "True";
            const badgeType = isDifferent 
                ? `<span class="table-badge-type error">Correction</span>` 
                : `<span class="table-badge-type ok">Correct</span>`;
                
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${dateStr}</td>
                <td title="${item.text}">${textTrunc}</td>
                <td>
                    <span class="badge-sentiment-correct ${predSentClass}">${item.predicted_sentiment}</span>
                    / ${item.predicted_category}
                </td>
                <td>
                    <span class="badge-sentiment-correct ${actualSentClass}">${item.actual_sentiment}</span>
                    / ${item.actual_category}
                </td>
                <td>${badgeType}</td>
            `;
            feedbackTableBody.appendChild(row);
        });
    }
    
    // Refresh button listener
    refreshMetricsBtn.addEventListener('click', () => {
        fetchMetrics();
        checkApiHealth();
    });
    
    // Start timers and initial check
    checkApiHealth();
    fetchMetrics();
    
    // Poll API status & dashboard metrics every 5 seconds
    setInterval(() => {
        checkApiHealth();
        // Only fetch metrics if on the monitoring or feedback tab
        const activeTab = document.querySelector('.nav-item.active').getAttribute('data-tab');
        if (activeTab === 'monitoring-tab' || activeTab === 'feedback-tab') {
            fetchMetrics();
        }
    }, 5000);
});
