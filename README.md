# CV-IPPM-Translator

A specialized tool for translating Spanish football/soccer coaching session plans into standardized English format for Coaches' Voice.

## Overview

This translator converts detailed Spanish drill descriptions into clear, practical English coaching formats. It streamlines the process of curating session plans by automatically organizing content into standardized sections that coaches can easily understand and implement.

## Features

- Translates Spanish football drill descriptions to English
- Standardizes output format for consistency
- Focuses on coach-friendly language over literal translation
- Automatically converts measurements (meters to yards)
- Organizes content into structured sections:
  - Topic and principle
  - Time, players, and equipment
  - Detailed description
  - Progressions (advanced/simplified)
  - Coaching points

## Input Format

The tool expects Spanish drill descriptions containing these sections:
- **CONTENIDO**: Skill focus (e.g., "Control y pase", "Centro")
- **CONSIGNA**: Technical principles
- **TIEMPO**: Duration and sets
- **ESPACIO**: Field dimensions and zones
- **Nº JUGADORES**: Number of players
- **DESCRIPCIÓN**: Detailed drill explanation
- **NORMATIVAS**: Rules for attackers and defenders
- **GRADIENTE**: Difficulty progressions (+) and regressions (-)

## Output Format

Translated drills follow this structure:

```
**Topic**
[Main skill focus]

**Principle**
[Key technical instruction]

**Microcycle day**
[Training cycle timing]

**Time**
[Duration and repetitions]

**Players**
[Number of participants]

**Physical focus**
[Conditioning aspect]

**Space/equipment**
[Field setup and materials needed]

**Description**
[Complete drill explanation with rules]

**Progressions**
- More advanced: [Harder variation]
- Simplified: [Easier variation]

**Coaching points**
- [Title]: [Detailed instruction]
- [Title]: [Detailed instruction]
- [Title]: [Detailed instruction]
```

## Usage

1. Copy the Spanish drill description
2. Paste into the translator
3. Copy the formatted English output
4. Use in Coaches' Voice session plans

## Technical Implementation

Built using:
- Anthropic Claude API for translation
- Custom prompt engineering for football-specific terminology
- Structured output formatting for consistency

## Setup

1. Clone the repository
2. Set your Anthropic API key
3. Deploy to your preferred platform (Streamlit Cloud recommended)

## API Configuration

The translator uses Claude 3.7 Sonnet with:
- Temperature: 1.0
- Max tokens: 20904
- Specialized system prompts for football coaching context

## Contributing

This tool is designed specifically for Coaches' Voice session plan translation workflow. Modifications should maintain the standardized output format for consistency across all translated drills.
