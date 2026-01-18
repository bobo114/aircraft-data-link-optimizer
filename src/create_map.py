import folium
import os

# Base map
m = folium.Map(location=[56, -96], zoom_start=4, tiles="OpenStreetMap")

# Save to absolute path
map_file = os.path.abspath("map.html")
m.save(map_file)
print(f"Map saved to: {map_file}")
