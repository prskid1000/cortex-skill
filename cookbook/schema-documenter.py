#!/usr/bin/env python3
"""
Cortex Example: schema-documenter
Description: Generate Markdown docs from MySQL schema
Tags: mysql,database,schema,documentation
Captured: 2026-03-25
Source: schema-documenter.py

Usage:
  python ~/.claude/skills/cortex/cookbook/schema-documenter.py
"""

#!/usr/bin/env python3
"""
Generate Markdown documentation of a MySQL database schema.
Queries INFORMATION_SCHEMA for tables, columns, keys, and relationships.
Output can be saved to Obsidian vault.

Usage:
    python schema-documenter.py --host localhost --db myapp --user root -o schema.md
    python schema-documenter.py --host localhost --db myapp --user root --password pass -o schema.md
"""

import argparse
import getpass
from datetime import date

# Uses mysql-connector or pymysql — try both
try:
    import mysql.connector as mysql_lib
    def connect(args):
        return mysql_lib.connect(host=args.host, port=args.port, user=args.user,
                                  password=args.password, database="information_schema")
except ImportError:
    import pymysql as mysql_lib
    def connect(args):
        return mysql_lib.connect(host=args.host, port=args.port, user=args.user,
                                  password=args.password, database="information_schema")


def query(conn, sql, params=None):
    cur = conn.cursor(dictionary=True) if hasattr(conn.cursor(), 'dictionary') else conn.cursor()
    cur.execute(sql, params or ())
    if not hasattr(cur, 'description') or cur.description is None:
        return []
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def document_schema(args):
    conn = connect(args)
    db = args.db
    lines = []
    lines.append(f"# Database Schema: `{db}`")
    lines.append(f"\n> Auto-generated on {date.today().isoformat()}\n")

    # Get all tables
    tables = query(conn, """
        SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT
        FROM TABLES WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME
    """, (db,))

    lines.append(f"## Overview ({len(tables)} tables)\n")
    lines.append("| Table | Rows | Comment |")
    lines.append("|-------|------|---------|")
    for t in tables:
        lines.append(f"| [{t['TABLE_NAME']}](#{t['TABLE_NAME']}) | {t['TABLE_ROWS'] or '?'} | {t['TABLE_COMMENT'] or ''} |")

    # Detail each table
    for t in tables:
        tname = t['TABLE_NAME']
        lines.append(f"\n---\n\n## {tname}\n")
        if t['TABLE_COMMENT']:
            lines.append(f"> {t['TABLE_COMMENT']}\n")

        # Columns
        cols = query(conn, """
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, EXTRA, COLUMN_COMMENT
            FROM COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION
        """, (db, tname))

        lines.append("| Column | Type | Nullable | Key | Default | Extra | Comment |")
        lines.append("|--------|------|----------|-----|---------|-------|---------|")
        for c in cols:
            key = c.get('COLUMN_KEY', '') or ''
            lines.append(f"| `{c['COLUMN_NAME']}` | `{c['COLUMN_TYPE']}` | {c['IS_NULLABLE']} | {key} | {c['COLUMN_DEFAULT'] or ''} | {c.get('EXTRA', '')} | {c.get('COLUMN_COMMENT', '') or ''} |")

        # Foreign keys
        fks = query(conn, """
            SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND REFERENCED_TABLE_NAME IS NOT NULL
        """, (db, tname))

        if fks:
            lines.append(f"\n**Foreign Keys:**")
            for fk in fks:
                lines.append(f"- `{fk['COLUMN_NAME']}` → `{fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}`")

        # Indexes
        idxs = query(conn, """
            SELECT INDEX_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as COLUMNS, NON_UNIQUE
            FROM STATISTICS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            GROUP BY INDEX_NAME, NON_UNIQUE
        """, (db, tname))

        if idxs:
            lines.append(f"\n**Indexes:**")
            for idx in idxs:
                unique = "" if idx.get('NON_UNIQUE', 1) else " (UNIQUE)"
                lines.append(f"- `{idx['INDEX_NAME']}`: {idx['COLUMNS']}{unique}")

    conn.close()

    output = "\n".join(lines)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Schema documented: {args.output} ({len(tables)} tables)")
    else:
        print(output)


def main():
    parser = argparse.ArgumentParser(description="Document MySQL schema as Markdown")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default=None, help="Password (prompts if omitted)")
    parser.add_argument("-o", "--output", help="Output .md file")
    args = parser.parse_args()

    if args.password is None:
        args.password = getpass.getpass("MySQL password: ")

    document_schema(args)


if __name__ == "__main__":
    main()
