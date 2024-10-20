function initializeDataTable(data, leagueId, orderByLatestPoints = false) { // Added parameter

    const tableHeader = document.getElementById('table-header');
    const tableBody = document.getElementById('data-body');
    const loadingButton = document.getElementById('toggle-button');
    loadingButton.style.display = 'none'; // Hide loading message

    // Create table headers dynamically
    const headers = data[0]; // First row contains headers
    const headerRow = document.createElement('tr');
    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header; // Set header text
        headerRow.appendChild(th);
    });
    tableHeader.appendChild(headerRow); // Append header row to the table

    // Initialize arrays to track max points and hits for each week
    const maxPoints = Array(headers.length - 1).fill(0); // Exclude team name
    const maxHits = Array(headers.length - 1).fill(0); // Exclude team name

    // Sort data by latest points if the parameter is true
    if (orderByLatestPoints) {
        data = [data[0], ...data.slice(1).sort((a, b) => { // Update this line
            const latestPointsA = parseInt(a[a.length - 1].split(':')[0]); // Get latest points for team A
            const latestPointsB = parseInt(b[b.length - 1].split(':')[0]); // Get latest points for team B
            return latestPointsB - latestPointsA; // Sort in descending order
        })]; // Ensure the header row is included
    }

    // Process each team row
    data.slice(1).forEach(row => {
        const tr = document.createElement('tr');

        // Team name
        const teamCell = document.createElement('td');
        teamCell.textContent = row[0]; // Team name
        tr.appendChild(teamCell);

        // Process scores and hits for each week
        row.slice(1).forEach((weekData, index) => {
            const [points, hits] = weekData.split(':'); // Split points and hits
            const weekCell = document.createElement('td');

            // Format the cell text as "points (hits)" if hits > 0
            weekCell.textContent = points; // Set cell text to points
            if (parseInt(hits) > 0) {
                const hitSpan = document.createElement('span'); // Create a span for hits
                hitSpan.textContent = ` (${hits})`; // Format hits
                hitSpan.style.color = 'blue'; // Change color for hits
                hitSpan.style.fontWeight = 'bold'; // Make hits bold
                weekCell.appendChild(hitSpan); // Append hits to the cell
            }

            // Update max points and hits for the week
            maxPoints[index] = Math.max(maxPoints[index], parseInt(points));
            maxHits[index] = Math.max(maxHits[index], parseInt(hits));

            // Append the week cell to the row
            tr.appendChild(weekCell);
        });

        // Append the completed row to the table body
        tableBody.appendChild(tr);
    });

    // Highlight max points in red and hits in blue for each week
    const weekCells = tableBody.querySelectorAll('tr');
    weekCells.forEach(row => {
        row.querySelectorAll('td:not(:first-child)').forEach((cell, index) => {
            const points = parseInt(cell.textContent.split(' ')[0]); // Get the points part
            if (points === maxPoints[index]) {
                cell.style.color = 'red'; // Highlight max points in red
                cell.style.fontWeight = 'bold'; // Make max points bold
            }
            const hits = cell.textContent.split('(')[1]; // Get hits part if exists
            if (hits && parseInt(hits) > 0) {
                cell.querySelector('span').style.color = 'blue'; // Highlight hits in blue
            }
        });
    });

    document.getElementById('data-table').style.display = 'table'; // Show the table
    if (orderByLatestPoints)
        drawLineChart(data); // Add this line to draw the chart
}
// New function to draw a line chart
function drawLineChart(data) {
    const teams = data.slice(1).map(row => row[0]); // Extract team names
    const pointsData = data.slice(1).map(row => row.slice(1).map(weekData => parseInt(weekData.split(':')[0]))); // Extract points for each week

    // Prepare data for each week
    const weeks = pointsData[0].length; // Number of weeks
    const rankings = Array.from({ length: weeks }, (_, weekIndex) => {
        const teamPoints = teams.map((team, index) => ({
            team,
            points: pointsData[index][weekIndex],
        }));
        teamPoints.sort((a, b) => b.points - a.points);
        return teamPoints.map((teamPoint, rank) => ({
            team: teamPoint.team,
            rank: rank + 1, // Rank starts from 1
        }));
    });

    const latestPoints = teams.map((team, index) => pointsData[index][weeks - 1]);
    const sortedTeams = teams
        .map((team, index) => ({ team, latestPoints: latestPoints[index] }))
        .sort((a, b) => b.latestPoints - a.latestPoints)
        .map(item => item.team);

    const traces = sortedTeams.map((team) => {
        const index = teams.indexOf(team);
        return {
            x: Array.from({ length: weeks }, (_, i) => `Week ${i + 1}`),
            y: rankings.map(week => week.find(t => t.team === team).rank),
            mode: 'lines+markers',
            name: team,
            line: {
                color: getRandomColor(),
                width: 2,
            },
            marker: {
                size: 6,
            },
            opacity: 1,
        };
    });

    const layout = {
        title: 'Team Rankings Over Weeks',
        xaxis: {
            title: 'Weeks',
        },
        yaxis: {
            title: 'Team Rank',
            autorange: 'reversed',
        },
        hovermode: 'closest',
        showlegend: true,
        legend: {
            orientation: 'h', // Change orientation to horizontal
            x: 0.5, // Center the legend
            y: -0.2, // Position it below the chart
            xanchor: 'center', // Anchor the legend to the center
            yanchor: 'top', // Anchor the legend to the top
            traceorder: 'normal',
        },
    };

    // Adjust layout for mobile screens
    if (window.matchMedia("(max-width: 600px)").matches) {
        layout.xaxis.title = 'Weeks';
        layout.yaxis.title = 'Team Rank';
        layout.xaxis.tickangle = -45; // Rotate x-axis labels
    }

    Plotly.newPlot('line-chart', traces, layout);

    // Add hover event to highlight the selected line
    const chartDiv = document.getElementById('line-chart');
    chartDiv.on('plotly_hover', function(data) {
        const index = data.points[0].curveNumber;
        const update = {
            'opacity': traces.map((_, i) => (i === index ? 1 : 0.3)),
            'line.width': traces.map((_, i) => (i === index ? 4 : 2)),
            'marker.size': traces.map((_, i) => (i === index ? 8 : 6)),
        };
        Plotly.restyle('line-chart', update);
    });

    chartDiv.on('plotly_unhover', function() {
        Plotly.restyle('line-chart', {
            'opacity': traces.map(() => 1),
            'line.width': traces.map(() => 2),
            'marker.size': traces.map(() => 6),
        });
    });
}

// Helper function to generate a random color
function getRandomColor() {
    const hue = Math.floor(Math.random() * 360); // Random hue between 0 and 360
    const saturation = '70%'; // Set saturation to 70%
    const lightness = '50%'; // Set lightness to 50%
    return `hsl(${hue}, ${saturation}, ${lightness})`; // Return the color in HSL format
}