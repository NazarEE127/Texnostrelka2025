//
//import { YMap, YMapDefaultSchemeLayer } from './lib/ymaps.js'
//
//const map = new ymaps.Map(
//    document.getElementById('map'),{
//                   center: [55.76, 37.64], // координаты центра карты
//                   zoom: 10 // уровень масштабирования
//               });
//
//               // Проверка координат перед добавлением маркера
//               var coordinates = [55.76, 37.64]; // пример координат
//
//               if (coordinates && coordinates.length === 2) {
//                   var myPlacemark = new ymaps.Placemark(coordinates, {
//                       balloonContent: 'Это мой маркер!'
//                   });
//
//                   map.geoObjects.add(myPlacemark);
//               } else {
//                   console.error('Координаты не определены или имеют неправильный формат');
//               }
//
//map.addChild(new YMapDefaultSchemeLayer());


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
    console.log(points[0][0])
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

        map.geoObjects.add(multiRoute);
        map.setBounds(multiRoute.getBounds());
    })
}
