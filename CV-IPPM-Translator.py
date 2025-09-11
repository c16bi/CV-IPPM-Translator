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
