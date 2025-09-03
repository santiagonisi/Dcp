import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QLineEdit, QTableWidget,
    QTableWidgetItem, QTabWidget, QMessageBox, QComboBox, QCheckBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class DcpApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ensayo DCP")
        self.setGeometry(100, 100, 1000, 720)

        # Unidad seleccionada por el usuario (no convierte, solo etiqueta)
        self.unidad_dn = "golpes/mm"

        # Para re-graficar al cambiar opciones
        self.last_df_excel = None
        self.last_df_manual = None

        # Tabs principales
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab Excel
        self.tab_excel = QWidget()
        self.tabs.addTab(self.tab_excel, "Cargar desde Excel")
        self.init_tab_excel()

        # Tab Manual
        self.tab_manual = QWidget()
        self.tabs.addTab(self.tab_manual, "Ingreso manual")
        self.init_tab_manual()

    # ----- UTIL -----
    def _extract_depth_dn(self, df: pd.DataFrame):
        name_map = {c.lower().strip(): c for c in df.columns}
        depth_key = None
        for k in ("profundidad [mm]", "profundidad"):
            if k in name_map:
                depth_key = name_map[k]
                break
        dn_key = name_map.get("dn")
        if depth_key is None or dn_key is None:
            raise ValueError("El archivo debe contener columnas 'Profundidad' (o 'Profundidad [mm]') y 'DN'.")

        profundidad = pd.to_numeric(df[depth_key], errors="coerce")
        dn = pd.to_numeric(df[dn_key], errors="coerce")

        out = pd.DataFrame({"Profundidad [mm]": profundidad, "DN": dn}).dropna()
        out = out.sort_values("Profundidad [mm]").reset_index(drop=True)
        return out

    # -------- TAB EXCEL --------
    def init_tab_excel(self):
        layout = QVBoxLayout()

        opts_layout = QHBoxLayout()
        opts_layout.addWidget(QLabel("Unidad DN:"))
        self.unidad_combo_excel = QComboBox()
        self.unidad_combo_excel.addItems(["golpes/mm", "golpes/cm"])
        self.unidad_combo_excel.currentTextChanged.connect(self.cambiar_unidad)
        opts_layout.addWidget(self.unidad_combo_excel)

        self.invert_y_excel = QCheckBox("Invertir eje Y (profundidad hacia abajo)")
        self.invert_y_excel.setChecked(True)
        self.invert_y_excel.toggled.connect(self.replot_excel)
        opts_layout.addWidget(self.invert_y_excel)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)

        btn_layout = QHBoxLayout()
        btn_open = QPushButton("Abrir archivo Excel")
        btn_open.clicked.connect(self.open_excel)
        btn_save_img = QPushButton("Guardar gráfico")
        btn_save_img.clicked.connect(lambda: self.save_figure(self.figure_excel))
        btn_export_excel = QPushButton("Exportar datos a Excel")
        btn_export_excel.clicked.connect(lambda: self.export_to_excel(self.last_df_excel))
        btn_layout.addWidget(btn_open)
        btn_layout.addWidget(btn_save_img)
        btn_layout.addWidget(btn_export_excel)
        layout.addLayout(btn_layout)

        self.figure_excel = Figure()
        self.canvas_excel = FigureCanvas(self.figure_excel)
        layout.addWidget(self.canvas_excel)

        self.table_excel = QTableWidget()
        layout.addWidget(self.table_excel)

        self.tab_excel.setLayout(layout)

    def open_excel(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir archivo Excel", "", "Excel Files (*.xlsx *.xls)")
        if not file_name:
            return
        try:
            raw = pd.read_excel(file_name)
            df = self._extract_depth_dn(raw)
            self.last_df_excel = df
            self.plot_data(df, self.figure_excel, self.canvas_excel, self.table_excel, invert_y=self.invert_y_excel.isChecked())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir o procesar el archivo:\n{e}")

    def replot_excel(self):
        if self.last_df_excel is not None:
            self.plot_data(self.last_df_excel, self.figure_excel, self.canvas_excel, self.table_excel, invert_y=self.invert_y_excel.isChecked())

    # -------- TAB MANUAL --------
    def init_tab_manual(self):
        layout = QVBoxLayout()

        opts_layout = QHBoxLayout()
        opts_layout.addWidget(QLabel("Unidad DN:"))
        self.unidad_combo_manual = QComboBox()
        self.unidad_combo_manual.addItems(["golpes/mm", "golpes/cm"])
        self.unidad_combo_manual.currentTextChanged.connect(self.cambiar_unidad)
        opts_layout.addWidget(self.unidad_combo_manual)

        self.invert_y_manual = QCheckBox("Invertir eje Y (profundidad hacia abajo)")
        self.invert_y_manual.setChecked(True)
        self.invert_y_manual.toggled.connect(self.replot_manual)
        opts_layout.addWidget(self.invert_y_manual)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)

        input_layout = QHBoxLayout()
        self.input_profundidad = QLineEdit()
        self.input_profundidad.setPlaceholderText("Profundidad [mm]")
        self.input_dn = QLineEdit()
        self.input_dn.setPlaceholderText("DN")
        btn_add = QPushButton("Agregar fila")
        btn_add.clicked.connect(self.add_row_manual)
        btn_delete = QPushButton("Borrar fila")
        btn_delete.clicked.connect(self.delete_row_manual)
        btn_plot = QPushButton("Generar gráfico")
        btn_plot.clicked.connect(self.plot_manual)
        input_layout.addWidget(self.input_profundidad)
        input_layout.addWidget(self.input_dn)
        input_layout.addWidget(btn_add)
        input_layout.addWidget(btn_delete)
        input_layout.addWidget(btn_plot)
        layout.addLayout(input_layout)

        btn_layout = QHBoxLayout()
        btn_save_img = QPushButton("Guardar gráfico")
        btn_save_img.clicked.connect(lambda: self.save_figure(self.figure_manual))
        btn_export_excel = QPushButton("Exportar datos a Excel")
        btn_export_excel.clicked.connect(lambda: self.export_to_excel(self.last_df_manual))
        btn_layout.addWidget(btn_save_img)
        btn_layout.addWidget(btn_export_excel)
        layout.addLayout(btn_layout)

        self.table_manual = QTableWidget()
        self.table_manual.setColumnCount(2)
        self.table_manual.setHorizontalHeaderLabels(["Profundidad [mm]", "DN"])
        layout.addWidget(self.table_manual)

        self.figure_manual = Figure()
        self.canvas_manual = FigureCanvas(self.figure_manual)
        layout.addWidget(self.canvas_manual)

        self.tab_manual.setLayout(layout)

    def cambiar_unidad(self, text):
        self.unidad_dn = text
        self.replot_excel()
        self.replot_manual()

    def add_row_manual(self):
        profundidad = self.input_profundidad.text().strip()
        dn = self.input_dn.text().strip()
        if not profundidad or not dn:
            QMessageBox.warning(self, "Atención", "Debe ingresar Profundidad y DN.")
            return
        try:
            float(profundidad)
            float(dn)
        except ValueError:
            QMessageBox.warning(self, "Atención", "Use punto (.) como separador decimal.")
            return
        row = self.table_manual.rowCount()
        self.table_manual.insertRow(row)
        self.table_manual.setItem(row, 0, QTableWidgetItem(profundidad))
        self.table_manual.setItem(row, 1, QTableWidgetItem(dn))
        self.input_profundidad.clear()
        self.input_dn.clear()

    def delete_row_manual(self):
        r = self.table_manual.currentRow()
        if r >= 0:
            self.table_manual.removeRow(r)

    def plot_manual(self):
        rows = self.table_manual.rowCount()
        if rows == 0:
            QMessageBox.warning(self, "Atención", "Debe ingresar al menos una fila.")
            return
        data = []
        for i in range(rows):
            try:
                p = float(self.table_manual.item(i, 0).text())
                d = float(self.table_manual.item(i, 1).text())
                data.append((p, d))
            except Exception:
                QMessageBox.warning(self, "Atención", "Los valores deben ser numéricos (usar punto decimal).")
                return
        df = pd.DataFrame(data, columns=["Profundidad [mm]", "DN"]).dropna().sort_values("Profundidad [mm]").reset_index(drop=True)
        self.last_df_manual = df
        self.plot_data(df, self.figure_manual, self.canvas_manual, None, invert_y=self.invert_y_manual.isChecked())

    def plot_data(self, df: pd.DataFrame, figure: Figure, canvas: FigureCanvas, table_widget: QTableWidget | None, invert_y: bool = True):
        figure.clear()
        ax = figure.add_subplot(111)
        ax.plot(df["DN"], df["Profundidad [mm]"], marker="o", linestyle="-", label=f"DN ({self.unidad_dn})")
        ax.set_xlabel(f"DN ({self.unidad_dn})")
        ax.set_ylabel("Profundidad [mm]")
        ax.set_title("ensayo DCP – DN vs Profundidad")
        ax.grid(True)
        if invert_y:
            ax.invert_yaxis()
        ax.legend()
        canvas.draw()

        if table_widget is not None:
            table_widget.setRowCount(len(df))
            table_widget.setColumnCount(2)
            table_widget.setHorizontalHeaderLabels([f"DN ({self.unidad_dn})", "Profundidad [mm]"])
            for i, row in df.iterrows():
                table_widget.setItem(i, 0, QTableWidgetItem(str(row["DN"])))
                table_widget.setItem(i, 1, QTableWidgetItem(str(row["Profundidad [mm]"])))

    def replot_manual(self):
        if self.last_df_manual is not None:
            self.plot_data(self.last_df_manual, self.figure_manual, self.canvas_manual, None, invert_y=self.invert_y_manual.isChecked())

    # -------- EXPORTAR --------
    def save_figure(self, figure: Figure):
        if figure is None:
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Guardar gráfico", "grafico.png", "Imagen PNG (*.png);;Imagen JPG (*.jpg)")
        if file_name:
            try:
                figure.savefig(file_name)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el gráfico:\n{e}")

    def export_to_excel(self, df: pd.DataFrame | None):
        if df is None or df.empty:
            QMessageBox.warning(self, "Atención", "No hay datos para exportar.")
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Exportar datos a Excel", "datos.xlsx", "Excel Files (*.xlsx)")
        if file_name:
            try:
                df.to_excel(file_name, index=False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo exportar a Excel:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DcpApp()
    window.show()
    sys.exit(app.exec())
