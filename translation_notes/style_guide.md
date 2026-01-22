# Translation Style Guide

Guidelines for consistent tone and style across the translation.

## General Principles

1. **Preserve personality** - Each character has a distinct voice; maintain it
2. **Natural English** - Don't translate literally; make it sound natural
3. **Context matters** - Consider who's speaking and the situation
4. **Brevity** - Dialog boxes have limited space; be concise

## Tone

This is a high school fighting game with comedic and dramatic elements. The tone should be:
- Energetic and youthful
- Dramatic during serious moments
- Playful during comedic scenes
- Appropriate to each character's personality

## Honorifics

**Decision**: Keep Japanese honorifics

- Keep `-san`, `-kun`, `-chan`, `-senpai`, `-sensei`
- These are integral to character relationships and personality
- Exception: "Chairperson" or "Rep" for 委員長 (Iinchou) depending on space

Current approach: **Keep honorifics**

## Name Order

**Decision**: Western order for character names, Japanese honorifics attached

- Batsu Ichimonji → "Batsu" or "Batsu-kun"
- Hinata Wakaba → "Hinata" or "Hinata-san"
- Teachers: Use given name + sensei (e.g., "Hayato-sensei", "Kyoko-sensei")

Current approach: **Western order (Given Family)**

## Punctuation

- Use `...` for trailing off or pauses
- Use `!` for excitement/shouting (don't overuse)
- Use `?!` for shocked questions

## Common Expressions

| Japanese | Translation | Notes |
|----------|-------------|-------|
| よろしく | Nice to meet you / Let's do this | Context-dependent |
| がんばれ | Good luck / Do your best / You got this | |
| すごい | Awesome / Amazing / Incredible | |
| やった | Yes! / I did it! / Alright! | |
| まさか | No way / It can't be | |

## Conciseness Techniques

When translations exceed byte limits, use these strategies:

| Technique | Example |
|-----------|---------|
| Contractions | "I will" → "I'll", "do not" → "don't" |
| Shorter synonyms | "because" → "since", "understand" → "get" |
| Remove redundancy | "in order to" → "to" |
| Abbreviate | "Two-Platoon technique" → "Two-Platoon" |
| Shorten phrases | "What are you doing?" → "What're you doing?" |
| Use context | "Eiyu-sensei, what are you holding?" → "Eiyu-sensei, what's that?" |
| Truncate names | "Discipline Committee room" → "Discipline Room" |

### Common Shortenings

| Long | Short | Saves |
|------|-------|-------|
| Chairperson | Rep | 7 bytes |
| Justice characters | Jus chars | 9 bytes |
| Student Council Room | Council Room | 8 bytes |
| Career Guidance Room | Career Guidance | 5 bytes |
| Two-Platoon technique | Two-Platoon | 10 bytes |

## Things to Avoid

- ❌ Overly formal language for casual characters
- ❌ Modern slang that feels anachronistic
- ❌ Inconsistent terminology
- ❌ Losing character voice
- ❌ Translations that are much longer than originals
- ❌ Cutting meaning to save bytes (find better phrasing instead)

## Review Checklist

Before finalizing a batch:
- [ ] Character voices are consistent
- [ ] Terminology matches `terminology.md`
- [ ] Formatting codes are correct (`!cXX`, `!pXXXX!eYY`, `!0`, `/`)
- [ ] Line breaks are appropriate
- [ ] No obvious typos or errors
- [ ] `en_bytes` ≤ `jp_bytes` (run `check_lengths.py`)
- [ ] Color code `!` or `/` characters land on even byte positions
