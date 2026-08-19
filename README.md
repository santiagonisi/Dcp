# Procesador DCP

Aplicación de escritorio para el análisis de ensayos de penetración dinámica de cono (DCP).

## Stack

- **Lenguaje:** Python
- **Interfaz de escritorio:** Tkinter
- **Análisis de datos:** Pandas
- **Visualización:** Matplotlib
- **Importación y exportación:** OpenPyXL
- **Distribución:** PyInstaller
- **Recursos gráficos:** Pillow

## Estructura del proyecto

```
Dcp/
├── dcp_appy.py           # Aplicación principal
├── ProcesadorDCP.spec    # Configuración del ejecutable
└── requirements.txt      # Dependencias de Python
```

## Módulos

- **Carga de ensayos:** importación de datos de mediciones DCP.
- **Procesamiento:** análisis de profundidad, golpes y parámetros del ensayo.
- **Visualización:** generación de gráficos para interpretar los resultados.
- **Informes:** exportación de resultados y gráficos.
- **Aplicación de escritorio:** interfaz gráfica para operar el procesador.
