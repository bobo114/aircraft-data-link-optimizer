import sys
from PyQt6.QtWidgets import QApplication
from map_GUI import MapWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec())