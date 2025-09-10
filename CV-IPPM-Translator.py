import streamlit as st
import anthropic
import json
from datetime import datetime
import time

# Set up the page
st.set_page_config(page_title="CV Spanish Drill Translator", layout="wide")
st.title("CV Spanish Drill Translator")

# Initialize session state for history
if 'translation_history' not in st.session_state:
    st.session_state.translation_history = []

# Sidebar for history
with st.sidebar:
    st.header("Translation History")
    
    if st.session_state.translation_history:
        st.write(f"Total translations: {len(st.session_state.translation_history)}")
        
        # Show recent translations
        for i, translation in enumerate(reversed(st.session_state.translation_history[-10:])):  # Last 10
            with st.expander(f"Translation {len(st.session_state.translation_history) - i} - {translation['timestamp'][:16]}"):
                st.write("**Spanish (first 100 chars):**")
                st.text(translation['spanish_input'][:100] + "..." if len(translation['spanish_input']) > 100 else translation['spanish_input'])
                
                if st.button(f"Load Translation {len(st.session_state.translation_history) - i}", key=f"load_{i}"):
                    st.session_state.loaded_spanish = translation['spanish_input']
                    st.session_state.loaded_english = translation['english_output']
                    st.rerun()
        
        if st.button("Clear History"):
            st.session_state.translation_history = []
            st.rerun()
    else:
        st.write("No translations yet")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Spanish Input")
    
    # Load from history if available
    default_spanish = st.session_state.get('loaded_spanish', '')
    
    spanish_text = st.text_area(
        "Paste your Spanish drill description here:",
        height=600,
        value=default_spanish,
        key="spanish_input",
        placeholder="Paste the Spanish drill content here...",
        help="Copy and paste the complete Spanish drill description"
    )
    
    # Character count
    if spanish_text:
        st.caption(f"Character count: {len(spanish_text)}")

with col2:
    st.header("English Output")
    
    # Load from history if available
    default_english = st.session_state.get('loaded_english', '')
    
    english_output = st.text_area(
        "English translation will appear here:",
        height=600,
        value=default_english,
        key="english_output",
        help="Copy this formatted translation for use in Coaches' Voice"
    )

# Clear loaded history after displaying
if 'loaded_spanish' in st.session_state:
    del st.session_state.loaded_spanish
if 'loaded_english' in st.session_state:
    del st.session_state.loaded_english

# API setup
try:
    client = anthropic.Anthropic(
        api_key=st.secrets["ANTHROPIC_API_KEY"]
    )
    api_ready = True
except KeyError:
    st.error("API key not found. Please set ANTHROPIC_API_KEY in Streamlit secrets.")
    api_ready = False

# Translate button
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

with col_btn2:
    translate_button = st.button("🔄 Translate", type="primary", use_container_width=True)

# Logging expander
with st.expander("🔍 API Call Logs", expanded=False):
    log_container = st.container()

if translate_button and api_ready:
    if spanish_text.strip():
        start_time = time.time()
        
        with st.spinner("Translating..."):
            try:
                # Prepare the full prompt
                full_prompt = f"""<examples>
<example>
<SPANISH_DRILL_DESCRIPTION>
Sub-fase Activación: Rondo condicional
BLOQUE: Habilidades Motrices Específicas.
CONTENIDO: Control y pase
[... your examples here ...]
</SPANISH_DRILL_DESCRIPTION>
<ideal_output>
[... your ideal output examples ...]
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

Your translated drill must follow this exact structure with bullet points under each section:

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
- [Brief title]: [Detailed coaching instruction]

Before providing your final translation, systematically analyze the Spanish content in <content_breakdown> tags."""

                # Log the API request
                with log_container:
                    st.write("**📤 API Request:**")
                    st.write(f"**Model:** claude-3-7-sonnet-20250219")
                    st.write(f"**Max Tokens:** 20904")
                    st.write(f"**Temperature:** 1")
                    st.write(f"**Request Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    with st.expander("View Full Request Payload"):
                        request_payload = {
                            "model": "claude-3-7-sonnet-20250219",
                            "max_tokens": 20904,
                            "temperature": 1,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [{"type": "text", "text": full_prompt}]
                                },
                                {
                                    "role": "assistant",
                                    "content": [{"type": "text", "text": "<content_breakdown>"}]
                                }
                            ]
                        }
                        st.json(request_payload)
                
                # Make the API call
                message = client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=20904,
                    temperature=1,
                    messages=[
                        {
                            "role": "user",
                            "content": [{"type": "text", "text": full_prompt}]
                        },
                        {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "<content_breakdown>"}]
                        }
                    ]
                )
                
                end_time = time.time()
                
                # Extract the response
                english_translation = message.content[0].text
                
                # Log the API response
                with log_container:
                    st.write("**📥 API Response:**")
                    st.write(f"**Response Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Duration:** {end_time - start_time:.2f} seconds")
                    st.write(f"**Input Tokens:** {message.usage.input_tokens}")
                    st.write(f"**Output Tokens:** {message.usage.output_tokens}")
                    st.write(f"**Total Tokens:** {message.usage.input_tokens + message.usage.output_tokens}")
                    
                    with st.expander("View Full Response"):
                        st.text(english_translation)
                
                # Update the output text area
                st.session_state.english_output = english_translation
                
                # Add to history
                translation_entry = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'spanish_input': spanish_text,
                    'english_output': english_translation,
                    'input_tokens': message.usage.input_tokens,
                    'output_tokens': message.usage.output_tokens,
                    'duration': round(end_time - start_time, 2)
                }
                st.session_state.translation_history.append(translation_entry)
                
                st.success(f"✅ Translation completed in {end_time - start_time:.2f} seconds!")
                st.rerun()
                
            except Exception as e:
                with log_container:
                    st.write("**❌ API Error:**")
                    st.write(f"**Error Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    st.error(f"Translation failed: {str(e)}")
                    st.write("**Error Details:**")
                    st.code(str(e))
    else:
        st.warning("Please enter some Spanish text to translate.")

# Usage statistics
if st.session_state.translation_history:
    st.write("---")
    col1, col2, col3, col4 = st.columns(4)
    
    total_translations = len(st.session_state.translation_history)
    total_input_tokens = sum(t.get('input_tokens', 0) for t in st.session_state.translation_history)
    total_output_tokens = sum(t.get('output_tokens', 0) for t in st.session_state.translation_history)
    avg_duration = sum(t.get('duration', 0) for t in st.session_state.translation_history) / total_translations
    
    with col1:
        st.metric("Total Translations", total_translations)
    with col2:
        st.metric("Total Input Tokens", f"{total_input_tokens:,}")
    with col3:
        st.metric("Total Output Tokens", f"{total_output_tokens:,}")
    with col4:
        st.metric("Avg Duration", f"{avg_duration:.1f}s")
