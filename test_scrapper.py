from app.backend.classes.scrapper_class import ScrapperClass
import json

# Mock de DB para testing
class MockDB:
    pass

def test_scrapper():
    scrapper = ScrapperClass(MockDB())
    result = scrapper.get_customer_data('76063822', '6')
    
    print("🚀 Resultado del ScrapperClass:")
    print("="*50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("="*50)
    
    return result

if __name__ == "__main__":
    test_scrapper()
