document.addEventListener('DOMContentLoaded', function () {

    const chatBox = document.getElementById("chat-box");
    if (chatBox && chatBox.dataset.ticketId) {
        setInterval(() => {
            fetch(`/api/users/ticket/${chatBox.dataset.ticketId}/messages/`)
                .then(res => res.json())
                .then(data => {
                    chatBox.innerHTML = data.html;
                });
        }, 5000);
    }


    // === scroll restore ===
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', () => {
            localStorage.setItem('scrollPos', window.scrollY);
        });
    });

    const pos = localStorage.getItem('scrollPos');
    if (pos) {
        window.scrollTo(0, parseInt(pos));
        localStorage.removeItem('scrollPos');
    }

    initFlatpickr();
    initMapForm();

    const toggleBtn = document.getElementById('menu-toggle');
    const navLinks = document.getElementById('nav-links');

    if (toggleBtn && navLinks) {
        toggleBtn.addEventListener('click', () => {
            navLinks.classList.toggle('open');
        });
    }

    // Анимация появления карточек
    const cards = document.querySelectorAll('.event-card');
    cards.forEach((card, index) => {
        card.style.setProperty('--order', index);
    });

    // Скрыть/показать карту
    const toggleMapBtn = document.querySelector('[data-toggle-map]');
    const mapContainer = document.querySelector('.map-section .map-box');
    if (toggleMapBtn && mapContainer) {
        let mapInitialized = false;

        toggleMapBtn.addEventListener('click', () => {
            mapContainer.classList.toggle('visible');

            if (!mapInitialized && mapContainer.classList.contains('visible')) {
                ymaps.ready(function () {
                    const lat = parseFloat(mapContainer.dataset.lat);
                    const lon = parseFloat(mapContainer.dataset.lon);
                    const title = mapContainer.dataset.title;

                    window.myMap = new ymaps.Map("map", {
                        center: [lat, lon],
                        zoom: 14
                    });

                    const placemark = new ymaps.Placemark([lat, lon], {
                        balloonContent: title
                    });
                    window.myMap.geoObjects.add(placemark);
                });
                mapInitialized = true;
            }
        });
    }

    // Показ/скрытие формы ответа
    document.querySelectorAll('.reply-toggle').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const commentId = this.dataset.commentId;
            const form = document.querySelector(`.reply-form[data-form-for="${commentId}"]`);
            if (form) {
                form.style.display = form.style.display === 'none' ? 'block' : 'none';
            }
        });
    });

    // Показ/скрытие вложенных комментариев
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const commentId = this.getAttribute('onclick').match(/\d+/)[0];
            const replies = document.getElementById(`replies-${commentId}`);
            if (replies) {
                const isHidden = replies.style.display === 'none';
                replies.style.display = isHidden ? 'block' : 'none';
                this.textContent = isHidden ? 'Скрыть ответы' : 'Показать ответы';
            }
        });
    });

    // Вывод Django сообщений в toast
    const djangoMessages = document.querySelectorAll('.messages .message');
    djangoMessages.forEach(msg => {
        const text = msg.textContent.trim();
        let type = 'info';
        if (msg.classList.contains('success')) type = 'success';
        else if (msg.classList.contains('error')) type = 'error';
        else if (msg.classList.contains('warning')) type = 'warning';
        showToast(type, text);
        msg.remove();
    });
});

function previewImage(event) {
    const preview = document.getElementById('preview');
    const currentImage = document.getElementById('current-image');

    if (!preview) return;

    preview.src = URL.createObjectURL(event.target.files[0]);
    preview.style.display = 'block';

    if (currentImage) {
        currentImage.style.display = 'none';
    }
}

function initFlatpickr() {
    if (typeof flatpickr === 'undefined') return;

    flatpickr.localize(flatpickr.l10ns.ru);

    const startInput = document.getElementById('start_time');
    const endInput = document.getElementById('end_time');

    if (!startInput || !endInput) return;

    const endPicker = flatpickr(endInput, {
        enableTime: true,
        dateFormat: "d.m.Y, H:i",
        time_24hr: true,
        minDate: "today"
    });

    flatpickr(startInput, {
        enableTime: true,
        dateFormat: "d.m.Y, H:i",
        time_24hr: true,
        minDate: "today",
        onChange: function (selectedDates) {
            if (selectedDates.length) {
                endPicker.set("minDate", selectedDates[0]);
            }
        }
    });
}

function initMapForm() {
    const latInput = document.getElementById('latitude');
    const lonInput = document.getElementById('longitude');
    const locationInput = document.getElementById('location');
    const mapContainer = document.getElementById('map');

    if (!latInput || !lonInput || !mapContainer) return;

    const lat = parseFloat(latInput.value) || 55.751574;
    const lon = parseFloat(lonInput.value) || 37.573856;

    ymaps.ready(function () {
        const myMap = new ymaps.Map("map", {
            center: [lat, lon],
            zoom: 10
        });

        const placemark = new ymaps.Placemark([lat, lon], {}, { draggable: true });
        myMap.geoObjects.add(placemark);

        placemark.events.add('dragend', function () {
            const coords = placemark.geometry.getCoordinates();
            latInput.value = coords[0].toFixed(6);
            lonInput.value = coords[1].toFixed(6);
            getAddressFromCoords(coords, locationInput);
        });

        myMap.events.add('click', function (e) {
            const coords = e.get('coords');
            placemark.geometry.setCoordinates(coords);
            latInput.value = coords[0].toFixed(6);
            lonInput.value = coords[1].toFixed(6);
            getAddressFromCoords(coords, locationInput);
        });
    });
}

function getAddressFromCoords(coords, locationInput) {
    ymaps.geocode(coords, { results: 1, sco: "latlong" }).then(function (res) {
        const firstGeoObject = res.geoObjects.get(0);
        if (firstGeoObject) {
            const address = firstGeoObject.getAddressLine();
            setTimeout(function () {
                locationInput.value = address;
                locationInput.blur();
                locationInput.focus();
            }, 200);
        } else {
            locationInput.value = "";
        }
    }).catch(function () {
        locationInput.value = "";
    });
}

function showToast(type, message) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerText = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 7000);
}
