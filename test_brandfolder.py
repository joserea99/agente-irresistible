#!/usr/bin/env python3
"""
Test Brandfolder API connection
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.brandfolder_service import BrandfolderAPI, test_connection

def main():
    print("=" * 60)
    print("🔍 Testing Brandfolder API Connection")
    print("=" * 60)
    
    # Check for API key
    api_key = os.environ.get('BRANDFOLDER_API_KEY')
    
    if not api_key:
        print("\n❌ BRANDFOLDER_API_KEY not found in environment")
        print("\n💡 To test locally, set the API key:")
        print("   export BRANDFOLDER_API_KEY='your-key-here'")
        print("\n📝 The API key should be configured in Railway for production")
        return 1
    
    print(f"\n✅ API Key found: {api_key[:10]}...")
    
    # Test connection
    print("\n🔌 Testing connection...")
    result = test_connection(api_key)
    
    if result['success']:
        print(f"\n{result['message']}")
        print("\n📁 Available Brandfolders:")
        for bf in result['brandfolders']:
            print(f"\n  📂 {bf['name']}")
            print(f"     Slug: {bf['slug']}")
            print(f"     ID: {bf['id']}")
            
            # Check if this is the Irresistible Church Network
            if bf['slug'] == 'irresistiblechurchnetwork':
                print(f"     🎯 This is the Irresistible Church Network!")
                print(f"     URL: https://my.irresistible.church/irresistiblechurchnetwork")
                
                # Try to get some assets
                print(f"\n     📊 Fetching assets...")
                try:
                    api = BrandfolderAPI(api_key)
                    content = api.get_all_content(bf['id'])
                    
                    print(f"     ✅ Total Assets: {content['total_assets']}")
                    print(f"     📹 Videos: {len(content['videos'])}")
                    print(f"     🎵 Audios: {len(content['audios'])}")
                    print(f"     📄 Documents: {len(content['documents'])}")
                    print(f"     📑 Sections: {len(content['sections'])}")
                    
                    if content['sections']:
                        print(f"\n     📑 Sections:")
                        for section in content['sections'][:5]:  # Show first 5
                            print(f"        - {section['name']}")
                    
                    if content['assets']:
                        print(f"\n     📦 Sample Assets:")
                        for asset in content['assets'][:3]:  # Show first 3
                            print(f"        - {asset['name']}")
                            if asset['description']:
                                desc = asset['description'][:60]
                                print(f"          {desc}...")
                    
                except Exception as e:
                    print(f"     ❌ Error fetching assets: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Brandfolder integration is working!")
        print("=" * 60)
        return 0
    else:
        print(f"\n{result['message']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
