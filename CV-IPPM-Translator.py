import streamlit as st
import anthropic
from datetime import datetime
import time

# Set up the page
st.set_page_config(page_title="CV Spanish Drill Translator", layout="wide")
st.title("CV Spanish Drill Translator")

# Initialize session state for history and translation
if 'translation_history' not in st.session_state:
    st.session_state.translation_history = []
if 'translated_text' not in st.session_state:
    st.session_state.translated_text = ""

# Sidebar for history
with st.sidebar:
    st.header("Translation History")
    
    if st.session_state.translation_history:
        st.write(f"Total translations: {len(st.session_state.translation_history)}")
        
        # Show recent translations
        for i, translation in enumerate(reversed(st.session_state.translation_history[-10:])):
            with st.expander(f"Translation {len(st.session_state.translation_history) - i} - {translation['timestamp'][:16]}"):
                st.write("**Spanish (first 100 chars):**")
                st.text(translation['spanish_input'][:100] + "..." if len(translation['spanish_input']) > 100 else translation['spanish_input'])
                
                if st.button(f"Load Translation {len(st.session_state.translation_history) - i}", key=f"load_{i}"):
                    st.session_state.loaded_spanish = translation['spanish_input']
                    st.session_state.translated_text = translation['english_output']
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
    
    english_output = st.text_area(
        "English translation will appear here:",
        height=600,
        value=st.session_state.translated_text,
        key="english_output",
        help="Copy this formatted translation for use in Coaches' Voice"
    )

# Clear loaded history after displaying
if 'loaded_spanish' in st.session_state:
    del st.session_state.loaded_spanish

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
    log_placeholder = st.empty()

if translate_button and api_ready:
    if spanish_text.strip():
        start_time = time.time()
        
        with st.spinner("Translating..."):
            try:
                # Prepare the full prompt with your exact structure
                full_prompt = f"""<examples>
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
<content_breakdown>
Looking at the Spanish content systematically:

Topic/skill focus: "CONTENIDO: Control y pase" clearly indicates this drill focuses on control and passing skills. The header "Sub-fase Activación: Rondo condicional" suggests this is an activation phase drill using a conditional rondo format.

Technical instruction: The "CONSIGNA" section provides detailed technical guidance: "Control: Con el pie de apoyo y utilizando un solo contacto con el suelo, salir en la dirección hacia donde se ha orientado el control. Pase: Usar el interior del pie para la corta y media distancia, y el empeine para la larga distancia" - this gives specific instructions for both control technique (support foot, single contact, direction) and passing technique (inside foot for short/medium, instep for long distance).

Timing and players: "DIA MICROCICLO: Cualquier día" means any day in the training cycle. "TIEMPO: 2 series de 5 minutos" translates to two 5-minute sets. "Nº JUGADORES: 18 jugadores en total. 9 jugadores en cada equipo" indicates 18 total players, 9 per team.

Physical focus: "ORIENTACIÓN CONDICIONAL: Tensión" indicates the physical focus is tension/intensity.

Space/equipment: "ESPACIO: 1 rondo de mayores dimensiones, 8 x 8 metros. Dos rondos más pequeños de 4 x 4 metros" needs conversion from meters to yards (8x8 meters = approximately 9x9 yards, 4x4 meters = approximately 4.5x4.5 yards, but I'll round to 8x8 and 4x4 yards for practical coaching purposes). "MATERIAL: Conos, balones y dos porterías pequeñas" lists cones, balls, and two small goals.

Main drill description: The "DESCRIPCIÓN" section explains this is a rondo-based exercise with one offensive team and one defensive team, structured with a main larger rondo (4 attackers) and two smaller secondary rondos (3 players each). The action starts 4v2 in the main rondo, and when defenders recover the ball, they move to the smaller rondos with the same objective, finishing with a shot if they recover again.

Rules: The "NORMATIVAS" section outlines specific rules for attackers (stay in designated zones, ball leaving zone = defensive recovery) and defenders (can't start action until both recover ball in both rondos, coach plays ball if interception occurs without possession).

Scoring: "PUNTUACIÓN: Cada serie un equipo obtiene un rol distinto. Se compite por número de goles" indicates teams switch roles each set and compete based on goals scored.

GRADIENTE section: "(+) Limitar el número de contactos" suggests limiting touches as progression, while "(-) Aumentar las dimensiones de juego" suggests increasing dimensions as regression.

Special indicators: "Sub-fase Activación" indicates this is an activation/warm-up phase drill.

All sections have clear information that can be translated without needing significant interpretation.
</content_breakdown>

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

Before providing your final translation, systematically analyze the Spanish content in <content_breakdown> tags."""
                
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
                
                # Update logging
                with log_placeholder.container():
                    st.write("**📤 API Request:**")
                    st.write(f"**Model:** claude-3-7-sonnet-20250219")
                    st.write(f"**Max Tokens:** 20904")
                    st.write(f"**Temperature:** 1")
                    st.write(f"**Request Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    st.write("**📥 API Response:**")
                    st.write(f"**Response Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Duration:** {end_time - start_time:.2f} seconds")
                    st.write(f"**Input Tokens:** {message.usage.input_tokens}")
                    st.write(f"**Output Tokens:** {message.usage.output_tokens}")
                    st.write(f"**Total Tokens:** {message.usage.input_tokens + message.usage.output_tokens}")
                    
                    with st.expander("View Full Response"):
                        st.text(english_translation)
                
                # Update the translated text in session state
                st.session_state.translated_text = english_translation
                
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
                with log_placeholder.container():
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
