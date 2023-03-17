document.addEventListener('DOMContentLoaded', async () => {
    const chartElement = document.getElementById('myChart');
    chartElement.width = 2000;
    chartElement.height = 1200;
    const response = await fetch('/chart_data');
    const chartData = await response.json();
    const data = chartData.data;
    const labels = data.map(item => item.genre);
    const counts = data.map(item => item.count);

    const chart = new Chart(chartElement, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Genres',
                data: counts,
                backgroundColor: [
                    'rgba(49, 85, 87, 0.8)',
                    'rgba(96, 125, 128, 0.8)',
                    'rgba(144, 165, 168, 0.8)',
                    'rgba(192, 205, 208, 0.8)',
                    'rgba(240, 245, 245, 0.8)',
                    'rgba(248, 232, 198, 0.8)',
                    'rgba(245, 193, 121, 0.8)'
                ],
                borderColor: [
                    'rgba(49, 85, 87, 1)',
                    'rgba(96, 125, 128, 1)',
                    'rgba(144, 165, 168, 1)',
                    'rgba(192, 205, 208, 1)',
                    'rgba(240, 245, 245, 1)',
                    'rgba(248, 232, 198, 1)',
                    'rgba(245, 193, 121, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    chartElement.onclick = (event) => {
        const elements = chart.getElementsAtEventForMode(event, 'nearest', { intersect: true });
        if (elements.length) {
            const index = elements[0].index;
            const genre = chart.data.labels[index];
            window.location.href = `/songs/${genre}`;
        }
    };
});
