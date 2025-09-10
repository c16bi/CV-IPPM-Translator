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
<example>
<SPANISH_DRILL_DESCRIPTION>
Fase Activación: Chunks
BLOQUE: Fundamento básico individual con balón.
CONTENIDO: Centro
CONSIGNA: Superar la posición de los primeros defensores, ya sea el centro por arriba o por abajo.
DIA MICROCICLO: Cualquier día.
TIEMPO: 3 series de 4 minutos.
ESPACIO: 60 x 25 m cada tarea. 20 x 25 metros cada zona.
ORIENTACIÓN CONDICIONAL: Tensión
Nº JUGADORES: 18 jugadores en tarea. 2 equipos de 8 jugadores + dos porteros.
MATERIAL: Conos, balones, 8 petos y 2 porterías.
DESCRIPCIÓN: La segunda tarea de la sesión se desarrolla a través de chunks. El terreno de juego está dividido en dos espacios diferenciados, donde se llevan a cabo simultáneamente dos tareas paralelas. Cada una está compuesta por dos equipos de cuatro jugadores y estructurada en tres zonas consecutivas.
La acción comienza siempre en la Zona 1 (Z1), donde se disputa un 3 contra 3. Mientras tanto, un jugador de cada equipo permanece en espera en la Zona 2 (Z2), preparado para intervenir. El objetivo principal consiste en superar la primera zona mediante combinaciones o acciones individuales para alcanzar la portería y finalizar, evitando que el equipo rival recupere o intercepte el balón durante la progresión.

NORMATIVAS:  Atacantes: I) El jugador situado en Z2 pude ocupar la Z1 con el objetivo de ayudar a superar las zonas mediante la posesión de balón. II) Si la zona 2 está libre, esta puede ser ocupada por cualquier jugador mediante un pase. No obstante, si la zona 2 está ocupada, se debe ocupar la zona 3 de forma directa, a través de un centro, pudiéndote apoyar en el jugador de la zona 2 si es necesario. III) En el momento que el equipo rival intercepta el balón, se reinicia la acción o finalizan a portería si el balón está en juego.
Defensores: I) En todo momento se debe respetar la ubicación en cada zona. II) El jugador defensor ubicado en Z2 puede seguir al jugador atacante que ocupe la zona 1.
PUNTUACIÓN:

- Por cada gol realizado por cada uno de los equipos, estos obtienen un punto. Si el gol viene precedido de un centro, este tiene un valor doble.
GRADIENTE:
(+) Introducir un comodín, facilitando el dinamismo de la tarea y una mayor circulación de balón.
(-) Limitar el comportamiento del jugador en defensor en Z2, obligando a mantenerse en dicha zona.
</SPANISH_DRILL_DESCRIPTION>
<ideal_output>
<content_breakdown>
Analyzing the Spanish content systematically:

Topic/skill focus: "CONTENIDO: Centro" clearly indicates this drill focuses on crossing. The header "Fase Activación: Chunks" shows this is an activation phase drill using chunks methodology.

Technical instruction: "CONSIGNA: Superar la posición de los primeros defensores, ya sea el centro por arriba o por abajo" provides the key principle - beat the position of first defenders with crosses delivered either high or low.

Timing and players: "DIA MICROCICLO: Cualquier día" indicates any day in the training cycle. "TIEMPO: 3 series de 4 minutos" means three 4-minute sets. "Nº JUGADORES: 18 jugadores en tarea. 2 equipos de 8 jugadores + dos porteros" shows 18 players total, with two teams of 8 players plus two goalkeepers.

Physical focus: "ORIENTACIÓN CONDICIONAL: Tensión" indicates tension/intensity as the physical focus.

Space/equipment: "ESPACIO: 60 x 25 m cada tarea. 20 x 25 metros cada zona" needs conversion - approximately 60 x 25 yards per exercise, 20 x 25 yards per zone. "MATERIAL: Conos, balones, 8 petos y 2 porterías" lists cones, balls, eight bibs, and two goals.

