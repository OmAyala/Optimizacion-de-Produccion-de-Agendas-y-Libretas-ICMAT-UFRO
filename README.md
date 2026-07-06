# Optimizacion-de-Produccion-de-Agendas-y-Libretas-ICMAT-UFRO
El proyecto busca optimizar el proyecto de agendas y libretas icmat ufro

## Estructura del Proyecto

```text
.
|
| (Horarios)
├── scheduling2-2.py
├── Una única maquinaria/
│   ├── Reportes (HTML)
│   └── ...
├── Varias Maquinas/
│   ├── Reportes (HTML)
│   └── ...
|
| (Optimizaciones de Corte)
├── escenarios.m
├── script_optimizacion_fuerza_bruta.m
├── script_optimizacion_vinilo_economico.m
├── script_optimizacion_vinilos.m
├── script_simulacion_estres.m
├── Resultados.txt
|
└──README.md (Este archivo)
```
# script_optimizacion_fuerza_bruta.m
Implementación de Problema de Corte.

# script_optimizacion_vinilos.m
Implementación de Problema de Vinilo.

# script_optimizacion_vinilo_economico.m
Implementación de Problema de Vinilo Económico.

# escenarios.m
Calcula escenarios según cantidad de estudiantes (trabajadores)

# script_simulacion_estres.m
Script que ejecuta los demás optimizadores y les añade estrés estocástico.

# Resultados.txt
Archivo con los resultados de la ejecución.


# scheduling2-2.py
Ejecutable para el problema de horarios, con implementación de trabajadores y horarios para cada uno.

# Una única Maquinaria
Carpeta con reportes con maquinaria única

# Varias Maquinas
Carpeta con reportes con varias máquinas
