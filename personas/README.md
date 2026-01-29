# Personas

This directory contains the three health personas used in the user study. Each persona represents a distinct behavioral profile with specific health goals, derived from real data in the [LifeSnaps dataset](https://github.com/Kaist-ICLab/LifeSnaps-Fitbit).

![Persona Comparison](/figures/persona_comparison.png)

## Persona A: Sedentary / Sleep-Deprived

A late-20s office worker with a sedentary lifestyle and chronic sleep deficit. Typically gets 5–6 hours of sleep on weeknights and attempts to catch up on weekends, but still experiences daytime tiredness.

**Health Goals:**
- Understand why they feel tired despite weekend sleep-ins
- Identify 1–2 small, realistic changes to improve activity and sleep

**Files:**
- `persona_A.md` – Full persona description
- `persona_A.pdf` – Printable version for study participants
- `persona_a.json` – 14 days of step count and sleep data


## Persona B: Active / Stressed

A 24-year-old student with an active lifestyle but irregular schedule due to exams and late-night studying. Despite regular high-intensity workouts, they often feel sore or not fully recovered.

**Health Goals:**
- Understand why they feel sore despite daily exercise
- Identify adjustments for better recovery and stress reduction

**Files:**
- `persona_B.md` – Full persona description
- `persona_B.pdf` – Printable version for study participants
- `persona_b.json` – 14 days of step count and sleep data


## Persona C: Active Senior / Slow Recovery

A person in their late 60s who stays moderately active through daily walks and light activities. Sleep has become lighter and more fragmented, and recovery from exertion takes longer than it used to.

**Health Goals:**
- Understand why recovery takes longer after moderately active days
- Identify small adjustments for more continuous sleep and better rest

**Files:**
- `persona_C.md` – Full persona description
- `persona_c.json` – 14 days of step count and sleep data


## Data Format

The JSON files contain 14 consecutive days of health data:

```json
{
  "persona": "A",
  "id": "<lifesnaps_participant_id>",
  "start_date": "2022-01-07",
  "days": [
    {
      "date": "Friday, 2022-01-07",
      "steps": 2634.0,
      "sleep_hours": 6.45
    },
    ...
  ]
}
```

These files serve as input for the [statistics and insights generation pipeline](../src/statistics_and_insights_generation/).
