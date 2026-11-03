-- Denominators: pages in the 10k sample per date and client.
SELECT date, client, COUNT(*) AS pages, COUNTIF(is_root_page) AS root_pages
FROM httparchive.sample_data.pages_10k
GROUP BY date, client
ORDER BY date, client
