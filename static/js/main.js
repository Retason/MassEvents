document.addEventListener('DOMContentLoaded', function () {
    initFlatpickr();
    initMapForm();
    const toggleBtn = document.getElementById('menu-toggle');
    const navLinks = document.getElementById('nav-links');

    toggleBtn.addEventListener('click', () => {
        navLinks.classList.toggle('open');
    });

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

});

// Предпросмотр изображения
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

// Инициализация Flatpickr для полей даты
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
        onChange: function(selectedDates) {
            if (selectedDates.length) {
                endPicker.set("minDate", selectedDates[0]);
            }
        }
    });
}

// Инициализация Яндекс.Карты в форме
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


// Поддержка сброса превью при повторной загрузке
document.getElementById('image')?.addEventListener('change', function(event) {
    const preview = document.getElementById('preview');
    if (event.target.files.length > 0) {
        const file = event.target.files[0];
        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        const maxSize = 5 * 1024 * 1024; // 5MB

        if (!allowedTypes.includes(file.type)) {
            alert('Разрешены только изображения (JPG, PNG, WEBP)');
            event.target.value = '';
            preview.style.display = 'none';
            return;
        }

        if (file.size > maxSize) {
            alert('Размер изображения не должен превышать 5MB');
            event.target.value = '';
            preview.style.display = 'none';
            return;
        }

        preview.src = URL.createObjectURL(file);
        preview.style.display = 'block';
    }
});