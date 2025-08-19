import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io
import base64

class SIIScraper:
    def __init__(self):
        self.setup_driver()
        
    def setup_driver(self):
        """Configurar el driver de Chrome"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Instalar ChromeDriver automáticamente
        service = Service(ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def get_captcha_image(self):
        """Extraer la imagen del captcha"""
        try:
            # Buscar la imagen del captcha
            captcha_img = self.driver.find_element(By.ID, "imgCaptcha")
            
            # Obtener la imagen como base64
            img_base64 = self.driver.execute_script("""
                var canvas = document.createElement('canvas');
                var ctx = canvas.getContext('2d');
                var img = arguments[0];
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                return canvas.toDataURL('image/png').substring(22);
            """, captcha_img)
            
            # Convertir base64 a imagen
            img_data = base64.b64decode(img_base64)
            img = Image.open(io.BytesIO(img_data))
            
            # Guardar imagen para inspección manual
            img.save("captcha_image.png")
            print("Imagen del captcha guardada como 'captcha_image.png'")
            
            return img
            
        except Exception as e:
            print(f"Error al obtener captcha: {e}")
            return None
    
    def solve_captcha_manual(self):
        """Resolver captcha manualmente (usuario ingresa el valor)"""
        try:
            # Obtener imagen del captcha
            self.get_captcha_image()
            
            # Solicitar al usuario que resuelva el captcha
            print("\n" + "="*50)
            print("CAPTCHA DETECTADO")
            print("="*50)
            print("Se ha guardado una imagen del captcha como 'captcha_image.png'")
            print("Por favor, abre esta imagen y mira el código del captcha.")
            print("="*50)
            
            captcha_value = input("Ingresa el código del captcha: ").strip()
            return captcha_value
            
        except Exception as e:
            print(f"Error al resolver captcha: {e}")
            return None
    
    def scrape_sii_data(self, rut_sin_dv="76063822", dv="6", max_attempts=3):
        """
        Scrapear datos del SII
        
        Args:
            rut_sin_dv (str): RUT sin dígito verificador
            dv (str): Dígito verificador
            max_attempts (int): Número máximo de intentos
        """
        url = "https://zeus.sii.cl/cvc/stc/stc.html"
        
        for attempt in range(max_attempts):
            try:
                print(f"\n🔄 Intento {attempt + 1} de {max_attempts}")
                print(f"🌐 Navegando a: {url}")
                
                # Navegar a la página
                self.driver.get(url)
                
                # Esperar a que la página cargue
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "RUT"))
                )
                
                print("✅ Página cargada exitosamente")
                
                # Completar el RUT
                rut_input = self.driver.find_element(By.ID, "RUT")
                rut_input.clear()
                rut_input.send_keys(rut_sin_dv)
                print(f"✅ RUT ingresado: {rut_sin_dv}")
                
                # Completar el dígito verificador
                dv_input = self.driver.find_element(By.ID, "DV")
                dv_input.clear()
                dv_input.send_keys(dv)
                print(f"✅ DV ingresado: {dv}")
                
                # Esperar un momento para que aparezca el captcha
                time.sleep(2)
                
                # Resolver captcha manualmente
                captcha_code = self.solve_captcha_manual()
                
                if not captcha_code:
                    print("❌ No se pudo resolver el captcha")
                    continue
                
                # Ingresar el código del captcha
                captcha_input = self.driver.find_element(By.ID, "txt_code")
                captcha_input.clear()
                captcha_input.send_keys(captcha_code)
                print(f"✅ Captcha ingresado: {captcha_code}")
                
                # Hacer clic en el botón de consultar
                submit_button = self.driver.find_element(By.ID, "bt_aceptar")
                submit_button.click()
                print("✅ Formulario enviado")
                
                # Esperar a que aparezca el resultado
                WebDriverWait(self.driver, 10).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CLASS_NAME, "resultado")),
                        EC.presence_of_element_located((By.CLASS_NAME, "error")),
                        EC.presence_of_element_located((By.ID, "contenido"))
                    )
                )
                
                # Esperar un poco más para asegurar que la página se cargue completamente
                time.sleep(3)
                
                # Extraer los datos del resultado
                result_data = self.extract_result_data()
                
                if result_data and "error" not in result_data.lower():
                    print("✅ Datos extraídos exitosamente")
                    return result_data
                else:
                    print("❌ Error en la respuesta o captcha incorrecto")
                    if attempt < max_attempts - 1:
                        print("🔄 Reintentando...")
                        time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Error en intento {attempt + 1}: {str(e)}")
                if attempt < max_attempts - 1:
                    print("🔄 Reintentando...")
                    time.sleep(2)
        
        print("❌ Se agotaron todos los intentos")
        return None
    
    def extract_result_data(self):
        """Extraer los datos del resultado"""
        try:
            # Obtener todo el HTML de la página de resultado
            page_source = self.driver.page_source
            
            # Buscar diferentes elementos que pueden contener el resultado
            result_elements = [
                "resultado", "contenido", "respuesta", "datos",
                "informacion", "detalle", "tabla"
            ]
            
            extracted_data = {
                "html_completo": page_source,
                "url_actual": self.driver.current_url,
                "titulo": self.driver.title
            }
            
            # Intentar extraer texto específico
            try:
                # Buscar tabla de resultados
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                if tables:
                    extracted_data["tablas"] = []
                    for i, table in enumerate(tables):
                        extracted_data["tablas"].append({
                            f"tabla_{i}": table.get_attribute("outerHTML")
                        })
                
                # Buscar divs con información
                divs = self.driver.find_elements(By.TAG_NAME, "div")
                content_divs = []
                for div in divs:
                    text = div.text.strip()
                    if text and len(text) > 10:  # Solo divs con contenido significativo
                        content_divs.append(text)
                
                extracted_data["contenido_divs"] = content_divs
                
            except Exception as e:
                print(f"Error extrayendo elementos específicos: {e}")
            
            return extracted_data
            
        except Exception as e:
            print(f"Error extrayendo datos: {e}")
            return None
    
    def save_result_to_file(self, data, filename="sii_result.html"):
        """Guardar resultado en archivo"""
        try:
            if data and "html_completo" in data:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(data["html_completo"])
                print(f"✅ Resultado guardado en: {filename}")
            
            # También guardar en formato JSON legible
            import json
            json_filename = filename.replace(".html", ".json")
            
            # Preparar datos para JSON (sin HTML completo para mejor legibilidad)
            json_data = {k: v for k, v in data.items() if k != "html_completo"}
            
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Datos estructurados guardados en: {json_filename}")
            
        except Exception as e:
            print(f"Error guardando resultado: {e}")
    
    def close(self):
        """Cerrar el navegador"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("🔒 Navegador cerrado")

