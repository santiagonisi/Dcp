import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def procesar_dcp(df):
    """Procesa datos de ensayo DCP: calcula profundidad y DN."""
    df = df.sort_values("N° Golpes Ac.").reset_index(drop=True)

    # Golpes por pasada
    df["N° Golpes"] = df["N° Golpes Ac."].diff().fillna(df["N° Golpes Ac."])

    # Profundidad acumulada (mm)
    prof = [0]
    for i in range(1, len(df)):
        delta_d = df.loc[i - 1, "Lectura (mm)"] - df.loc[i, "Lectura (mm)"]
        prof.append(prof[-1] + delta_d * 10)  # convertir a mm
    df["Prof. (mm)"] = prof

    # DN (mm/golpe)
    dn_values = [None]
    for i in range(1, len(df)):
        delta_d = df.loc[i - 1, "Lectura (mm)"] - df.loc[i, "Lectura (mm)"]
        delta_c = df.loc[i, "N° Golpes Ac."] - df.loc[i - 1, "N° Golpes Ac."]
        dn = (delta_d / delta_c) * 10 if delta_c != 0 else None
        dn_values.append(dn)
    df["DN (mm/golpe)"] = dn_values

    return df.dropna().reset_index(drop=True)


def graficar_escalonado(df, titulo="DCP - Escalonado"):
    """Gráfico escalonado: DN vs Profundidad."""
    x_vals = []
    y_vals = []

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
    """Gráfico clásico: DN vs Profundidad (línea continua)."""
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(df["DN (mm/golpe)"], df["Prof. (mm)"], marker="o", linestyle="-", color="red")
    ax.set_xlabel("DN (mm/golpe)")
    ax.set_ylabel("Profundidad (mm)")
    ax.set_title(titulo)
    ax.grid(True)
    ax.invert_yaxis()
    return fig


def graficar_penetracion(df, titulo="DCP - Penetración"):
    """Gráfico: Lectura vs Profundidad."""
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(df["Lectura (mm)"], df["Prof. (mm)"], marker="s", linestyle="--", color="green")
    ax.set_xlabel("Lectura (mm)")
    ax.set_ylabel("Profundidad (mm)")
    ax.set_title(titulo)
    ax.grid(True)
    ax.invert_yaxis()
    return fig



def buscar_columnas(df):
    """Detecta columnas de golpes acumulados y lectura."""
    golpes_col, lectura_col = None, None
    for col in df.columns:
        col_norm = col.lower()
        if "golpe" in col_norm and golpes_col is None:
            golpes_col = col
        if ("lectura" in col_norm or "profund" in col_norm) and lectura_col is None:
            lectura_col = col
    return golpes_col, lectura_col


def exportar_resultados(df, nombre_base="Resultados_DCP"):
    """Exporta datos y gráficos en Excel, PNG y PDF."""
    # Excel
    df.to_excel(nombre_base + ".xlsx", index=False)

    # Gráficos
    fig1 = graficar_escalonado(df)
    fig2 = graficar_resistencia(df)
    fig3 = graficar_penetracion(df)

    # PNG
    fig1.savefig(nombre_base + "_escalonado.png")
    fig2.savefig(nombre_base + "_resistencia.png")
    fig3.savefig(nombre_base + "_penetracion.png")

    # Pdf
    with PdfPages(nombre_base + ".pdf") as pdf:
        pdf.savefig(fig1)
        pdf.savefig(fig2)
        pdf.savefig(fig3)

    plt.close("all")

    messagebox.showinfo(
        "Éxito",
        f"Resultados exportados:\n- {nombre_base}.xlsx\n- {nombre_base}.pdf (3 gráficos)\n- PNG individuales"
    )


def cargar_excel():
    archivo = filedialog.askopenfilename(
        title="Seleccione un archivo Excel DCP",
        filetypes=[("Excel", "*.xlsx *.xls")]
    )
    if not archivo:
        return

    try:
        xls = pd.ExcelFile(archivo)

        #Elegir hoja
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
                exportar_resultados(df_proc, nombre_base=f"Resultados_DCP_{hoja}")
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

    entradas_golpes = []
    entradas_lectura = []

    for i in range(20):
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
        exportar_resultados(df_proc, nombre_base="Resultados_DCP_manual")
        ventana.destroy()

    tk.Button(ventana, text="Procesar", command=procesar_manual).pack(pady=10)


root = tk.Tk()
root.title("Procesador de Ensayos DCP")
root.geometry("420x250")

tk.Label(root, text="Procesador de Ensayos DCP", font=("Arial", 14, "bold")).pack(pady=10)

tk.Button(root, text="📂 Cargar Excel", command=cargar_excel, width=25, height=2).pack(pady=10)
tk.Button(root, text="✍️ Ingreso manual", command=ingreso_manual, width=25, height=2).pack(pady=10)

root.mainloop()
