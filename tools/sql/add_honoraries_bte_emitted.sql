-- Persist whether BTE was emitted in SII for each honorary.
-- bte_emitted: 1 = emitted, 0 = not emitted
-- bte_folio: SII folio when emitted

ALTER TABLE honoraries
  ADD COLUMN bte_emitted TINYINT NOT NULL DEFAULT 0 AFTER observation,
  ADD COLUMN bte_folio INT NULL DEFAULT NULL AFTER bte_emitted;
