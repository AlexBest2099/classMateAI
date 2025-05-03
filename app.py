import pandas as pd
import streamlit as st
import plotly.express as px

# Load generated metrics
daily = pd.read_csv('daily_metrics.csv', parse_dates=['date_recorded'])
by_topic = pd.read_csv('topic_metrics.csv')

st.title("📊 Performance Dashboard")

# 1. Error Rate Over Time
fig1 = px.line(
    daily,
    x='date_recorded',
    y='error_rate',
    title="Error Rate Over Time",
    labels={'date_recorded': 'Date', 'error_rate': 'Error Rate'}
)
st.plotly_chart(fig1, use_container_width=True)

# 2. Error Rate by Topic
fig2 = px.bar(
    by_topic,
    x='topic_name',
    y='error_rate',
    title="Error Rate by Topic",
    labels={'topic_name': 'Topic', 'error_rate': 'Error Rate'}
)
st.plotly_chart(fig2, use_container_width=True)

# 3. Good vs Bad by Topic
by_topic['bad'] = by_topic['total'] - by_topic['correct']
melted = by_topic.melt(
    id_vars=['topic_name'],
    value_vars=['correct','bad'],
    var_name='Outcome',
    value_name='Count'
)
# Rename for clarity
melted['Outcome'] = melted['Outcome'].map({'correct': 'Good Answers', 'bad': 'Mistakes'})
fig3 = px.bar(
    melted,
    x='topic_name',
    y='Count',
    color='Outcome',
    barmode='group',
    title="Correct vs Mistakes by Topic"
)
st.plotly_chart(fig3, use_container_width=True)