# Download a BigQuery table to JSONL with parallel `bq head` calls (tabledata.list, not billed).
# Usage: python3 -I bq_download.py PROJECT:DATASET.TABLE OUT.jsonl [CHUNK]
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor


def rows(table):
    out = subprocess.run(['bq', 'show', '--format=json', table], capture_output=True, text=True, check=True)
    return int(json.loads(out.stdout)['numRows'])


def chunk(table, start, n):
    for _ in range(3):
        p = subprocess.run(['bq', 'head', '--format=json', f'--start_row={start}', f'--max_rows={n}', table],
                           capture_output=True, text=True)
        if p.returncode == 0:
            return json.loads(p.stdout)
    raise RuntimeError(p.stderr[-500:])


def main():
    table, out = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
    total = rows(table)
    with ThreadPoolExecutor(6) as ex, open(out, 'w') as f:
        for part in ex.map(lambda s: chunk(table, s, size), range(0, total, size)):
            for r in part:
                f.write(json.dumps(r) + '\n')
    print(total, 'rows')


if __name__ == '__main__':
    main()
