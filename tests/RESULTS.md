# ASCENT codec test results

Date: 2026-07-29

## Command

```
py -3 tests/test_ascent_codec.py
py -3 ref/ascent_decode.py --self-test
```

## Pass list

| Test | Result |
|------|--------|
| test_vectors_encode_hex | PASS |
| test_roundtrip_v_mode | PASS |
| test_hello_universe_three_units | PASS |
| test_surrogate_raises | PASS |
| test_ascent7_rejects_non_ascii | PASS |
| test_events_kind_strings_only | PASS |
| test_encoding_guard_long | PASS |
| test_cont_frozen | PASS |
| ALL TESTS PASS | PASS |
| ascent_decode --self-test | PASS (builder 132 == SPEC hex) |

## Vectors covered

- ascii_identity
- header_only_empty_body
- role_guide_after_hi
- hello_universe (product SPEC E.2)
- surrogate_reject
- latin1_e_acute_v (round-trip)
- rocket_emoji_v (round-trip)
- bridge_cafe (MM INLINE)
- encoding_guard_vectors (LONG overlong ASCII + non-minimal reject; first legal LONG U+2C280)

## Notes

- Cont primary range: 0xA0-0xBF (5 payload bits), frozen in `ref/ascent_codec.py`.
- Multimodal events keep `kind="multimodal"`; wire kind is `mm_kind`.
- Event JSON flatten never overwrites string `kind` with numeric wire fields.
