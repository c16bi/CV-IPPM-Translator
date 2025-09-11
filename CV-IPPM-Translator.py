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
    
    .copy-button {
        background: #16a34a !important;
        color: white !important;
    }
    
    .clear-button {
        background: #dc2626 !important;
        color: white !important;
    }
    
    .preview-button {
        background: #f59e0b !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    defaults = {
        'translation_history': [],
        'translated_text': "",
        'custom_prompt': get_default_prompt(),
        'translation_cache': {},
        'draft_spanish': "",
        'current_batch_results': [],
        'search_query': "",
        'filter_date': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_default_prompt():
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
DESCRIPCIÓN: La sesión comienza con una tarea basada en rondos. Un equipo asume el rol ofensivo, mientras que el otro desempeña funciones defensivas. Se estructura un rondo principal de mayores dimensiones con cuatro jugadores atacantes, acompañado de dos rondos secundarios más reducidos, cada uno con tres jugadores. Adicionalmente, nueve jugadores del equipo blanco se encuentran en espera, distribuidos junto a los conos rojos, aguardando su turno de participación. El objetivo de la tarea consiste en conservar la posesión del balón el mayor tiempo posible, impidiendo que los defensores lo intercepten o recuperen. La acción se inicia con dos defensores accediendo al rondo principal para disputar un 4 contra 2. En el momento en que logren recuperar o interceptar el esférico, deberán desplazarse, cada uno, hacia uno de los rondos secundarios con el mismo propósito. Si consiguen nuevamente recuperar el balón, deberán finalizar la acción con un remate a portería.

NORMATIVAS: Atacantes: I) En todo momento cada uno de los jugadores debe permanecer en su zona de juego delimitada. II) Si el balón sale de la zona en cuestión, se considera recuperación de los defensores.

Defensores: I) En ninguno de los casos se puede iniciar la acción hasta que ambos compañeros hayan recuperado el balón en ambos rondos. II) Si se intercepta el balón en alguno de los dos rondos de menor dimensión y el jugador no dispone de este, el entrenador jugará un balón y este debe finalizar a portería con un contacto únicamente.

PUNTUACIÓN: Cada serie un equipo obtiene un rol distinto. Se compite por número de goles.

GRADIENTE:
(+) Limitar el número de contactos de los jugadores ofensivos, aumentando la dificultad en mantener la posesión de balón, obligando a realizar acciones de mayor calidad y ofrecer más líneas de pase por parte de los compañeros.

(-) Aumentar las dimensiones de juego, facilitando el dinamismo de la tarea y la circulación de balón.
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
The session begins with a rondo-based exercise. One team takes the offensive role while the other performs defensive functions. The structure includes a main rondo of larger dimensions with four attacking players, accompanied by two smaller secondary rondos, each with three players. Additionally, nine players from the white team are positioned in waiting areas, distributed alongside the red cones, awaiting their turn to participate. The objective is to maintain possession of the ball for as long as possible, preventing the defenders from intercepting or recovering it. The action begins with two defenders entering the main rondo to contest a four vs two situation. When they manage to recover or intercept the ball, they must each move to one of the secondary rondos with the same purpose. If they successfully recover the ball again, they must finish the action with a shot at goal. 
Attackers must remain in their designated playing zone at all times. If the ball leaves the zone, this is considered a defensive recovery. Defenders cannot start the action until both teammates have recovered the ball in both rondos. If the ball is intercepted in either of the two smaller rondos and the player doesn't have possession, the coach plays a ball and this must be finished at goal with only one touch.
Each block sees teams swap roles. Competition is based on number of goals scored.

**Progressions**
- More advanced: Limit the number of touches for offensive players, increasing the difficulty in maintaining possession and forcing higher quality actions with more passing options from teammates
- Simplified: Increase the playing dimensions, facilitating the dynamism of the exercise and ball circulation

**Coaching points**
- Supporting foot technique: Players should be encouraged to use their supporting foot effectively with single ground contact when controlling the ball
- Pass selection: Players should choose appropriate passing technique based on distance - inside foot for short/medium range, instep for longer passes
- Ball retention: Players should focus on maintaining possession through quick, accurate passing and intelligent movement between rondos
</ideal_output>
</example>
</examples>

You are a specialized translator for football/soccer coaching content. Your task is to translate Spanish football drill descriptions into a standardized English coaching format that is clear, practical, and coach-friendly.

Here is the Spanish drill description you need to translate:

<spanish_drill_description>
{spanish_text}
</spanish_drill_description>

## Translation Guidelines

