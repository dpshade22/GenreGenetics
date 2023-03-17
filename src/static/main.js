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

    // Function to handle the intersection observer events
    function handleIntersection(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add the "show" class to the recommendations container when it is in view
                $('#recommendations-container').addClass('show');
                // Stop observing the element, since we only need to apply the effect once
                observer.unobserve(entry.target);
            }
        });
    }

    // Create a new intersection observer
    const observer = new IntersectionObserver(handleIntersection, { threshold: 0.2 });

    // Observe the recommendations container element
    observer.observe(document.querySelector('#recommendations-container'));

    // Function to handle the intersection observer events for fade-in effect
    function handleFadeIn(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add the "is-visible" class to the element when it is in view
                entry.target.classList.add('is-visible');
                // Stop observing the element, since we only need to apply the effect once
                observer.unobserve(entry.target);
            }
        });
    }

    // Create a new intersection observer for fade-in effect
    const fadeInObserver = new IntersectionObserver(handleFadeIn, { threshold: 0.2 });

    // Observe all elements with the "fade-in" class
    document.querySelectorAll('.fade-in').forEach(element => {
        fadeInObserver.observe(element);
    });
});
