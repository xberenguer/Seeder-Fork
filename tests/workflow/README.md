# Shared control checks

Run `python3 tests/workflow/build.py`. A C/C++ compiler is required. The harness
compiles production button detection, workflow and uBitcoin calculations with
both board pin mappings; display/power initialization is excluded.

It verifies active-low/high inputs, 12/24-word generation, matching page sets
and counters without CompactSeedQR, big-forward/small-back navigation, the same
hold overlay during input and Exit, ignored navigation while holding, release
to cancel, three-second confirmation and application-field clearing. UI callbacks
record screen identity; native rendering and physical hardware checks are separate.
