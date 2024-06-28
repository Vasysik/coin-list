var currentRanges = {};

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
        paper_bgcolor: '#343a40',
        plot_bgcolor: '#343a40',
        xaxis: {
            type: 'date',
            autorange: true,
            fixedrange: true,
            color: 'white'
        },
        yaxis: {
            autorange: true,
            fixedrange: true,
            color: 'white'
        },
        margin: {
            l: 50,
            r: 20,
            b: 50,
            t: 20,
            pad: 4
        }
    };

    var config = { responsive: true };

    Plotly.newPlot(`chart-${table}`, [trace], layout, config);
}

function updateRange(table, range) {
    if (range) {
        currentRanges[table] = range;
    } else if (currentRanges[table]) {
        range = currentRanges[table];
    } else {
        range = '1d'; 
    }

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
            updateButtonStyles(table, range);
        });
}

function updateButtonStyles(table, activeRange) {
    const buttonGroup = document.querySelector(`#chart-${table}`).closest('.card-body').querySelector('.btn-group');
    buttonGroup.querySelectorAll('.btn').forEach(button => {
        if (button.getAttribute('onclick').includes(activeRange)) {
            button.classList.add('btn-active');
        } else {
            button.classList.remove('btn-active');
        }
    });
}