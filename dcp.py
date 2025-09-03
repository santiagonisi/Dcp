import sys
import pandas as pd
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTabWidget,
    QTableWidget, QTableWidgetItem
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class DcpApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ensayo DCP")
        self.setGeometry(200, 100, 900, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab 1: Abrir Excel
        self.tab_excel = QWidget()
        self.tabs.addTab(self.tab_excel, "Abrir Excel")
        self.setup_excel_tab()

        # Tab 2: Ingreso manual
        self.tab_manual = QWidget()
        self.tabs.addTab(self.tab_manual, "Ingreso manual")
        self.setup_manual_tab()

    # -------- TAB EXCEL --------
    def setup_excel_tab(self):
        layout = QVBoxLayout()
        self.excel_canvas = FigureCanvas(plt.Figure())
        layout.addWidget(self.excel_canvas)

        btn_open = QPushButton("Abrir archivo Excel")
        btn_open.clicked.connect(self.load_excel)
        layout.addWidget(btn_open)

        self.tab_excel.setLayout(layout)

    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Excel", "", "Archivos Excel (*.xlsx *.xls)")
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path)
            columnas = [col.lower() for col in df.columns]

            # Normalizar nombres de columnas
            if "golpe" in columnas and ("profundidad" in columnas or "profundidad [mm]" in columnas):
                col_golpe = df.columns[columnas.index("golpe")]
                if "profundidad" in columnas:
                    col_profundidad = df.columns[columnas.index("profundidad")]
                else:
                    col_profundidad = df.columns[columnas.index("profundidad [mm]")]

                golpes = df[col_golpe]
                profundidad = df[col_profundidad]

                self.plot_data(golpes, profundidad, self.excel_canvas)
            else:
                QMessageBox.warning(self, "Error", "El Excel debe contener las columnas 'Golpe' y 'Profundidad' o 'Profundidad [mm]'.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo: {e}")

    # -------- TAB MANUAL --------
    def setup_manual_tab(self):
        layout = QVBoxLayout()

        # Inputs
        input_layout = QHBoxLayout()
        self.input_golpe = QLineEdit()
        self.input_golpe.setPlaceholderText("Golpe")
        self.input_profundidad = QLineEdit()
        self.input_profundidad.setPlaceholderText("Profundidad [mm]")

        btn_add = QPushButton("Agregar fila")
        btn_add.clicked.connect(self.add_row)
        btn_delete = QPushButton("Borrar fila seleccionada")
        btn_delete.clicked.connect(self.delete_row)

        input_layout.addWidget(QLabel("Golpe:"))
        input_layout.addWidget(self.input_golpe)
        input_layout.addWidget(QLabel("Profundidad:"))
        input_layout.addWidget(self.input_profundidad)
        input_layout.addWidget(btn_add)
        input_layout.addWidget(btn_delete)
        layout.addLayout(input_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Golpe", "Profundidad [mm]"])
        layout.addWidget(self.table)

        # Botón para graficar
        btn_plot = QPushButton("Generar gráfico")
        btn_plot.clicked.connect(self.plot_manual_data)
        layout.addWidget(btn_plot)

        # Canvas de gráfico
        self.manual_canvas = FigureCanvas(plt.Figure())
        layout.addWidget(self.manual_canvas)

        self.tab_manual.setLayout(layout)

    def add_row(self):
        golpe = self.input_golpe.text().strip()
        profundidad = self.input_profundidad.text().strip()

        if not golpe or not profundidad:
            QMessageBox.warning(self, "Error", "Debes ingresar Golpe y Profundidad.")
            return

        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)
        self.table.setItem(row_pos, 0, QTableWidgetItem(golpe))
        self.table.setItem(row_pos, 1, QTableWidgetItem(profundidad))

        self.input_golpe.clear()
        self.input_profundidad.clear()

    def delete_row(self):
        selected = self.table.currentRow()
        if selected >= 0:
            self.table.removeRow(selected)

    def plot_manual_data(self):
        golpes, profundidad = [], []
        for row in range(self.table.rowCount()):
            try:
                golpes.append(float(self.table.item(row, 0).text()))
                profundidad.append(float(self.table.item(row, 1).text()))
            except:
                QMessageBox.warning(self, "Error", "Todos los valores deben ser numéricos.")
                return

        if not golpes or not profundidad:
            QMessageBox.warning(self, "Error", "No hay datos para graficar.")
            return

        self.plot_data(golpes, profundidad, self.manual_canvas)

    # -------- FUNCION DE GRAFICO --------
    def plot_data(self, golpes, profundidad, canvas):
        ax = canvas.figure.subplots()
        ax.clear()
        ax.plot(profundidad, golpes, marker="o", linestyle="-", color="blue")
        ax.set_xlabel("Profundidad [mm]")
        ax.set_ylabel("Golpe")
        ax.set_title("ensayo DCP – Profundidad vs Golpes")
        ax.grid(True)
        canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DcpApp()
    window.show()
    sys.exit(app.exec())
