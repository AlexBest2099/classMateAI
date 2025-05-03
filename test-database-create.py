#!/usr/bin/env python3
# save as create_test_db.py

import sqlite3
import os
import datetime
import sys

# Ensure we import your initializer
sys.path.insert(0, os.path.dirname(__file__))
from create_database import initialize_database_schema

DB_FILE = 'test_database.db'

# Remove old test DB
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

# 1. Init schema
initialize_database_schema(DB_FILE)

# 2. Connect for inserts
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# 3. Create a subject and topics
cursor.execute("INSERT INTO Subjects (subject_name, subject_description) VALUES (?, ?)",
               ("TestSubject", "A subject for testing"))
subject_id = cursor.lastrowid

topic_ids = []
for name in ("TopicA", "TopicB"):
    cursor.execute("INSERT INTO Topics (subject_id, topic_name, topic_description) VALUES (?, ?, ?)",
                   (subject_id, name, f"Description for {name}"))
    topic_ids.append(cursor.lastrowid)

# 4. Create sources
for filename in ("test1.pdf", "test2.pdf"):
    cursor.execute("INSERT INTO Sources (filename, filepath) VALUES (?, ?)",
                   (filename, "/test/"))

cursor.execute("SELECT source_id FROM Sources")
source_ids = [row[0] for row in cursor.fetchall()]

# 5. Insert 10 mistakes
today = datetime.date.today()
for i in range(10):
    src = source_ids[i % len(source_ids)]
    t_id = topic_ids[i % len(topic_ids)]
    cursor.execute("""
        INSERT INTO Mistakes
        (source_id, topic_id, subtopic_id, mistake_description, problem_formulation,
         mistake_type, page_number, location_detail, mistake_details, date_recorded)
        VALUES (?, ?, NULL, ?, ?, ?, ?, ?, '', ?)
    """, (
        src,
        t_id,
        f"Sample mistake #{i+1}",
        f"Problem formulation for mistake #{i+1}",
        ["Calculation","Conceptual","Syntax"][i % 3],
        (i % 5) + 1,
        f"Q{(i % 7) + 1}",
        today - datetime.timedelta(days=i % 3)
    ))

conn.commit()
conn.close()

print(f"Created test database with 10 mistakes: {DB_FILE}")