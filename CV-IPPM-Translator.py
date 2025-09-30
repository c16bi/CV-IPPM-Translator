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
    page_title="CV Spanish Translator", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Available Claude models (updated with new models and pricing)
CLAUDE_MODELS = {
    "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5 (Recommended)",
    "claude-sonnet-4-20250514": "Claude Sonnet 4",
    "claude-3-5-haiku-20241022": "Claude Haiku 3.5"
}

# Cleaner, more modern CSS
st.markdown("""
<style>
    /* Clean, modern design system */
    :root {
        --primary: #5B47E0;
        --primary-dark: #4536B8;
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --gray-50: #F9FAFB;
        --gray-100: #F3F4F6;
        --gray-200: #E5E7EB;
        --gray-300: #D1D5DB;
        --gray-600: #4B5563;
        --gray-800: #1F2937;
    }
    
    /* Clean header */
    .main-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
    }
    
    .main-header p {
        margin: 0.25rem 0 0 0;
        opacity: 0.95;
        font-size: 1rem;
    }
    
    /* Clean cards */
    .clean-card {
        background: white;
        border: 1px solid var(--gray-200);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--gray-50);
        padding: 4px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: var(--gray-600);
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: white;
        color: var(--primary);
    }
    
    /* Metric cards */
    .metric-card {
        background: var(--gray-50);
        border: 1px solid var(--gray-200);
        border-radius: 8px;
        padding: 0.75rem;
        text-align: center;
    }
    
    .metric-card .value {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--gray-800);
    }
    
    .metric-card .label {
        font-size: 0.875rem;
        color: var(--gray-600);
        margin-top: 0.25rem;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-success {
        background: #D1FAE5;
        color: #065F46;
    }
    
    .status-warning {
        background: #FEF3C7;
        color: #92400E;
    }
    
    .status-info {
        background: #DBEAFE;
        color: #1E40AF;
    }
    
    /* Clean buttons */
    .stButton > button {
        border-radius: 8px;
        border: none;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Text areas */
    .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid var(--gray-300) !important;
        font-size: 0.95rem !important;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 1px var(--primary) !important;
    }
    
    /* Info boxes */
    .info-box {
        background: var(--gray-50);
        border-left: 4px solid var(--primary);
        border-radius: 6px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .cost-box {
        background: linear-gradient(135deg, #F3E8FF 0%, #E9D5FF 100%);
        border: 1px solid #C084FC;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    
    /* Quick tips */
    .quick-tip {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 1px solid var(--success);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.75rem 0;
        font-size: 0.9rem;
    }
    
    /* History items */
    .history-item {
        background: var(--gray-50);
        border: 1px solid var(--gray-200);
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        transition: all 0.2s;
    }
    
    .history-item:hover {
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Output container styling */
    .output-container {
        background: #f8f9fa;
        border: 1px solid var(--gray-300);
        border-radius: 8px;
        padding: 1rem;
        min-height: 400px;
        max-height: 400px;
        overflow-y: auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 0.95rem;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    .output-container:empty:before {
        content: 'Your translated drill will appear here...';
        color: #999;
        font-style: italic;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def get_default_drill_prompt():
    """Return the default drill translation prompt"""
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

First, systematically analyze the Spanish content in <translation_breakdown> tags. Work through:

1. **Key Spanish phrases**: Quote the most important phrases
2. **Measurement conversion**: List meters and yard equivalents
3. **Terminology mapping**: Spanish terms to American equivalents
4. **Drill structure**: Break down timing, players, space, rules
5. **Progressions**: Note any difficulty variations
6. **Natural language check**: Identify complex constructions needing rewrite

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
[Clear, step-by-step explanation in natural, flowing English]

**Progressions**
- **More advanced:** [Ways to increase difficulty]
- **Simplified:** [Ways to reduce complexity]

**Coaching points**
- **[Brief title]:** [Specific, actionable instruction]
- **[Brief title]:** [Specific, actionable instruction]  
- **[Brief title]:** [Specific, actionable instruction]"""

def get_default_general_prompt():
    """Return the default general translation prompt"""
    return """You are a professional Spanish to English translator specializing in soccer/football content. Translate the following Spanish text into clear, natural English that American soccer coaches and players will easily understand.

<spanish_text>
{spanish_text}
</spanish_text>

Guidelines:
- Use American soccer terminology where appropriate
- Convert metric measurements to yards/feet
- Keep technical soccer terms accurate
- Ensure the translation sounds natural in English
- Preserve the original meaning and tone

Provide only the English translation without any additional commentary."""

def get_text_hash(text: str) -> str:
    """Generate a hash for caching purposes"""
    return hashlib.md5(text.encode()).hexdigest()

def estimate_tokens(text: str, model: str = "claude-sonnet-4-5-20250929") -> int:
    """Rough estimation of tokens based on model"""
    if not text:
        return 0
    
    base_estimate = len(text) // 4
    
    model_multipliers = {
        "claude-sonnet-4-5-20250929": 1.0,
        "claude-sonnet-4-20250514": 1.0,
        "claude-3-5-haiku-20241022": 0.95
    }
    
    multiplier = model_multipliers.get(model, 1.0)
    return int(base_estimate * multiplier)

def get_model_cost_per_token(model: str) -> dict:
    """Get cost per token for input/output (USD per 1M tokens)"""
    costs = {
        "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0}
    }
    return costs.get(model, {"input": 3.0, "output": 15.0})

def calculate_estimated_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """Calculate estimated cost for a translation"""
    costs = get_model_cost_per_token(model)
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost

def safe_get(item: dict, key: str, default=0):
    """Safely get a value from a dictionary"""
    try:
        return item.get(key, default)
    except (AttributeError, TypeError):
        return default

def initialize_session_state():
    """Initialize session state with defaults"""
    defaults = {
        'translation_history': [],
        'translated_text': "",
        'drill_prompt': get_default_drill_prompt(),
        'general_prompt': get_default_general_prompt(),
        'saved_drill_prompt': get_default_drill_prompt(),
        'saved_general_prompt': get_default_general_prompt(),
        'translation_cache': {},
        'current_batch_results': [],
        'selected_model': "claude-sonnet-4-5-20250929",
        'api_ready': False,
        'spanish_input': "",
        'general_spanish_input': "",
        'general_translated_text': "",
        'clear_input': False,
        'last_translation_time': None,
        'show_prompt_editor': False,
        'active_tab': 'drill'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Fix any invalid model selection
    if st.session_state.selected_model not in CLAUDE_MODELS:
        st.session_state.selected_model = "claude-sonnet-4-5-20250929"

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

def translate_text(client, text: str, prompt_template: str, model: str):
    """Generic translation function"""
    if not text.strip():
        return None, "Please enter text to translate"
    
    cache_key = get_text_hash(text + prompt_template + model)
    
    # Check cache
    if cache_key in st.session_state.translation_cache:
        cached = st.session_state.translation_cache[cache_key]
        return cached['translation'], None
    
    # Perform translation
    try:
        full_prompt = prompt_template.format(spanish_text=text)
        
        message = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0.1,
            messages=[{"role": "user", "content": full_prompt}]
        )
        
        translation = message.content[0].text
        
        # Cache result
        st.session_state.translation_cache[cache_key] = {
            'translation': translation,
            'input_tokens': message.usage.input_tokens,
            'output_tokens': message.usage.output_tokens,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to history
        st.session_state.translation_history.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'drill' if 'drill' in prompt_template[:100].lower() else 'general',
            'spanish_input': text,
            'english_output': translation,
            'input_tokens': message.usage.input_tokens,
            'output_tokens': message.usage.output_tokens,
            'model': model
        })
        
        return translation, None
        
    except Exception as e:
        return None, str(e)

