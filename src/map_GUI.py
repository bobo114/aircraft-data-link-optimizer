import sys
import os
import folium
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QTimer, QUrl
from random import uniform

# UAV initial positions
uavs = {
    "UAV 1": [44.0, -78.0],
    "UAV 2": [46.0, -74.0],
    "UAV 3": [45.0, -76.0]
}

# Create Folium map centered over Canada
m = folium.Map(location=[56, -96], zoom_start=4, tiles="OpenStreetMap")

# Save markers data to inject later with JS
marker_js = ""
for uav, (lat, lon) in uavs.items():
    marker_js += f"window.{uav.replace(' ', '_')} = L.marker([{lat}, {lon}]).addTo(map).bindTooltip('{uav}');\n"

# Wrap JS in window.onload so it runs after map is ready
full_js = f"""
<script>
window.onload = function() {{
    {marker_js}
}};
</script>
"""
m.get_root().html.add_child(folium.Element(full_js))

# Save map HTML
map_file = os.path.abspath("map.html")
m.save(map_file)
print(f"Map saved to: {map_file}")

# PyQt6 GUI
app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("UAV Map Tracker")

view = QWebEngineView()
view.setUrl(QUrl.fromLocalFile(map_file))
window.setCentralWidget(view)
window.resize(900, 600)
window.show()

# Function to update UAV positions
def update_positions():
    for uav in uavs:
        # Random movement for demo
        uavs[uav][0] += uniform(-0.05, 0.05)
        uavs[uav][1] += uniform(-0.05, 0.05)
        js = f"""
        if(window.{uav.replace(' ', '_')}) {{
            window.{uav.replace(' ', '_')}.setLatLng([{uavs[uav][0]}, {uavs[uav][1]}]);
        }}
        """
        view.page().runJavaScript(js)

# Timer to update positions every second
timer = QTimer()
timer.timeout.connect(update_positions)
timer.start(1000)

sys.exit(app.exec())
