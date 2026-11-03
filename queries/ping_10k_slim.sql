-- Slim copy of ping_10k.sql's result: keep the body only for HTML responses with a ping attribute
-- on some tag (parsed locally to confirm). Run against the anonymous result table of ping_10k.sql.
SELECT * EXCEPT (body),
  IF(type = 'html' AND REGEXP_CONTAINS(body, r'''(?i)<[a-z][^<>]*\sping\s*='''), body, NULL) AS body
FROM `<anonymous result table of ping_10k.sql>`
