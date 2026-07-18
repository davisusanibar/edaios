# Data Plane Port

El puerto intercambia contratos, locks, comandos y receipts por archivos.
Consumer y Core no comparten classpath ni runtime. El host ejecuta el data plane;
Core solo valida la evidencia devuelta. Un adapter futuro debe declarar
capacidad, permisos, reversa y madurez sin elevar claims.
