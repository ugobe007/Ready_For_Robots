# Definition of Done

## Every AI feature

- [ ] Deterministic / validated output schema
- [ ] Provenance attached
- [ ] Confidence attached
- [ ] Truth state attached
- [ ] UNKNOWN supported
- [ ] Explicit failure path
- [ ] Model / prompt version recorded
- [ ] Golden tests
- [ ] Hallucination regression passes
- [ ] Inspectable in Admin QA

## Every scoring feature

- [ ] Explicit inputs
- [ ] Missing inputs handled
- [ ] Blockers handled
- [ ] Score version stored
- [ ] Reasons returned
- [ ] Thresholds configurable
- [ ] Regression tests
- [ ] UI labels do not imply unsupported precision

## Every screen

- [ ] Loading, empty, and error states
- [ ] UNKNOWN renders correctly
- [ ] Evidence inspectable where relevant
- [ ] Inference never styled as verified fact
- [ ] Primary action obvious
- [ ] Analytics event on primary action

## Pilot validation protocol

For each pilot robot:

1. Generate Top 10 opportunities.  
2. Seller independently marks CALL, RESEARCH, KNOWN, BAD FIT, or GARBAGE.  
3. Record whether opportunity was previously known.  
4. Validate workflow interpretation.  
5. Validate usefulness of timing evidence.  
6. Record pursuit decision.  
7. Record contact outcome.  
8. Capture customer-confirmed facts.  
9. Track state.  
10. Record eventual win/loss reason (including `RFR_PREDICTION_WRONG` when applicable).
