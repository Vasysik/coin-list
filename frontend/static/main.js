function createPlot(table, labels, openPrices) {
    var trace = {
        x: labels,
        y: openPrices,
        type: 'scatter',
        mode: 'lines',
        marker: { color: 'blue' },
        line: { shape: 'linear' }
    };

    var layout = {
        title: 'Currency Exchange Rates for ' + table,
        xaxis: {
            title: 'Time',
            rangeselector: {
                buttons: [
                    { count: 1, label: '1h', step: 'hour', stepmode: 'backward' },
                    { count: 24, label: '1d', step: 'hour', stepmode: 'backward' },
                    { count: 7, label: '1w', step: 'day', stepmode: 'backward' },
                    { count: 1, label: '1m', step: 'month', stepmode: 'backward' },
                    { step: 'all', label: 'All' }
                ]
            },
            rangeslider: { visible: false },
            type: 'date',
            autorange: true,
            fixedrange: true
        },
        yaxis: {
            title: 'Open Price',
            autorange: true,
            fixedrange: true
        }
    };

    var config = { responsive: true };

    Plotly.newPlot('chart-' + table, [trace], layout, config);

    document.getElementById('chart-' + table).on('plotly_relayout', function(eventdata) {
        if (eventdata['xaxis.range[0]'] && eventdata['xaxis.range[1]']) {
            updateYAxisRange('chart-' + table, labels, openPrices);
        }
    });
}

function updateYAxisRange(chartId, labels, openPrices) {
    var xRange = document.getElementById(chartId).layout.xaxis.range;
    var xStart = new Date(xRange[0]);
    var xEnd = new Date(xRange[1]);

    var filteredPrices = openPrices.filter((price, index) => {
        var date = new Date(labels[index]);
        return date >= xStart && date <= xEnd;
    });

    if (filteredPrices.length > 0) {
        var yMin = Math.min(...filteredPrices);
        var yMax = Math.max(...filteredPrices);

        Plotly.relayout(chartId, {
            'yaxis.range': [yMin, yMax]
        });
    }
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

            Plotly.update('chart-' + table, update);

            var currentXRange = document.getElementById('chart-' + table).layout.xaxis.range;
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

                Plotly.relayout('chart-' + table, {
                    'xaxis.range': [newXStart, newXEnd],
                    'yaxis.range': [yMin, yMax]
                });
            }
        }
    }
});
