
from db import obtener_conexion

try:
    conexion = obtener_conexion()

    print("¡Conexión exitosa con XAMPP!")

    cursor = conexion.cursor()
    cursor.execute("SELECT DATABASE()")

    print("Base de datos:", cursor.fetchone()[0])

    cursor.close()
    conexion.close()

except Exception as error:
    print("Error de conexión:", error)
