import streamlit as st
import requests
import json
import time
from datetime import datetime
import sys
import os
from pathlib import Path

# Add parent directory to path for config
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from config import API_BASE_URL

# Page configuration
st.set_page_config(
    page_title="RCA Platform",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .confidence-high {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.375rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    .confidence-medium {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.375rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    .confidence-low {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.375rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    .evidence-item {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .remediation-item {
        background-color: #e7f3ff;
        border: 1px solid #b6d7ff;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def check_api_health():
    """Check if API is healthy"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_api_stats():
    """Get API statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def perform_rca_analysis(logs, metrics, traces):
    """Call RCA API"""
    try:
        payload = {
            "logs": logs,
            "metrics": metrics,
            "traces": traces
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/analyze",
            json=payload,
            timeout=90
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return None, "Request timed out. The analysis is taking longer than expected."
    except requests.exceptions.ConnectionError:
        return None, "Could not connect to API. Please ensure the backend is running."
    except Exception as e:
        return None, f"Error: {str(e)}"

def ingest_data(data_type, content):
    """Ingest data into knowledge base"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/upload/{data_type}",
            data=content,
            headers={"Content-Type": "text/plain"},
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "Data ingested successfully"
        else:
            return False, f"Failed to ingest data: {response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def render_confidence_badge(confidence_level, overall_confidence):
    """Render confidence badge"""
    color_class = f"confidence-{confidence_level}"
    return f"""
    <div class="{color_class}">
        <strong>Confidence: {confidence_level.upper()}</strong> ({overall_confidence:.1%})
    </div>
    """

def render_evidence_section(evidence):
    """Render evidence section"""
    if not evidence:
        st.warning("No evidence found")
        return
    
    for i, ev in enumerate(evidence):
        with st.expander(f"Evidence {i+1}: {ev['source']} ({ev['confidence']:.1%} confidence)"):
            st.markdown(f"""
            <div class="evidence-item">
                <strong>Source:</strong> {ev['source']} ({ev['data_type']})<br>
                <strong>Confidence:</strong> {ev['confidence']:.1%}<br>
                <strong>Description:</strong> {ev['description']}
            </div>
            """, unsafe_allow_html=True)

def render_related_incidents(incidents):
    """Render related incidents section"""
    if not incidents:
        st.info("No related incidents found")
        return
    
    for i, incident in enumerate(incidents):
        with st.expander(f"Incident {i+1}: {incident['incident_id']} (Similarity: {incident['similarity_score']:.1%})"):
            st.write(f"**Description:** {incident['description']}")
            if incident.get('resolution'):
                st.write(f"**Resolution:** {incident['resolution']}")
            if incident.get('timestamp'):
                st.write(f"**Timestamp:** {incident['timestamp']}")

def render_remediation_suggestions(suggestions):
    """Render remediation suggestions"""
    if not suggestions:
        st.warning("No remediation suggestions available")
        return
    
    for i, suggestion in enumerate(suggestions):
        priority_color = {
            'low': '#28a745',
            'medium': '#ffc107', 
            'high': '#fd7e14',
            'critical': '#dc3545'
        }.get(suggestion['priority'], '#6c757d')
        
        st.markdown(f"""
        <div class="remediation-item">
            <h4 style="color: {priority_color};">
                {suggestion['title']} 
                <span style="background-color: {priority_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;">
                    {suggestion['priority'].upper()}
                </span>
            </h4>
            <p><strong>Description:</strong> {suggestion['description']}</p>
            {f"<p><strong>Estimated Time:</strong> {suggestion['estimated_time']}</p>" if suggestion.get('estimated_time') else ""}
        </div>
        """, unsafe_allow_html=True)
        
        if suggestion.get('steps'):
            st.write("**Implementation Steps:**")
            for step_num, step in enumerate(suggestion['steps'], 1):
                st.write(f"{step_num}. {step}")

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🔍 RCA Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Generative AI-Driven Observability for Automated Root Cause Analysis</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 System Status")
        
        # API Health Check
        api_healthy = check_api_health()
        if api_healthy:
            st.success("✅ API is healthy")
        else:
            st.error("❌ API is not responding")
            st.warning("Please ensure the backend is running on port 8000")
        
        # API Statistics
        if api_healthy:
            stats = get_api_stats()
            if stats:
                st.subheader("Knowledge Base Stats")
                st.metric("Total Incidents", stats.get('total_incidents', 0))
                st.metric("Confidence Threshold", f"{stats.get('confidence_threshold', 0):.1%}")
        
        st.markdown("---")
        st.subheader("🔧 Actions")
        if st.button("Clear Knowledge Base"):
            try:
                response = requests.delete(f"{API_BASE_URL}/api/v1/knowledge-base")
                if response.status_code == 200:
                    st.success("Knowledge base cleared!")
                else:
                    st.error("Failed to clear knowledge base")
            except:
                st.error("Could not connect to API")
    
    # Main content area
    if not api_healthy:
        st.error("🚨 Backend API is not available. Please start the backend service.")
        st.code("cd backend && python main.py")
        return
    
    # Input section
    st.markdown('<h2 class="section-header">📝 Input Observability Data</h2>', unsafe_allow_html=True)
    
    # Create three columns for input
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📋 Logs")
        logs = st.text_area(
            "Enter log data:",
            height=200,
            placeholder="Paste your log entries here...\nExample:\n2024-01-01 10:00:00 ERROR Database connection failed\n2024-01-01 10:00:05 WARN Retrying connection..."
        )
        if st.button("💾 Save Logs to KB", key="save_logs"):
            if logs.strip():
                success, message = ingest_data("logs", logs)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    with col2:
        st.subheader("📊 Metrics")
        metrics = st.text_area(
            "Enter metrics data:",
            height=200,
            placeholder="Paste your metrics here...\nExample:\ncpu_usage_percent: 85.2\nmemory_usage_mb: 1024\nresponse_time_ms: 2500"
        )
        if st.button("💾 Save Metrics to KB", key="save_metrics"):
            if metrics.strip():
                success, message = ingest_data("metrics", metrics)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    with col3:
        st.subheader("🔗 Traces")
        traces = st.text_area(
            "Enter trace data:",
            height=200,
            placeholder="Paste your trace data here...\nExample:\nspan_id: abc123, operation: database_query, duration: 250ms, status: error"
        )
        if st.button("💾 Save Traces to KB", key="save_traces"):
            if traces.strip():
                success, message = ingest_data("traces", traces)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # RCA Analysis button
    st.markdown("---")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🔍 Run RCA Analysis", type="primary", use_container_width=True):
            if not any([logs.strip(), metrics.strip(), traces.strip()]):
                st.error("⚠️ Please provide at least one type of observability data")
            else:
                with st.spinner("🤖 Analyzing observability data..."):
                    start_time = time.time()
                    result, error = perform_rca_analysis(logs, metrics, traces)
                    analysis_time = time.time() - start_time
                
                if error:
                    st.error(f"❌ Analysis failed: {error}")
                else:
                    st.success(f"✅ Analysis completed in {analysis_time:.2f} seconds")
                    
                    # Store result in session state
                    st.session_state['rca_result'] = result
    
    # Display results
    if 'rca_result' in st.session_state and st.session_state['rca_result']:
        result = st.session_state['rca_result']
        
        st.markdown("---")
        st.markdown('<h2 class="section-header">📋 RCA Analysis Results</h2>', unsafe_allow_html=True)
        
        # Root Cause Summary
        st.subheader("🎯 Root Cause Summary")
        st.markdown(render_confidence_badge(result['confidence_level'], result['overall_confidence']), unsafe_allow_html=True)
        st.write(result['root_cause_summary'])
        
        # Create tabs for detailed results
        tab1, tab2, tab3 = st.tabs(["🔍 Evidence", "📚 Related Incidents", "🛠️ Remediation"])
        
        with tab1:
            st.subheader("Evidence & Analysis")
            render_evidence_section(result.get('evidence', []))
        
        with tab2:
            st.subheader("Similar Past Incidents")
            render_related_incidents(result.get('related_incidents', []))
        
        with tab3:
            st.subheader("Recommended Actions")
            render_remediation_suggestions(result.get('remediation_suggestions', []))
        
        # Metadata
        if result.get('processing_time_ms'):
            st.caption(f"⏱️ Processing time: {result['processing_time_ms']}ms | Analysis timestamp: {result.get('analysis_timestamp', 'N/A')}")

if __name__ == "__main__":
    main()
