from generate_rca import AlertRCASystem
alert_system = AlertRCASystem(
csv_file_path="csv_file",
collection_name="java_alerts_chunked",
max_tokens_per_chunk=512,
chunk_overlap=50
)

results = alert_system.find_rca_and_fix(
log="java.net.SocketTimeoutException: Read timed out [instance=70]",
metric="network_latency: 5500ms, retry_count: 0, cpu_load: 72%, mem_free: 1000MB",
top_k=3
)

for i, result in enumerate(results, 1):
     print(f"   Result {i} (similarity: {result['similarity_score']}):")
     print(f"   RCA: {result['rca']}")
     print(f"   Fix: {result['fix']}")
     print()
