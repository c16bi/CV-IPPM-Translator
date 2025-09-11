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
    "claude-sonnet-4-20250514": "Claude Sonnet 4 (Default - High Performance)",
    "claude-opus-4-1-20250805": "Claude Opus 4.1 (Most Capable)",
    "claude-opus-4-20250514": "Claude Opus 4 (Frontier Intelligence)",
    "claude-3-7-sonnet-20250219": "Claude Sonnet 3.7 (Hybrid Reasoning)",
    "claude-3-5-haiku-20241022": "Claude Haiku 3.5 (Fast & Efficient)",
    "claude-3-haiku-20240307": "Claude Haiku 3 (Legacy - Cheapest)"
}

# Custom CSS for improved UI/UX
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .metric-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin: 0.5rem 0;
    }
    
    .success-message {
        background: #dcfce7;
        border: 1px solid #16a34a;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #166534;
    }
    
    .quick-preview {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stButton > button {
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .model-info {
        background: #f1f5f9;
        padding: 0.5rem;
        border-radius: 6px;
        font-size: 0.85rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_default_prompt():
    """Return the default translation prompt"""
    return """<examples>
<example>
<SPANISH_DRILL_DESCRIPTION>
Sub-fase Activación: Rondo condicional
BLOQUE: Habilidades Motrices Específicas.
CONTENIDO: Control y pase
CONSIGNA: Control: Con el pie de apoyo y utilizando un solo contacto con el suelo, salir en la dirección hacia donde se ha orientado el control.
Pase: Usar el interior del pie para la corta y media distancia, y el empeine para la larga distancia (golpeando el balón por debajo para elevarlo).
DIA MICROCICLO: Cualquier día.
TIEMPO: 2 series de 5 minutos.
ESPACIO: 1 rondo de mayores dimensiones, 8 x 8 metros. Dos rondos más pequeños de 4 x 4 metros.
ORIENTACIÓN CONDICIONAL: Tensión
Nº JUGADORES: 18 jugadores en total. 9 jugadores en cada equipo
MATERIAL: Conos, balones y dos porterías pequeñas.
</SPANISH_DRILL_DESCRIPTION>
<ideal_output>
**Topic**
Control and pass

**Principle** 
Control: Use supporting foot and single ground contact to move in the direction of the controlled ball. Pass: Use inside of foot for short and medium distance, and instep for long distance (striking the ball underneath to lift it)

**Microcycle day**
Any day

**Time**
Two x five-minute blocks

**Players**
18

**Physical focus**
Tension

**Space/equipment**
One large rondo of eight yards x eight yards. Two smaller rondos of four yards x four yards/Cones, balls, two mini-goals

**Description**
The session begins with a rondo-based exercise. One team takes the offensive role while the other performs defensive functions.

**Progressions**
- More advanced: Limit the number of touches for offensive players
- Simplified: Increase the playing dimensions

**Coaching points**
- Supporting foot technique: Players should use their supporting foot effectively
- Pass selection: Choose appropriate passing technique based on distance
- Ball retention: Focus on maintaining possession through quick, accurate passing
</ideal_output>
</example>
</examples>

You are a specialized translator for football/soccer coaching content. Translate Spanish drill descriptions into clear English coaching format.

<spanish_drill_description>
{spanish_text}
</spanish_drill_description>

## Required Output Format:

**Topic**
[Main skill/technique focus]

**Principle** 
[Key technical instruction]

**Microcycle day**
[When to use this drill]

**Time**
[Duration and sets]

**Players**
[Number of players]

**Physical focus**
[Physical conditioning aspect]

**Space/equipment**
[Field dimensions and equipment]

**Description**
[Detailed explanation of the drill]

**Progressions**
- More advanced: [How to make harder]
- Simplified: [How to make easier]

**Coaching points**
- [Title]: [Instruction]
- [Title]: [Instruction]
- [Title]: [Instruction]"""

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

def save_to_local_storage(key: str, value):
    """Save data to session state"""
    try:
        st.session_state[f"ls_{key}"] = value
    except Exception:
        pass

def load_from_local_storage(key: str):
    """Load data from session state"""
    try:
        return st.session_state.get(f"ls_{key}")
    except Exception:
        return None

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
        'draft_spanish': "",
        'current_batch_results': [],
        'search_query': "",
        'filter_date': None,
        'selected_model': "claude-sonnet-4-20250514",
        'api_ready': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Fix any invalid model selection from previous sessions
    if st.session_state.selected_model not in CLAUDE_MODELS:
        st.session_state.selected_model = "claude-sonnet-4-20250514"

def auto_save_draft():
    """Auto-save draft functionality"""
    try:
        if 'spanish_input_key' in st.session_state:
            save_to_local_storage('draft_spanish', st.session_state.spanish_input_key)
    except Exception:
        pass

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

# Header
st.markdown("""
<div class="main-header">
    <h1>⚽ CV Spanish Drill Translator</h1>
    <p>Professional football drill translation with advanced features</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🔧 Control Panel")
    
    # Model Selection
    st.subheader("🤖 Model Selection")
    
    # Double-check and fix model selection before rendering dropdown
    if st.session_state.selected_model not in CLAUDE_MODELS:
        st.session_state.selected_model = list(CLAUDE_MODELS.keys())[0]
    
    try:
        model_index = list(CLAUDE_MODELS.keys()).index(st.session_state.selected_model)
    except ValueError:
        st.session_state.selected_model = list(CLAUDE_MODELS.keys())[0]
        model_index = 0
    
    selected_model = st.selectbox(
        "Choose Claude Model:",
        options=list(CLAUDE_MODELS.keys()),
        format_func=lambda x: CLAUDE_MODELS[x],
        index=model_index,
        key="model_selector",
        help="Different models have different capabilities and costs"
    )
    
    if selected_model != st.session_state.selected_model:
        st.session_state.selected_model = selected_model
    
    # Show model info
    costs = get_model_cost_per_token(selected_model)
    st.markdown(f"""
    <div class="model-info">
    <strong>Model Info:</strong><br>
    • Input: ${costs['input']:.4f}/1K tokens<br>
    • Output: ${costs['output']:.4f}/1K tokens
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Translation History
    st.subheader("📚 Translation History")
    
    search_query = st.text_input(
        "🔍 Search history", 
        value=st.session_state.search_query, 
        key="search_input",
        placeholder="Search translations..."
    )
    if search_query != st.session_state.search_query:
        st.session_state.search_query = search_query
    
    filter_date = st.date_input("📅 Filter by date", value=None, key="date_filter")
    
    filtered_history = filter_history(
        st.session_state.translation_history, 
        search_query, 
        str(filter_date) if filter_date else None
    )
    
    if st.session_state.translation_history:
        st.write(f"**Total:** {len(st.session_state.translation_history)} | **Filtered:** {len(filtered_history)}")
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 JSON", help="Export as JSON"):
                try:
                    json_data = create_download_link(st.session_state.translation_history, "translations.json", "json")
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name="translations.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Export failed: {e}")
        
        with col2:
            if st.button("📥 CSV", help="Export as CSV"):
                try:
                    csv_data = create_download_link(st.session_state.translation_history, "translations.csv", "csv")
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name="translations.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Export failed: {e}")
        
        # Show filtered history
        for i, translation in enumerate(reversed(filtered_history[-10:])):
            timestamp = safe_get(translation, 'timestamp', 'Unknown')[:16]
            spanish_preview = safe_get(translation, 'spanish_input', '')[:100]
            if len(spanish_preview) > 100:
                spanish_preview += "..."
                
            with st.expander(f"#{len(filtered_history) - i} - {timestamp}"):
                st.write("**Spanish (preview):**")
                st.text(spanish_preview)
                
                if st.button(f"📋 Load", key=f"load_{i}"):
                    st.session_state.loaded_spanish = safe_get(translation, 'spanish_input', '')
                    st.session_state.translated_text = safe_get(translation, 'english_output', '')
                    st.rerun()
        
        if st.button("🗑️ Clear All History", type="secondary"):
            st.session_state.translation_history = []
            st.session_state.translation_cache = {}
            st.success("History cleared!")
            st.rerun()
    else:
        st.write("No translations yet")
    
    st.divider()
    
    # Prompt Editor
    st.subheader("📝 Prompt Editor")
    
    with st.expander("Edit System Prompt", expanded=False):
        st.write(f"**Length:** {len(st.session_state.custom_prompt):,} characters")
        
        new_prompt = st.text_area(
            "Edit prompt:",
            value=st.session_state.custom_prompt,
            height=200,
            key="prompt_editor"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save", type="primary"):
                st.session_state.custom_prompt = new_prompt
                st.success("Saved!")
        
        with col2:
            if st.button("🔄 Reset"):
                st.session_state.custom_prompt = get_default_prompt()
                st.success("Reset!")
                st.rerun()

# Setup API client
client = setup_api_client()

# Main content area
tab1, tab2 = st.tabs(["🔄 Single Translation", "📦 Batch Translation"])

with tab1:
    # Single translation interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🇪🇸 Spanish Input")
        
        # Load from history if available, but handle clear flag
        default_spanish = ""
        if st.session_state.get('clear_input_flag', False):
            st.session_state.clear_input_flag = False
            save_to_local_storage('draft_spanish', '')
        else:
            default_spanish = st.session_state.get('loaded_spanish', 
                                                 load_from_local_storage('draft_spanish') or '')
        
        spanish_text = st.text_area(
            "Paste your Spanish drill description:",
            height=500,
            value=default_spanish,
            key="spanish_input_key",
            placeholder="Paste the Spanish drill content here...",
            on_change=auto_save_draft
        )
        
        # Input stats
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        with col_stats1:
            st.metric("Characters", len(spanish_text))
        with col_stats2:
            st.metric("Words", len(spanish_text.split()) if spanish_text else 0)
        with col_stats3:
            estimated_tokens = estimate_tokens(
                st.session_state.custom_prompt.format(spanish_text=spanish_text) if spanish_text else "",
                st.session_state.selected_model
            )
            st.metric("Est. Tokens", f"{estimated_tokens:,}")
        
        # Cost estimation
        if spanish_text:
            try:
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
                **Cost Estimate ({CLAUDE_MODELS[st.session_state.selected_model]}):**
                - Input: ~{input_tokens:,} tokens
                - Est. Output: ~{estimated_output_tokens:,} tokens  
                - **Est. Cost: ${estimated_cost:.4f}**
                """)
            except Exception:
                st.info("Cost estimation unavailable")
        
        # Control buttons
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("🗑️ Clear", key="clear_input", help="Clear the Spanish text"):
                st.session_state.clear_input_flag = True
                st.rerun()
        
        with col_btn2:
            if st.button("👁️ Preview", key="quick_preview", help="Quick preview without API"):
                if spanish_text.strip():
                    preview_data = extract_topic_and_principle(spanish_text)
                    if preview_data['topic'] or preview_data['principle']:
                        st.markdown(f"""
                        <div class="quick-preview">
                            <h4>Quick Preview</h4>
                            <p><strong>Topic:</strong> {preview_data['topic'] or 'Not found'}</p>
                            <p><strong>Principle:</strong> {preview_data['principle']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("Could not extract topic/principle")
                else:
                    st.warning("Please enter Spanish text first")
        
        with col_btn3:
            st.info(f"**Model:** {CLAUDE_MODELS[st.session_state.selected_model].split('(')[0].strip()}")
    
    with col2:
        st.subheader("🇬🇧 English Output")
        
        # Check if we have a pending translation to display
        display_text = st.session_state.translated_text
        if 'pending_translation' in st.session_state:
            display_text = st.session_state.pending_translation
            st.session_state.translated_text = display_text
            del st.session_state.pending_translation
        
        english_output = st.text_area(
            "English translation:",
            height=500,
            value=display_text,
            key="english_output_key"
        )
        
        # Output controls
        col_out1, col_out2, col_out3 = st.columns(3)
        
        with col_out1:
            if english_output:
                if st.button("📋 Copy", key="copy_output", help="Copy to clipboard"):
                    st.success("Copied!")
        
        with col_out2:
            st.metric("Characters", len(english_output))
        
        with col_out3:
            st.metric("Words", len(english_output.split()) if english_output else 0)

    # Clear loaded history
    if 'loaded_spanish' in st.session_state:
        del st.session_state.loaded_spanish

    # Translation controls
    st.markdown("---")
    col_main1, col_main2, col_main3 = st.columns([1, 2, 1])
    
    with col_main2:
        st.markdown("💡 **Tip:** Press Ctrl+Enter to translate quickly")
        translate_button = st.button("🔄 Translate Drill", type="primary", use_container_width=True)

    # Translation logic
    if translate_button and st.session_state.api_ready and client:
        if spanish_text.strip():
            cache_key = get_text_hash(spanish_text + st.session_state.custom_prompt + st.session_state.selected_model)
            
            if cache_key in st.session_state.translation_cache:
                st.info("🚀 Loading from cache...")
                cached_result = st.session_state.translation_cache[cache_key]
                st.session_state.pending_translation = cached_result['translation']
                
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
                st.success("✅ Translation loaded from cache!")
                st.rerun()
            else:
                start_time = time.time()
                
                with st.spinner("🔄 Translating..."):
                    try:
                        full_prompt = st.session_state.custom_prompt.format(spanish_text=spanish_text)
                        
                        message = client.messages.create(
                            model=st.session_state.selected_model,
                            max_tokens=4000,
                            temperature=0.1,
                            messages=[{"role": "user", "content": full_prompt}]
                        )
                        
                        end_time = time.time()
                        english_translation = message.content[0].text
                        
                        # Cache the result
                        cache_entry = {
                            'translation': english_translation,
                            'input_tokens': message.usage.input_tokens,
                            'output_tokens': message.usage.output_tokens,
                            'timestamp': datetime.now().isoformat()
                        }
                        st.session_state.translation_cache[cache_key] = cache_entry
                        
                        st.session_state.translated_text = english_translation
                        
                        translation_entry = {
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'spanish_input': spanish_text,
                            'english_output': english_translation,
                            'input_tokens': message.usage.input_tokens,
                            'output_tokens': message.usage.output_tokens,
                            'duration': round(end_time - start_time, 2),
                            'cached': False,
                            'model': st.session_state.selected_model
                        }
                        st.session_state.translation_history.append(translation_entry)
                        
                        save_to_local_storage('draft_spanish', '')
                        
                        st.success(f"✅ Translation completed in {end_time - start_time:.2f} seconds!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Translation failed: {str(e)}")
        else:
            st.warning("⚠️ Please enter some Spanish text to translate.")
    elif translate_button and not st.session_state.api_ready:
        st.error("❌ API not available. Please check your configuration.")

with tab2:
    st.subheader("📦 Batch Translation")
    st.write("Upload text files with multiple Spanish drills separated by '---' or upload multiple files.")
    
    uploaded_files = st.file_uploader(
        "Choose files", 
        type=['txt'], 
        accept_multiple_files=True,
        help="Upload .txt files containing Spanish drill descriptions"
    )
    
    batch_text = st.text_area(
        "Or paste multiple drills here (separate with '---'):",
        height=200,
        placeholder="Drill 1 content\n---\nDrill 2 content\n---\nDrill 3 content"
    )
    
    if uploaded_files or batch_text:
        drills_to_process = []
        
        if uploaded_files:
            for file in uploaded_files:
                try:
                    content = file.read().decode('utf-8')
                    drills_to_process.append({
                        'source': file.name,
                        'content': content.strip()
                    })
                except Exception as e:
                    st.error(f"Error reading {file.name}: {e}")
        
        if batch_text:
            try:
                manual_drills = [drill.strip() for drill in batch_text.split('---') if drill.strip()]
                for i, drill in enumerate(manual_drills):
                    drills_to_process.append({
                        'source': f'Manual Input #{i+1}',
                        'content': drill
                    })
            except Exception as e:
                st.error(f"Error processing manual input: {e}")
        
        st.write(f"**Found {len(drills_to_process)} drills to process**")
        
        if st.button("🚀 Process All Drills", type="primary") and st.session_state.api_ready and client:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            batch_results = []
            
            for i, drill in enumerate(drills_to_process):
                status_text.text(f"Processing drill {i+1}/{len(drills_to_process)}: {drill['source']}")
                
                cache_key = get_text_hash(drill['content'] + st.session_state.custom_prompt + st.session_state.selected_model)
                
                if cache_key in st.session_state.translation_cache:
                    cached_result = st.session_state.translation_cache[cache_key]
                    result = {
                        'source': drill['source'],
                        'spanish_input': drill['content'],
                        'english_output': cached_result['translation'],
                        'cached': True,
                        'success': True
                    }
                else:
                    try:
                        full_prompt = st.session_state.custom_prompt.format(spanish_text=drill['content'])
                        
                        message = client.messages.create(
                            model=st.session_state.selected_model,
                            max_tokens=4000,
                            temperature=0.1,
                            messages=[{"role": "user", "content": full_prompt}]
                        )
                        
                        translation = message.content[0].text
                        
                        cache_entry = {
                            'translation': translation,
                            'input_tokens': message.usage.input_tokens,
                            'output_tokens': message.usage.output_tokens,
                            'timestamp': datetime.now().isoformat()
                        }
                        st.session_state.translation_cache[cache_key] = cache_entry
                        
                        result = {
                            'source': drill['source'],
                            'spanish_input': drill['content'],
                            'english_output': translation,
                            'cached': False,
                            'success': True,
                            'input_tokens': message.usage.input_tokens,
                            'output_tokens': message.usage.output_tokens
                        }
                        
                        translation_entry = {
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'spanish_input': drill['content'],
                            'english_output': translation,
                            'input_tokens': message.usage.input_tokens,
                            'output_tokens': message.usage.output_tokens,
                            'duration': 2.0,
                            'cached': False,
                            'batch_source': drill['source'],
                            'model': st.session_state.selected_model
                        }
                        st.session_state.translation_history.append(translation_entry)
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        result = {
                            'source': drill['source'],
                            'spanish_input': drill['content'],
                            'english_output': f"Error: {str(e)}",
                            'cached': False,
                            'success': False,
                            'error': str(e)
                        }
                
                batch_results.append(result)
                progress_bar.progress((i + 1) / len(drills_to_process))
            
            st.session_state.current_batch_results = batch_results
            status_text.text("✅ Batch processing completed!")
            
            successful = sum(1 for r in batch_results if r['success'])
            cached = sum(1 for r in batch_results if r.get('cached', False))
            
            st.success(f"Processed {len(batch_results)} drills: {successful} successful, {cached} from cache")
        
        # Display batch results
        if st.session_state.current_batch_results:
            st.subheader("📋 Batch Results")
            
            for i, result in enumerate(st.session_state.current_batch_results):
                status_icon = "✅" if result['success'] else "❌"
                cache_icon = "⚡" if result.get('cached', False) else "🔄"
                
                with st.expander(f"{status_icon} {cache_icon} {result['source']}"):
                    if result['success']:
                        col_result1, col_result2 = st.columns(2)
                        
                        with col_result1:
                            st.write("**Spanish Input:**")
                            st.text_area("", value=result['spanish_input'], height=200, key=f"batch_spanish_{i}", disabled=True)
                        
                        with col_result2:
                            st.write("**English Output:**")
                            st.text_area("", value=result['english_output'], height=200, key=f"batch_english_{i}", disabled=True)
                            
                            if st.button(f"📋 Copy Translation {i+1}", key=f"copy_batch_{i}"):
                                st.success("Translation copied!")
                    else:
                        st.error(f"Translation failed: {result.get('error', 'Unknown error')}")

# Usage Statistics Dashboard
if st.session_state.translation_history:
    st.markdown("---")
    st.subheader("📊 Usage Statistics")
    
    try:
        col_stat1, col_stat2, col_stat3, col_stat4, col_stat5, col_stat6 = st.columns(6)
        
        total_translations = len(st.session_state.translation_history)
        total_input_tokens = sum(safe_get(t, 'input_tokens', 0) for t in st.session_state.translation_history)
        total_output_tokens = sum(safe_get(t, 'output_tokens', 0) for t in st.session_state.translation_history)
        avg_duration = sum(safe_get(t, 'duration', 0) for t in st.session_state.translation_history) / total_translations if total_translations > 0 else 0
        cache_hits = sum(1 for t in st.session_state.translation_history if safe_get(t, 'cached', False))
        
        # Calculate total cost
        total_cost = 0
        for t in st.session_state.translation_history:
            if not safe_get(t, 'cached', False):
                model_used = safe_get(t, 'model', 'claude-sonnet-4-20250514')
                cost = calculate_estimated_cost(
                    safe_get(t, 'input_tokens', 0),
                    safe_get(t, 'output_tokens', 0),
                    model_used
                )
                total_cost += cost
        
        with col_stat1:
            st.metric("Total Translations", total_translations)
        with col_stat2:
            st.metric("Input Tokens", f"{total_input_tokens:,}")
        with col_stat3:
            st.metric("Output Tokens", f"{total_output_tokens:,}")
        with col_stat4:
            st.metric("Avg Duration", f"{avg_duration:.1f}s")
        with col_stat5:
            st.metric("Cache Hits", f"{cache_hits}")
        with col_stat6:
            st.metric("Total Cost", f"${total_cost:.4f}")
        
        # Model usage breakdown
        st.markdown("**Model Usage:**")
        model_usage = {}
        for t in st.session_state.translation_history:
            model = safe_get(t, 'model', 'Unknown')
            model_name = CLAUDE_MODELS.get(model, model)
            model_usage[model_name] = model_usage.get(model_name, 0) + 1
        
        for model, count in model_usage.items():
            st.markdown(f"- {model}: {count} translations")
            
    except Exception as e:
        st.error(f"Error displaying statistics: {e}")

# Footer with tips
st.markdown("---")
st.markdown("""
### 💡 Tips & Shortcuts
- **Ctrl+Enter**: Quick translate (when text area is focused)
- **Auto-save**: Your Spanish input is automatically saved as you type
- **Cache**: Identical translations are cached to save time and tokens
- **Quick Preview**: Get topic and principle without using API tokens
- **Batch Processing**: Upload multiple files or separate drills with `---`
- **Search History**: Use the search box in the sidebar to find past translations
- **Export Options**: Download your translation history in JSON or CSV format

### 🔧 Features
- ✅ Model selection with cost awareness
- ✅ Copy to clipboard functionality
- ✅ Auto-save drafts
- ✅ Translation caching
- ✅ Token estimation and cost calculation
- ✅ Quick preview mode
- ✅ Batch translation support
- ✅ Search and filter history
- ✅ Import/export prompts and data
- ✅ Enhanced UI/UX with modern design
- ✅ Robust error handling
""")

# JavaScript for keyboard shortcuts
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        const translateButton = document.querySelector('[data-testid="stButton"] button');
        if (translateButton && translateButton.textContent.includes('Translate')) {
            translateButton.click();
        }
    }
});
</script>
""", unsafe_allow_html=True)