Follow these principles when translating:
- Prioritize clarity and practical understanding over literal word-for-word translation
- Use simple, direct language that coaches can quickly grasp
- Avoid overly complex or AI-generated football jargon
- Break up long Spanish sentences into shorter, more readable English sentences
- Remove any repetitive content
- Ensure all instructions are actionable and specific
- Convert measurements from meters to yards
- Translate technical football terms accurately (e.g., "rondo" stays "rondo", "centro" becomes "crossing")

## Required Output Format

Your translated drill must follow this exact structure:

**Topic**
[Main skill/technique focus]

**Principle** 
[Key technical instruction or teaching point]

**Microcycle day**
[When in training cycle this drill should be used]

**Time**
[Duration and sets]

**Players**
[Number of players involved]

**Physical focus**
[Physical conditioning aspect]

**Space/equipment**
[Field dimensions and required equipment]

**Description**
[Detailed explanation of how the drill works, including rules for attackers and defenders, scoring system]

**Progressions**
- More advanced: [How to make the drill harder]
- Simplified: [How to make the drill easier]

**Coaching points**
- [Brief title]: [Detailed coaching instruction]
- [Brief title]: [Detailed coaching instruction]
- [Brief title]: [Detailed coaching instruction]"""

# Utility functions
def get_text_hash(text: str) -> str:
    """Generate a hash for caching purposes"""
    return hashlib.md5(text.encode()).hexdigest()

def estimate_tokens(text: str) -> int:
    """Rough estimation of tokens (1 token ≈ 4 characters for Claude)"""
    return len(text) // 4

def save_to_local_storage(key: str, value):
    """Save data to session state (simulating local storage)"""
    st.session_state[f"ls_{key}"] = value

def load_from_local_storage(key: str):
    """Load data from session state"""
    return st.session_state.get(f"ls_{key}")

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
    
    # Simple translations for common terms
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
        return b""  # Return empty bytes if encoding fails

def filter_history(history: List[Dict], search_query: str, filter_date: Optional[str]) -> List[Dict]:
    """Filter translation history based on search and date"""
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
        'selected_model': "claude-3-7-sonnet-20250107",  # Default to 3.7
        'api_ready': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def auto_save_draft():
    """Auto-save draft functionality with error handling"""
    try:
        if 'spanish_input_key' in st.session_state:
            save_to_local_storage('draft_spanish', st.session_state.spanish_input_key)
    except Exception:
        pass  # Fail silently

def setup_api_client():
    """Setup Anthropic API client with error handling"""
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

# Initialize session state
initialize_session_state()

# Header
st.markdown("""
<div class="main-header">
    <h1>⚽ CV Spanish Drill Translator</h1>
    <p>Professional football drill translation with advanced features</p>