Main drill description: The "DESCRIPCIÓN" explains this is developed through chunks with the playing area divided into two separate spaces running parallel exercises simultaneously. Each has two teams of four players structured in three consecutive zones. Action begins in Zone 1 (Z1) with 3v3, while one player from each team waits in Zone 2 (Z2). The objective is to overcome the first zone through combinations or individual actions to reach the goal.

Rules: "NORMATIVAS" outlines that attacking players in Z2 can occupy Z1 to help, if Z2 is free it can be occupied by any player via pass, but if Z2 is occupied then Z3 must be occupied directly through a cross. Defenders must respect zone locations, and the Z2 defender can follow attackers who occupy Z1.

Scoring: "PUNTUACIÓN: Por cada gol realizado por cada uno de los equipos, estos obtienen un punto. Si el gol viene precedido de un centro, este tiene un valor doble" - each goal scores one point, but goals from crosses score double.

GRADIENTE section: "(+) Introducir un comodín" suggests adding a neutral player as progression, "(-) Limitar el comportamiento del jugador en defensor en Z2" suggests limiting the Z2 defender's movement as regression.

No special drill type indicators present beyond "Activación".

All sections provide clear information that can be directly translated.
</content_breakdown>

**Topic**
Crossing

**Principle** 
Beat the position of the first defenders, whether the cross is delivered high or low

**Microcycle day**
Any day

**Time**
Three x four-minute blocks

**Players**
18

**Physical focus**
Tension

**Space/equipment**
60 yards x 25 yards per exercise. 20 yards x 25 yards per zone/Cones, balls, eight bibs, two goals

**Description**
The second exercise of the session is developed through chunks. The playing area is divided into two separate spaces where two parallel exercises take place simultaneously. Each is composed of two teams of four players and structured in three consecutive zones.
The action always begins in Zone 1 (Z1), where a three vs three is contested. Meanwhile, one player from each team remains waiting in Zone 2 (Z2), ready to intervene. The main objective is to overcome the first zone through combinations or individual actions to reach the goal and finish, preventing the opposing team from recovering or intercepting the ball during progression. 
Attackers: The player positioned in Z2 can occupy Z1 with the objective of helping to overcome the zones through ball possession. If zone two is free, it can be occupied by any player through a pass. However, if zone two is occupied, zone three must be occupied directly through a cross, with support from the zone two player if necessary. When the opposing team intercepts the ball, the action restarts or they finish at goal if the ball is in play. 
Defenders must respect their location in each zone at all times. The defending player located in Z2 can follow the attacking player who occupies zone one. Each goal scored by either team earns one point. If the goal comes from a cross, it has double value.

**Progressions**
- More advanced: Introduce a neutral player, facilitating the dynamism of the exercise and greater ball circulation
- Simplified: Limit the behaviour of the defending player in Z2, forcing them to remain in that zone

