document.addEventListener('DOMContentLoaded', async () => {
    let chart;

    function showLoadingScreen() {
        const loadingScreen = document.getElementById("loading-screen");
        loadingScreen.style.display = "flex";
        loadingScreen.style.opacity = "1";
    }

    function hideLoadingScreen() {
        const loadingScreen = document.getElementById("loading-screen");
        loadingScreen.style.opacity = "0";
        setTimeout(() => {
            loadingScreen.style.display = "none";
        }, 1000); // Hide the loading screen after 500ms to allow for fade out animation
    }


    async function renderChart() {
        if (chart) {
            chart.destroy(); // Destroy the previous chart instance if it exists
        }

        const chartElement = document.getElementById('myChart');
        chartElement.width = 2000;
        chartElement.height = 1200;


        const response = await fetch(`/chart_data`);
        const chartData = await response.json();
        const data = chartData.data;
        const labels = data.map(item => item.genre);
        const counts = data.map(item => item.count);
        const maxCount = Math.max(...counts);

        const gradient = chartElement.getContext('2d').createLinearGradient(0, 0, 1750, 0);
        gradient.addColorStop(0, '#990000'); // Bright yellow color
        gradient.addColorStop(0.46, '#00CA65'); // Bright teal color
        gradient.addColorStop(0.99, '#00CA65'); // Bright teal color

        chart = new Chart(chartElement, {
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
    }

    async function updateSidebarCards() {
        const response = await fetch(`/sidebar_card_data`);
        const sidebarCards = await response.json();

        const sidebarCardContainer = document.querySelector('.recently-played-cards');
        sidebarCardContainer.innerHTML = '';

        const recentlyPlayedHeader = document.querySelector('.sidebar-container h2');

        recentlyPlayedHeader.textContent = 'Recently Played:';

        for (const song of sidebarCards) {
            const songCard = document.createElement('a');
            songCard.href = song.url;
            songCard.target = '_blank';
            songCard.classList.add('song-card', 'fade-in');

            const songImage = document.createElement('img');
            songImage.src = song.image_url;
            songImage.alt = `${song.name} image`;
            songImage.classList.add('song-image');

            const songCardDetails = document.createElement('div');
            songCardDetails.classList.add('song-card-details');

            const songName = document.createElement('h3');
            songName.textContent = song.name;

            const songArtist = document.createElement('p');
            songArtist.textContent = song.artist;

            const songGene = document.createElement('p');
            songGene.textContent = song.gene;
            songGene.classList.add('gene');


            const libraryIndicator = document.createElement('i');
            if (song.is_in_library) {
                libraryIndicator.classList.add('fas', 'fa-check-circle', 'in-library-indicator', 'library-indicator', 'in-library');
                libraryIndicator.title = "This song is in your library";
            } else {
                libraryIndicator.classList.add('fas', 'fa-times-circle', 'not-in-library-indicator', 'library-indicator', 'not-in-library');
                libraryIndicator.title = "This song is not in your library";
            }


            songCardDetails.appendChild(songName);
            songCardDetails.appendChild(songArtist);
            songCardDetails.appendChild(songGene);
            songCardDetails.appendChild(libraryIndicator);

            songCard.appendChild(songImage);
            songCard.appendChild(songCardDetails);

            sidebarCardContainer.appendChild(songCard);
        }
        hideLoadingScreen();
    }

    async function updateChartAndSidebar() {
        showLoadingScreen();

        try {
            await Promise.all([renderChart(), updateSidebarCards()]);
        } catch (error) {
            console.error(error);
            // Handle error as needed
        } finally {
            hideLoadingScreen();
        }
    }


    // Call the function initially to render the chart and update the sidebar cards
    await updateChartAndSidebar();
});