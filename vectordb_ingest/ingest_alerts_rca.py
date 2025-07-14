from error_rca_system import ErrorRCASystem

# Initialize
system = ErrorRCASystem()

# Load your CSV data
system.store_errors_in_chromadb("java_production_errors_10k.csv")

# Search for similar errors
results = system.search_similar_errors("NullPointerException in authentication")

# Filter by criteria
filtered = system.search_by_filters(error_type="RuntimeException", severity="HIGH")
