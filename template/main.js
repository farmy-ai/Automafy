

$(document).ready(async () => {

    const res = await fetch('http://localhost:5000/stats');
    const stats = res.json()

    const data = {
        labels: ['Total', 'Healthy', 'Class 1', 'Class 2', 'Class 3'],
        datasets: [
            {
                label: 'Stats',
                data: [600, 200, 5, 2, 20],
            }
        ]
    };

    const config = {
        type: 'bar',
        data,
        options: {}
    };

    var myChart = new Chart(
        document.getElementById('myChart'),
        config
    );
})