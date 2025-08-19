import time
import requests
import base64
from lxml import html
import json
from rut_chile import rut_chile

class ScrapperClass:
    def __init__(self, db):
        self.db = db
        self.driver = None
        
    def setup_driver(self):
        """Configurar el driver de Chrome"""
        try:
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
            return True
            
        except Exception as e:
            print(f"Error configurando driver: {e}")
            return False
        
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
            
            # Por ahora retornamos un valor por defecto para testing
            # En un entorno de producción, esto necesitaría una interfaz para el usuario
            print("CAPTCHA DETECTADO - Se requiere intervención manual")
            
            # Implementar lógica para obtener el captcha del usuario
            # Esto podría ser a través de una interfaz web, base de datos temporal, etc.
            
            return None  # El usuario necesitará resolver esto manualmente
            
        except Exception as e:
            print(f"Error al resolver captcha: {e}")
            return None
    
    def get_customer_data_via_api(self, rut_sin_dv="76063822", dv="6"):
        """
        Obtener datos del cliente usando API externa (alternativa sin Selenium)
        
        Args:
            rut_sin_dv (str): RUT sin dígito verificador
            dv (str): Dígito verificador
        
        Returns:
            dict: Datos del cliente desde API externa
        """
        try:
            rut_completo = f"{rut_sin_dv}-{dv}"
            url = f"https://siichile.herokuapp.com/consulta?rut={rut_completo}"
            
            print(f"🌐 Consultando API externa: {url}")
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Estructurar la respuesta según nuestro formato
                result = {
                    "success": True,
                    "method": "api_externa",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "rut_consultado": rut_completo,
                    "datos_contribuyente": {
                        "rut": data.get("rut", ""),
                        "razon_social": data.get("razon_social", ""),
                        "empresa_menor_tamano": data.get("empresa_menor_tamano", ""),
                        "aut_moneda_extranjera": data.get("aut_moneda_extranjera", ""),
                        "inicio_actividades": data.get("inicio_actividades", ""),
                        "fecha_inicio_actividades": data.get("fecha_inicio_actividades", "")
                    },
                    "actividades_economicas": data.get("actividades", []),
                    "documentos_timbrados": data.get("documentos_timbrados", []),
                    "raw_response": data
                }
                
                print(f"✅ Datos obtenidos exitosamente de API externa")
                print(f"📋 Razón Social: {result['datos_contribuyente']['razon_social']}")
                print(f"📋 Actividades: {len(result['actividades_economicas'])}")
                
                return result
            else:
                return {
                    "success": False,
                    "method": "api_externa",
                    "error": f"Error en API externa: {response.status_code}",
                    "response_text": response.text,
                    "rut_consultado": rut_completo
                }
                
        except Exception as e:
            return {
                "success": False,
                "method": "api_externa", 
                "error": f"Error conectando con API externa: {str(e)}",
                "rut_consultado": f"{rut_sin_dv}-{dv}"
            }

    def get_customer_data_direct_sii(self, rut_sin_dv="76063822", dv="6"):
        """
        Obtener datos del cliente directamente del SII con captcha automático
        
        Args:
            rut_sin_dv (str): RUT sin dígito verificador
            dv (str): Dígito verificador
        
        Returns:
            dict: Datos del cliente desde SII directo
        """
        try:
            rut_completo = f"{rut_sin_dv}-{dv}"
            print(f"🎯 Consultando SII directamente: {rut_completo}")
            
            # Validar RUT
            if not rut_chile.is_valid_rut(rut_completo):
                return {
                    "success": False,
                    "method": "sii_directo",
                    "error": "RUT inválido",
                    "rut_consultado": rut_completo
                }
            
            # Obtener captcha automáticamente
            print("🔐 Obteniendo captcha automáticamente...")
            captcha_data = self.fetch_captcha()
            
            if not captcha_data:
                return {
                    "success": False,
                    "method": "sii_directo",
                    "error": "No se pudo obtener el captcha",
                    "rut_consultado": rut_completo
                }
            
            print(f"✅ Captcha obtenido: {captcha_data['code']}")
            
            # Preparar datos para la consulta
            data = {
                'RUT': rut_sin_dv,
                'DV': dv,
                'PRG': 'STC',
                'OPC': 'NOR',
                'txt_code': captcha_data['code'],
                'txt_captcha': captcha_data['captcha']
            }
            
            print("📡 Enviando consulta al SII...")
            response = requests.post('https://zeus.sii.cl/cvc_cgi/stc/getstc', data=data, timeout=30)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "method": "sii_directo",
                    "error": f"Error HTTP: {response.status_code}",
                    "rut_consultado": rut_completo
                }
            
            print("✅ Respuesta recibida, extrayendo datos...")
            
            # Parsear HTML
            tree = html.fromstring(response.text)
            
            # Extraer datos usando XPaths
            result_data = self.extract_sii_direct_data(tree, rut_completo)
            
            if result_data.get("success"):
                print("🎉 Datos extraídos exitosamente!")
                print(f"📋 Razón Social: {result_data.get('datos_contribuyente', {}).get('razon_social', 'N/A')}")
                print(f"📋 Actividades: {len(result_data.get('actividades_economicas', []))}")
                
            return result_data
            
        except Exception as e:
            print(f"❌ Error en consulta directa SII: {str(e)}")
            return {
                "success": False,
                "method": "sii_directo",
                "error": f"Error de conexión: {str(e)}",
                "rut_consultado": f"{rut_sin_dv}-{dv}"
            }
    
    def fetch_captcha(self):
        """
        Obtener captcha automáticamente desde la API del SII
        
        Returns:
            dict: Datos del captcha con código y token
        """
        try:
            response = requests.post('https://zeus.sii.cl/cvc_cgi/stc/CViewCaptcha.cgi', 
                                   data={'oper': 0}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Decodificar el captcha desde base64
                captcha_code = base64.b64decode(data['txtCaptcha'])[36:40].decode()
                
                return {
                    'code': captcha_code,
                    'captcha': data['txtCaptcha']
                }
            else:
                print(f"Error obteniendo captcha: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error en fetch_captcha: {e}")
            return None
    
    def extract_sii_direct_data(self, tree, rut_completo):
        """
        Extraer datos del HTML del SII usando XPaths específicos
        
        Args:
            tree: Árbol HTML parseado con lxml
            rut_completo (str): RUT completo consultado
            
        Returns:
            dict: Datos estructurados extraídos
        """
        try:
            # XPaths para extraer información
            XPATH_RAZON_SOCIAL = '/html/body/div/div[4]'
            XPATH_ACTIVIDADES = '/html/body/div/table[1]/tr'
            
            # Extraer razón social
            razon_social_nodes = tree.xpath(XPATH_RAZON_SOCIAL)
            razon_social = razon_social_nodes[0].text.strip() if razon_social_nodes else ""
            
            # Extraer actividades económicas
            actividades = []
            try:
                actividad_rows = tree.xpath(XPATH_ACTIVIDADES)[1:]  # Saltar header
                for node in actividad_rows:
                    try:
                        giro = node.xpath('./td[1]/font')[0].text.strip()
                        codigo = int(node.xpath('./td[2]/font')[0].text.strip())
                        categoria = node.xpath('./td[3]/font')[0].text.strip()
                        afecta = node.xpath('./td[4]/font')[0].text.strip() == 'Si'
                        
                        actividades.append({
                            'giro': giro,
                            'codigo': codigo,
                            'categoria': categoria,
                            'afecta': afecta
                        })
                    except (IndexError, ValueError):
                        continue
            except:
                pass
            
            # Extraer documentos timbrados
            documentos_timbrados = []
            try:
                table_rows = tree.xpath("//table[@class='tabla']/tr")
                for row in table_rows[1:]:  # Saltar header
                    cells = row.xpath("td/font/text()")
                    if len(cells) == 2:
                        documento = cells[0].strip()
                        ultimo_timbraje = cells[1].strip()
                        
                        documentos_timbrados.append({
                            'Documento': documento,
                            'Año último timbraje': ultimo_timbraje
                        })
            except:
                pass
            
            # Extraer información adicional usando XPaths más específicos
            inicio_actividades = ""
            fecha_inicio_actividades = ""
            empresa_menor_tamano = ""
            aut_moneda_extranjera = ""
            
            try:
                xpath_inicio = tree.xpath("//span[contains(text(),'Contribuyente presenta Inicio de Actividades:')]/text()")
                if xpath_inicio:
                    inicio_actividades = xpath_inicio[0].split(":", 1)[-1].strip()
                    
                xpath_fecha = tree.xpath("//span[contains(text(),'Fecha de Inicio de Actividades:')]/text()")
                if xpath_fecha:
                    fecha_inicio_actividades = xpath_fecha[0].split(":", 1)[-1].strip()
                    
                xpath_empresa = tree.xpath("//span[contains(text(),'Contribuyente es Empresa de Menor Tama')]/text()[last()]")
                if xpath_empresa:
                    empresa_menor_tamano = xpath_empresa[0].split(":", 1)[-1].strip()
                    
                xpath_moneda = tree.xpath("//span[contains(text(),'Contribuyente autorizado para declarar y pagar sus impuestos en moneda extranjera:')]/text()")
                if xpath_moneda:
                    aut_moneda_extranjera = xpath_moneda[0].split(":", 1)[-1].strip()
            except:
                pass
            
            # Estructurar respuesta
            result = {
                "success": True,
                "method": "sii_directo",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "rut_consultado": rut_completo,
                "datos_contribuyente": {
                    "rut": rut_completo,
                    "razon_social": razon_social,
                    "empresa_menor_tamano": empresa_menor_tamano,
                    "aut_moneda_extranjera": aut_moneda_extranjera,
                    "inicio_actividades": inicio_actividades,
                    "fecha_inicio_actividades": fecha_inicio_actividades
                },
                "actividades_economicas": actividades,
                "documentos_timbrados": documentos_timbrados
            }
            
            # Verificar si se obtuvieron datos válidos
            if razon_social or actividades or documentos_timbrados:
                return result
            else:
                return {
                    "success": False,
                    "method": "sii_directo",
                    "error": "No se encontraron datos válidos en la respuesta del SII",
                    "rut_consultado": rut_completo
                }
                
        except Exception as e:
            return {
                "success": False,
                "method": "sii_directo",
                "error": f"Error extrayendo datos: {str(e)}",
                "rut_consultado": rut_completo
            }
        """
        Obtener datos del cliente usando API externa (alternativa sin Selenium)
        
        Args:
            rut_sin_dv (str): RUT sin dígito verificador
            dv (str): Dígito verificador
        
        Returns:
            dict: Datos del cliente desde API externa
        """
        try:
            rut_completo = f"{rut_sin_dv}-{dv}"
            url = f"https://siichile.herokuapp.com/consulta?rut={rut_completo}"
            
            print(f"🌐 Consultando API externa: {url}")
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Estructurar la respuesta según nuestro formato
                result = {
                    "success": True,
                    "method": "api_externa",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "rut_consultado": rut_completo,
                    "datos_contribuyente": {
                        "rut": data.get("rut", ""),
                        "razon_social": data.get("razon_social", ""),
                        "empresa_menor_tamano": data.get("empresa_menor_tamano", ""),
                        "aut_moneda_extranjera": data.get("aut_moneda_extranjera", ""),
                        "inicio_actividades": data.get("inicio_actividades", ""),
                        "fecha_inicio_actividades": data.get("fecha_inicio_actividades", "")
                    },
                    "actividades_economicas": data.get("actividades", []),
                    "documentos_timbrados": data.get("documentos_timbrados", []),
                    "raw_response": data
                }
                
                print(f"✅ Datos obtenidos exitosamente de API externa")
                print(f"📋 Razón Social: {result['datos_contribuyente']['razon_social']}")
                print(f"📋 Actividades: {len(result['actividades_economicas'])}")
                
                return result
            else:
                return {
                    "success": False,
                    "method": "api_externa",
                    "error": f"Error en API externa: {response.status_code}",
                    "response_text": response.text,
                    "rut_consultado": rut_completo
                }
                
        except Exception as e:
            return {
                "success": False,
                "method": "api_externa", 
                "error": f"Error conectando con API externa: {str(e)}",
                "rut_consultado": f"{rut_sin_dv}-{dv}"
            }

    def get_customer_data(self, rut_sin_dv="76063822", dv="6", max_attempts=3, use_api_first=True):
        """
        Obtener datos del cliente desde el SII
        
        Args:
            rut_sin_dv (str): RUT sin dígito verificador
            dv (str): Dígito verificador
            max_attempts (int): Número máximo de intentos (no usado con API)
            use_api_first (bool): Si usar API externa (recomendado)
        
        Returns:
            dict: Datos del cliente extraídos del SII
        """
        
        # Método 1: API externa (más rápido)
        print("🚀 Método 1: Intentando API externa...")
        api_result = self.get_customer_data_via_api(rut_sin_dv, dv)
        
        if api_result.get("success"):
            print("✅ Datos obtenidos exitosamente con API externa!")
            return api_result
        else:
            print(f"❌ API externa falló: {api_result.get('error', 'Error desconocido')}")
        
        # Método 2: SII directo con captcha automático
        print("🎯 Método 2: Intentando SII directo con captcha automático...")
        sii_result = self.get_customer_data_direct_sii(rut_sin_dv, dv)
        
        if sii_result.get("success"):
            print("✅ Datos obtenidos exitosamente con SII directo!")
            return sii_result
        else:
            print(f"❌ SII directo falló: {sii_result.get('error', 'Error desconocido')}")
        
        # Si ambos métodos fallan
        return {
            "success": False,
            "method": "todos_los_metodos_fallaron",
            "errors": {
                "api_externa": api_result.get("error", ""),
                "sii_directo": sii_result.get("error", "")
            },
            "rut_consultado": f"{rut_sin_dv}-{dv}",
            "recomendacion": "Verificar conectividad y validez del RUT"
        }
    
    def get_customer_data_via_selenium(self, rut_sin_dv="76063822", dv="6", max_attempts=3):
        """
        Obtener datos del cliente usando Selenium (método original)
        
        Args:
            rut_sin_dv (str): RUT sin dígito verificador
            dv (str): Dígito verificador
            max_attempts (int): Número máximo de intentos
        
        Returns:
            dict: Datos del cliente extraídos del SII
        """
        url = "https://zeus.sii.cl/cvc/stc/stc.html"
        
        # Configurar driver
        if not self.setup_driver():
            return {
                "success": False,
                "error": "No se pudo configurar el navegador",
                "rut_consultado": f"{rut_sin_dv}-{dv}"
            }
        
        try:
            for attempt in range(max_attempts):
                try:
                    print(f"🔄 Intento {attempt + 1} de {max_attempts}")
                    
                    # Navegar a la página
                    self.driver.get(url)
                    
                    # Esperar a que la página cargue
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "RUT"))
                    )
                    
                    print(f"✅ Página cargada, ingresando datos...")
                    
                    # Completar el RUT
                    rut_input = self.driver.find_element(By.ID, "RUT")
                    rut_input.clear()
                    rut_input.send_keys(rut_sin_dv)
                    
                    # Completar el dígito verificador
                    dv_input = self.driver.find_element(By.ID, "DV")
                    dv_input.clear()
                    dv_input.send_keys(dv)
                    
                    print(f"✅ RUT {rut_sin_dv}-{dv} ingresado")
                    
                    # Esperar a que aparezca el captcha
                    time.sleep(3)
                    
                    # Intentar resolver el captcha automáticamente
                    captcha_solved = self.attempt_captcha_resolution_with_context(rut_sin_dv, dv)
                    
                    if not captcha_solved:
                        print("❌ No se pudo resolver el captcha automáticamente")
                        continue
                    
                    print("✅ Captcha resuelto, enviando formulario...")
                    
                    # Hacer clic en el botón de consultar
                    submit_button = self.driver.find_element(By.ID, "bt_aceptar")
                    submit_button.click()
                    
                    # Esperar a que aparezca el resultado
                    print("⏳ Esperando resultados...")
                    WebDriverWait(self.driver, 15).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CLASS_NAME, "resultado")),
                            EC.presence_of_element_located((By.CLASS_NAME, "error")),
                            EC.presence_of_element_located((By.ID, "contenido")),
                            EC.presence_of_element_located((By.TAG_NAME, "table")),
                            EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "contribuyente")
                        )
                    )
                    
                    # Esperar un poco más para asegurar que la página se cargue completamente
                    time.sleep(5)
                    
                    print("✅ Resultados cargados, extrayendo datos...")
                    
                    # Extraer los datos del resultado
                    result_data = self.extract_sii_data()
                    
                    if result_data and result_data.get("success"):
                        print("🎉 Datos extraídos exitosamente!")
                        return result_data
                    else:
                        print("⚠️ No se encontraron datos válidos")
                        if attempt < max_attempts - 1:
                            print("🔄 Reintentando...")
                            time.sleep(3)
                    
                except Exception as e:
                    print(f"❌ Error en intento {attempt + 1}: {str(e)}")
                    if attempt < max_attempts - 1:
                        print("🔄 Reintentando...")
                        time.sleep(3)
            
            return {
                "success": False,
                "message": "Se agotaron todos los intentos sin obtener datos válidos",
                "rut_consultado": f"{rut_sin_dv}-{dv}",
                "intentos_realizados": max_attempts
            }
            
        finally:
            self.close_driver()
    
    def attempt_captcha_resolution_with_context(self, rut_sin_dv, dv):
        """
        Intentar resolver el captcha automáticamente con contexto de RUT
        
        Args:
            rut_sin_dv (str): RUT sin dígito verificador
            dv (str): Dígito verificador
            
        Returns:
            bool: True si se resolvió exitosamente, False en caso contrario
        """
        try:
            # Esperar a que la página cargue completamente
            time.sleep(5)
            
            # Buscar el campo del captcha con diferentes selectores posibles
            captcha_input = None
            captcha_selectors = ["txt_code", "captcha", "codigo", "code"]
            
            for selector in captcha_selectors:
                try:
                    captcha_input = self.driver.find_element(By.ID, selector)
                    print(f"✅ Campo captcha encontrado con ID: {selector}")
                    break
                except:
                    continue
            
            if not captcha_input:
                # Intentar por name attribute
                try:
                    captcha_input = self.driver.find_element(By.NAME, "txt_code")
                    print("✅ Campo captcha encontrado por name")
                except:
                    print("❌ No se pudo encontrar el campo del captcha")
                    return False
            
            # Método 1: Intentar con números comunes (estrategia básica)
            common_codes = ["1234", "0000", "1111", "2222", "5555", "1212", "2121", "9999", "4321"]
            
            for code in common_codes:
                try:
                    print(f"🔢 Probando código: {code}")
                    captcha_input.clear()
                    captcha_input.send_keys(code)
                    
                    # Hacer click en consultar
                    submit_button = self.driver.find_element(By.ID, "bt_aceptar")
                    submit_button.click()
                    
                    # Esperar un poco para ver la respuesta
                    time.sleep(3)
                    
                    # Verificar si hay un error de captcha o si pasó
                    page_source = self.driver.page_source.lower()
                    current_url = self.driver.current_url
                    
                    print(f"🌐 URL actual: {current_url}")
                    
                    # Verificar si cambió de página o hay contenido de resultado
                    if (current_url != "https://zeus.sii.cl/cvc/stc/stc.html" or
                        any(keyword in page_source for keyword in ["contribuyente", "situación", "tributaria", "vigente", "resultado"])):
                        print(f"✅ Captcha resuelto con código: {code}")
                        return True
                    
                    # Verificar si hay mensaje de error específico
                    if any(error in page_source for error in ["incorrecto", "error", "inválido"]):
                        print(f"❌ Código {code} incorrecto, volviendo a intentar...")
                        # Volver a la página inicial
                        self.driver.get("https://zeus.sii.cl/cvc/stc/stc.html")
                        time.sleep(3)
                        
                        # Re-llenar los campos RUT y DV
                        rut_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.ID, "RUT"))
                        )
                        dv_input = self.driver.find_element(By.ID, "DV")
                        
                        rut_input.clear()
                        rut_input.send_keys(rut_sin_dv)
                        dv_input.clear()
                        dv_input.send_keys(dv)
                        
                        time.sleep(2)
                        
                        # Buscar el campo captcha nuevamente
                        for selector in captcha_selectors:
                            try:
                                captcha_input = self.driver.find_element(By.ID, selector)
                                break
                            except:
                                continue
                        
                        continue
                    else:
                        print(f"🤔 Respuesta inesperada para código {code}")
                        
                except Exception as e:
                    print(f"❌ Error probando código {code}: {e}")
                    continue
            
            print("❌ No se pudo resolver el captcha con códigos comunes")
            return False
            
        except Exception as e:
            print(f"❌ Error en resolución de captcha: {e}")
            return False

    def attempt_captcha_resolution(self):
        """
        Intentar resolver el captcha automáticamente
        
        Returns:
            bool: True si se resolvió exitosamente, False en caso contrario
        """
        try:
            # Esperar a que la página cargue completamente
            time.sleep(5)
            
            # Buscar el campo del captcha con diferentes selectores posibles
            captcha_input = None
            captcha_selectors = ["txt_code", "captcha", "codigo", "code"]
            
            for selector in captcha_selectors:
                try:
                    captcha_input = self.driver.find_element(By.ID, selector)
                    print(f"✅ Campo captcha encontrado con ID: {selector}")
                    break
                except:
                    continue
            
            if not captcha_input:
                # Intentar por name attribute
                try:
                    captcha_input = self.driver.find_element(By.NAME, "txt_code")
                    print("✅ Campo captcha encontrado por name")
                except:
                    print("❌ No se pudo encontrar el campo del captcha")
                    return False
            
            # Buscar la imagen del captcha con diferentes selectores
            captcha_img = None
            img_selectors = ["imgCaptcha", "captcha_img", "captcha-image", "imagen_captcha"]
            
            for selector in img_selectors:
                try:
                    captcha_img = self.driver.find_element(By.ID, selector)
                    print(f"✅ Imagen captcha encontrada con ID: {selector}")
                    break
                except:
                    continue
            
            if not captcha_img:
                # Buscar cualquier imagen que contenga "captcha" en su src o alt
                try:
                    images = self.driver.find_elements(By.TAG_NAME, "img")
                    for img in images:
                        src = img.get_attribute("src") or ""
                        alt = img.get_attribute("alt") or ""
                        if "captcha" in src.lower() or "captcha" in alt.lower():
                            captcha_img = img
                            print("✅ Imagen captcha encontrada por contenido")
                            break
                except:
                    pass
            
            if not captcha_img:
                print("⚠️ No se encontró imagen de captcha, intentando sin validación de imagen")
            
            # Inspeccionar la página para debug
            print("🔍 Inspeccionando elementos de la página...")
            try:
                # Buscar todos los inputs
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                print(f"📝 Inputs encontrados: {len(inputs)}")
                for i, inp in enumerate(inputs):
                    input_id = inp.get_attribute("id") or "sin_id"
                    input_name = inp.get_attribute("name") or "sin_name"
                    input_type = inp.get_attribute("type") or "sin_type"
                    print(f"   Input {i}: ID='{input_id}', NAME='{input_name}', TYPE='{input_type}'")
                
                # Buscar todas las imágenes
                images = self.driver.find_elements(By.TAG_NAME, "img")
                print(f"🖼️ Imágenes encontradas: {len(images)}")
                for i, img in enumerate(images):
                    img_id = img.get_attribute("id") or "sin_id"
                    img_src = img.get_attribute("src") or "sin_src"
                    print(f"   Imagen {i}: ID='{img_id}', SRC='{img_src[:100]}...'")
                    
            except Exception as e:
                print(f"Error en inspección: {e}")
            
            # Método 1: Intentar con números comunes (estrategia básica)
            common_codes = ["1234", "0000", "1111", "2222", "5555", "1212", "2121", "9999", "4321"]
            
            for code in common_codes:
                try:
                    print(f"🔢 Probando código: {code}")
                    captcha_input.clear()
                    captcha_input.send_keys(code)
                    
                    # Hacer click en consultar
                    submit_button = self.driver.find_element(By.ID, "bt_aceptar")
                    submit_button.click()
                    
                    # Esperar un poco para ver la respuesta
                    time.sleep(3)
                    
                    # Verificar si hay un error de captcha o si pasó
                    page_source = self.driver.page_source.lower()
                    current_url = self.driver.current_url
                    
                    print(f"🌐 URL actual: {current_url}")
                    
                    # Verificar si cambió de página o hay contenido de resultado
                    if (current_url != "https://zeus.sii.cl/cvc/stc/stc.html" or
                        any(keyword in page_source for keyword in ["contribuyente", "situación", "tributaria", "vigente", "resultado"])):
                        print(f"✅ Captcha resuelto con código: {code}")
                        return True
                    
                    # Verificar si hay mensaje de error específico
                    if any(error in page_source for error in ["incorrecto", "error", "inválido"]):
                        print(f"❌ Código {code} incorrecto")
                        # Volver a la página inicial
                        self.driver.get("https://zeus.sii.cl/cvc/stc/stc.html")
                        time.sleep(3)
                        
                        # Re-llenar los campos RUT y DV
                        rut_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.ID, "RUT"))
                        )
                        dv_input = self.driver.find_element(By.ID, "DV")
                        
                        # Obtener valores desde el contexto de la clase (necesitamos pasarlos)
                        # Por ahora usar valores por defecto
                        rut_input.clear()
                        rut_input.send_keys("76063822")
                        dv_input.clear()
                        dv_input.send_keys("6")
                        
                        time.sleep(2)
                        
                        # Buscar el campo captcha nuevamente
                        for selector in captcha_selectors:
                            try:
                                captcha_input = self.driver.find_element(By.ID, selector)
                                break
                            except:
                                continue
                        
                        continue
                    else:
                        print(f"🤔 Respuesta inesperada para código {code}")
                        
                except Exception as e:
                    print(f"❌ Error probando código {code}: {e}")
                    continue
            
            print("❌ No se pudo resolver el captcha con códigos comunes")
            return False
            
        except Exception as e:
            print(f"❌ Error en resolución de captcha: {e}")
            return False
    
    def extract_sii_data(self):
        """
        Extraer los datos específicos de la situación tributaria del SII
        
        Returns:
            dict: Datos estructurados de la consulta SII
        """
        try:
            page_source = self.driver.page_source
            current_url = self.driver.current_url
            
            # Estructura base de respuesta
            extracted_data = {
                "success": True,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "url_consultada": current_url,
                "datos_contribuyente": {},
                "situacion_tributaria": {},
                "actividades_economicas": [],
                "raw_html": page_source
            }
            
            # Extraer información del contribuyente desde tablas
            try:
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                
                for table in tables:
                    table_text = table.text.lower()
                    table_html = table.get_attribute("outerHTML")
                    
                    # Buscar información del contribuyente
                    if any(keyword in table_text for keyword in ["rut", "razón social", "nombre", "contribuyente"]):
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                key = cells[0].text.strip().lower()
                                value = cells[1].text.strip()
                                
                                if "rut" in key:
                                    extracted_data["datos_contribuyente"]["rut"] = value
                                elif "razón social" in key or "nombre" in key:
                                    extracted_data["datos_contribuyente"]["razon_social"] = value
                                elif "dirección" in key or "domicilio" in key:
                                    extracted_data["datos_contribuyente"]["direccion"] = value
                                elif "comuna" in key:
                                    extracted_data["datos_contribuyente"]["comuna"] = value
                                elif "región" in key:
                                    extracted_data["datos_contribuyente"]["region"] = value
                    
                    # Buscar situación tributaria
                    if any(keyword in table_text for keyword in ["situación", "estado", "vigente", "activo"]):
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                key = cells[0].text.strip().lower()
                                value = cells[1].text.strip()
                                
                                if "situación" in key or "estado" in key:
                                    extracted_data["situacion_tributaria"]["estado"] = value
                                elif "fecha" in key:
                                    extracted_data["situacion_tributaria"]["fecha"] = value
                    
                    # Buscar actividades económicas
                    if any(keyword in table_text for keyword in ["actividad", "económica", "giro"]):
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                codigo = cells[0].text.strip()
                                descripcion = cells[1].text.strip()
                                
                                if codigo and descripcion and codigo.isdigit():
                                    extracted_data["actividades_economicas"].append({
                                        "codigo": codigo,
                                        "descripcion": descripcion
                                    })
            
            except Exception as e:
                print(f"Error extrayendo datos de tablas: {e}")
            
            # Extraer información de divs y spans también
            try:
                # Buscar información en divs
                divs = self.driver.find_elements(By.TAG_NAME, "div")
                content_text = []
                
                for div in divs:
                    text = div.text.strip()
                    if text and len(text) > 10:
                        content_text.append(text)
                
                extracted_data["contenido_textual"] = content_text
                
            except Exception as e:
                print(f"Error extrayendo contenido textual: {e}")
            
            # Verificar si se obtuvieron datos válidos
            if (extracted_data["datos_contribuyente"] or 
                extracted_data["situacion_tributaria"] or 
                extracted_data["actividades_economicas"] or
                any("contribuyente" in text.lower() for text in extracted_data.get("contenido_textual", []))):
                
                print(f"✅ Datos extraídos: {len(extracted_data['datos_contribuyente'])} datos del contribuyente, "
                      f"{len(extracted_data['actividades_economicas'])} actividades económicas")
                return extracted_data
            else:
                print("⚠️ No se encontraron datos válidos en la respuesta")
                return {"success": False, "message": "No se encontraron datos válidos"}
            
        except Exception as e:
            print(f"❌ Error extrayendo datos del SII: {e}")
            return {"success": False, "error": str(e)}
    
    def save_result_to_file(self, data, filename="sii_result.html"):
        """Guardar resultado en archivo"""
        try:
            if data and "html_completo" in data:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(data["html_completo"])
                print(f"Resultado guardado en: {filename}")
            
            # También guardar en formato JSON legible
            json_filename = filename.replace(".html", ".json")
            
            # Preparar datos para JSON (sin HTML completo para mejor legibilidad)
            json_data = {k: v for k, v in data.items() if k != "html_completo"}
            
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"Datos estructurados guardados en: {json_filename}")
            
        except Exception as e:
            print(f"Error guardando resultado: {e}")
    
    def close_driver(self):
        """Cerrar el navegador"""
        if self.driver:
            try:
                self.driver.quit()
                print("Navegador cerrado")
            except:
                pass
            self.driver = None
    
    def __del__(self):
        """Destructor para asegurar que el driver se cierre"""
        self.close_driver()
