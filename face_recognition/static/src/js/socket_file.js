var socket = io.connect('http://' + document.domain + ':' + location.port);
    socket.on('update_name', function(data) {
        var nameElement = document.getElementById('detectedName');
        var imageElement = document.getElementById('matched-image');
        var dateElement = document.getElementById('recDate');
        var timeElement = document.getElementById('recTime');
        var personIDElement = document.getElementById('person_id');
        var designationElement = document.getElementById('designation');

        nameElement.innerText = data.name;
        dateElement.innerText = data.rec_date;
        timeElement.innerText = data.rec_time;
        personIDElement.innerText = data.person_id;
        designationElement.innerText = data.designation;

        imageElement.src = data.image_url;
        imageElement.style.display = 'block';
    });
