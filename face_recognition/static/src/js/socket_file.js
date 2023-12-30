var socket = io.connect('http://' + document.domain + ':' + location.port);
    socket.on('update_name', function(data) {
        var nameElement = document.getElementById('detectedName');
        var imageElement = document.getElementById('matched-image');
        var dateElement = document.getElementById('recDate');
        var timeElement = document.getElementById('recTime');

        nameElement.innerText = data.name;
        dateElement.innerText = data.rec_date;
        timeElement.innerText = data.rec_time;

        imageElement.src = data.image_url;
        imageElement.style.display = 'block';
    });
