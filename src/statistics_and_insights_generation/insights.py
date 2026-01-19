"""
LLM-based insight generation for persona data.

This module is OPTIONAL and requires an LLM provider to be configured.
It can generate personalized health insights based on the computed statistics.

The module is designed to be provider-agnostic - you can plug in any LLM
by implementing the generate_response function.
"""

import json
import pandas as pd
from typing import Dict, List, Any, Callable, Optional


def build_insight_prompt(
    persona_data: Dict[str, Any],
    statistics: Dict[str, Any],
    language: str = "en"
) -> str:
    """
    Build a prompt for LLM insight generation.

    Args:
        persona_data: Original persona JSON with daily data
        statistics: Computed statistics from statistics.py
        language: Language for insights ("en" or "de")

    Returns:
        Formatted prompt string
    """
    days = persona_data.get('days', [])
    df = pd.DataFrame(days)
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.day_name()

    # Build raw data text
    raw_data_lines = []
    for _, row in df.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        day_name = row['day_of_week']
        steps = row.get('steps', None)
        sleep = row.get('sleep_hours', None)

        steps_str = f"{steps:.0f} steps" if pd.notna(steps) else "N/A"
        sleep_str = f"{sleep:.1f}h sleep" if pd.notna(sleep) else "N/A"

        raw_data_lines.append(f"  {date_str} ({day_name}): {steps_str}, {sleep_str}")

    raw_data_text = "\n".join(raw_data_lines)

    # Extract statistics
    base = statistics.get('base_stats', {})
    corr = statistics.get('correlations', {}).get('steps_sleep', 'N/A')
    trends = statistics.get('trends', {})
    patterns = statistics.get('weekday_patterns', {})

    steps_trend = trends.get('steps', {}).get('trend', 'unknown')
    sleep_trend = trends.get('sleep', {}).get('trend', 'unknown')

    if language == "de":
        prompt = f"""Gesundheitsprofil des Nutzers:
- Persona: {persona_data.get('persona', 'Unknown')}

Rohdaten (Tag für Tag):
{raw_data_text}

Statistiken:
- Durchschnittliche Schritte: {base.get('avg_steps', 0):.0f} (Std: {base.get('steps_std', 0):.0f})
- Durchschnittlicher Schlaf: {base.get('avg_sleep', 0):.2f}h (Std: {base.get('sleep_std', 0):.2f}h)
- Korrelation Schritte/Schlaf: {corr if corr else 'N/A'}
- Schritt-Trend: {steps_trend}
- Schlaf-Trend: {sleep_trend}

Wochentagsmuster:
- Schritte Wochentag: {patterns.get('weekday_avg_steps', 0):.0f}, Wochenende: {patterns.get('weekend_avg_steps', 0):.0f}
- Schlaf Wochentag: {patterns.get('weekday_avg_sleep', 0):.2f}h, Wochenende: {patterns.get('weekend_avg_sleep', 0):.2f}h

Anweisungen:
Erstelle 5 personalisierte Gesundheits-Insights basierend auf den Daten. Die Insights sollen:
- Spezifische Muster in den täglichen Daten erkennen
- Zusammenhänge zwischen Wochentagen identifizieren
- Kurz und prägnant formuliert sein
- Einen Vertrauenswert (0-10) enthalten

Ausgabeformat (JSON-Array):
[
    {{"insight": "...", "explanation": "...", "confidence_score": 0-10}},
    ...
]"""
    else:
        prompt = f"""User Health Profile:
- Persona: {persona_data.get('persona', 'Unknown')}

Raw Data (day by day):
{raw_data_text}

Statistics:
- Average steps: {base.get('avg_steps', 0):.0f} (std: {base.get('steps_std', 0):.0f})
- Average sleep: {base.get('avg_sleep', 0):.2f}h (std: {base.get('sleep_std', 0):.2f}h)
- Steps/Sleep correlation: {corr if corr else 'N/A'}
- Steps trend: {steps_trend}
- Sleep trend: {sleep_trend}

Weekday Patterns:
- Steps weekday: {patterns.get('weekday_avg_steps', 0):.0f}, weekend: {patterns.get('weekend_avg_steps', 0):.0f}
- Sleep weekday: {patterns.get('weekday_avg_sleep', 0):.2f}h, weekend: {patterns.get('weekend_avg_sleep', 0):.2f}h

Instructions:
Generate 5 personalized health insights based on the data. Each insight should:
- Identify specific patterns in daily data
- Recognize weekday/weekend differences
- Be concise and actionable
- Include a confidence score (0-10)

Output format (JSON array):
[
    {{"insight": "...", "explanation": "...", "confidence_score": 0-10}},
    ...
]"""

    return prompt


