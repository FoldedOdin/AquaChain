#!/usr/bin/env python3
import boto3
from datetime import datetime, timedelta, timezone

logs = boto3.client('logs', region_name='ap-south-1')
group = '/aws/lambda/aquachain-function-service-request-dev'

streams = logs.describe_log_streams(
    logGroupName=group,
    orderBy='LastEventTime',
    descending=True,
    limit=5
)['logStreams']

print("Recent log streams:")
for s in streams:
    last = s.get('lastEventTimestamp', 0)
    dt = datetime.fromtimestamp(last / 1000, tz=timezone.utc)
    name = s['logStreamName']
    print(f"  {dt.isoformat()} - {name}")

# Read the most recent stream
if streams:
    stream_name = streams[0]['logStreamName']
    print(f"\n--- Latest stream: {stream_name} ---")
    start_ms = int((datetime.now(tz=timezone.utc) - timedelta(hours=1)).timestamp() * 1000)
    events = logs.get_log_events(
        logGroupName=group,
        logStreamName=stream_name,
        startTime=start_ms,
        limit=200
    )['events']
    for e in events:
        print(e['message'].rstrip())
