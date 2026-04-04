/*
 * EduTrack Pro - Charts JavaScript
 * Chart.js implementation for dashboard charts
 */

// Weekly Bar Chart
let weeklyChartInstance = null;

function initWeeklyChart(data) {
    const ctx = document.getElementById('weeklyChart');
    if (!ctx) return;
    
    if (weeklyChartInstance) {
        weeklyChartInstance.destroy();
    }
    
    const labels = data.map(item => item.day);
    const presentData = data.map(item => item.present);
    const absentData = data.map(item => item.absent);
    
    weeklyChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Present',
                    data: presentData,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: 'rgb(16, 185, 129)',
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: 'Absent',
                    data: absentData,
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderColor: 'rgb(239, 68, 68)',
                    borderWidth: 1,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            const total = presentData[context.dataIndex] + absentData[context.dataIndex];
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Doughnut Chart
let doughnutChartInstance = null;

function initDoughnutChart(data) {
    const ctx = document.getElementById('doughnutChart');
    if (!ctx) return;
    
    if (doughnutChartInstance) {
        doughnutChartInstance.destroy();
    }
    
    const total = data.present + data.absent;
    const presentPercentage = total > 0 ? Math.round((data.present / total) * 100) : 0;
    const absentPercentage = total > 0 ? Math.round((data.absent / total) * 100) : 0;
    
    doughnutChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Present', 'Absent'],
            datasets: [{
                data: [data.present, data.absent],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderColor: [
                    'rgb(16, 185, 129)',
                    'rgb(239, 68, 68)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const percentage = context.dataIndex === 0 ? presentPercentage : absentPercentage;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                },
                centerText: {
                    display: true,
                    text: total > 0 ? presentPercentage + '%' : '0%',
                    subText: 'Present'
                }
            }
        },
        plugins: [{
            id: 'centerText',
            beforeDraw: function(chart) {
                if (chart.config.options.plugins.centerText.display) {
                    const { width, height, ctx } = chart;
                    ctx.restore();
                    
                    const fontSize = (height / 200).toFixed(2);
                    ctx.font = 'bold ' + fontSize + 'em Inter, sans-serif';
                    ctx.textBaseline = 'middle';
                    ctx.textAlign = 'center';
                    
                    const text = chart.config.options.plugins.centerText.text;
                    const subText = chart.config.options.plugins.centerText.subText;
                    const x = width / 2;
                    const y = height / 2;
                    
                    ctx.fillStyle = '#1e293b';
                    ctx.fillText(text, x, y - 10);
                    
                    ctx.font = fontSize / 2 + 'em Inter, sans-serif';
                    ctx.fillStyle = '#64748b';
                    ctx.fillText(subText, x, y + 20);
                    
                    ctx.save();
                }
            }
        }]
    });
}

// Line Chart
let lineChartInstance = null;

function initLineChart(data) {
    const ctx = document.getElementById('lineChart');
    if (!ctx) return;
    
    if (lineChartInstance) {
        lineChartInstance.destroy();
    }
    
    // Filter out null values and prepare data
    const validData = data.filter(item => item.percentage !== null);
    const labels = validData.map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    const percentages = validData.map(item => item.percentage);
    
    // Create gradient
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(79, 70, 229, 0.3)');
    gradient.addColorStop(1, 'rgba(79, 70, 229, 0)');
    
    lineChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Attendance %',
                data: percentages,
                borderColor: 'rgb(79, 70, 229)',
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5,
                pointBackgroundColor: 'rgb(79, 70, 229)',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Attendance: ${context.parsed.y}%`;
                        }
                    }
                },
                annotation: {
                    annotations: {
                        line75: {
                            type: 'line',
                            yMin: 75,
                            yMax: 75,
                            borderColor: 'rgb(239, 68, 68)',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {
                                display: true,
                                content: '75% Target',
                                position: 'end'
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Export functions
window.initWeeklyChart = initWeeklyChart;
window.initDoughnutChart = initDoughnutChart;
window.initLineChart = initLineChart;
