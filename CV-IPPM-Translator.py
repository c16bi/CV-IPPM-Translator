import streamlit as st
import anthropic

# Set up the page
st.title("CV Spanish Drill Translator")
st.write("Translate Spanish football drill descriptions into standardized English coaching format")

# Get API key from secrets
try:
    client = anthropic.Anthropic(
        api_key=st.secrets["ANTHROPIC_API_KEY"]
    )
except KeyError:
    st.error("API key not found. Please set ANTHROPIC_API_KEY in Streamlit secrets.")
    st.stop()

# Input area for Spanish text
spanish_text = st.text_area(
    "Paste your Spanish drill description here:",
    height=300,
    placeholder="Paste the Spanish drill content here..."
)

# Translate button
if st.button("Translate", type="primary"):
    if spanish_text.strip():
        with st.spinner("Translating..."):
            try:
                # Your existing API call with the Spanish text inserted
                message = client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=20904,
                    temperature=1,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"<examples>\n<example>\n<SPANISH_DRILL_DESCRIPTION>\n{spanish_text}\n</SPANISH_DRILL_DESCRIPTION>\n</example>\n</examples>\n\nYou are a specialized translator for football/soccer coaching content..."  # Your full prompt here
                                }
                            ]
                        },
                        {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "<content_breakdown>"}]
                        }
                    ]
                )
                
                # Display the result
                st.text_area(
                    "English Translation:",
                    value=message.content[0].text,
                    height=500
                )
                
            except Exception as e:
                st.error(f"Translation failed: {str(e)}")
    else:
        st.warning("Please enter some Spanish text to translate.")
