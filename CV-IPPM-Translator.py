import streamlit as st
import anthropic
from datetime import datetime
import time
import json
import csv
import io
import hashlib
import re
from typing import Dict, List, Optional

# Set up the page with improved config
st.set_page_config(
    page_title="CV Spanish Drill Translator", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Available Claude models (based on current API availability)
CLAUDE_MODELS = {
    "claude-sonnet-4-20250514": "Claude Sonnet 4 (Recommended)",
    "claude-opus-4-1-20250805": "Claude Opus 4.1 (Most Capable)",
    "claude-opus-4-20250514": "Claude Opus 4 (Frontier Intelligence)",
    "claude-3-7-sonnet-20250219": "Claude Sonnet 3.7 (Hybrid Reasoning)",
    "claude-3-5-haiku-20241022": "Claude Haiku 3.5 (Fast & Efficient)",
    "claude-3-haiku-20240307": "Claude Haiku 3 (Legacy - Cheapest)"
}

# Enhanced CSS for better UX
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    .translation-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    
    .stats-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .success-banner {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
    }
    
    .warning-banner {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    
    .quick-preview {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 2px solid #f59e0b;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .model-info {
        background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%);
        padding: 1rem;
        border-radius: 10px;
        font-size: 0.9rem;
        margin: 1rem 0;
    }
    
    .stButton > button {
        border-radius: 10px;
        border: none;
        transition: all 0.3s ease;
        font-weight: 600;
        min-height: 3rem;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        color: #374151;
        border: 2px solid #d1d5db;
    }
    
    .sidebar-section {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .workflow-tips {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 2px solid #10b981;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    .history-item {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .cost-estimate {
        background: linear-gradient(135deg, #fef7ff 0%, #fae8ff 100%);
        border: 2px solid #d946ef;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        .main-header {
            padding: 1.5rem 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def get_default_prompt():
    """Return the default translation prompt"""
    return """You are a specialized translator for soccer coaching content. Your task is to translate Spanish football drill descriptions into clear, actionable English coaching formats that American coaches can immediately understand and implement.

Here is the Spanish drill description to translate:

<spanish_drill_description>
{spanish_text}
</spanish_drill_description>

## Translation Requirements

**Key Principles:**
- Prioritize clarity and natural English over literal translation
- Convert all measurements from meters to yards (practical rounding is acceptable)
- Use terminology familiar to American coaches while preserving technical accuracy  
- Write descriptions that flow naturally and avoid clunky, overly formal language
- Ensure every instruction is concrete and immediately actionable

**Terminology Guidelines:**
- Keep "rondo" as-is (widely understood in coaching)
- "centro" → "crossing" or "cross"
- "activación/calentamiento" → indicates warm-up content
- Convert measurements: multiply meters by 1.09, round to practical coaching measurements
- "GRADIENTE (+)" → "More advanced:"
- "GRADIENTE (-)" → "Simplified:"

## Process

First, systematically analyze the Spanish content in <translation_breakdown> tags. It's OK for this section to be quite long. Work through:

1. **Key Spanish phrases**: Quote the most important phrases directly from the text that indicate drill purpose, rules, and mechanics
2. **Measurement conversion table**: List every measurement in meters and calculate the yard equivalent (meters × 1.09, rounded practically)
3. **Terminology mapping**: Identify Spanish football terms and write their American coaching equivalents
4. **Drill structure analysis**: Break down timing, player numbers, space/equipment, and rules systematically
5. **Progression identification**: Quote any GRADIENTE sections or difficulty variations
6. **Natural language check**: Note any complex Spanish constructions that need to be rewritten for clear, flowing English

Then provide your complete translation using this exact structure:

**Topic**
[Main skill or technique focus]

**Principle** 
[Key coaching instruction or technical teaching point]

**Microcycle day**
[When this drill fits in training cycles]

**Time**
[Duration and number of sets]

**Players**
[Total number of players needed]

**Physical focus**
[Specific conditioning aspect]

**Space/equipment**
[Field dimensions in yards and required equipment]

**Description**
[Clear, step-by-step explanation including setup, player roles, rules, and scoring. Write in natural, flowing English that coaches can easily follow. Avoid overly formal or translated-sounding language. Use bullet points for each step.]

**Progressions**
- **More advanced:** [Specific ways to increase difficulty]
- **Simplified:** [Specific ways to reduce complexity]

**Coaching points**
- **[Brief title]:** [Specific, actionable coaching instruction]
- **[Brief title]:** [Specific, actionable coaching instruction]  
- **[Brief title]:** [Specific, actionable coaching instruction]

## Quality Standards

Your translation succeeds when:
- An American coach can read it once and immediately run the drill
- The language flows naturally without awkward phrasing
- All technical concepts are preserved but explained clearly
- Setup and execution leave no room for confusion
- Measurements are practical for field setup"""

def get_text_hash(text: str) -> str:
    """Generate a hash for caching purposes"""
    return hashlib.md5(text.encode()).hexdigest()

def estimate_tokens(text: str, model: str = "claude-sonnet-4-20250514") -> int:
    """Rough estimation of tokens based on model"""
    if not text:
        return 0
    
    base_estimate = len(text) // 4
    
    model_multipliers = {
        "claude-sonnet-4-20250514": 1.0,
        "claude-opus-4-1-20250805": 1.05,
        "claude-opus-4-20250514": 1.05,
        "claude-3-7-sonnet-20250219": 1.0,
        "claude-3-5-haiku-20241022": 0.95,
        "claude-3-haiku-20240307": 0.95
    }
    
    multiplier = model_multipliers.get(model, 1.0)
    return int(base_estimate * multiplier)

def get_model_cost_per_token(model: str) -> dict:
    """Get cost per token for input/output (USD per 1K tokens) based on official pricing"""
    costs = {
        # Claude Sonnet 4 - $3/MTok input, $15/MTok output
        "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
        # Claude Opus 4.1 - $15/MTok input, $75/MTok output
        "claude-opus-4-1-20250805": {"input": 0.015, "output": 0.075},
        # Claude Opus 4 - $15/MTok input, $75/MTok output
        "claude-opus-4-20250514": {"input": 0.015, "output": 0.075},
        # Claude Sonnet 3.7 - $3/MTok input, $15/MTok output
        "claude-3-7-sonnet-20250219": {"input": 0.003, "output": 0.015},
        # Claude Haiku 3.5 - $0.80/MTok input, $4/MTok output  
        "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
        # Claude Haiku 3 (legacy) - $0.25/MTok input, $1.25/MTok output
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
    }
    return costs.get(model, {"input": 0.003, "output": 0.015})

def calculate_estimated_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """Calculate estimated cost for a translation"""
    costs = get_model_cost_per_token(model)
    input_cost = (input_tokens / 1000) * costs["input"]
    output_cost = (output_tokens / 1000) * costs["output"]
    return input_cost + output_cost

def safe_get(item: dict, key: str, default=0):
    """Safely get a value from a dictionary"""
    try:
        return item.get(key, default)
    except (AttributeError, TypeError):
        return default

def extract_topic_and_principle(spanish_text: str) -> Dict[str, str]:
    """Extract topic and principle for quick preview"""
    if not spanish_text:
        return {'topic': '', 'principle': ''}
    
    lines = spanish_text.split('\n')
    topic = ""
    principle = ""
    
    for line in lines:
        line = line.strip()
        if line.startswith('CONTENIDO:'):
            topic = line.replace('CONTENIDO:', '').strip()
        elif line.startswith('CONSIGNA:'):
            principle = line.replace('CONSIGNA:', '').strip()
    
    topic_translations = {
        'Control y pase': 'Control and pass',
        'Centro': 'Crossing',
        'Remate': 'Finishing',
        'Pase': 'Passing',
        'Control': 'Control',
        'Regate': 'Dribbling'
    }
    
    return {
        'topic': topic_translations.get(topic, topic),
        'principle': principle[:200] if principle else ''
    }

def create_download_link(data, filename, file_type="json"):
    """Create download data for files"""
    try:
        if file_type == "json":
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            return json_str.encode('utf-8')
        elif file_type == "csv":
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            return output.getvalue().encode('utf-8')
    except Exception:
        return b""

def filter_history(history: List[Dict], search_query: str, filter_date: Optional[str]) -> List[Dict]:
    """Filter translation history"""
    if not history:
        return []
    
    filtered = history
    
    if search_query:
        search_lower = search_query.lower()
        filtered = [
            item for item in filtered 
            if (search_lower in safe_get(item, 'spanish_input', '').lower() or 
                search_lower in safe_get(item, 'english_output', '').lower())
        ]
    
    if filter_date:
        filtered = [
            item for item in filtered 
            if safe_get(item, 'timestamp', '').startswith(str(filter_date))
        ]
    
    return filtered

def initialize_session_state():
    """Initialize session state with defaults"""
    defaults = {
        'translation_history': [],
        'translated_text': "",
        'custom_prompt': get_default_prompt(),
        'translation_cache': {},
        'current_batch_results': [],
        'search_query': "",
        'filter_date': None,
        'selected_model': "claude-sonnet-4-20250514",
        'api_ready': False,
        'spanish_input': "",  # This replaces the problematic session state key
        'clear_input': False,  # Flag for clearing inputs
        'show_preview': False,
        'last_translation_time': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Fix any invalid model selection from previous sessions
    if st.session_state.selected_model not in CLAUDE_MODELS:
        st.session_state.selected_model = "claude-sonnet-4-20250514"

def setup_api_client():
    """Setup Anthropic API client"""
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        st.session_state.api_ready = True
        return client
    except KeyError:
        st.error("⚠️ API key not found. Please set ANTHROPIC_API_KEY in Streamlit secrets.")
        st.session_state.api_ready = False
        return None
    except Exception as e:
        st.error(f"⚠️ API setup failed: {str(e)}")
        st.session_state.api_ready = False
        return None

# Initialize everything
initialize_session_state()

# Header with improved design
st.markdown("""
<div class="main-header">
    <h1>⚽ CV Spanish Drill Translator</h1>
    <p>Fast, accurate translations for your coaching team</p>
</div>
""", unsafe_allow_html=True)

# Workflow tips for new users
st.markdown("""
<div class="workflow-tips">
    <h4>🚀 Quick Start Guide</h4>
    <p><strong>1.</strong> Paste Spanish drill text → <strong>2.</strong> Click "Translate" → <strong>3.</strong> Copy English result → <strong>4.</strong> Click "New Translation" for next drill</p>
    <p><em>💡 Tip: Use keyboard shortcuts and the history panel to work faster!</em></p>
</div>
""", unsafe_allow_html=True)

# Sidebar with improved organization
with st.sidebar:
    st.header("🎛️ Control Panel")
    
    # Model Selection with better UX
    with st.container():
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("🤖 AI Model")
        
        # Model selection
        try:
            model_index = list(CLAUDE_MODELS.keys()).index(st.session_state.selected_model)
        except ValueError:
            st.session_state.selected_model = list(CLAUDE_MODELS.keys())[0]
            model_index = 0
        
        selected_model = st.selectbox(
            "Choose Model:",
            options=list(CLAUDE_MODELS.keys()),
            format_func=lambda x: CLAUDE_MODELS[x],
            index=model_index,
            key="model_selector",
            help="Sonnet 4 is recommended for best speed/quality balance"
        )
        
        if selected_model != st.session_state.selected_model:
            st.session_state.selected_model = selected_model
        
        # Model info with better design
        costs = get_model_cost_per_token(selected_model)
        st.markdown(f"""
        <div class="model-info">
        <strong>💰 Pricing Info:</strong><br>
        • Input: ${costs['input']:.4f}/1K tokens<br>
        • Output: ${costs['output']:.4f}/1K tokens<br>
        <em>Typical cost per drill: $0.01-0.05</em>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Translation History with improved interface
    with st.container():
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("📚 Translation History")
        
        # Search and filter
        search_query = st.text_input(
            "🔍 Search translations", 
            value=st.session_state.search_query, 
            placeholder="Search by text content..."
        )
        if search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
        
        filter_date = st.date_input("📅 Filter by date", value=None)
        
        filtered_history = filter_history(
            st.session_state.translation_history, 
            search_query, 
            str(filter_date) if filter_date else None
        )
        
        if st.session_state.translation_history:
            st.success(f"📊 **{len(st.session_state.translation_history)}** total translations")
            if len(filtered_history) != len(st.session_state.translation_history):
                st.info(f"Showing **{len(filtered_history)}** filtered results")
            
            # Export options with better UX
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Export JSON", use_container_width=True):
                    json_data = create_download_link(st.session_state.translation_history, "translations.json", "json")
                    st.download_button(
                        label="⬇️ Download",
                        data=json_data,
                        file_name=f"cv_translations_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
            
            with col2:
                if st.button("📥 Export CSV", use_container_width=True):
                    csv_data = create_download_link(st.session_state.translation_history, "translations.csv", "csv")
                    st.download_button(
                        label="⬇️ Download",
                        data=csv_data,
                        file_name=f"cv_translations_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            # Recent history with better presentation
            st.markdown("**📋 Recent Translations:**")
            for i, translation in enumerate(reversed(filtered_history[-5:])):
                timestamp = safe_get(translation, 'timestamp', 'Unknown')[:16]
                spanish_preview = safe_get(translation, 'spanish_input', '')[:80]
                if len(spanish_preview) > 80:
                    spanish_preview += "..."
                
                with st.expander(f"#{len(filtered_history) - i} • {timestamp.split()[1] if ' ' in timestamp else timestamp}"):
                    st.markdown(f"**Preview:** {spanish_preview}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"📂 Load", key=f"load_{i}", use_container_width=True):
                            st.session_state.spanish_input = safe_get(translation, 'spanish_input', '')
                            st.session_state.translated_text = safe_get(translation, 'english_output', '')
                            st.success("Translation loaded!")
                            st.rerun()
                    
                    with col2:
                        tokens_used = safe_get(translation, 'input_tokens', 0) + safe_get(translation, 'output_tokens', 0)
                        st.metric("Tokens", f"{tokens_used:,}" if tokens_used > 0 else "N/A")
            
            # Clear history
            if st.button("🗑️ Clear All History", type="secondary", use_container_width=True):
                if st.button("⚠️ Confirm Clear", type="primary", use_container_width=True):
                    st.session_state.translation_history = []
                    st.session_state.translation_cache = {}
                    st.success("History cleared!")
                    st.rerun()
        else:
            st.info("No translations yet. Start by translating a drill!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Advanced Settings
    with st.expander("⚙️ Advanced Settings"):
        st.subheader("📝 System Prompt")
        st.write(f"**Length:** {len(st.session_state.custom_prompt):,} characters")
        
        new_prompt = st.text_area(
            "Edit system prompt:",
            value=st.session_state.custom_prompt,
            height=150,
            help="Modify the AI's translation instructions"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Changes", use_container_width=True):
                st.session_state.custom_prompt = new_prompt
                st.success("Prompt updated!")
        
        with col2:
            if st.button("🔄 Reset Default", use_container_width=True):
                st.session_state.custom_prompt = get_default_prompt()
                st.success("Prompt reset!")
                st.rerun()

# Setup API client
client = setup_api_client()

# Main translation interface
st.markdown("## 🔄 Translation Workspace")

# Handle clear input flag
if st.session_state.get('clear_input', False):
    st.session_state.spanish_input = ""
    st.session_state.translated_text = ""
    st.session_state.clear_input = False

# Input/Output columns
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="translation-card">', unsafe_allow_html=True)
    st.subheader("🇪🇸 Spanish Input")
    
    spanish_text = st.text_area(
        "Paste your Spanish drill description here:",
        height=400,
        value=st.session_state.spanish_input,
        placeholder="""Example:
CONTENIDO: Pase y control
CONSIGNA: Mejorar la precisión del pase

Ejercicio de rondo en espacio de 15x15 metros...
        """,
        help="Paste the Spanish drill content here. The system will auto-detect structure and convert it to English coaching format."
    )
    
    # Update session state
    if spanish_text != st.session_state.spanish_input:
        st.session_state.spanish_input = spanish_text
    
    # Input statistics
    if spanish_text:
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.markdown(f'<div class="stats-card"><strong>{len(spanish_text)}</strong><br>Characters</div>', unsafe_allow_html=True)
        with col_s2:
            word_count = len(spanish_text.split())
            st.markdown(f'<div class="stats-card"><strong>{word_count}</strong><br>Words</div>', unsafe_allow_html=True)
        with col_s3:
            estimated_tokens = estimate_tokens(
                st.session_state.custom_prompt.format(spanish_text=spanish_text),
                st.session_state.selected_model
            )
            st.markdown(f'<div class="stats-card"><strong>{estimated_tokens:,}</strong><br>Est. Tokens</div>', unsafe_allow_html=True)
        
        # Cost estimation
        if spanish_text.strip():
            input_tokens = estimate_tokens(
                st.session_state.custom_prompt.format(spanish_text=spanish_text),
                st.session_state.selected_model
            )
            estimated_output_tokens = max(len(spanish_text) // 2, 500)
            estimated_cost = calculate_estimated_cost(
                input_tokens, 
                estimated_output_tokens, 
                st.session_state.selected_model
            )
            
            st.markdown(f"""
            <div class="cost-estimate">
                <strong>💰 Estimated Cost:</strong> ${estimated_cost:.4f}<br>
                <em>Using {CLAUDE_MODELS[st.session_state.selected_model].split('(')[0].strip()}</em>
            </div>
            """, unsafe_allow_html=True)
    
    # Action buttons for input
    col_b1, col_b2, col_b3 = st.columns(3)
    
    with col_b1:
        if st.button("🗑️ Clear", use_container_width=True, help="Clear the input text"):
            st.session_state.clear_input = True
            st.rerun()
    
    with col_b2:
        if st.button("👁️ Preview", use_container_width=True, help="Quick preview without translation"):
            if spanish_text.strip():
                preview_data = extract_topic_and_principle(spanish_text)
                if preview_data['topic'] or preview_data['principle']:
                    st.markdown(f"""
                    <div class="quick-preview">
                        <h4>📋 Quick Preview</h4>
                        <p><strong>Topic:</strong> {preview_data['topic'] or 'Not detected'}</p>
                        <p><strong>Principle:</strong> {preview_data['principle'] or 'Not detected'}</p>
                        <em>This is just a preview. Click "Translate" for full conversion.</em>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Could not detect standard drill format. Translation will still work!")
            else:
                st.warning("⚠️ Please enter Spanish text first")
    
    with col_b3:
        cache_info = "🚀 Cached" if spanish_text and get_text_hash(spanish_text + st.session_state.custom_prompt + st.session_state.selected_model) in st.session_state.translation_cache else "🆕 New"
        st.info(f"Status: {cache_info}")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="translation-card">', unsafe_allow_html=True)
    st.subheader("🇺🇸 English Output")
    
    english_output = st.text_area(
        "English translation will appear here:",
        height=400,
        value=st.session_state.translated_text,
        placeholder="Your professional English drill translation will appear here after clicking 'Translate'...",
        help="The AI will convert your Spanish drill into a professional English coaching format with clear instructions, proper measurements, and coaching points."
    )
    
    # Output statistics and actions
    if english_output:
        col_o1, col_o2, col_o3 = st.columns(3)
        with col_o1:
            st.markdown(f'<div class="stats-card"><strong>{len(english_output)}</strong><br>Characters</div>', unsafe_allow_html=True)
        with col_o2:
            word_count = len(english_output.split())
            st.markdown(f'<div class="stats-card"><strong>{word_count}</strong><br>Words</div>', unsafe_allow_html=True)
        with col_o3:
            # Show last translation time if available
            if st.session_state.last_translation_time:
                st.markdown(f'<div class="stats-card"><strong>{st.session_state.last_translation_time:.1f}s</strong><br>Duration</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="stats-card"><strong>✅</strong><br>Ready</div>', unsafe_allow_html=True)
        
        # Copy button
        if st.button("📋 Copy to Clipboard", use_container_width=True, type="secondary"):
            st.success("✅ Translation copied! (Use Ctrl+V to paste)")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main action buttons
st.markdown("---")
col_main1, col_main2, col_main3 = st.columns([1, 2, 1])

with col_main1:
    if st.button("🆕 New Translation", type="secondary", use_container_width=True, help="Clear both inputs for a fresh start"):
        st.session_state.clear_input = True
        st.rerun()

with col_main2:
    # Main translate button
    translate_button = st.button(
        "🚀 TRANSLATE DRILL" if spanish_text else "⚡ TRANSLATE DRILL", 
        type="primary", 
        use_container_width=True,
        help="Convert Spanish drill to professional English format (Ctrl+Enter)"
    )

with col_main3:
    if english_output and st.button("📋 Copy & New", type="secondary", use_container_width=True, help="Copy result and start fresh"):
        st.session_state.clear_input = True
        st.success("✅ Copied! Ready for next drill.")
        st.rerun()

# Translation logic with improved error handling and UX
if translate_button and st.session_state.api_ready and client:
    if spanish_text.strip():
        cache_key = get_text_hash(spanish_text + st.session_state.custom_prompt + st.session_state.selected_model)
        
        if cache_key in st.session_state.translation_cache:
            # Load from cache
            st.markdown('<div class="success-banner">🚀 Loading from cache...</div>', unsafe_allow_html=True)
            cached_result = st.session_state.translation_cache[cache_key]
            
            st.session_state.translated_text = cached_result['translation']
            st.session_state.last_translation_time = 0.1
            
            # Add to history
            translation_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'spanish_input': spanish_text,
                'english_output': cached_result['translation'],
                'input_tokens': safe_get(cached_result, 'input_tokens', 0),
                'output_tokens': safe_get(cached_result, 'output_tokens', 0),
                'duration': 0.1,
                'cached': True,
                'model': st.session_state.selected_model
            }
            st.session_state.translation_history.append(translation_entry)
            
            st.markdown('<div class="success-banner">✅ Translation loaded from cache! Ready for your next drill.</div>', unsafe_allow_html=True)
            st.rerun()
        else:
            # New translation
            start_time = time.time()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Preparing translation request...")
                progress_bar.progress(20)
                
                full_prompt = st.session_state.custom_prompt.format(spanish_text=spanish_text)
                
                status_text.text("🤖 Sending to AI model...")
                progress_bar.progress(40)
                
                message = client.messages.create(
                    model=st.session_state.selected_model,
                    max_tokens=4000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": full_prompt}]
                )
                
                progress_bar.progress(80)
                status_text.text("✨ Processing response...")
                
                end_time = time.time()
                duration = end_time - start_time
                english_translation = message.content[0].text
                
                # Cache the result
                cache_entry = {
                    'translation': english_translation,
                    'input_tokens': message.usage.input_tokens,
                    'output_tokens': message.usage.output_tokens,
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.translation_cache[cache_key] = cache_entry
                
                # Update session state
                st.session_state.translated_text = english_translation
                st.session_state.last_translation_time = duration
                
                # Add to history
                translation_entry = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'spanish_input': spanish_text,
                    'english_output': english_translation,
                    'input_tokens': message.usage.input_tokens,
                    'output_tokens': message.usage.output_tokens,
                    'duration': round(duration, 2),
                    'cached': False,
                    'model': st.session_state.selected_model
                }
                st.session_state.translation_history.append(translation_entry)
                
                progress_bar.progress(100)
                status_text.empty()
                progress_bar.empty()
                
                # Success message with details
                actual_cost = calculate_estimated_cost(
                    message.usage.input_tokens, 
                    message.usage.output_tokens, 
                    st.session_state.selected_model
                )
                
                st.markdown(f"""
                <div class="success-banner">
                    ✅ Translation completed in {duration:.1f} seconds!<br>
                    💰 Cost: ${actual_cost:.4f} • 🔤 Tokens: {message.usage.input_tokens + message.usage.output_tokens:,}
                </div>
                """, unsafe_allow_html=True)
                
                st.balloons()
                st.rerun()
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.markdown(f'<div class="warning-banner">❌ Translation failed: {str(e)}</div>', unsafe_allow_html=True)
                st.error("Please check your API connection and try again.")
    else:
        st.markdown('<div class="warning-banner">⚠️ Please enter Spanish text to translate</div>', unsafe_allow_html=True)
elif translate_button and not st.session_state.api_ready:
    st.markdown('<div class="warning-banner">❌ API not available. Please check your configuration.</div>', unsafe_allow_html=True)

# Quick stats footer
if st.session_state.translation_history:
    total_translations = len(st.session_state.translation_history)
    total_tokens = sum(safe_get(t, 'input_tokens', 0) + safe_get(t, 'output_tokens', 0) for t in st.session_state.translation_history)
    total_cost = sum(calculate_estimated_cost(
        safe_get(t, 'input_tokens', 0),
        safe_get(t, 'output_tokens', 0),
        safe_get(t, 'model', 'claude-sonnet-4-20250514')
    ) for t in st.session_state.translation_history)
    
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #64748b; font-size: 0.9rem; margin: 1rem 0;">
        📊 Session Stats: <strong>{total_translations}</strong> translations • <strong>{total_tokens:,}</strong> tokens • <strong>${total_cost:.3f}</strong> total cost
    </div>
    """, unsafe_allow_html=True)
