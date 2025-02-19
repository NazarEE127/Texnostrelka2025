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
     var searchControl = new ymaps.control.SearchControl({
                options: {
                    float: 'right'
                }
            });

     map.controls.add(searchControl);

    // Обработчик клика по карте
    map.events.add('click', function (e) {
        const coords = e.get('coords');
        addPoint(coords);
    });

    document.getElementById('myButton').onclick = getRoute;
    document.getElementById('myButton2').onclick = clearRoute;
    document.getElementById('import').onclick = import_coords;
    document.getElementById('q').onclick = Q;
}

function addPoint(coords) {
    var i = placemarks.length + 1
    // Добавляем маркер на карту
    let placemark = new ymaps.Placemark(coords, {
        balloonContent: 'Точка' + i.toString(),
        balloonContent: `
                <p><input type="text" id="marker-title" placeholder="Введите название метки"></p>
                <p><input type="text" id="marker-description" placeholder="Введите описание метки"></p>
                <p><input type="file" id="fileInput" name="file" required></p>
                <p><button onclick="saveMarkerName([${coords}])">Сохранить</button></p>
            `
    });
    // Открываем балун при клике на метку
    placemark.events.add('click', function () {
        placemark.balloon.open();
    });

    map.geoObjects.add(placemark);
    placemarks.push(placemark);

    // Сохраняем координаты точки
    points.push(coords);

    // Обновляем список точек на странице
    updatePointsList();
}
window.saveMarkerName = function (coords) {
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        fetch("/add_point_photo", {
               method: 'POST',
               body: formData
        })
        .then(response => {
            if (response.ok) {
                return response.json(); // Преобразуем ответ в JSON
            }
            throw new Error('Ошибка при загрузке файла');
        })
        .then(points_id => {
            fetch("/add_point", {
                   method: 'POST',
                   headers: {
                    'Content-Type': 'application/json'
                    },
                   body: JSON.stringify({ "title":  document.getElementById('marker-title').value,
                                          "description": document.getElementById('marker-description').value,
                                           "point_id": points_id[0]})
            })
            document.getElementById('points_id').value = document.getElementById('points_id').value + "|" + points_id[0];
        })


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
        document.getElementById('routeCoordinates').value = JSON.stringify(coordinates);
        map.geoObjects.add(multiRoute);
        map.setBounds(multiRoute.getBounds());

    })
    .catch(err => console.error(err));

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
function import_coords() {
    if (document.getElementById('url').value.length == 0){
        alert('Пожалуйста, введите ссылку');
        return;
    }
    fetch('/import_coords', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ "url":  document.getElementById('url').value})
    })
    .then(response => response.json())
    .then(imp_coord => {
    for (const item of imp_coord){
        addPoint(item);
    }
    })
    .catch(err => console.error(err));
}
function Q() {
    alert("Инструкция 'Как создать маршрут без импорта':\n1)Поставить точки на карте, через которые будет проходить маршрут\n2)Нажать кнопку 'Построить маршрут'\nИнструкция 'Импорт маршрута':\n1)В текстовом поле введите ссылку на маршрут из доступных сервисов(OSM, Google Map, Yandex Map)\nСсылка должна выглядеть так:\nOSM - https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=56.01%2C92.87%3B55.63%2C37.61#map=3/55.43/65.21\nGoogle Map - https://maps.app.goo.gl/giaX2teWu1PL3YUo7\nYandex Map - https://yandex.ru/maps/?ll=65.234010%2C55.550930&mode=routes&rtext=56.010543%2C92.852581~55.755864%2C37.617698&rtt=auto\n2)Нажать кнопку 'Построить маршрут'\nЕсли хотите очистить всё, нажмите кнопку 'Очистить маршрут'")
}