def parse_insights_response(response: str) -> List[Dict[str, Any]]:
    """
    Parse LLM response into structured insights.

    Args:
        response: Raw LLM response string

    Returns:
        List of insight dicts with insight, explanation, confidence_score
    """
    # Clean up response
    json_str = response.strip()

    # Remove markdown code blocks if present
    if json_str.startswith("```json"):
        json_str = json_str[7:]
    elif json_str.startswith("```"):
        json_str = json_str[3:]

    if json_str.endswith("```"):
        json_str = json_str[:-3]

    json_str = json_str.strip()

    # Parse JSON
    try:
        insights_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse LLM response as JSON: {e}")
        return []

    # Validate and extract insights
    insights = []
    for item in insights_data:
        if isinstance(item, dict) and 'insight' in item:
            insights.append({
                'insight': item.get('insight', ''),
                'explanation': item.get('explanation', ''),
                'confidence_score': item.get('confidence_score', 5)
            })

    return insights


def generate_insights(
    persona_data: Dict[str, Any],
    statistics: Dict[str, Any],
    llm_function: Callable[[str], str],
    language: str = "en"
) -> List[Dict[str, Any]]:
    """
    Generate insights using a provided LLM function.

    This function is provider-agnostic. You provide the LLM call function.

    Args:
        persona_data: Original persona JSON with daily data
        statistics: Computed statistics from statistics.py
        llm_function: Function that takes a prompt string and returns LLM response
        language: Language for insights ("en" or "de")

    Returns:
        List of insight dicts

    Example:
        # Using OpenAI
        def call_openai(prompt):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

        insights = generate_insights(persona_data, stats, call_openai)
    """
    prompt = build_insight_prompt(persona_data, statistics, language)
    response = llm_function(prompt)
    return parse_insights_response(response)


def add_insights_to_statistics(
    statistics: Dict[str, Any],
    insights: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Add generated insights to statistics dict.

    Args:
        statistics: Computed statistics dict
        insights: List of insight dicts

    Returns:
        Statistics dict with insights added
    """
    result = statistics.copy()
    result['insights'] = insights
    return result


# Example usage with mock LLM (for testing)
def mock_llm_function(prompt: str) -> str:
    """Mock LLM function for testing without actual API calls."""
    return json.dumps([
        {
            "insight": "Weekend recovery pattern detected",
            "explanation": "Sleep duration increases on weekends, suggesting weekday sleep debt.",
            "confidence_score": 8
        },
        {
            "insight": "Activity levels are consistent",
            "explanation": "Step counts show low variability, indicating stable daily routine.",
            "confidence_score": 7
        },
        {
            "insight": "Negative correlation between steps and sleep",
            "explanation": "More active days tend to have slightly shorter sleep, possibly due to time constraints.",
            "confidence_score": 6
        },
        {
            "insight": "Mid-week activity dip",
            "explanation": "Wednesday shows lower step counts compared to other weekdays.",
            "confidence_score": 5
        },
        {
            "insight": "Sleep quality may need attention",
            "explanation": "Average sleep is below recommended 7-9 hours for adults.",
            "confidence_score": 9
        }
    ])
