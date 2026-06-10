-- Boletas v2: pool central (branch_office_id=0, used_id=0, dte_id=0, document_type_id=39)
-- Cambia @desde y @hasta según necesites.

SET @desde := 32130031;
SET @hasta := 32180030;

SET SESSION cte_max_recursion_depth := (@hasta - @desde + 2);

INSERT INTO folios (
  folio,
  dte_id,
  used_id,
  document_type_id,
  branch_office_id,
  added_date,
  updated_date
)
WITH RECURSIVE folio_rango AS (
  SELECT @desde AS folio
  UNION ALL
  SELECT folio + 1
  FROM folio_rango
  WHERE folio < @hasta
)
SELECT
  folio,
  0,
  0,
  39,
  0,
  NOW(),
  NOW()
FROM folio_rango;

-- Verificación
SELECT
  COUNT(*) AS total,
  MIN(folio) AS min_folio,
  MAX(folio) AS max_folio
FROM folios
WHERE document_type_id = 39
  AND dte_id = 0
  AND used_id = 0
  AND branch_office_id = 0
  AND folio BETWEEN @desde AND @hasta;