# Initialize
initialize_session_state()
client = setup_api_client()

# Clean header
st.markdown("""
<div class="main-header">
    <h1>⚽ CV Spanish Translator</h1>
    <p>Professional translations for soccer coaching content</p>
</div>
""", unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Drill Translation", "📝 General Translation", "⚙️ Settings", "📚 History"])

# DRILL TRANSLATION TAB
with tab1:
    # Quick tip
    st.markdown("""
    <div class="quick-tip">
        💡 <strong>Quick workflow:</strong> Paste Spanish drill → Click Translate → Copy result → Click "Clear & New" for next drill
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        st.subheader("🇪🇸 Spanish Drill")
        
        spanish_text = st.text_area(
            "Paste drill description:",
            height=400,
            value=st.session_state.spanish_input,
            placeholder="CONTENIDO: Control y pase\nCONSIGNA: Mejorar la precisión...",
            key="drill_spanish_input"
        )
        
        # Metrics
        if spanish_text:
            cols = st.columns(3)
            with cols[0]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="value">{len(spanish_text):,}</div>
                    <div class="label">Characters</div>
                </div>
                """, unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="value">{len(spanish_text.split()):,}</div>
                    <div class="label">Words</div>
                </div>
                """, unsafe_allow_html=True)
            with cols[2]:
                est_tokens = estimate_tokens(spanish_text, st.session_state.selected_model)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="value">{est_tokens:,}</div>
                    <div class="label">Est. Tokens</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Cost estimate
            if spanish_text.strip():
                input_tokens = estimate_tokens(
                    st.session_state.drill_prompt.format(spanish_text=spanish_text),
                    st.session_state.selected_model
                )
                output_tokens = max(len(spanish_text) // 2, 500)
                est_cost = calculate_estimated_cost(input_tokens, output_tokens, st.session_state.selected_model)
                
                st.markdown(f"""
                <div class="cost-box">
                    💰 <strong>Estimated cost:</strong> ${est_cost:.4f}
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("🇺🇸 English Translation")
        
        # Display translation using markdown in a styled container
        if st.session_state.translated_text:
            st.markdown(f'<div class="output-container">{st.session_state.translated_text}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="output-container"></div>', unsafe_allow_html=True)
        
        # Output actions
        if st.session_state.translated_text:
            cols = st.columns(2)
            with cols[0]:
                # Use a hidden text area that can be copied
                st.text_area(
                    "Copy from here:",
                    value=st.session_state.translated_text,
                    height=0,
                    key="drill_copy_field",
                    label_visibility="collapsed"
                )
                st.markdown("**👆 Select text above and copy (Ctrl+C / Cmd+C)**")
            with cols[1]:
                st.download_button(
                    "💾 Download",
                    data=st.session_state.translated_text,
                    file_name=f"drill_translation_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("🗑️ Clear Both", use_container_width=True, key="clear_drill"):
            st.session_state.spanish_input = ""
            st.session_state.translated_text = ""
            st.rerun()
    
    with col2:
        if st.button("🚀 TRANSLATE DRILL", type="primary", use_container_width=True, key="translate_drill"):
            if client and spanish_text:
                with st.spinner("Translating..."):
                    translation, error = translate_text(
                        client, 
                        spanish_text, 
                        st.session_state.drill_prompt,
                        st.session_state.selected_model
                    )
                    if translation:
                        st.session_state.translated_text = translation
                        st.session_state.spanish_input = spanish_text
                        st.success("✅ Translation complete!")
                        st.balloons()
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ Translation failed: {error}")
            elif not spanish_text:
                st.warning("⚠️ Please enter Spanish text first")
    
    with col3:
        if st.session_state.translated_text and st.button("📋 Clear & New", use_container_width=True, key="copy_new_drill"):
            st.session_state.spanish_input = ""
            st.session_state.translated_text = ""
            st.success("✅ Ready for next drill")
            time.sleep(0.5)
            st.rerun()

# GENERAL TRANSLATION TAB
with tab2:
    st.markdown("""
    <div class="info-box">
        📌 <strong>General Translation Mode:</strong> For any soccer-related content without strict formatting requirements.
        Perfect for emails, articles, general instructions, or informal content.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        st.subheader("🇪🇸 Spanish Text")
        
        general_spanish = st.text_area(
            "Enter any Spanish text:",
            height=400,
            value=st.session_state.general_spanish_input,
            placeholder="Enter any Spanish soccer content here...",
            key="general_spanish_input_field"
        )
        
        # Metrics
        if general_spanish:
            cols = st.columns(2)
            with cols[0]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="value">{len(general_spanish):,}</div>
                    <div class="label">Characters</div>
                </div>
                """, unsafe_allow_html=True)
            with cols[1]:
                est_tokens = estimate_tokens(general_spanish, st.session_state.selected_model)
                est_cost = calculate_estimated_cost(est_tokens, est_tokens//2, st.session_state.selected_model)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="value">${est_cost:.4f}</div>
                    <div class="label">Est. Cost</div>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("🇺🇸 English Translation")
        
        # Display translation using markdown in a styled container
        if st.session_state.general_translated_text:
            st.markdown(f'<div class="output-container">{st.session_state.general_translated_text}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="output-container"></div>', unsafe_allow_html=True)
        
        if st.session_state.general_translated_text:
            st.text_area(
                "Copy from here:",
                value=st.session_state.general_translated_text,
                height=0,
                key="general_copy_field",
                label_visibility="collapsed"
            )
            st.markdown("**👆 Select text above and copy (Ctrl+C / Cmd+C)**")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_general"):
            st.session_state.general_spanish_input = ""
            st.session_state.general_translated_text = ""
            st.rerun()
    
    with col2:
        if st.button("🚀 TRANSLATE", type="primary", use_container_width=True, key="translate_general"):
            if client and general_spanish:
                with st.spinner("Translating..."):
                    translation, error = translate_text(
                        client,
                        general_spanish,
                        st.session_state.general_prompt,
                        st.session_state.selected_model
                    )
                    if translation:
                        st.session_state.general_translated_text = translation
                        st.session_state.general_spanish_input = general_spanish
                        st.success("✅ Translation complete!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ Translation failed: {error}")
            elif not general_spanish:
                st.warning("⚠️ Please enter Spanish text first")
    
    with col3:
        if st.session_state.general_translated_text:
            st.download_button(
                "💾 Download",
                data=st.session_state.general_translated_text,
                file_name=f"translation_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )

# SETTINGS TAB
with tab3:
    st.subheader("⚙️ Translation Settings")
    
    # Model selection
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_model = st.selectbox(
            "🤖 AI Model",
            options=list(CLAUDE_MODELS.keys()),
            format_func=lambda x: CLAUDE_MODELS[x],
            index=list(CLAUDE_MODELS.keys()).index(st.session_state.selected_model),
            help="Sonnet 4.5 recommended for best performance"
        )
        
        if selected_model != st.session_state.selected_model:
            st.session_state.selected_model = selected_model
    
    with col2:
        costs = get_model_cost_per_token(st.session_state.selected_model)
        st.markdown(f"""
        <div class="info-box">
            <strong>Pricing:</strong><br>
            Input: ${costs['input']:.2f}/1M<br>
            Output: ${costs['output']:.2f}/1M
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Prompt Management
    st.subheader("📝 Prompt Templates")
    
    tab_prompt1, tab_prompt2 = st.tabs(["Drill Prompt", "General Prompt"])
    
    with tab_prompt1:
        st.markdown("Edit the drill translation prompt template:")
        
        # Show current vs saved status
        if st.session_state.drill_prompt != st.session_state.saved_drill_prompt:
            st.warning("⚠️ You have unsaved changes to the drill prompt")
        else:
            st.success("✅ Using saved drill prompt")
        
        # Prompt editor
        edited_drill_prompt = st.text_area(
            "Drill Translation Prompt:",
            value=st.session_state.drill_prompt,
            height=300,
            key="drill_prompt_editor"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Save as Default", use_container_width=True, key="save_drill_prompt"):
                st.session_state.drill_prompt = edited_drill_prompt
                st.session_state.saved_drill_prompt = edited_drill_prompt
                st.success("✅ Drill prompt saved as default!")
                st.rerun()
        
        with col2:
            if st.button("↩️ Revert to Saved", use_container_width=True, key="revert_drill_prompt"):
                st.session_state.drill_prompt = st.session_state.saved_drill_prompt
                st.success("✅ Reverted to saved prompt")
                st.rerun()
        
        with col3:
            if st.button("🔄 Reset to Original", use_container_width=True, key="reset_drill_prompt"):
                st.session_state.drill_prompt = get_default_drill_prompt()
                st.session_state.saved_drill_prompt = get_default_drill_prompt()
                st.success("✅ Reset to original prompt")
                st.rerun()
    
    with tab_prompt2:
        st.markdown("Edit the general translation prompt template:")
        
        # Show current vs saved status
        if st.session_state.general_prompt != st.session_state.saved_general_prompt:
            st.warning("⚠️ You have unsaved changes to the general prompt")
        else:
            st.success("✅ Using saved general prompt")
        
        # Prompt editor
        edited_general_prompt = st.text_area(
            "General Translation Prompt:",
            value=st.session_state.general_prompt,
            height=300,
            key="general_prompt_editor"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Save as Default", use_container_width=True, key="save_general_prompt"):
                st.session_state.general_prompt = edited_general_prompt
                st.session_state.saved_general_prompt = edited_general_prompt
                st.success("✅ General prompt saved as default!")
                st.rerun()
        
        with col2:
            if st.button("↩️ Revert to Saved", use_container_width=True, key="revert_general_prompt"):
                st.session_state.general_prompt = st.session_state.saved_general_prompt
                st.success("✅ Reverted to saved prompt")
                st.rerun()
        
        with col3:
            if st.button("🔄 Reset to Original", use_container_width=True, key="reset_general_prompt"):
                st.session_state.general_prompt = get_default_general_prompt()
                st.session_state.saved_general_prompt = get_default_general_prompt()
                st.success("✅ Reset to original prompt")
                st.rerun()
    
    st.markdown("---")
    
    # Cache Management
    st.subheader("💾 Cache Management")
    
    col1, col2 = st.columns(2)
    with col1:
        cache_size = len(st.session_state.translation_cache)
        st.metric("Cached Translations", cache_size)
    
    with col2:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.session_state.translation_cache = {}
            st.success("✅ Cache cleared!")
            st.rerun()

# HISTORY TAB
with tab4:
    st.subheader("📚 Translation History")
    
    if st.session_state.translation_history:
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        
        total_translations = len(st.session_state.translation_history)
        total_tokens = sum(
            safe_get(t, 'input_tokens', 0) + safe_get(t, 'output_tokens', 0) 
            for t in st.session_state.translation_history
        )
        total_cost = sum(
            calculate_estimated_cost(
                safe_get(t, 'input_tokens', 0),
                safe_get(t, 'output_tokens', 0),
                safe_get(t, 'model', 'claude-sonnet-4-5-20250929')
            ) for t in st.session_state.translation_history
        )
        drill_count = len([t for t in st.session_state.translation_history if safe_get(t, 'type') == 'drill'])
        
        with col1:
            st.metric("Total Translations", total_translations)
        with col2:
            st.metric("Drill Translations", drill_count)
        with col3:
            st.metric("Total Tokens", f"{total_tokens:,}")
        with col4:
            st.metric("Total Cost", f"${total_cost:.3f}")
        
        st.markdown("---")
        
        # Search and filter
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_query = st.text_input("🔍 Search history", placeholder="Search translations...")
        
        with col2:
            filter_type = st.selectbox("Type", ["All", "Drill", "General"])
        
        with col3:
            filter_date = st.date_input("Date", value=None)
        
        # Filter history
        filtered_history = st.session_state.translation_history.copy()
        
        if search_query:
            search_lower = search_query.lower()
            filtered_history = [
                h for h in filtered_history 
                if search_lower in safe_get(h, 'spanish_input', '').lower() 
                or search_lower in safe_get(h, 'english_output', '').lower()
            ]
        
        if filter_type != "All":
            type_filter = filter_type.lower()
            filtered_history = [
                h for h in filtered_history 
                if safe_get(h, 'type', 'drill') == type_filter
            ]
        
        if filter_date:
            date_str = str(filter_date)
            filtered_history = [
                h for h in filtered_history 
                if safe_get(h, 'timestamp', '').startswith(date_str)
            ]
        
        # Export buttons
        st.markdown("### 📥 Export Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            json_data = json.dumps(filtered_history, indent=2, ensure_ascii=False)
            st.download_button(
                "📄 Export as JSON",
                data=json_data,
                file_name=f"translations_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            if filtered_history:
                output = io.StringIO()
                fieldnames = ['timestamp', 'type', 'model', 'input_tokens', 'output_tokens']
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(filtered_history)
                csv_data = output.getvalue()
                
                st.download_button(
                    "📊 Export as CSV",
                    data=csv_data,
                    file_name=f"translations_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col3:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.translation_history = []
                st.success("✅ History cleared!")
                st.rerun()
        
        # Display history items
        st.markdown("### 📋 Recent Translations")
        st.info(f"Showing {len(filtered_history)} of {total_translations} translations")
        
        for i, item in enumerate(reversed(filtered_history[-10:])):
            timestamp = safe_get(item, 'timestamp', 'Unknown')
            trans_type = safe_get(item, 'type', 'drill').capitalize()
            spanish_preview = safe_get(item, 'spanish_input', '')[:100]
            tokens = safe_get(item, 'input_tokens', 0) + safe_get(item, 'output_tokens', 0)
            
            with st.expander(f"**{trans_type}** • {timestamp} • {tokens:,} tokens"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Spanish Input:**")
                    st.text_area(
                        "Spanish", 
                        value=safe_get(item, 'spanish_input', ''),
                        height=200,
                        disabled=True,
                        key=f"hist_spanish_{i}"
                    )
                
                with col2:
                    st.markdown("**English Output:**")
                    st.text_area(
                        "English",
                        value=safe_get(item, 'english_output', ''),
                        height=200,
                        disabled=True,
                        key=f"hist_english_{i}"
                    )
                
                # Load button
                if trans_type.lower() == 'drill':
                    if st.button(f"📂 Load into Drill Translator", key=f"load_drill_{i}"):
                        st.session_state.spanish_input = safe_get(item, 'spanish_input', '')
                        st.session_state.translated_text = safe_get(item, 'english_output', '')
                        st.success("✅ Loaded into Drill Translator!")
                        st.rerun()
                else:
                    if st.button(f"📂 Load into General Translator", key=f"load_general_{i}"):
                        st.session_state.general_spanish_input = safe_get(item, 'spanish_input', '')
                        st.session_state.general_translated_text = safe_get(item, 'english_output', '')
                        st.success("✅ Loaded into General Translator!")
                        st.rerun()
    else:
        st.info("No translation history yet. Start translating to build your history!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 0.875rem; padding: 1rem;">
    CV Spanish Translator • Powered by Claude AI • 
    <span style="color: #5B47E0;">Model:</span> {model}
</div>
""".format(model=CLAUDE_MODELS[st.session_state.selected_model].split('(')[0].strip()), 
unsafe_allow_html=True)
