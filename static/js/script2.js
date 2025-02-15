let map;
let placemarks = [];
let point_on_map = [];

ymaps.ready(init);

function init() {
    map = new ymaps.Map(document.getElementById('map'), {
        center: [56.0184, 92.8672],
        zoom: 10,
        controls: ['zoomControl']
    });

    // Обработчик клика по карте
    map.events.add('click', function (e) {
        if (point_on_map.length != 1) {
            const coords = e.get('coords');
            addPoint(coords);

        } else {alert('Должна быть всего одна точка.');}
    });

    const route_id = document.getElementById('current_id').value
    var text = '/get_coords/' + route_id.toString()
    fetch(text)
    .then(response => response.json())
    .then(data => {
          let points = data.map(location => [location[0], location[1]]);
          let multiRoute = new ymaps.multiRouter.MultiRoute({
              referencePoints: points
     });

          map.geoObjects.add(multiRoute);
    });
    document.getElementById('search_places').onclick = getNearbyPlaces;
    document.getElementById('myButton2').onclick = clearRoute;
}

function addPoint(coords) {
    // Добавляем маркер на карту
    let placemark = new ymaps.Placemark(coords, {
        balloonContent: 'Точка'
    },
    {
        preset: 'islands#icon',
        iconColor: '#FF0000' // Задайте нужный цвет в формате HEX
    });

    map.geoObjects.add(placemark);
    placemarks.push(placemark);

    // Сохраняем координаты точки
    point_on_map.push(coords);
}


function getNearbyPlaces() {
    if (point_on_map.length == 0) {
        alert("Добавьте точку на карту, около которой искать");
        return;
    }
    fetch('/places', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'
        },
        body: JSON.stringify({ latitude: point_on_map[0][0], longitude: point_on_map[0][1] ,
                                "place": document.getElementById('place').value})
    })
    .then(response => response.json())
    .then(places => {
        displayPlaces(places);
    })
    .catch(err => console.error(err));
}

function displayPlaces(places) {
    // Удаляем все маркеры с карты
    placemarks.forEach(placemark => {
        map.geoObjects.remove(placemark);
    });
    // Очищаем массив маркеров и точек
    placemarks = [];
    let placemark = new ymaps.Placemark(point_on_map[0], {
        balloonContent: 'Точка'
    },
    {
        preset: 'islands#icon',
        iconColor: '#FF0000' // Задайте нужный цвет в формате HEX
    });

    map.geoObjects.add(placemark);
    placemarks.push(placemark);

    const placesDiv = document.getElementById('places');
    placesDiv.innerHTML = '';
    places.forEach(place => {
        const div = document.createElement('div');
        div.className = 'place';
        div.innerHTML = '<strong>' + place.name + '</strong> - ' + place.address + '<br>';

        // Добавляем маркер на карту для каждого места
        let placemark = new ymaps.Placemark(place.coordinates.reverse(), {
            balloonContent: place.name
        });
        map.geoObjects.add(placemark);
        placemarks.push(placemark);

        placesDiv.appendChild(div);
    });
}

function clearRoute() {
    // Удаляем все маркеры с карты
    placemarks.forEach(placemark => {
        map.geoObjects.remove(placemark);
    });

    // Очищаем массив маркеров и точек
    placemarks = [];
    point_on_map = [];
    const placesDiv = document.getElementById('places');
    placesDiv.innerHTML = '';
    document.getElementById('place').value = ""

}