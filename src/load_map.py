import sys
from random import uniform
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QTimer
import folium

# -----------------------
# UAV positions
# -----------------------
uavs = {
    "UAV_1": [44.0, -78.0],
    "UAV_2": [46.0, -74.0],
    "UAV_3": [45.0, -76.0]
}

# -----------------------
# Create Folium map in memory
# -----------------------
m = folium.Map(location=[56, -96], zoom_start=4, tiles="OpenStreetMap")

# FIX 1: This script finds the secret Folium map name and makes it accessible as 'window.map'
map_finder_js = """
<script>
    window.onload = function() {
        for (let key in window) {
            if (key.startsWith('map_') && window[key] instanceof L.Map) {
                window.map = window[key];
                break;
            }
        }
    };
</script>
"""
m.get_root().html.add_child(folium.Element(map_finder_js))
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

# Load map HTML
view.setHtml(map_html)

# -----------------------
# Add UAV markers dynamically
# -----------------------
def add_markers():
    for uav, (lat, lon) in uavs.items():
        # FIX 2: Sanitize the name (UAV 1 -> UAV_1) for JS variable safety
        js_id = uav.replace(" ", "_")
        js = f"""
        if (window.map) {{
            var marker = L.marker([{lat}, {lon}]).addTo(window.map).bindTooltip("{uav}");
            window.{js_id} = marker;
        }} else {{
            console.error("Map not ready yet!");
        }}
        """
        view.page().runJavaScript(js)

# FIX 3: Don't use a random 1s timer. Wait for the 'loadFinished' signal.
view.loadFinished.connect(lambda: QTimer.singleShot(500, add_markers))

# -----------------------
# Update UAV positions every second
# -----------------------
def update_positions():
    for uav in uavs:
        uavs[uav][0] += uniform(-0.05, 0.05)
        uavs[uav][1] += uniform(-0.05, 0.05)
        js_id = uav.replace(" ", "_")
        js = f"""
        if(window.{js_id}) {{
            window.{js_id}.setLatLng([{uavs[uav][0]}, {uavs[uav][1]}]);
        }}
        """
        view.page().runJavaScript(js)

sys.exit(app.exec())
