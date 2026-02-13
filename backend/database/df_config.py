"""
Configuración y utilidades para conexión a Oracle Autonomous Database
Soporta thin mode sin instalación de cliente Oracle
Usa el patrón oficial de oracledb con pool de conexiones
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import oracledb

logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env en la raíz del proyecto
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path)

# Configuración de conexión Oracle Autonomous DB
ORACLE_CONFIG = {
    'user': os.environ.get('ORACLE_USER', 'ADMIN'),
    'password': os.environ.get('ORACLE_PASSWORD', ''),
    'connection_string': os.environ.get('ORACLE_CONNECTION_STRING', ''),
}

# Pool global (lazy initialization)
_pool = None


def _get_pool():
    """
    Obtiene o crea el pool de conexiones
    Patrón oficial de oracledb
    """
    global _pool
    
    if _pool is not None:
        return _pool
    
    if not ORACLE_CONFIG['connection_string']:
        raise ValueError("ORACLE_CONNECTION_STRING no está configurada")
    
    # Crear pool con parámetros optimizados (patrón oficial - thin mode)
    _pool = oracledb.create_pool(
        user=ORACLE_CONFIG['user'],
        password=ORACLE_CONFIG['password'],
        dsn=ORACLE_CONFIG['connection_string'],
        min=2,           # Mínimo 2 conexiones en el pool
        max=10,          # Máximo 10 conexiones
        increment=1      # Agregar 1 conexión cuando sea necesario
    )
    
    logger.info("✅ Pool de conexiones Oracle inicializado")
    return _pool


# Context manager para uso automático de conexión (patrón oficial)
class OracleConnection:
    """
    Context manager para conexiones Oracle
    Usa el patrón oficial: pool.acquire() con context manager
    
    Uso:
        with OracleConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(...)
    """
    
    def __enter__(self):
        self.pool = _get_pool()
        self.conn = self.pool.acquire()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
        return False


def test_connection():
    """
    Prueba la conexión a Oracle Autonomous Database (patrón oficial)
    """
    try:
        print("=" * 70)
        print("PRUEBA DE CONEXIÓN A ORACLE AUTONOMOUS DATABASE")
        print("=" * 70)
        print(f"\nIntentando conectar con:")
        print(f"  Usuario: {ORACLE_CONFIG['user']}")
        print(f"  Connection String: {ORACLE_CONFIG['connection_string']}")
        print()
        
        # Usar patrón oficial con context manager
        with OracleConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                if result:
                    print(f"✅ CONEXIÓN EXITOSA!")
                    print(f"   Query result: {result[0]}\n")
        
        print("=" * 70)
        print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
        print("=" * 70 + "\n")
        
    except oracledb.Error as e:
        print(f"\n❌ ERROR EN LA CONEXIÓN:")
        print(f"   oracledb.Error: {str(e)}\n")
        raise
    except Exception as e:
        print(f"\n❌ ERROR EN LA CONEXIÓN:")
        print(f"   {type(e).__name__}: {str(e)}\n")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    test_connection()
