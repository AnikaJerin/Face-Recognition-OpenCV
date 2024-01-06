let imageIndex = 0;

function captureImage() {
        fetch('/capture_frame')
            .then(response => response.blob())
            .then(blob => {
                    const imageUrl = URL.createObjectURL(blob);
                    
                    const imgId = 'avtImg' + imageIndex;
                    document.getElementById(imgId).src = imageUrl;

                    imageIndex = (imageIndex + 1) % 3;
                });
        }