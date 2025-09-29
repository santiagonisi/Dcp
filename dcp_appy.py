import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os


def procesar_dcp(df):
    """Procesa datos de ensayo DCP: calcula N° golpes, profundidad y DN."""
    df = df.sort_values("N° Golpes Ac.").reset_index(drop=True)

    df["N° Golpes"] = df["N° Golpes Ac."].diff().fillna(df["N° Golpes Ac."])

    prof = [0]
    for i in range(1, len(df)):
        delta_d = df.loc[i - 1, "Lectura (mm)"] - df.loc[i, "Lectura (mm)"]
        prof.append(prof[-1] + delta_d * 10)
    df["Prof. (mm)"] = prof

    dn_values = [None]
    for i in range(1, len(df)):
        delta_d = df.loc[i - 1, "Lectura (mm)"] - df.loc[i, "Lectura (mm)"]
        delta_c = df.loc[i, "N° Golpes Ac."] - df.loc[i - 1, "N° Golpes Ac."]
        dn = (delta_d / delta_c) * 10 if delta_c != 0 else None
        dn_values.append(dn)
    df["DN (mm/golpe)"] = dn_values

    return df


def graficar_escalonado(df, titulo="DCP - Escalonado"):
    x_vals, y_vals = [], []
    for i in range(len(df)):
        dn = df.loc[i, "DN (mm/golpe)"]
        p = df.loc[i, "Prof. (mm)"]
        x_vals.extend([dn, dn])
        y_vals.extend([df.loc[i - 1, "Prof. (mm)"] if i > 0 else 0, p])

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(x_vals, y_vals, drawstyle="steps-post", color="blue")
    ax.set_xlabel("DN (mm/golpe)")
    ax.set_ylabel("Profundidad (mm)")
    ax.set_title(titulo)
    ax.grid(True)
    ax.invert_yaxis()
    return fig


def graficar_resistencia(df, titulo="DCP - Resistencia"):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(df["DN (mm/golpe)"], df["Prof. (mm)"], marker="o", linestyle="-", color="red")
    ax.set_xlabel("DN (mm/golpe)")
    ax.set_ylabel("Profundidad (mm)")
    ax.set_title(titulo)
    ax.grid(True)
    ax.invert_yaxis()
    return fig


def graficar_penetracion(df, titulo="DCP - Penetración"):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(df["Lectura (mm)"], df["Prof. (mm)"], marker="s", linestyle="--", color="green")
    ax.set_xlabel("Lectura (mm)")
    ax.set_ylabel("Profundidad (mm)")
    ax.set_title(titulo)
    ax.grid(True)
    ax.invert_yaxis()
    return fig


def buscar_columnas(df):
    golpes_col, lectura_col = None, None
    for col in df.columns:
        col_norm = col.lower()
        if "golpe" in col_norm and golpes_col is None:
            golpes_col = col
        if ("lectura" in col_norm or "profund" in col_norm) and lectura_col is None:
            lectura_col = col
    return golpes_col, lectura_col


def exportar_resultados(df, nombre_base):
    """Exporta datos y gráficos con mismo nombre base (Excel, PDF y PNGs)."""
    carpeta = os.path.dirname(nombre_base)
    base = os.path.splitext(os.path.basename(nombre_base))[0]

    archivo_excel = os.path.join(carpeta, f"{base}.xlsx")
    archivo_pdf = os.path.join(carpeta, f"{base}.pdf")
    archivo_png1 = os.path.join(carpeta, f"{base}_escalonado.png")
    archivo_png2 = os.path.join(carpeta, f"{base}_resistencia.png")
    archivo_png3 = os.path.join(carpeta, f"{base}_penetracion.png")

    df.to_excel(archivo_excel, index=False)

    fig1 = graficar_escalonado(df)
    fig2 = graficar_resistencia(df)
    fig3 = graficar_penetracion(df)

    fig1.savefig(archivo_png1)
    fig2.savefig(archivo_png2)
    fig3.savefig(archivo_png3)

    with PdfPages(archivo_pdf) as pdf:
        pdf.savefig(fig1)
        pdf.savefig(fig2)
        pdf.savefig(fig3)

    plt.close("all")

    messagebox.showinfo("Éxito", f"Archivos exportados en:\n{carpeta}")


