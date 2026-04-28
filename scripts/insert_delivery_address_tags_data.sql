-- Resuelve region_id y commune_id desde tablas `regions` y `communes`.
-- Ajusta los literales d.region / d.commune si en tu base los nombres difieren
-- (tildes, "Región Metropolitana" vs "Metropolitana de Santiago", etc.).
--
-- Nombre de tabla: el modelo usa `delivery_address_tags`. Si la tuya es
-- `delivery_adress_tags`, reemplaza el nombre abajo.

INSERT INTO delivery_address_tags (
  region_id,
  commune_id,
  branch_office,
  address,
  supervisor_rut,
  supervisor,
  phone,
  company_name,
  company_rut,
  company_phone,
  company_address,
  added_date,
  updated_date
)
SELECT
  r.id,
  c.id,
  d.branch_office,
  d.address,
  d.supervisor_rut,
  d.supervisor,
  d.phone,
  d.company_name,
  d.company_rut,
  d.company_phone,
  d.company_address,
  NOW(),
  NOW()
FROM (
  -- region, commune, resto de columnas (orden igual al final)
  SELECT 'Antofagasta' AS region, 'Antofagasta' AS commune, 'UNIMARC EL PAMPINO' AS branch_office, 'Jose Santos Ossa 2350, Antofagasta' AS address, '10923452-4' AS supervisor_rut, 'Fidelia Del Carmen Contreras Gonzalez' AS supervisor, '944320968' AS phone, 'JIS Parking Spa' AS company_name, '76.063.822-6' AS company_rut, '+569 68454900' AS company_phone, 'Matucana 40, Est Central. Santiago' AS company_address
  UNION ALL SELECT 'Antofagasta', 'Antofagasta', 'UNIMARC EL PARQUE', 'Antofagasta,Av. Jose Miguel Carrera Carrera 1527, Antofagasta', '10923452-4', 'Fidelia Del Carmen Contreras Gonzalez', '944320968', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Coquimbo', 'La Serena', 'UNIMARC LA SERENA', 'Avda. Brasil 766, La Serena', '11694645-9', 'Ana Maria Estolaza Peralta', '963413639', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Coquimbo', 'Ovalle', 'UNIMARC OVALLE', 'Libertad 230, Ovalle', '16849126-3', 'Sofia Alejandra Mundaca Mundaca', '966423344', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Valparaíso', 'Quillota', 'UNIMARC QUILLOTA', 'Bernardo O''higgins 34, Quillota', '10137545-5', 'Margarita Del Carmen Contreras Paredes', '972498288', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Valparaíso', 'Viña del Mar', 'STA ISABEL REÑACA', 'Rafael Sotomayor 230, Viña del Mar', '14481738-9', 'Evelyn Damarys Molina Saavedra', '996468885', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Valparaíso', 'Quilpué', 'STA ISABEL LOS CARRERAS', 'Portales 770, Valparaiso', '09134412-2', 'Gladys Antonia Villegas Alvarez', '954263344', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Valparaíso', 'Quilpué', 'STA ISABEL CLAUDIO VICUÑA', 'Claudio Vicuña 696, Quilpue', '09134412-2', 'Gladys Antonia Villegas Alvarez', '954263344', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Valparaíso', 'Quillota', 'MALL PASEO DEL VALLE', 'O''higgins 176, Quillota', '10137545-5', 'Margarita Del Carmen Contreras Paredes', '972498288', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Maipú', 'ALVI MAIPU', 'Los Pajaritos 1631, Santiago', '28888888-8', 'Marcelo Inzunza (Supervisor)', '968454900', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Providencia', 'UNIMARC FCO BILBAO', 'Avda. Francisco Bilbao 2050, Providencia', '21902443-6', 'David Wilder Gomez Figueroa', '942998970', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Las Condes', 'UNIMARC LOS MILITARES', 'Avda. Manquehue Norte 457, Las Condes', '21902443-6', 'David Wilder Gomez Figueroa', '942998970', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Maipú', 'MEDS MAIPU', 'Los Pajaritos 1968, Maipu', '28888888-8', 'Marcelo Inzunza (Supervisor)', '968454900', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Ñuñoa', 'SODIMAC ÑUBLE', 'Vicuña Mackenna 1770, Ñuñoa', '21902443-6', 'David Wilder Gomez Figueroa', '942998970', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Santiago', 'TOTTUS NATANIEL', 'Nataniel Cox 620, Santiago', '21902443-6', 'David Wilder Gomez Figueroa', '942998970', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'San Bernardo', 'TOTTUS SAN BERNARDO', 'O''Higgins 528, San Bernardo', '12233298-5', 'Elizabeth Patricia Gonzalez Carrasco', '984744916', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Santiago', 'TOTTUS VICUÑA MACKENNA', 'Vicuña Mackenna 665, Santiago', '21902443-6', 'David Wilder Gomez Figueroa', '942998970', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Ñuble', 'Chillán', 'UNIMARC CHILLAN', 'Arauco 755, Chillán', '15757306-3', 'Dario De Jesus Contreras Martinez', '997184924', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Los Lagos', 'Osorno', 'UNIMARC OSORNO', 'Avenida Patricio Lynch 1278, Osorno', '17125113-3', 'Debora Eunice Filun Filun', '984365326', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Biobío', 'Concepción', 'UNIMARC CONCEPCION', 'Chacabuco 70, Concepcion', '15808735-9', 'Adriana Paulina Castillo Aguirre', '946201725', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Maule', 'Linares', 'UNIMARC LINARES', 'Maipu 556-B, Linares', '16404869-1', 'Fabiola Yamilet Fuentealba Viveros', '984606050', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Santiago', 'EL MUSEO', 'Matucana 501, Santiago', '08820315-1', 'Benjamin Leonardo Bruyer Gonzalez', '942547662', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Santiago', 'MALL CENTRO', 'Puente 689, Santiago', '08820315-1', 'Benjamin Leonardo Bruyer Gonzalez', '942547662', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Melipilla', 'MALL MELIPILLA', 'Av. Serrano 395, Melipilla', '13708510-0', 'Alejandrina Del Carmen Contreras Lopez', '974103963', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'San Bernardo', 'MALL SAN BERNARDO', 'Eyzaguirre 650, San Bernardo', '12233298-5', 'Elizabeth Patricia Gonzalez Carrasco', '984744916', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Santiago', 'TOTTUS CATEDRAL', 'Catedral 1850, Santiago', '08820315-1', 'Benjamin Leonardo Bruyer Gonzalez', '942547662', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Providencia', 'UNIV AUTONOMA', 'Pedro de Valdivia 425, Providencia', '21902443-6', 'David Wilder Gomez Figueroa', '942998970', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'San Miguel', 'CLINICA AUTONOMA', 'Llano subercaseaux 2801, San Miguel', '08820315-1', 'Benjamin Leonardo Bruyer Gonzalez', '942547662', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Libertador General Bernardo O''Higgins', 'Rengo', 'TOTTUS RENGO', 'Carlos Condell 100', '28888888-8', 'Marcelo Inzunza (Supervisor)', '968454900', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Valparaíso', 'Villa Alemana', 'STA ISABEL VILLA ALEMANA', 'Av. Valparaiso 569, Valparaiso', '09134412-2', 'Gladys Antonia Villegas Alvarez', '954263344', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'San Bernardo', 'TOTTUS SAN BERNARDO ESTACION', 'Arturo Prat 117, San Bernardo', '12233298-5', 'Elizabeth Patricia Gonzalez Carrasco', '984744916', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Los Lagos', 'Osorno', 'LIDER OSORNO', 'Federico Errazuriz 1358, Osorno', '17125113-3', 'Debora Eunice Filun Filun', '984365326', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Los Lagos', 'Puerto Montt', 'LIDER PUERTO MONTT', 'Balmaceda, Nro: 212', '27834958-6', 'Eliana Marcela Alquerque Avendaño', '945714126', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Biobío', 'Los Ángeles', 'STA ISABEL LOS ANGELES', 'Av Alemania 770, Los Angeles', '16062562-7', 'Pamela Soraya Morales Medina', '942604657', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Talagante', 'LIDER TALAGANTE', 'Av Bernanrdo Ohiggins, Nro: 807', '25310683-2', 'Edwin Alexander Arteaga Barrios', '962581133', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Santiago', 'EDIFICIO BANCOESTADO', 'Santo Domingo, Nro: 1568, Santiago', '26803446-3', 'Carlos Eduardo Bruestlen Tovar', '977714194', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Los Ríos', 'Valdivia', 'LIDER VALDIVIA', 'Av. Ramon Picarte 640, Valdivia', '12996111-2', 'Viviana Del Carmen Navarro Gonzalez', '961005025', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Estación Central', 'OFICINA', 'Matucana 40, Estación Central', '10033741-K', 'Marcelo Alejandro Inzunza Gonzalez', '968454900', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Estación Central', 'ALMACEN', 'Matucana 40, Estación Central', '18415383-1', '', NULL, 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'San Miguel', 'LIDER GRAN AVENIDA', 'G. AV. JOSE MIGUEL CARRERA #4004', '21902443-6', 'David Wilder Gomez Figueroa', '942998970', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Libertador General Bernardo O''Higgins', 'Rancagua', 'LIDER RANCAGUA', 'JOSÉ DOMINGO MUJICA 1029', '28888888-8', 'Marcelo Inzunza (Supervisor)', '968454900', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Valparaíso', 'Limache', 'LIDER LIMACHE', 'Arturo Prat Lote B SN Fco #244, Limache', '27333165-4', 'Ana Rosa Acuña Segura', '950455498', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Coquimbo', 'Ovalle', 'LIDER OVALLE', 'ARISTIA ORIENTE LT #B', '11938713-2', 'Walter Arnaldo Pasten Cortes', '985567214', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Providencia', 'LIDER TOBALABA', 'Avenida Tobalaba #691', '21902443-6', 'David Wilder Gomez Figueroa', '942998970', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Santiago', 'UNIV BERNARDO OHIGGINS', 'GENERAL GANA #1670 Block #SUBT. DEPTO. #-2Y-3 CIUDAD SANTIAGO', '08820315-1', 'Benjamin Leonardo Bruyer Gonzalez', '942547662', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Atacama', 'Copiapó', 'LIDER COPIAPO', 'Chacabuco 120', '24773648-4', 'Delvy Zamira Hernandez Arias', '986020991', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Maule', 'Talca', 'STRIP TALCA', 'CALLE 2 NORTE #3230 CIUDAD TALCA COMUNA TALCA REGION DEL MAULE', '18228287-1', 'Anibal Isaac Alvear Saavedra', '974032166', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Peñalolén', 'LIDER QUILIN', 'AV. AMERICO VESPUCIO #3100 CIUDAD SANTIAGO COMUNA PENALOLEN REGION METROPOLITANA', '21902443-6', 'David Wilder Gomez Figueroa', '942998970', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Valparaíso', 'Viña del Mar', 'STA ISABEL VILLANELO', 'AV VALPARAÍSO E.VILLANELO #236 CIUDAD VALPARAÍSO COMUNA VINA DEL MAR REGION DE VALPARAISO', '15498400-3', 'Silvana Vanessa Molina Saavedra', '985186485', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Biobío', 'Los Ángeles', 'TOTTUS LOS ANGELES', 'Av. ALEMANIA 831,Los Angeles', '14594420-1', 'Nayade Macarena Valverde Valverde', '941491729', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Biobío', 'Los Ángeles', 'LIDER LOS ANGELES', 'Av. Ricardo Vicuña 284, Los Angeles', '16062562-7', 'Pamela Soraya Morales Medina', '942604657', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Estación Central', 'LIDER ALAMEDA', 'Av. Padre alberto hurtado #060, Estación Central', '08820315-1', 'Benjamin Leonardo Bruyer Gonzalez', '942547662', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Los Lagos', 'Osorno', 'EDIFICIO BüHLER', 'Avda. Guillermo Bühler #2005, Osorno', '17125113-3', 'Debora Eunice Filun Filun', '984365326', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Biobío', 'Los Ángeles', 'JUMBO LOS ANGELES', 'AV. ERCILLA #190, LOS ANGELES, REGION DEL BIO BIO', '17551177-6', 'Valeria Nicole Zagal Rodriguez', '990557528', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Valparaíso', 'Quillota', 'LIDER QUILLOTA', 'AV. 21 DE MAYO RECINTO ESTACION COMUNA QUILLOTA REGION DE VALPARAISO', '26707126-8', 'Fabiana Cristina Montaño Acuña', '948818234', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Las Condes', 'STA ISABEL CANTAGALLO', 'LAS CONDES 12207 Block #01 DEPTO. #OF. COMUNA LAS CONDES REGION METROPOLITANA', '28888888-8', 'Marcelo Inzunza (Supervisor)', '968454900', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Valparaíso', 'Valparaíso', 'STA ISABEL PEDRO MONTT', 'Av Pedro Montt 1845, Valparaiso', '10033741-K', 'Marcelo Alejandro Inzunza Gonzalez', '968454900', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Santiago', 'LIDER SAN PABLO', 'Neptuno N°720', '08820315-1', 'Benjamin Leonardo Bruyer Gonzalez', '942547662', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Libertador General Bernardo O''Higgins', 'San Vicente', 'LIDER SAN VICENTE', 'Calle Germán Riesco 510, Esquina Diego Portales,San Vicente de Tagua Tagua', '28888888-8', 'Marcelo Inzunza (Supervisor)', '968454900', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Santiago', 'LIDER 10 DE JULIO', 'Diez de julio 1625, Santiago', '08820315-1', 'Benjamin Leonardo Bruyer Gonzalez', '942547662', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Atacama', 'Vallenar', 'TOTTUS VALLENAR', 'Brasil 941, Vallenar', '28888888-8', 'Marcelo Inzunza (Supervisor)', '968454900', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
  UNION ALL SELECT 'Metropolitana de Santiago', 'Puente Alto', 'LIDER CORDILLERA', 'Avda Los Toros 05441', '16462551-6', 'Cintia Beatriz Gonzalez Orellana', '984911692', 'JIS Parking Spa', '76.063.822-6', '+569 68454900', 'Matucana 40, Est Central. Santiago'
) AS d
INNER JOIN regions r ON r.region = d.region
INNER JOIN communes c ON c.region_id = r.id AND c.commune = d.commune;
