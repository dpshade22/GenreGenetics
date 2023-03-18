document.addEventListener('DOMContentLoaded', async () => {
    const chartElement = document.getElementById('myChart');
    chartElement.width = 2000;
    chartElement.height = 1200;
    const response = await fetch('/chart_data');
    const chartData = await response.json();
    const data = chartData.data;
    const labels = data.map(item => item.genre);
    const counts = data.map(item => item.count);
    const maxCount = Math.max(...counts);

    const gradient = chartElement.getContext('2d').createLinearGradient(0, 0, 1750, 0);
    gradient.addColorStop(0, 'rgb(20, 70, 70)');
    gradient.addColorStop(0.99, 'rgb(239, 221, 141)');


    const chart = new Chart(chartElement, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Genres',
                data: counts,
                backgroundColor: gradient,
                borderColor: gradient,
                borderWidth: 0.1
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: maxCount + 1

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