**Coaching points**
- Cross delivery: Players should be encouraged to deliver crosses that beat the first line of defenders through height and placement
- Zone occupation: Attackers should time their movement into zones to create numerical advantages and crossing opportunities  
- Support play: Players should provide effective support from Z2 when crosses are delivered into the final zone
</ideal_output>
</example>
<example>
<SPANISH_DRILL_DESCRIPTION>
Sub-Fase Principal: Juego de invasión discontinua
BLOQUE: Fundamento básico individual con balón.
CONTENIDO: Centro
CONSIGNA: Superar la posición de los primeros defensores, ya sea el centro por arriba o por abajo.
DIA MICROCICLO: Cualquier día.
TIEMPO: 3 series de 5 minutos.
ESPACIO: 55 x 35 metros. Dos zonas de 27 x 17 m. 3 carriles, dos laterales de 55 x 8 metros y un carril central de 55 x 20 metros.
ORIENTACIÓN CONDICIONAL: Tensión
Nº JUGADORES: 18 jugadores por tarea. 2 equipos de 7 jugadores + 2 porteros
MATERIAL: Conos, balones, 8 petos y 2 porterías.
DESCRIPCIÓN: La tercera tarea de la sesión se plantea como un juego de invasión discontinua con una unidad de competición, por lo tanto, están implicadas las 3 fases del juego. Ambos equipos se estructuran 3-3-2. Se observan dos zonas distintas (Z1, Z2) y tres carriles distintos, dos carriles laterales (CL) y un carril central (CC). El objetivo es circular el balón hasta alguno de los carriles laterales para realizar un centro e intentar finalizar a portería con gol.
NORMATIVAS:
Atacantes: I) En todo momento, solo pueden ocupar cada carril lateral dos jugadores como máximo. II) En el momento que un jugador recibe el balón en un carril lateral, en zona de finalización (Z1 para los naranjas y Z2 para los blancos) estos deben centrar con intención para intentar marcar gol. III) En el momento que un jugador recibe el balón en carril lateral en zona de finalización, un jugador del mismo equipo puede ayudar a generar superioridad numérica en el mismo carril, para centrar el balón al área.

Defensores: I) Únicamente un jugador puede ocupar cualquier carril lateral de forma simultánea.

PUNTUACIÓN:

- Cada acción que finaliza con gol, suma un punto para el equipo en cuestión. No obstante, si el gol viene procedido de un centro en el carril lateral, este tiene un valor doble.

GRADIENTE:

(+) Eliminar la normativa de los defensores referente al número de jugadores que pueden ocupar cada carril. De esta forma, se darán situaciones mucho más similares al partido, con necesidad de desborde o con mayor velocidad gestual y de reacción, por lo tanto, aumentando la especificidad de la acción.

(-) Introducir dos comodines con la función de dinamizadores, de esta forma, habrá una mayor circulación de balón, más espacios y, de forma consecuente, se darán más centros.
</SPANISH_DRILL_DESCRIPTION>
<ideal_output>
<content_breakdown>
Systematically analyzing the Spanish content:

Topic/skill focus: "CONTENIDO: Centro" clearly identifies crossing as the main skill focus. The header "Sub-Fase Principal: Juego de invasión discontinua" indicates this is a main phase drill using discontinuous invasion game format.

Technical instruction: "CONSIGNA: Superar la posición de los primeros defensores, ya sea el centro por arriba o por abajo" provides the same principle as previous drills - beat first defenders with high or low crosses.

Timing and players: "DIA MICROCICLO: Cualquier día" means any day in the training cycle. "TIEMPO: 3 series de 5 minutos" translates to three 5-minute sets. "Nº JUGADORES: 18 jugadores por tarea. 2 equipos de 7 jugadores + 2 porteros" indicates 18 players per exercise, with two teams of 7 players plus 2 goalkeepers.

Physical focus: "ORIENTACIÓN CONDICIONAL: Tensión" indicates tension/intensity.

Space/equipment details: "ESPACIO: 55 x 35 metros. Dos zonas de 27 x 17 m. 3 carriles, dos laterales de 55 x 8 metros y un carril central de 55 x 20 metros" requires conversion from meters to yards. 55x35m becomes approximately 55x35 yards, zones of 27x17m become approximately 27x17 yards, wide channels of 55x8m become 55x8 yards, central channel of 55x20m becomes 55x20 yards. "MATERIAL: Conos, balones, 8 petos y 2 porterías" lists cones, balls, eight bibs, two goals.

Main drill description: "DESCRIPCIÓN" explains this is a discontinuous invasion game involving all three phases of play. Both teams use 3-3-2 formation. There are two distinct zones (Z1, Z2) and three channels - two wide channels (CL) and one central channel (CC). The objective is to circulate the ball to wide channels to deliver crosses and score.

Rules: "NORMATIVAS" outlines that attacking teams can have maximum two players in each wide channel, must cross with intent when receiving in finishing zones (Z1 for orange, Z2 for white), and can create numerical superiority in wide channels. Defenders can only have one player in any wide channel simultaneously.

