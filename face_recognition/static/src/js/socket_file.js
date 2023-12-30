var socket = io.connect('http://' + document.domain + ':' + location.port);
    socket.on('update_name', function(data) {
        var nameElement = document.getElementById('detectedName');
        var imageElement = document.getElementById('matched-image');

        nameElement.innerText = data.name;


        imageElement.src = data.image_url;
        console.log(imageElement.src);
        imageElement.style.display = 'block';
    });