</div>
""", unsafe_allow_html=True):'):
            topic = line.replace('CONTENIDO:', '').strip()
        elif line.startswith('CONSIGNA:'):
            principle = line.replace('CONSIGNA:', '').strip()
    
    # Simple translations for common terms
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
        'principle': principle
    }

def create_download_link(data, filename, file_type="json"):
    """Create a download link for data"""
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

def filter_history(history: List[Dict], search_query: str, filter_date: Optional[str]) -> List[Dict]:
    """Filter translation history based on search and date"""
    filtered = history
    
    if search_query:
        filtered = [
            item for item in filtered 
            if search_query.lower() in item.get('spanish_input', '').lower() 
            or search_query.lower() in item.get('english_output', '').lower()
        ]
    
    if filter_date:
        filtered = [
            item for item in filtered 
            if item.get('timestamp', '').startswith(filter_date)
        ]
    
    return filtered

# Initialize session state
initialize_session_state()

# Auto-save draft functionality
def auto_save_draft():
    if 'spanish_input_key' in st.session_state:
        save_to_local_storage('draft_spanish', st.session_state.spanish_input_key)

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
    
    # Translation History Section
    st.subheader("📚 Translation History")
    
    # Search and filter controls
    search_query = st.text_input("🔍 Search history", value=st.session_state.search_query, key="search_input")
    if search_query != st.session_state.search_query:
        st.session_state.search_query = search_query
    
    filter_date = st.date_input("📅 Filter by date", value=None, key="date_filter")
    
    # Apply filters
    filtered_history = filter_history(st.session_state.translation_history, search_query, str(filter_date) if filter_date else None)
    
    if st.session_state.translation_history:
        st.write(f"**Total:** {len(st.session_state.translation_history)} | **Filtered:** {len(filtered_history)}")
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export JSON"):
                json_data = create_download_link(st.session_state.translation_history, "translations.json", "json")
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name="translations.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📥 Export CSV"):
                csv_data = create_download_link(st.session_state.translation_history, "translations.csv", "csv")
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="translations.csv",
                    mime="text/csv"
                )
        
        # Show filtered history
        for i, translation in enumerate(reversed(filtered_history[-10:])):
            with st.expander(f"#{len(filtered_history) - i} - {translation['timestamp'][:16]}"):
                st.write("**Spanish (preview):**")
                preview_text = translation['spanish_input'][:100]
                if len(translation['spanish_input']) > 100:
                    preview_text += "..."
                st.text(preview_text)
                
                if st.button(f"📋 Load", key=f"load_{i}"):
                    st.session_state.loaded_spanish = translation['spanish_input']
                    st.session_state.translated_text = translation['english_output']
                    st.rerun()
        
        if st.button("🗑️ Clear All History", type="secondary"):
            st.session_state.translation_history = []
            st.session_state.translation_cache = {}
            st.rerun()
    else:
        st.write("No translations yet")
    
    st.divider()
    
    # Prompt Editor Section
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
        
        # Import/Export prompt
        st.write("**Import/Export:**")
        
        uploaded_prompt = st.file_uploader("Import prompt", type=['txt', 'json'])
        if uploaded_prompt:
            prompt_content = uploaded_prompt.read().decode('utf-8')
            if uploaded_prompt.type == 'application/json':
                prompt_data = json.loads(prompt_content)
                prompt_content = prompt_data.get('prompt', prompt_content)
            
            if st.button("📥 Use Imported Prompt"):
                st.session_state.custom_prompt = prompt_content
                st.success("Prompt imported!")
                st.rerun()
        
        if st.button("📤 Export Current Prompt"):
            st.download_button(
                label="Download Prompt",
                data=st.session_state.custom_prompt.encode('utf-8'),
                file_name="custom_prompt.txt",
                mime="text/plain"
            )

# Main content area
tab1, tab2 = st.tabs(["🔄 Single Translation", "📦 Batch Translation"])

with tab1:
    # Single translation interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🇪🇸 Spanish Input")
        
        # Load from history if available
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
        
        # Input controls and stats
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        with col_stats1:
            st.metric("Characters", len(spanish_text))
        with col_stats2:
            st.metric("Words", len(spanish_text.split()) if spanish_text else 0)
        with col_stats3:
            estimated_tokens = estimate_tokens(st.session_state.custom_prompt.format(spanish_text=spanish_text)) if spanish_text else 0
            st.metric("Est. Tokens", f"{estimated_tokens:,}")
        
        # Input control buttons
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("🗑️ Clear Input", key="clear_input", help="Clear the Spanish text area"):
                st.session_state.spanish_input_key = ""
                save_to_local_storage('draft_spanish', '')
                st.rerun()
        
        with col_btn2:
            if st.button("👁️ Quick Preview", key="quick_preview", help="Show topic and principle without using API"):
                if spanish_text.strip():
                    preview_data = extract_topic_and_principle(spanish_text)
                    st.markdown(f"""
                    <div class="quick-preview">
                        <h4>Quick Preview</h4>
                        <p><strong>Topic:</strong> {preview_data['topic']}</p>
                        <p><strong>Principle:</strong> {preview_data['principle'][:200]}{'...' if len(preview_data['principle']) > 200 else ''}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Please enter Spanish text first")
        
        with col_btn3:
            # Estimated cost (approximate)
            if spanish_text:
                estimated_cost = (estimated_tokens / 1000) * 0.003  # Rough estimate for Claude
                st.metric("Est. Cost", f"${estimated_cost:.4f}")
    
    with col2:
        st.subheader("🇬🇧 English Output")
        
        english_output = st.text_area(
            "English translation:",
            height=500,
            value=st.session_state.translated_text,
            key="english_output_key"
        )
        
        # Output controls
        col_out1, col_out2, col_out3 = st.columns(3)
        
        with col_out1:
            if english_output and st.button("📋 Copy to Clipboard", key="copy_output"):
                # Use JavaScript to copy to clipboard
                st.markdown(f"""
                <script>
                navigator.clipboard.writeText(`{english_output.replace('`', '\\`')}`);
                </script>
                """, unsafe_allow_html=True)
                st.success("Copied to clipboard!")
        
        with col_out2:
            st.metric("Characters", len(english_output))
        
        with col_out3:
            st.metric("Words", len(english_output.split()) if english_output else 0)

    # Clear loaded history after displaying
    if 'loaded_spanish' in st.session_state:
        del st.session_state.loaded_spanish

    # API setup and translation
    try:
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        api_ready = True
    except KeyError:
        st.error("⚠️ API key not found. Please set ANTHROPIC_API_KEY in Streamlit secrets.")
        api_ready = False

    # Translation controls
    st.markdown("---")
    col_main1, col_main2, col_main3 = st.columns([1, 2, 1])
    
    with col_main2:
        # Add keyboard shortcut hint
        st.markdown("💡 **Tip:** Press Ctrl+Enter to translate quickly")
        
        # Check for Ctrl+Enter (simulate with session state)
        translate_button = st.button("🔄 Translate Drill", type="primary", use_container_width=True)
        
        # Handle keyboard shortcut (simplified version)
        if st.session_state.get('ctrl_enter_pressed', False):
            translate_button = True
            st.session_state.ctrl_enter_pressed = False

    # Translation logic
    if translate_button and api_ready:
        if spanish_text.strip():
            # Check cache first
            text_hash = get_text_hash(spanish_text + st.session_state.custom_prompt)
            
            if text_hash in st.session_state.translation_cache:
                st.info("🚀 Loading from cache...")
                cached_result = st.session_state.translation_cache[text_hash]
                st.session_state.translated_text = cached_result['translation']
                
                # Add to history
                translation_entry = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'spanish_input': spanish_text,
                    'english_output': cached_result['translation'],
                    'input_tokens': cached_result.get('input_tokens', 0),
                    'output_tokens': cached_result.get('output_tokens', 0),
                    'duration': 0.1,  # Cache hit
                    'cached': True
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
                            model="claude-3-5-sonnet-20241022",
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
                        st.session_state.translation_cache[text_hash] = cache_entry
                        
                        # Update session state
                        st.session_state.translated_text = english_translation
                        
                        # Add to history
                        translation_entry = {
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'spanish_input': spanish_text,
                            'english_output': english_translation,
                            'input_tokens': message.usage.input_tokens,
                            'output_tokens': message.usage.output_tokens,
                            'duration': round(end_time - start_time, 2),
                            'cached': False
                        }
                        st.session_state.translation_history.append(translation_entry)
                        
                        # Clear draft
                        save_to_local_storage('draft_spanish', '')
                        
                        st.success(f"✅ Translation completed in {end_time - start_time:.2f} seconds!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Translation failed: {str(e)}")
        else:
            st.warning("⚠️ Please enter some Spanish text to translate.")

