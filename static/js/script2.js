let map;

ymaps.ready(init);

function init() {
    map = new ymaps.Map(document.getElementById('map'), {
        center: [56.0184, 92.8672],
        zoom: 10,
        controls: ['zoomControl']
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
}