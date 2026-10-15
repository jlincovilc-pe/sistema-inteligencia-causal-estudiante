# Requisitos para los notebooks

## Entorno comprobado

- Linux x86_64
- Python 3.13.13
- Dependencias fijadas en [`../requirements.txt`](../requirements.txt)
- Ejecución local; no requiere nube, Docker ni credenciales

## Instalación

```bash
python3 -m venv .venv-causal
. .venv-causal/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m ipykernel install --user --name sic-estudiante --display-name "Python (SIC estudiante)"
python scripts/doctor_minimo.py
python scripts/validate_student_repo.py
```

Abre Jupyter desde la raíz del repositorio y selecciona el kernel `Python (SIC estudiante)`. Los notebooks de Serie A esperan ejecutarse desde `03_notebooks_caso_estudio/notebooks/`; los labs pueden abrirse directamente desde su carpeta.

## Datos y límites

El paquete incluye solo observables y metadata permitida para cinco escenarios benchmark. Los archivos `truth`, resultados oráculo y soluciones docentes no se incluyen. Por eso el estudiante puede reportar una estimación, intervalo, diagnóstico y decisión condicionada, pero no un error contra el efecto verdadero. Las secciones marcadas como evaluación reservada se revisan en el entorno docente.

Si la instalación falla, conserva la salida de `doctor_minimo.py`, continúa con la lectura y registra el lab incompleto. No copies soluciones ni inventes resultados.
