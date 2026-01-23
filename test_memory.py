
from rag_manager import RAGManager
import os

def test_deduplication():
    print("🧪 Iniciando prueba de deduplicación...")
    
    # Initialize RAG
    rag = RAGManager()
    
    source = "test://document_A"
    content = "Este es un contenido de prueba para verificar la memoria."
    
    # 1. Agregar por primera vez
    print(f"📝 Intentando agregar {source} (1ra vez)...")
    added = rag.add_document(content, source, title="Test Doc")
    if added:
        print("✅ Éxito: Documento agregado correctamente.")
    else:
        print("⚠️ Advertencia: El documento ya existía (esto puede pasar si corres el test varias veces sin limpiar DB).")

    # 2. Intentar agregar de nuevo
    print(f"📝 Intentando agregar {source} (2da vez)...")
    added_again = rag.add_document(content, source, title="Test Doc")
    
    if not added_again:
        print("✅ Éxito: El sistema detectó el duplicado y lo omitió.")
    else:
        print("❌ Error: El sistema agregó el documento nuevamente (duplicado no detectado).")

if __name__ == "__main__":
    test_deduplication()