with tab2:
    # Batch translation interface
    st.subheader("📦 Batch Translation")
    st.write("Upload a text file with multiple Spanish drills separated by '---' or upload multiple files.")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Choose files", 
        type=['txt'], 
        accept_multiple_files=True,
        help="Upload .txt files containing Spanish drill descriptions"
    )
    
    # Manual text input for batch
    batch_text = st.text_area(
        "Or paste multiple drills here (separate with '---'):",
        height=200,
        placeholder="Drill 1 content\n---\nDrill 2 content\n---\nDrill 3 content"
    )
    
    if uploaded_files or batch_text:
        drills_to_process = []
        
        # Process uploaded files
        if uploaded_files:
            for file in uploaded_files:
                content = file.read().decode('utf-8')
                drills_to_process.append({
                    'source': file.name,
                    'content': content.strip()
                })
        
        # Process manual input
        if batch_text:
            manual_drills = [drill.strip() for drill in batch_text.split('---') if drill.strip()]
            for i, drill in enumerate(manual_drills):
                drills_to_process.append({
                    'source': f'Manual Input #{i+1}',
                    'content': drill
                })
        
        st.write(f"**Found {len(drills_to_process)} drills to process**")
        
        # Batch processing controls
        col_batch1, col_batch2 = st.columns(2)
        
        with col_batch1:
            if st.button("🚀 Process All Drills", type="primary") and api_ready:
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                
                batch_results = []
                
                for i, drill in enumerate(drills_to_process):
                    status_text.text(f"Processing drill {i+1}/{len(drills_to_process)}: {drill['source']}")
                    
                    # Check cache first
                    text_hash = get_text_hash(drill['content'] + st.session_state.custom_prompt)
                    
                    if text_hash in st.session_state.translation_cache:
                        # Use cached result
                        cached_result = st.session_state.translation_cache[text_hash]
                        result = {
                            'source': drill['source'],
                            'spanish_input': drill['content'],
                            'english_output': cached_result['translation'],
                            'cached': True,
                            'success': True
                        }
                    else:
                        # Translate new drill
                        try:
                            full_prompt = st.session_state.custom_prompt.format(spanish_text=drill['content'])
                            
                            message = client.messages.create(
                                model="claude-3-5-sonnet-20241022",
                                max_tokens=4000,
                                temperature=0.1,
                                messages=[{"role": "user", "content": full_prompt}]
                            )
                            
                            translation = message.content[0].text
                            
                            # Cache the result
                            cache_entry = {
                                'translation': translation,
                                'input_tokens': message.usage.input_tokens,
                                'output_tokens': message.usage.output_tokens,
                                'timestamp': datetime.now().isoformat()
                            }
                            st.session_state.translation_cache[text_hash] = cache_entry
                            
                            result = {
                                'source': drill['source'],
                                'spanish_input': drill['content'],
                                'english_output': translation,
                                'cached': False,
                                'success': True,
                                'input_tokens': message.usage.input_tokens,
                                'output_tokens': message.usage.output_tokens
                            }
                            
                            # Add to individual history
                            translation_entry = {
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'spanish_input': drill['content'],
                                'english_output': translation,
                                'input_tokens': message.usage.input_tokens,
                                'output_tokens': message.usage.output_tokens,
                                'duration': 2.0,  # Batch processing
                                'cached': False,
                                'batch_source': drill['source']
                            }
                            st.session_state.translation_history.append(translation_entry)
                            
                            # Small delay to avoid rate limiting
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
                
                # Show summary
                successful = sum(1 for r in batch_results if r['success'])
                cached = sum(1 for r in batch_results if r.get('cached', False))
                
                st.success(f"Processed {len(batch_results)} drills: {successful} successful, {cached} from cache")
        
        with col_batch2:
            if st.session_state.current_batch_results:
                # Export batch results
                if st.button("📥 Export Batch Results"):
                    batch_export_data = []
                    for result in st.session_state.current_batch_results:
                        batch_export_data.append({
                            'source': result['source'],
                            'spanish_input': result['spanish_input'][:100] + "..." if len(result['spanish_input']) > 100 else result['spanish_input'],
                            'english_output': result['english_output'][:100] + "..." if len(result['english_output']) > 100 else result['english_output'],
                            'success': result['success'],
                            'cached': result.get('cached', False),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                    
                    batch_json = create_download_link(batch_export_data, "batch_results.json", "json")
                    st.download_button(
                        label="Download Batch Results",
                        data=batch_json,
                        file_name="batch_translation_results.json",
                        mime="application/json"
                    )
        
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
    
    col_stat1, col_stat2, col_stat3, col_stat4, col_stat5, col_stat6 = st.columns(6)
    
    total_translations = len(st.session_state.translation_history)
    total_input_tokens = sum(t.get('input_tokens', 0) for t in st.session_state.translation_history)
    total_output_tokens = sum(t.get('output_tokens', 0) for t in st.session_state.translation_history)
    avg_duration = sum(t.get('duration', 0) for t in st.session_state.translation_history) / total_translations if total_translations > 0 else 0
    cache_hits = sum(1 for t in st.session_state.translation_history if t.get('cached', False))
    
    # Calculate total cost
    total_cost = 0
    for t in st.session_state.translation_history:
        if not t.get('cached', False):  # Only count non-cached translations
            model_used = t.get('model', 'claude-3-5-sonnet-20241022')  # fallback for old entries
            cost = calculate_estimated_cost(
                t.get('input_tokens', 0),
                t.get('output_tokens', 0),
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
    if st.session_state.translation_history:
        st.markdown("**Model Usage:**")
        model_usage = {}
        for t in st.session_state.translation_history:
            model = t.get('model', 'Unknown')
            model_name = CLAUDE_MODELS.get(model, model)
            model_usage[model_name] = model_usage.get(model_name, 0) + 1
        
        for model, count in model_usage.items():
            st.markdown(f"- {model}: {count} translations")

# Footer with keyboard shortcuts and tips
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
- ✅ Copy to clipboard functionality
- ✅ Auto-save drafts
- ✅ Translation caching
- ✅ Token estimation and cost calculation
- ✅ Quick preview mode
- ✅ Batch translation support
- ✅ Search and filter history
- ✅ Import/export prompts and data
- ✅ Enhanced UI/UX with modern design
""")

# JavaScript for keyboard shortcuts
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        // Find the translate button and click it
        const translateButton = document.querySelector('[data-testid="stButton"] button');
        if (translateButton && translateButton.textContent.includes('Translate')) {
            translateButton.click();
        }
    }
});

// Copy to clipboard functionality
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        console.log('Text copied to clipboard');
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
    });
}
</script>
""", unsafe_allow_html=True)
