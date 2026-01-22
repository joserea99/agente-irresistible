"""
Test script para verificar la conexión con Brandfolder API.
Ejecutar: python test_brandfolder.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_brandfolder_connection():
    """Prueba la conexión con la API de Brandfolder."""
    
    print("=" * 60)
    print("🧪 TEST DE CONEXIÓN - BRANDFOLDER API")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv("BRANDFOLDER_API_KEY")
    
    if not api_key:
        print("\n❌ ERROR: No se encontró BRANDFOLDER_API_KEY en .env")
        print("\n📋 Pasos para configurar:")
        print("   1. Ve a: https://brandfolder.com/profile#integrations")
        print("   2. Genera o copia tu API Key")
        print("   3. Agrega a tu .env: BRANDFOLDER_API_KEY=tu_key_aqui")
        return False
    
    print(f"\n✅ API Key encontrada: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        from brandfolder_api import BrandfolderAPI, test_connection
        
        print("\n🔌 Conectando a Brandfolder API...")
        result = test_connection(api_key)
        
        if result["success"]:
            print(f"\n{result['message']}")
            print("\n📂 Brandfolders disponibles:")
            print("-" * 40)
            
            for bf in result["brandfolders"]:
                print(f"  • {bf['name']}")
                print(f"    ID: {bf['id']}")
                print(f"    Slug: {bf.get('slug', 'N/A')}")
                print()
            
            # Try to find Irresistible Church brandfolder
            target = None
            for bf in result["brandfolders"]:
                name = bf.get("name", "").lower()
                slug = bf.get("slug", "").lower()
                if "irresistible" in name or "irresistible" in slug:
                    target = bf
                    break
            
            if target:
                print(f"🎯 Brandfolder objetivo encontrado: {target['name']}")
                
                # Get more details
                api = BrandfolderAPI(api_key)
                print("\n📊 Obteniendo estadísticas...")
                
                # Get sections
                sections = api.get_sections(target["id"])
                print(f"   • Secciones: {len(sections)}")
                for s in sections[:5]:
                    print(f"     - {s.get('attributes', {}).get('name', 'Sin nombre')}")
                
                # Get assets (limited)
                assets = api.get_assets(brandfolder_id=target["id"])
                print(f"   • Assets encontrados: {len(assets)}")
                
                # Show sample assets
                print("\n📄 Muestra de assets:")
                for asset in assets[:5]:
                    info = api.extract_asset_info(asset)
                    ext = info.get("extension", "?")
                    print(f"   • [{ext}] {info['name'][:50]}")
                
                print("\n" + "=" * 60)
                print("✅ CONEXIÓN EXITOSA - La API está funcionando correctamente")
                print("=" * 60)
                return True
            else:
                print("⚠️ No se encontró un brandfolder con 'irresistible' en el nombre")
                print("   Usando el primer brandfolder disponible...")
                return True
        else:
            print(f"\n❌ Error de conexión: {result['message']}")
            return False
            
    except ImportError as e:
        print(f"\n❌ Error de importación: {e}")
        print("   Asegúrate de que brandfolder_api.py existe")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def show_api_capabilities():
    """Muestra las capacidades de la API."""
    print("\n" + "=" * 60)
    print("📚 CAPACIDADES DE LA API DE BRANDFOLDER")
    print("=" * 60)
    print("""
    La API permite:
    
    🔍 Búsqueda y Navegación:
       • Listar todos los brandfolders accesibles
       • Obtener secciones y colecciones
       • Buscar assets por palabra clave
    
    📥 Obtención de Assets:
       • Descargar metadatos de assets
       • Obtener descripciones y tags
       • Acceder a URLs de archivos
    
    📄 Tipos de Contenido Soportados:
       • Videos (MP4, MOV, AVI, WebM)
       • Audios (MP3, WAV, M4A)
       • Documentos (PDF, DOCX, PPTX)
       • Imágenes y otros archivos
    
    🧠 Integración con RAG:
       • Indexar automáticamente en ChromaDB
       • Transcribir multimedia (opcional)
       • Búsqueda semántica del contenido
    """)


if __name__ == "__main__":
    success = test_brandfolder_connection()
    
    if success:
        show_api_capabilities()
        print("\n🚀 SIGUIENTE PASO:")
        print("   Ejecuta: streamlit run app.py")
        print("   Ve a '🧠 Smart Learning' en el sidebar")
        print("   Haz clic en '🚀 Iniciar Aprendizaje via API'")
