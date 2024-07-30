let gestureDetected = false;
let selectedLabNumber = 906;  // Valor por defecto

function setLabNumber(labNumber) {
    selectedLabNumber = labNumber;
}

function startDetection() {
    document.getElementById('start-detection').style.display = 'none';
    document.getElementById('detection-container').style.display = 'block';
    processVideoFeed();
}

function postponeDetection() {
    document.getElementById('start-detection').style.display = 'none';
    document.getElementById('postpone-message').style.display = 'block';
}

function detectGesture(gesture) {
    if (!gestureDetected) {
        document.getElementById('gesture').innerText = gesture;
        document.getElementById('confirmation-message').style.display = 'block';
        document.getElementById('confirm-button').style.display = 'inline';
        document.getElementById('retry-button').style.display = 'inline';
        gestureDetected = true;
    }
}

function confirmReport() {
    let gesture = document.getElementById('gesture').innerText;
    // Aquí enviar el reporte a la base de datos
    fetch('/send_report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ gesture: gesture, num_lab: selectedLabNumber })
    }).then(response => {
        if (response.ok) {
            alert('Reporte enviado exitosamente');
            location.reload();  // Recargar la página para reiniciar la detección
        } else {
            alert('Error al enviar el reporte');
        }
    });
}

function retryDetection() {
    location.reload();
    document.getElementById('gesture').innerText = '';
    document.getElementById('confirmation-message').style.display = 'none';
    document.getElementById('confirm-button').style.display = 'none';
    document.getElementById('retry-button').style.display = 'none';
    document.getElementById('detection-container').style.display = 'none';
    document.getElementById('start-detection').style.display = 'block';
    gestureDetected = false;
}

// Ejemplo básico de detección de gestos
function processVideoFeed() {
    if (gestureDetected) return;

    fetch('/detect_gesture', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})  // Puedes enviar datos adicionales si es necesario
    }).then(response => response.json())
    .then(data => {
        let detectedGesture = data.gesture;
        if (detectedGesture) {
            detectGesture(detectedGesture);
        }
        setTimeout(processVideoFeed, 1000);  // Ajusta el intervalo según sea necesario
    });
}

// nuevos cambios

// script.js

// script.js

// Acceder a la cámara del usuario
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        document.getElementById('video').srcObject = stream;
    })
    .catch(error => {
        console.error("Error accessing the camera: ", error);
    });

function captureAndSubmit() {
    let video = document.getElementById('video');
    let canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    let context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convertir la imagen a base64
    let dataURL = canvas.toDataURL('image/jpg');
    let username = document.getElementById('username').value;

    // Enviar la imagen y el nombre de usuario al servidor
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            image: dataURL
        })
    }).then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    }).then(data => {
        if (data.success) {
            window.location.href = data.redirect_url;
        } else {
            alert('Login fallido: ' + data.message);
        }
    }).catch(error => {
        console.error('There was a problem with the fetch operation:', error);
    });
}
