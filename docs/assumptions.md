# Assumptions

1. **Cataclysm generation**: per-turn probabilities are sampled independently; at most one sandstorm can be active.
2. **Damage split tie rules**: equal last-turn damage split score equally (implemented as equal floating score parts).
3. **Construction conflicts**: if multiple players complete on the same tick, all constructions at cell reset as specified.
4. **Server JSON**: exact endpoint schema is unknown, so adapter provides stable internal schema and mappers.
5. **Respawn location**: deterministic edge spawn based on player id.
6. **Over-limit deletion**: oldest plantation by creation turn is removed at first progress tick over limit.
