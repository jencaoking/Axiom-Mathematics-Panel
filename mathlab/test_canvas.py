import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from PySide6.QtWidgets import QApplication, QMainWindow
from mathlab.ui.canvas import GeometryCanvas

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoGebra Constraint Solver Test")
        self.setGeometry(100, 100, 800, 600)
        self.canvas = GeometryCanvas(self)
        self.setCentralWidget(self.canvas)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TestWindow()
    win.show()
    sys.exit(app.exec())
