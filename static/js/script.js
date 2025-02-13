let map;
let placemarks = [];
let points = [];

ymaps.ready(init);

function init() {
    map = new ymaps.Map(document.getElementById('map'), {
        center: [56.0184, 92.8672],
        zoom: 10,
        controls: ['zoomControl']
    });

    // Обработчик клика по карте
    map.events.add('click', function (e) {
        const coords = e.get('coords');
        addPoint(coords);
    });

    document.getElementById('myButton').onclick = getRoute;
    document.getElementById('myButton2').onclick = clearRoute;
}

function addPoint(coords) {
    // Добавляем маркер на карту
    let placemark = new ymaps.Placemark(coords, {
        balloonContent: 'Точка'
    });

    map.geoObjects.add(placemark);
    placemarks.push(placemark);

    // Сохраняем координаты точки
    points.push(coords);

    // Обновляем список точек на странице
    updatePointsList();
}

function updatePointsList() {
    const pointsList = document.getElementById('pointsList');
    pointsList.innerHTML = '';

    points.forEach((point, index) => {
        const div = document.createElement('div');
        div.className = 'point';
        pointsList.appendChild(div);
    });
}

function getRoute() {
    if (points.length < 2) { // Проверяем, что есть хотя бы 2 точки
        alert('Пожалуйста, добавьте хотя бы 2 точки для построения маршрута.');
        return;
    }
    fetch('/map', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ points: points }) // Исправлено
    })
    .then(response => response.json())
    .then(coordinates => {
        // Удаляем предыдущий маршрут, если он есть
        if (map.geoObjects.getLength() > placemarks.length) {
            // Удаляем все маршруты
            for (let i = placemarks.length; i < map.geoObjects.getLength(); i++) {
                map.geoObjects.remove(map.geoObjects.get(i));
            }
        }

        // Создаем маршрут
        let multiRoute = new ymaps.multiRouter.MultiRoute({
            referencePoints: coordinates,
            params: {
                results: 1
            }
        });
        console.log(JSON.stringify(coordinates))
        document.getElementById('routeCoordinates').value = JSON.stringify(coordinates);
        map.geoObjects.add(multiRoute);
        map.setBounds(multiRoute.getBounds());

    })

}

// Функция для очистки маршрута и маркеров
function clearRoute() {
    // Удаляем все маркеры с карты
    placemarks.forEach(placemark => {
        map.geoObjects.remove(placemark);
    });

    // Очищаем массив маркеров и точек
    placemarks = [];
    points = [];

    // Очищаем список точек на странице
    updatePointsList();

    // Удаляем все маршруты с карты
    map.geoObjects.each(function (geoObject) {
        if (geoObject instanceof ymaps.multiRouter.MultiRoute) {
            map.geoObjects.remove(geoObject);
        }
    });
}
