-- Responses in the 10k sample whose body mentions `ping` as an attribute or property.
-- Superset prefilter; classified locally from the snippets and bodies.
SELECT
  date, client, page, is_root_page, rank, url, type, is_main_document,
  FARM_FINGERPRINT(response_body) AS body_fp,
  LENGTH(response_body) AS body_len,
  ARRAY(SELECT SUBSTR(m, 1, 600) FROM UNNEST(REGEXP_EXTRACT_ALL(response_body,
    r'''(?is)(.{0,200}(?:\bping\s*=\s*(?:\\?["'][^"']{0,300}|[^\s>"']{1,300})|setAttribute(?:NS)?\([^()]{0,40}["']ping["']|\.(?:attr|prop)\(\s*["']ping["']|["']ping["']\s+in\s|\.ping\s*=[^=]|prototype\.ping).{0,200})''')) AS m LIMIT 20) AS snippets,
  IF(type IN ('html', 'script') AND LENGTH(response_body) < 3000000, response_body, NULL) AS body
FROM httparchive.sample_data.requests_10k
WHERE response_body IS NOT NULL
  AND REGEXP_CONTAINS(response_body,
    r'''(?i)\bping\s*=|setAttribute(?:NS)?\([^()]{0,40}["']ping["']|\.(?:attr|prop)\(\s*["']ping["']|["']ping["']\s+in\s|\.ping\s*=[^=]|prototype\.ping''')
