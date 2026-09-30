# Snapdragon implementation plan

## Implemented today

The guard runs on the CPU. Reports identify this explicitly. Text processing, local storage and UI do not require NPU acceleration. Windows ARM64 and a Snapdragon-powered HP PC have not been available for measurement in this build.

## Candidates and official sources

| Stage | Candidate | Evidence and boundary |
|---|---|---|
| Generation / proposed model-assisted verifier | Qwen3-4B-Instruct-2507 | [Official Qualcomm recipe](https://github.com/qualcomm/ai-hub-models/blob/v0.63.0/src/qai_hub_models/models/qwen3_4b_instruct_2507/README.md). Recipe availability does not establish target-PC compatibility. |
| Smaller-model comparison | Qwen3-0.6B | [Official recipe](https://github.com/qualcomm/ai-hub-models/blob/v0.63.0/src/qai_hub_models/models/qwen3_0_6b/README.md). Language/judgement quality must be measured. |
| Retrieval / drift screening | multilingual-e5-small | [Publisher model card](https://huggingface.co/intfloat/multilingual-e5-small). CPU adapter exists here. Custom ONNX/QNN port remains future work. |

[GenieX](https://geniex.aihub.qualcomm.com/en/get-started/what-is-geniex) is a developer preview. Validate the [platform/runtime matrix](https://geniex.aihub.qualcomm.com/en/get-started/platforms) and the exact model bundle before choosing it. Some model catalogue pages have inconsistent support indicators. Do not infer support merely from a model appearing in the catalogue.

## Port and validation sequence

1. Record the HP model, exact SoC, RAM, Windows build, native Python/process architecture, driver and SDK/runtime versions.
2. Choose a supported route and matching model bundle. Check licences and memory requirements. Confirm Telugu/Tamil/Kannada output quality before adopting a model.
3. Preserve E5 tokenization, attention masking, mean pooling and normalization during ONNX export. Fix supported input shapes and record truncation limits.
4. Use [AI Hub Workbench compilation](https://workbench.aihub.qualcomm.com/docs/hub/compile_examples.html) and profiling for a proposed custom encoder port. Keep private user text out of remote development jobs.
5. Follow the [ONNX Runtime QNN execution-provider documentation](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html). Inspect actual HTP/backend traces and reject or disclose CPU fallback. Provider availability alone is insufficient.
6. Re-run task-quality checks after conversion and quantization. Record model hashes, precision and compile settings.
7. Compare CPU/NPU runs on the same HP device, with fixed power settings and equivalent shapes, model revisions and precision. Label non-equivalent artifacts as deployment comparisons.

## Measurement contract

Report cold-start/model-load time separately from warm inference. Use five warm-up runs and at least 30 timed repetitions per input-length group. Report median and p95 guard latency, memory peak, model/index size, time to first token and decode throughput where applicable. Measure quality alongside speed.

`speedup = median CPU latency / median NPU latency` is valid only for a disclosed comparable workload. No NPU speedup, battery or energy figures are claimed in this repository. Energy measurement needs a defined instrument and sampling procedure before reporting results.

Offline application inference is a deployment goal distinct from development-time model downloads or AI Hub jobs. Validate application behaviour with networking disabled after setup.
