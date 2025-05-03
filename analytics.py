import sqlite3
import pandas as pd
import json

# 1.1 Open a connection (swap for psycopg2/SQLAlchemy if not SQLite)
conn = sqlite3.connect('performance.db')

# 1.2 Read Mistakes + Good_Answers into DataFrames
mistakes = pd.read_sql('SELECT * FROM Mistakes;', conn, parse_dates=['date_recorded'])
goods    = pd.read_sql('SELECT * FROM Good_Answers;', conn, parse_dates=['date_recorded'])
topics   = pd.read_sql('SELECT topic_id, topic_name FROM Topics;', conn)

# Combine both
all_events = pd.concat([
    mistakes.assign(is_good=0),
    goods   .assign(is_good=1)
])

# Group by date
daily = all_events.groupby('date_recorded').agg(
    total=('is_good','size'),
    correct=('is_good','sum')
).reset_index()
daily['error_rate'] = 1 - daily['correct'] / daily['total']

# merge topic names
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

# 3. Export metrics to CSV
# ------------------------
daily.to_csv('daily_metrics.csv', index=False)
by_topic.to_csv('topic_metrics.csv', index=False)

# 4. Export summary to JSON for AI consumption
# ---------------------------------------------
json_payload = {
    "daily": daily[['date_recorded','error_rate']].to_dict(orient='records'),
    "by_topic": by_topic[['topic_name','error_rate']].to_dict(orient='records')
}
with open('latest_summary.json', 'w') as f:
    json.dump(json_payload, f, default=str)
