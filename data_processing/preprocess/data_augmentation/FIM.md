## FIM Data Construction Toolkit

This module provides utilities to construct Fill-In-the-Middle (FIM) data from raw JSONL files containing code. It supports:

- Generating a FIM evaluation dataset from a single input JSONL.
- Sampling X% of each of multiple JSONL files to convert into FIM format, interleaving with the remaining original samples, and writing mixed outputs per file.

### Input Format

Each line in the input JSONL should be a JSON object containing either `text` or `code` field with the source string. Optionally, an `llm_formatted` field may be present as a string (preferred) or as an object with a `text` field. Example line:

```json
{"text": "function add(a, b) { return a + b; }"}
```

```json
{"text": "...", "llm_formatted": "..."}
```

```json
{"text": "...", "llm_formatted": {"text": "..."}}
```

### Output Format

The generated FIM examples are written as JSONL lines, each with a `text` field containing a FIM-annotated string using the following tags:

- `<|fim_prefix|>`
- `<|fim_suffix|>`
- `<|fim_middle|>`

Example output line:

```json
{"text": "<|fim_prefix|>function add(a, b) { <|fim_suffix|> }<|fim_middle|>return a + b;"}
```

### Installation

```bash
pip install tree_sitter tree_sitter_typescript
```

### Usage 1: Build FIM eval dataset from a single file

```bash
python FIM.py \
  --input /abs/path/arkts_raw.jsonl \
  --output /abs/path/arkts_fim_eval.jsonl \
  --samples 2000 \
  --min_middle_chars 80 \
  --max_middle_chars 1200 \
  --seed 42 \
  --p_function 0.4 --p_line 0.3 --p_identifier 0.2 --p_token 0.1
```

python /data2/lyh/pretrain_etl/data_processing/preprocess/data_augmentation/FIM.py \
  --input /data2/lyh/pretrain_etl/data_processing/code_data/split_data/L2R_train_fullk.jsonl \
  --output /data2/lyh/pretrain_etl/data_processing/code_data/split_data/L2R_train_fullk_FIM.jsonl \
  --samples 112936 \
  --min_middle_chars 50 \
  --max_middle_chars 1200 \
  --seed 42 \
  --p_function 0.4 --p_line 0.3 --p_identifier 0.2 --p_token 0.1

Arguments:

- `--input`: Input JSONL file.
- `--output`: Output JSONL file for FIM eval data.
- `--samples`: Max number of samples to emit.
- `--min_middle_chars`/`--max_middle_chars`: Span size constraints for the removed middle.
- `--seed`: Random seed.
- Strategy probabilities: `--p_function`, `--p_line`, `--p_identifier`, `--p_token`.

### Usage 2: Sample X% to FIM per file and mix with the rest

For each input file, randomly sample X% of lines to convert to FIM. Two mixing modes are supported:

- interleave (default): evenly interleave FIM samples with the remaining originals
- random_replay: keep all original lines (including those converted) and randomly place both originals and FIM samples together

Output file naming: `originalStem_{X}FIM.jsonl` by default.

```bash
python FIM.py \
  --inputs /abs/path/a.jsonl /abs/path/b.jsonl \
  --fim_percent 20 \
  --output_dir /abs/path/out_dir \
  --out_ext .jsonl \
  --min_middle_chars 80 \
  --max_middle_chars 1200 \
  --seed 42 \
  --p_function 0.4 --p_line 0.3 --p_identifier 0.2 --p_token 0.1 \
  --mix_mode random_replay
```

Arguments:

- `--inputs`: List of input JSONL files.
- `--fim_percent`: Percent (0-100) of lines to convert to FIM for each file.
- `--output_dir`: Optional output directory. Defaults to each input file's directory.
- `--out_ext`: Output extension, default `.jsonl`.
- Span/strategy parameters are identical to Usage 1.
- `--mix_mode`: `interleave` or `random_replay`.

### LLM-formatted Input Handling

- Eval dataset mode (`make_fim_dataset`): If a line contains the `llm_formatted` field (string or object with `text`), it is preferred and used as the only source; otherwise, the base `text`/`code` is used. At most one FIM example is produced per input line.

- Mixing mode (`sample_fim_and_mix_for_file`): The tool may construct FIM samples from both the base `text` and the `llm_formatted.text` when a line is selected for conversion. In this mode:
  - All original base texts are kept.
  - FIM samples created from either base or `llm_formatted.text` are added according to the selected mix mode.

### Notes

- Lines lacking a non-empty `text` or `code` field are skipped.
- If a sampled line cannot produce a valid FIM span after multiple attempts, it is kept as an original sample.
- Interleaving is proportional, not a blind shuffle, to maintain roughly the target FIM ratio across the output.
- Outputs for the mixing mode always use `{ "text": ... }` schema to keep consistency.


