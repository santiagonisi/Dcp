import sys
import pandas as pd
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QVBoxLayout,
    QWidget, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QSpinBox,
    QDoubleSpinBox, QHBoxLayout, QCheckBox, QComboBox
)
from PySide6.QtGui import QAction
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ensayo DCP")

        self.df = None

        # Menú
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Archivo")

        open_action = QAction("Abrir Excel/CSV...", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Guardar gráfico...", self)
        save_action.triggered.connect(self.save_plot)
        file_menu.addAction(save_action)

        export_action = QAction("Exportar datos procesados...", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        # Layout principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Tabla
        self.table = QTableWidget()
        layout.addWidget(self.table, 40)

        # Panel derecho (controles + gráfico)
        right_panel = QVBoxLayout()

        # Controles
        controls_layout = QVBoxLayout()

        self.unit_label = QLabel("Unidad X (Penetración):")
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["mm", "cm"])
        controls_layout.addWidget(self.unit_label)
        controls_layout.addWidget(self.unit_combo)

        self.style_label = QLabel("Estilo de gráfico:")
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Línea + Puntos", "Solo Puntos", "Solo Línea"])
        controls_layout.addWidget(self.style_label)
        controls_layout.addWidget(self.style_combo)

        self.invert_y = QCheckBox("Invertir eje Y (profundidad hacia abajo)")
        self.invert_y.setChecked(True)
        controls_layout.addWidget(self.invert_y)

        self.range_label = QLabel("Rango Y (golpes):")
        controls_layout.addWidget(self.range_label)
        range_layout = QHBoxLayout()
        self.ymin_spin = QSpinBox()
        self.ymin_spin.setRange(0, 10000)
        self.ymin_spin.setValue(0)
        self.ymax_spin = QSpinBox()
        self.ymax_spin.setRange(0, 10000)
        self.ymax_spin.setValue(0)
        range_layout.addWidget(QLabel("Mín:"))
        range_layout.addWidget(self.ymin_spin)
        range_layout.addWidget(QLabel("Máx:"))
        range_layout.addWidget(self.ymax_spin)
        controls_layout.addLayout(range_layout)

        self.param_label = QLabel("Parámetros correlación CBR = a / DCP^b")
        controls_layout.addWidget(self.param_label)
        param_layout = QHBoxLayout()
        self.a_spin = QDoubleSpinBox()
        self.a_spin.setRange(0, 10000)
        self.a_spin.setValue(292)
        self.b_spin = QDoubleSpinBox()
        self.b_spin.setRange(0, 10)
        self.b_spin.setValue(1.12)
        param_layout.addWidget(QLabel("a:"))
        param_layout.addWidget(self.a_spin)
        param_layout.addWidget(QLabel("b:"))
        param_layout.addWidget(self.b_spin)
        controls_layout.addLayout(param_layout)

        self.result_label = QLabel("Resultados: DCP= -- mm/golpe, CBR= --")
        controls_layout.addWidget(self.result_label)

        self.plot_button = QPushButton("Actualizar gráfico")
        self.plot_button.clicked.connect(self.update_plot)
        controls_layout.addWidget(self.plot_button)

        right_panel.addLayout(controls_layout)

        # Figura matplotlib
        self.figure = Figure(figsize=(5,5))
        self.canvas = FigureCanvas(self.figure)
        right_panel.addWidget(self.canvas, 80)

        layout.addLayout(right_panel, 60)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo de datos de ensayo DCP", "", "Archivos Excel (*.xlsx);;Archivos CSV (*.csv)")
        if file_path:
            try:
                if file_path.endswith(".csv"):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)

                if not ("Golpe" in df.columns and "Penetracion" in df.columns):
                    QMessageBox.critical(self, "Error", "El archivo debe contener columnas 'Golpe' y 'Penetracion'")
                    return

                self.df = df
                self.load_table()
                self.update_plot()

            except Exception as e:
                QMessageBox.critical(self, "Error al abrir archivo", str(e))

    def load_table(self):
        if self.df is not None:
            self.table.setRowCount(len(self.df))
            self.table.setColumnCount(len(self.df.columns))
            self.table.setHorizontalHeaderLabels(self.df.columns)
            for i in range(len(self.df)):
                for j, col in enumerate(self.df.columns):
                    self.table.setItem(i, j, QTableWidgetItem(str(self.df.iloc[i, j])))

    def update_plot(self):
        if self.df is None:
            return

        df = self.df.copy()
        golpes = df["Golpe"].values
        penetracion = df["Penetracion"].values

        unit = self.unit_combo.currentText()
        if unit == "cm":
            penetracion = penetracion / 10.0

        estilo = self.style_combo.currentText()
        line = marker = None
        if estilo == "Línea + Puntos":
            line, marker = "-", "o"
        elif estilo == "Solo Puntos":
            line, marker = "", "o"
        elif estilo == "Solo Línea":
            line, marker = "-", None

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(penetracion, golpes, linestyle=line, marker=marker)
        ax.set_xlabel(f"Penetración ({unit})")
        ax.set_ylabel("Número de golpes")
        ax.set_title("ensayo DCP")
        ax.grid(True)

        if self.invert_y.isChecked():
            ax.invert_yaxis()

        if self.ymin_spin.value() < self.ymax_spin.value():
            ax.set_ylim(self.ymax_spin.value(), self.ymin_spin.value())

        # Calculo DCP y CBR
        if len(golpes) > 1:
            x = golpes
            y = penetracion
            coef = np.polyfit(x, y, 1)
            pendiente = coef[0]
            dcp = pendiente
            a = self.a_spin.value()
            b = self.b_spin.value()
            cbr = a / (dcp**b) if dcp > 0 else 0
            self.result_label.setText(f"Resultados: DCP= {dcp:.2f} {unit}/golpe, CBR= {cbr:.2f}")
            ax.plot(x, coef[0]*x + coef[1], color='red', linestyle='--', label='Regresión')
            ax.legend()

        self.canvas.draw()

    def save_plot(self):
        if self.df is None:
            QMessageBox.warning(self, "Atención", "Primero cargue un archivo de ensayo DCP")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar gráfico de ensayo DCP", "grafico.png", "PNG (*.png);;PDF (*.pdf)")
        if file_path:
            self.figure.savefig(file_path)

    def export_data(self):
        if self.df is None:
            QMessageBox.warning(self, "Atención", "Primero cargue un archivo de ensayo DCP")
            return

        try:
            df = self.df.copy()
            golpes = df["Golpe"].values
            penetracion = df["Penetracion"].values

            deltas = np.diff(penetracion)
            golpes_delta = np.diff(golpes)
            dcp_local = deltas / golpes_delta

            df_proc = pd.DataFrame({
                "Golpe inicial": golpes[:-1],
                "Golpe final": golpes[1:],
                "Penetración inicial": penetracion[:-1],
                "Penetración final": penetracion[1:],
                "DCP local (mm/golpe)": dcp_local
            })

            dcp_global = (penetracion[-1] - penetracion[0]) / (golpes[-1] - golpes[0])
            a = self.a_spin.value()
            b = self.b_spin.value()
            cbr = a / (dcp_global**b) if dcp_global > 0 else 0

            resumen = pd.DataFrame({"DCP global (mm/golpe)": [dcp_global], "CBR estimado": [cbr]})

            file_path, _ = QFileDialog.getSaveFileName(self, "Exportar datos procesados de ensayo DCP", "procesado.xlsx", "Excel (*.xlsx)")
            if file_path:
                with pd.ExcelWriter(file_path) as writer:
                    df_proc.to_excel(writer, sheet_name="Datos_y_DCP_local", index=False)
                    resumen.to_excel(writer, sheet_name="Resumen_global", index=False)

        except Exception as e:
            QMessageBox.critical(self, "Error al exportar datos", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
