import sys
from random import uniform
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QTimer
import folium
import math
import pickle

# -----------------------
# UAV positions
# -----------------------
with open("../tests/planes_canada.pkl", "rb") as f:
    planes_data = pickle.load(f)

planes_list = []
for plane in planes_data.get("states", []):
    if plane[8]:
        continue
    planes_list.append({
        "icao24": plane[0],
        "callsign": plane[1],
        "lat": plane[6],
        "lon": plane[5],
        "geo_alt": plane[13] if plane[13] else 0
    })

uavs = {
    plane["callsign"]:[plane["lat"], plane["lon"]] for plane in planes_list if  plane["callsign"] and  plane["callsign"]!=""
}

# -----------------------
# Create Folium map
# -----------------------
m = folium.Map(location=[56, -96], zoom_start=4, tiles="OpenStreetMap")

# Add UAV markers with smaller custom icon
for uav, (lat, lon) in uavs.items():
    icon = folium.CustomIcon(
        icon_image='plane_icon.png',  # your PNG
        icon_size=(20, 20),           # smaller size
        icon_anchor=(10, 10)          # center
    )

    # Add marker to map
    marker = folium.Marker(
        location=[lat, lon],
        tooltip=uav,
        icon=icon
    )
    marker.add_to(m)

    # CRITICAL: Register the marker in a global JS object so Python can find it
    marker_id = uav.replace(" ", "_")
    marker_script = f"""
    <script>
        window.uav_markers = window.uav_markers || {{}};
        // Wait for the map to exist, then capture the marker
        window.addEventListener('DOMContentLoaded', function() {{
            // Folium markers are added to the map object automatically
            // We find the last marker added to the map and store it
            var map_el = document.querySelector('.folium-map');
            var map_id = map_el.id;
            var map_obj = window[map_id];
            
            // We find the marker by its coordinates or just assign it
            // A cleaner way is to use folium's own element ID:
            window.uav_markers['{marker_id}'] = {marker.get_name()};
        }});
    </script>
    """
    m.get_root().html.add_child(folium.Element(marker_script))

map_html = m.get_root().render()

# -----------------------
# PyQt6 GUI
# -----------------------
app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("UAV Map Tracker")

view = QWebEngineView()
window.setCentralWidget(view)
window.resize(900, 600)
window.show()

# Load map
view.setHtml(map_html)

# -----------------------
# Update UAV positions every second (small random drift)
# -----------------------

def update_positions():
    print("update")
    for i, uav_id in enumerate(uavs.keys()):
        lat = uniform(42.0, 60.0)
        lon = uniform(-130.0, -60.0)

        # Use setLatLng to move the existing marker instead of creating a new one
        js = f"""
        if (window.uav_markers && window.uav_markers['{uav_id}']) {{
            window.uav_markers['{uav_id}'].setLatLng([{lat}, {lon}]);
        }}
        """
        view.page().runJavaScript(js)

# Wait for page load before starting updates
view.loadFinished.connect(lambda _: QTimer.singleShot(500, lambda: QTimer.singleShot(0, update_positions)))

# timer = QTimer()
# timer.timeout.connect(update_positions)
# timer.start(1000)  # update every second


sys.exit(app.exec())
