(() => {
    "use strict";

    const mapElement = document.getElementById("aetheon-map");

    if (!mapElement || typeof L === "undefined") {
        return;
    }

    const statusElement = document.getElementById(
        "aetheon-map-status"
    );

    const setStatus = (message) => {
        if (statusElement) {
            statusElement.textContent = message;
        }
    };

    const valueFromFeature = (feature, key) => {
        const properties = feature.properties || {};
        return feature[key] ?? properties[key];
    };

    const buildPopup = (feature) => {
        const fields = [
            ["Nombre", valueFromFeature(feature, "name")],
            ["Tipo", valueFromFeature(feature, "kind")],
            ["ID", valueFromFeature(feature, "id")],
        ].filter(([, value]) => value !== undefined && value !== null && value !== "");

        if (!fields.length) {
            return null;
        }

        const container = document.createElement("dl");

        fields.forEach(([label, value]) => {
            const term = document.createElement("dt");
            const description = document.createElement("dd");

            term.textContent = label;
            description.textContent = String(value);
            container.append(term, description);
        });

        return container;
    };

    const map = L.map(mapElement);

    L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        {
            maxNativeZoom: 19,
            maxZoom: 22,
            attribution: "Tiles &copy; Esri &mdash; Source: Esri and contributors",
        }
    ).addTo(map);

    fetch(mapElement.dataset.geojson)
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return response.json();
        })
        .then((data) => {
            const geojsonLayer = L.geoJSON(data, {
                onEachFeature(feature, layer) {
                    const popup = buildPopup(feature);

                    if (popup) {
                        layer.bindPopup(popup);
                    }
                },
            }).addTo(map);

            const bounds = geojsonLayer.getBounds();

            if (!bounds.isValid()) {
                throw new Error("El GeoJSON no contiene geometrías válidas.");
            }

            map.fitBounds(bounds, { padding: [20, 20] });
            setStatus("");
        })
        .catch((error) => {
            console.error("Unable to load AETHEON.geojson:", error);
            setStatus("No se ha podido cargar la cartografía de Aetheon.");
        });
})();
