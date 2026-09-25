# Native robustness targets

Run from `native/omnisus-dbf` with `cargo-fuzz` and a nightly Rust toolchain.
The target enables AddressSanitizer, consumes at most 64 KiB per input, and
exercises header preflight, iteration, repeated close, all four encodings and
numeric parsing. The `dbc` target exercises DBC header checks and the
imploded-stream decoder with the same input bound. Neither links Python.

```sh
cargo install cargo-fuzz --version 0.13.2 --locked
rustup toolchain install nightly-2026-09-10 --profile minimal
mkdir -p /tmp/omnisus-dbf-fuzz-corpus
cp ../../tests/fixtures/dbf/*.dbf /tmp/omnisus-dbf-fuzz-corpus/
cargo +nightly-2026-09-10 fuzz run dbf /tmp/omnisus-dbf-fuzz-corpus -- \
  -max_total_time=30 -max_len=65536 -timeout=5 -rss_limit_mb=2048
mkdir -p /tmp/omnisus-dbc-fuzz-corpus
cp ../../tests/fixtures/dbc/sia_aq_rr_2024_01_mini.dbc ../../tests/fixtures/blast/test.pk /tmp/omnisus-dbc-fuzz-corpus/
cargo +nightly-2026-09-10 fuzz run dbc /tmp/omnisus-dbc-fuzz-corpus -- \
  -max_total_time=30 -max_len=65536 -timeout=5 -rss_limit_mb=2048
```

Keep the generated corpus in temporary storage. The original small seeds and
their hashes live in the repository's shared `tests/fixtures/dbf`; fuzzing must
not mutate them. Minimize any crash input and add it as a regression before a fix.

On macOS arm64, the 2026-09-10 campaign used cargo-fuzz 0.13.2, libfuzzer-sys
0.4.13 and rustc 1.100.0-nightly (a36d05efa 2026-09-09), default AddressSanitizer,
and seed 3259971411. It completed 995,082 executions in 31 seconds with no crash
or sanitizer error (coverage 978, feature count 3,847). This is bounded evidence,
not proof of parser safety. Rust unit tests additionally check 512 arbitrary byte
inputs and 512 generated valid numeric tables per run.
