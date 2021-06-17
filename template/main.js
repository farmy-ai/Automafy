
var myChart;

$(document).ready(async () => {

    await setup();

    $('.on_off').on('click', async () => {


        alive = !$('.on_off').hasClass('active');

        await fetch('http://localhost:5000/power', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
                // 'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: JSON.stringify({ alive })
        })

        alive
            ? $('.on_off').addClass('active')
            : $('.on_off').removeClass('active');

        alive
            ? $('.on_off>h2').addClass('active')
            : $('.on_off>h2').removeClass('active');

    })

    setInterval(async () => {

        const s = await get_stats();
        myChart.data.datasets.forEach(d => {
            d.data = s;
        })

        myChart.update();

    }, 5000);
})

function indexOfMax(arr) {
    if (arr.length === 0) {
        return -1;
    }

    var max = arr[0];
    var maxIndex = 0;

    for (var i = 1; i < arr.length; i++) {
        if (arr[i] > max) {
            maxIndex = i;
            max = arr[i];
        }
    }

    return maxIndex;
}

async function setup() {

    let predictions = await get_stats();

    console.log(predictions);

    const data = {
        labels: ['Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5', 'Class 6'],
        datasets: [
            {
                label: 'Stats',
                data: predictions,
            }
        ]
    };

    const config = {
        type: 'bar',
        data,
        options: {}
    };

    myChart = new Chart(
        document.getElementById('myChart'),
        config
    );
}

async function get_stats() {
    let res = await fetch('http://localhost:5000/stats');
    res = await res.json();

    let predictions = [];

    for (let i = 0; i < res.statistics[0].prediction.length; i++) {
        predictions.push(0);
    }


    res.statistics.map(v => v.prediction).forEach(p => {


        predictions[indexOfMax(p)]++;

    });
    return predictions;
}
