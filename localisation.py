#!/usr/bin/env python3
"""
locate_mistakes.py

Connects to your SQLite DB, fetches every mistake with its file, page & location,
and either prints a plain text report or exports JSON for downstream use.
"""

import sqlite3
import json
import argparse

def get_mistake_locations(db_file):
    """
    Connect to `db_file`, query the Mistakes join Sources table,
    and return a list of dicts with keys:
      - filename
      - date
      - subject
      - topic
      - page_number
      - problem_formulation
      - location_detail
      - mistake_description
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            S.filename,
            M.date_recorded,
            U.subject_name,
            T.topic_name,
            M.page_number,
            M.problem_formulation,
            M.location_detail,
            M.mistake_description
        FROM Mistakes M
        JOIN Sources  S ON M.source_id = S.source_id
        JOIN Topics   T ON M.topic_id   = T.topic_id
        JOIN Subjects U ON T.subject_id = U.subject_id
        ORDER BY M.date_recorded, S.filename;
    """)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            'filename': row[0],
            'date': row[1],
            'subject': row[2],
            'topic': row[3],
            'page_number': row[4],
            'problem_formulation': row[5],
            'location_detail': row[6],
            'mistake_description': row[7]
        }
        for row in rows
    ]


def main():
    p = argparse.ArgumentParser(
        description="Locate mistakes in your SQLite DB and print or export JSON."
    )
    p.add_argument(
        "--db", "-d",
        required=True,
        help="Path to your SQLite database file (e.g. database.db)"
    )
    p.add_argument(
        "--json", "-j",
        action="store_true",
        help="If set, outputs the results as JSON to stdout; otherwise prints plain text."
    )
    mode_group = p.add_mutually_exclusive_group(required=False)
    mode_group.add_argument(
        '--date',
        help="Filter mistakes by date (YYYY-MM-DD) and filename"
    )
    mode_group.add_argument(
        '--topic', '-t',
        help="Filter mistakes by topic name"
    )
    p.add_argument(
        '--filename', '-f',
        help="Filename to filter (required with --date)"
    )

    args = p.parse_args()
    mistakes = get_mistake_locations(args.db)

    if args.json:
        print(json.dumps(mistakes, indent=2, default=str))
        return

    # Plain-text output modes
    if args.date:
        # date filter requires filename
        if not args.filename:
            p.error("--filename is required when using --date")
        filtered = [m for m in mistakes if str(m['date']) == args.date and m['filename'] == args.filename]
        print("---")
        for m in filtered:
            print(f"Topic: {m['topic']}")
            print(f"Page: {m['page_number']}")
            print(f"Question: {m['problem_formulation']}")
            print(f"Mistake: {m['mistake_description']}")
            print("---")
    elif args.topic:
        filtered = [m for m in mistakes if m['topic'] == args.topic]
        for m in filtered:
            print(f"Filename: {m['filename']}")
            print(f"Date: {m['date']}")
            print(f"Page: {m['page_number']}")
            print(f"Question: {m['problem_formulation']}")
            print(f"Mistake: {m['mistake_description']}")
            print("---")
    else:
        # no filters: list all mistakes
        filtered = mistakes
        for m in filtered:
            print(f"File: {m['filename']}")
            print(f"Date: {m['date']}")
            print(f"Subject: {m['subject']}")
            print(f"Topic: {m['topic']}")
            print(f"Page: {m['page_number']}")
            print(f"Question: {m['problem_formulation']}")
            print(f"Mistake: {m['mistake_description']}")
            print("---")

    # After printing results, output questions to a text file
    try:
        with open('questions.txt', 'w') as f:
            for q in filtered:
                f.write(q['problem_formulation'] + '\n')
        # print("Questions written to questions.txt")
    except Exception as e:
        print(f"try again: {e}")


if __name__ == "__main__":
    main()