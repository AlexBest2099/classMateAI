import sqlite3
import pandas as pd
import json
import create_database

DB_FILE = 'test_database.db'   # match whatever your importer wrote
conn = sqlite3.connect(DB_FILE)
create_database.initialize_database_schema(DB_FILE)

# Pull raw data
mistakes = pd.read_sql('SELECT * FROM Mistakes;', conn, parse_dates=['date_recorded'])
goods    = pd.read_sql('SELECT * FROM Good_Answers;', conn, parse_dates=['date_recorded'])
topics   = pd.read_sql('SELECT topic_id, topic_name FROM Topics;', conn)

# Compute metrics (as you already have)
all_events = pd.concat([
    mistakes.assign(is_good=0),
    goods   .assign(is_good=1)
])
daily = all_events.groupby('date_recorded').agg(
    total=('is_good','size'),
    correct=('is_good','sum')
).reset_index()
daily['error_rate'] = 1 - daily['correct'] / daily['total']

m2 = mistakes.merge(topics, on='topic_id')
g2 = goods   .merge(topics, on='topic_id')
topic_events = pd.concat([
    m2.assign(is_good=0),
    g2.assign(is_good=1)
])
by_topic = topic_events.groupby('topic_name').agg(
    total=('is_good','size'),
    correct=('is_good','sum')
).reset_index()
by_topic['error_rate'] = 1 - by_topic['correct'] / by_topic['total']

# Export CSV/JSON
daily.to_csv('daily_metrics.csv', index=False)
by_topic.to_csv('topic_metrics.csv', index=False)

json_payload = {
    "daily": daily[['date_recorded','error_rate']].to_dict(orient='records'),
    "by_topic": by_topic[['topic_name','error_rate']].to_dict(orient='records')
}
with open('latest_summary.json', 'w') as f:
    json.dump(json_payload, f, default=str)