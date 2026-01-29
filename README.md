# Sistema de Gestión Académica (Full Stack) 🎓

Aplicación web integrada para la gestión de estudiantes, inscripciones e historial académico. Este proyecto demuestra la conexión eficiente entre un motor de base de datos relacional y una aplicación backend.

## Objetivo
Crear una solución que resuelva problemas lógicos complejos (como prerrequisitos de materias y cálculo de índices) delegando la validación de datos al motor SQL y la experiencia de usuario a la aplicación web.

## Tech Stack
* **Base de Datos:** SQL Server
* **Backend:** Python (Flask Framework)
* **Frontend:** HTML5, JavaScript (Básico)
* **Conectividad:** PyODBC / SQLAlchemy

## Funcionalidades Clave
### Base de Datos (SQL Server)
* **Triggers de Integridad:** Disparadores automáticos que validan reglas de negocio (ej. impedir inscripción si el cupo está lleno).
* **Cálculo Automático:** Stored Procedures que recalculan el índice académico del estudiante tras cada cierre de ciclo.
* **Modelado Complejo:** Relaciones "Muchos a Muchos" (N:M) para estudiantes y asignaturas.

### Aplicación (Python/Flask)
* **API RESTful:** Endpoints para crear, leer, actualizar y eliminar (CRUD) registros de estudiantes.
* **Manejo de Errores:** Captura de excepciones SQL directamente en la interfaz de usuario para feedback inmediato.

## ómo ejecutar
1. Ejecutar el script `setup_database.sql` en SSMS.
2. Configurar la cadena de conexión en `app.py`.
3. Ejecutar `python app.py`.