Scoring system: "PUNTUACIÓN: Cada acción que finaliza con gol, suma un punto para el equipo en cuestión. No obstante, si el gol viene procedido de un centro en el carril lateral, este tiene un valor doble" - each goal scores one point, but goals from wide channel crosses score double.

GRADIENTE section: "(+) Eliminar la normativa de los defensores referente al número de jugadores que pueden ocupar cada carril" suggests removing defender channel restrictions as progression. "(-) Introducir dos comodines con la función de dinamizadores" suggests adding two neutral playmaker players as regression.

No special drill type indicators beyond the main phase designation.

All information is clearly provided and can be translated without significant interpretation needed.
</content_breakdown>

**Topic**
Crossing

**Principle** 
Beat the position of the first defenders, whether the cross is delivered high or low

**Microcycle day**
Any day

**Time**
Three x five-minute blocks

**Players**
18

**Physical focus**
Tension

**Space/equipment**
55 yards x 35 yards. Two zones of 27 yards x 17 yards. Three channels: two wide channels of 55 yards x eight yards and one central channel of 55 yards x 20 yards/Cones, balls, eight bibs, two goals

**Description**
The third exercise of the session is set up as a discontinuous invasion game with a competitive unit, therefore involving all three phases of play. Both teams are structured 3-3-2. Two distinct zones are observed (Z1, Z2) and three different channels: two wide channels (WC) and one central channel (CC). The objective is to circulate the ball to one of the wide channels to deliver a cross and attempt to finish at goal. 
Attackers: Only a maximum of two players can occupy each wide channel at any time. When a player receives the ball in a wide channel in the finishing zone (Z1 for orange team and Z2 for white team), they must cross with intent to try to score. When a player receives the ball in a wide channel in the finishing zone, a teammate can help create numerical superiority in the same channel to cross the ball into the area.
Defenders: Only one player can occupy any wide channel simultaneously.
Each action that finishes with a goal scores one point for the team. However, if the goal comes from a cross in the wide channel, it has double value.

**Progressions**
- More advanced: Remove the defensive rule regarding the number of players who can occupy each channel. This creates situations much more similar to a match, with the need for dribbling or greater speed and reaction, therefore increasing the specificity of the action
- Simplified: Introduce two neutral players with the function of playmakers, creating greater ball circulation, more space and consequently more crosses

**Coaching points**
- Channel occupation: Players should be encouraged to time their movement into wide channels to create crossing opportunities
- Cross quality: Crosses should beat the first defender and be delivered with the right weight and trajectory for teammates
- Numerical advantages: Players should create and exploit numerical superiority in wide channels to improve crossing success
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

## Special Instructions

1. **First drill handling:** If the Spanish content indicates this is the first drill in a session (words like "activación" or "calentamiento"), title it "Warm-up Circuit"

2. **Progressions format:** The Spanish "GRADIENTE" section with (+) and (-) should become "More advanced:" and "Simplified:" respectively

3. **Coaching points format:** Each coaching point should start with a brief descriptive title followed by a colon, then the detailed instruction

4. **Empty response prevention:** Always provide a complete translation following the format above. If any section is unclear in the Spanish, make reasonable interpretations based on football coaching context rather than leaving sections blank.

Before providing your final translation, systematically analyze the Spanish content in <content_breakdown> tags:
- Quote the Spanish phrases that indicate the topic/skill focus
- Quote phrases related to timing, player numbers, and physical focus
- Quote space/equipment details and note any meter-to-yard conversions needed
- Quote the main drill description and identify key rules/scoring systems
- Quote the GRADIENTE section (if present) and identify (+) and (-) elements
- Quote coaching instruction phrases and identify key teaching points
- Note any special drill type indicators (activación, calentamiento, etc.)
- Identify any sections where information appears to be missing and will need reasonable interpretation

It's OK for this section to be quite long. Then provide your complete translation following the format above."""

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
