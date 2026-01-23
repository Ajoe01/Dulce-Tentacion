"""
Script para cargar variables de entorno desde archivo .env
"""
import os

def load_env_file(env_file='.env'):
    """Carga variables de entorno desde un archivo"""
    if not os.path.exists(env_file):
        print(f"⚠️  Archivo {env_file} no encontrado")
        print("💡 Crea un archivo .env basado en .env.example")
        return False
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Ignorar comentarios y líneas vacías
            if not line or line.startswith('#'):
                continue
            
            # Parsear variable=valor
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                os.environ[key] = value
                print(f"✅ {key} cargado")
    
    return True

if __name__ == "__main__":
    print("🔧 Cargando variables de entorno...")
    if load_env_file():
        print("\n✅ Variables de entorno cargadas correctamente")
        print("\nVariables configuradas:")
        print(f"  SECRET_KEY: {'✅ Configurado' if os.environ.get('SECRET_KEY') else '❌ No configurado'}")
        print(f"  ADMIN_PASSWORD: {'✅ Configurado' if os.environ.get('ADMIN_PASSWORD') else '❌ No configurado'}")
        print(f"  CLOUDINARY_CLOUD_NAME: {'✅ Configurado' if os.environ.get('CLOUDINARY_CLOUD_NAME') else '❌ No configurado'}")
        print(f"  CLOUDINARY_API_KEY: {'✅ Configurado' if os.environ.get('CLOUDINARY_API_KEY') else '❌ No configurado'}")
        print(f"  CLOUDINARY_API_SECRET: {'✅ Configurado' if os.environ.get('CLOUDINARY_API_SECRET') else '❌ No configurado'}")
    else:
        print("\n❌ No se pudieron cargar las variables de entorno")