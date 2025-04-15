
# In your existing script
def get_new_runs(last_id=None, last_timestamp=None):
    client = Client()
    filters = []
    
    if last_id:
        filters.append(f'gt(id, "{last_id}")')
    if last_timestamp:
        filters.append(f'gt(start_time, "{last_timestamp.isoformat()}")')
    
    return client.list_runs(
        project_name="your_project",
        filter=" and ".join(filters) if filters else None
    )

# Usage
new_runs = get_new_runs(
    last_id="abc123",
    last_timestamp=datetime.now() - timedelta(minutes=30)
)
