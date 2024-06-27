function createPlot(table, labels, openPrices) {
    var trace = {
        x: labels,
        y: openPrices,
        type: 'scatter',
        mode: 'lines',
        marker: { color: 'orange' },
        line: { shape: 'linear', color: 'orange' }
    };

    var layout = {
        title: `Currency Exchange Rates for ${table}`,
        titlefont: { color: 'white' },
        paper_bgcolor: '#343a40',
        plot_bgcolor: '#343a40',
        xaxis: {
            title: 'Time',
            type: 'date',
            autorange: true,
            fixedrange: true,
            color: 'white'
        },
        yaxis: {
            title: 'Open Price',
            autorange: true,
            fixedrange: true,
            color: 'white'
        }
    };

    var config = { responsive: true };

    Plotly.newPlot(`chart-${table}`, [trace], layout, config);
}

function updateRange(table, range) {
    let endDate = new Date();
    let startDate = new Date();
    
    switch(range) {
        case '1h':
            startDate.setHours(endDate.getHours() - 1);
            break;
        case '1d':
            startDate.setDate(endDate.getDate() - 1);
            break;
        case '1w':
            startDate.setDate(endDate.getDate() - 7);
            break;
        case '1m':
            startDate.setMonth(endDate.getMonth() - 1);
            break;
        case '1y':
            startDate.setFullYear(endDate.getFullYear() - 1);
            break;
    }

    fetch(`/data/${table}/${startDate.toISOString()}/${endDate.toISOString()}/${range}`)
        .then(response => response.json())
        .then(data => {
            createPlot(table, data.labels, data.open_prices);
        });
}

var socket = io();

socket.on('update_data', function(data) {
    for (var table in data) {
        if (data.hasOwnProperty(table)) {
            var labels = data[table][0];
            var openPrices = data[table][1];

            var update = {
                x: [labels],
                y: [openPrices]
            };

            Plotly.update(`chart-${table}`, update);

            var currentXRange = document.getElementById(`chart-${table}`).layout.xaxis.range;
            if (currentXRange) {
                var rangeDuration = new Date(currentXRange[1]) - new Date(currentXRange[0]);
                var newXEnd = new Date(labels[labels.length - 1]);
                var newXStart = new Date(newXEnd - rangeDuration);

                var filteredPrices = openPrices.filter((price, index) => {
                    var date = new Date(labels[index]);
                    return date >= newXStart && date <= newXEnd;
                });

                var yMin = Math.min(...filteredPrices);
                var yMax = Math.max(...filteredPrices);

                Plotly.relayout(`chart-${table}`, {
                    'xaxis.range': [newXStart, newXEnd],
                    'yaxis.range': [yMin, yMax]
                });
            }
        }
    }
});
