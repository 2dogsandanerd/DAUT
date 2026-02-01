import sys
from smart_ingestor import ingest_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python demo.py <path_to_file>")
        print("Supported: .pdf, .docx, .pptx, .md, .html")
        return

    file_path = sys.argv[1]
    print(f"--- Smart Ingest Demo: {file_path} ---")
    
    try:
        docs = ingest_file(file_path)
        doc = docs[0]
        
        print("\n✅ Success!")
        print(f"📄 Extracted Length: {len(doc.text)} chars")
        print(f"🧠 Metadata & Heuristics:")
        for k, v in doc.metadata.items():
            print(f"   - {k}: {v}")
            
        print("\n--- Content Preview (Markdown) ---")
        print(doc.text[:500] + "...")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