def main():
    """Función principal"""
    scraper = SIIScraper()
    
    try:
        print("🚀 Iniciando scraper del SII...")
        print("📋 RUT a consultar: 76063822-6")
        
        # Realizar scraping
        result = scraper.scrape_sii_data(rut_sin_dv="76063822", dv="6")
        
        if result:
            print("\n🎉 ¡Scraping completado exitosamente!")
            
            # Guardar resultado
            scraper.save_result_to_file(result)
            
            # Mostrar resumen
            print("\n📊 RESUMEN DEL RESULTADO:")
            print("="*50)
            print(f"URL actual: {result.get('url_actual', 'N/A')}")
            print(f"Título: {result.get('titulo', 'N/A')}")
            
            if "contenido_divs" in result:
                print(f"Elementos de contenido encontrados: {len(result['contenido_divs'])}")
                for i, content in enumerate(result['contenido_divs'][:3]):  # Mostrar solo los primeros 3
                    print(f"  - Contenido {i+1}: {content[:100]}...")
            
            if "tablas" in result:
                print(f"Tablas encontradas: {len(result['tablas'])}")
            
        else:
            print("\n❌ No se pudo completar el scraping")
            
    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrumpido por el usuario")
    except Exception as e:
        print(f"\n💥 Error inesperado: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
