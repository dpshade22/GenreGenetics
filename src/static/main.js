document.addEventListener('DOMContentLoaded', async () => {
    let chart;

    function showLoadingScreen() {
        document.getElementById("loading-screen").style.display = "flex";
    }

    function hideLoadingScreen() {
        document.getElementById("loading-screen").style.display = "none";
    }

    async function fetchDataAndRenderChart() {
        if (chart) {
            chart.destroy(); // Destroy the previous chart instance if it exists
        }

        const chartElement = document.getElementById('myChart');
        chartElement.width = 2000;
        chartElement.height = 1200;
        const topTracks = document.querySelector('input[name="top_tracks"]:checked').value;
        const response = await fetch(`/chart_data?top_tracks=${topTracks}`);
        const chartData = await response.json();
        const data = chartData.data;
        const labels = data.map(item => item.genre);
        const counts = data.map(item => item.count);
        const maxCount = Math.max(...counts);

        const gradient = chartElement.getContext('2d').createLinearGradient(0, 0, 1750, 0);
        gradient.addColorStop(0, 'rgb(20, 70, 70)');
        gradient.addColorStop(0.99, 'rgb(239, 221, 141)');

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
        const topTracks = document.querySelector('input[name="top_tracks"]:checked').value;
        const response = await fetch(`/sidebar_card_data?top_tracks=${topTracks}`);
        const sidebarCards = await response.json();

        const sidebarCardContainer = document.querySelector('.recently-played-cards');
        sidebarCardContainer.innerHTML = '';

        const recentlyPlayedHeader = document.querySelector('.sidebar-container h2');
        if (topTracks === 'True') {
            recentlyPlayedHeader.textContent = 'Top Songs:';
        } else {
            recentlyPlayedHeader.textContent = 'Recently Played:';
        }
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

            songCardDetails.appendChild(songName);
            songCardDetails.appendChild(songArtist);
            songCardDetails.appendChild(songGene);

            songCard.appendChild(songImage);
            songCard.appendChild(songCardDetails);

            sidebarCardContainer.appendChild(songCard);
        }
    }




    // Call the function initially to render the chart
    fetchDataAndRenderChart();
    updateSidebarCards(); // Call the function to update the sidebar cards

    hideLoadingScreen();

    // Add the submit event listener to the form
    document.getElementById("top-tracks-form").addEventListener("submit", async function (event) {
        event.preventDefault(); // prevent the default form submission behavior


        // Collect the form data
        const formData = new FormData(event.target);

        // Post the form data
        const response = await fetch(event.target.action, {
            method: 'POST',
            body: formData
        });

        // Check if the response is ok, and re-execute the chart rendering function
        if (response.ok) {
            showLoadingScreen(); // Show the loading screen
            fetchDataAndRenderChart(); // Call the function to render the chart
            await updateSidebarCards(); // Call the function to update the sidebar cards'
            hideLoadingScreen(); // Hide the loading screen
        }
    });
});