def cargar_excel():
    archivo = filedialog.askopenfilename(
        title="Seleccione un archivo Excel DCP",
        filetypes=[("Excel", "*.xlsx *.xls")]
    )
    if not archivo:
        return

    try:
        xls = pd.ExcelFile(archivo)

        hoja_window = tk.Toplevel(root)
        hoja_window.title("Seleccionar hoja")

        tk.Label(hoja_window, text="Seleccione la hoja a procesar:").pack(pady=5)
        hoja_combo = ttk.Combobox(hoja_window, values=xls.sheet_names, state="readonly")
        hoja_combo.pack(pady=5)
        hoja_combo.current(0)

        def procesar_hoja():
            hoja = hoja_combo.get()
            df = pd.read_excel(archivo, sheet_name=hoja)
            golpes_col, lectura_col = buscar_columnas(df)

            if golpes_col and lectura_col:
                df_sel = df[[golpes_col, lectura_col]].copy()
                df_sel.columns = ["N° Golpes Ac.", "Lectura (mm)"]
                df_proc = procesar_dcp(df_sel)

                nombre_salida = filedialog.asksaveasfilename(
                    title="Guardar resultados como",
                    defaultextension=".xlsx",
                    filetypes=[("Archivos Excel", "*.xlsx")]
                )
                if nombre_salida:
                    exportar_resultados(df_proc, nombre_salida)
            else:
                messagebox.showwarning("Atención", "No se encontraron columnas válidas en la hoja seleccionada.")

            hoja_window.destroy()

        tk.Button(hoja_window, text="Procesar", command=procesar_hoja).pack(pady=10)

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")


def ingreso_manual():
    ventana = tk.Toplevel(root)
    ventana.title("Ingreso manual de datos")

    tk.Label(ventana, text="Ingrese los datos de Golpes Acumulados y Lectura (mm)").pack(pady=5)

    frame = tk.Frame(ventana)
    frame.pack()

    tk.Label(frame, text="N° Golpes Ac.").grid(row=0, column=0, padx=5)
    tk.Label(frame, text="Lectura (mm)").grid(row=0, column=1, padx=5)

    entradas_golpes, entradas_lectura = [], []

    for i in range(15):
        e1 = tk.Entry(frame, width=10)
        e2 = tk.Entry(frame, width=10)
        e1.grid(row=i + 1, column=0, padx=5, pady=2)
        e2.grid(row=i + 1, column=1, padx=5, pady=2)
        entradas_golpes.append(e1)
        entradas_lectura.append(e2)

    def procesar_manual():
        datos = []
        for e1, e2 in zip(entradas_golpes, entradas_lectura):
            if e1.get() and e2.get():
                try:
                    datos.append((int(e1.get()), float(e2.get())))
                except ValueError:
                    messagebox.showwarning("Atención", "Los valores deben ser numéricos.")
                    return

        if not datos:
            messagebox.showwarning("Atención", "Debe ingresar al menos una fila de datos.")
            return

        df = pd.DataFrame(datos, columns=["N° Golpes Ac.", "Lectura (mm)"])
        df_proc = procesar_dcp(df)

        nombre_salida = filedialog.asksaveasfilename(
            title="Guardar resultados como",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")]
        )
        if nombre_salida:
            exportar_resultados(df_proc, nombre_salida)
        ventana.destroy()

    tk.Button(ventana, text="Procesar", command=procesar_manual).pack(pady=10)


root = tk.Tk()
root.title("Procesador de Ensayos DCP")
root.geometry("420x250")

tk.Label(root, text="Procesador de Ensayos DCP", font=("Arial", 14, "bold")).pack(pady=10)

tk.Button(root, text="📂 Cargar Excel", command=cargar_excel, width=25, height=2).pack(pady=10)
tk.Button(root, text="✍️ Ingreso manual", command=ingreso_manual, width=25, height=2).pack(pady=10)

root.mainloop()
