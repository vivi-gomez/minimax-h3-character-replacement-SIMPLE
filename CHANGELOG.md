# MiniMax H3 Studio v1.0.2

This update selects native PyTorch attention for H3 and explicitly disables the optional Triton backend in the stable launcher. An internal attention safety node covers all three workflow modes. The models, default LoRA, trim controls, five main nodes, three removable mode notes, and Barn Owl example settings are preserved, along with the earlier low-copy Windows CPU weight reader.

[Download MiniMax-H3-Studio.zip](https://github.com/BiggerFishy/comfyui-minimax-h3-studio/releases/latest/download/MiniMax-H3-Studio.zip). Use this installation ZIP; GitHub's automatically generated Source code archives do not contain the complete installation package.

## Changes

- Updated `Start-MiniMax-H3-Studio.bat` and `h3_studio_start.py` to require `--use-pytorch-cross-attention` alongside `--disable-fast-disk`. The launcher stops if the installed ComfyUI cannot explicitly select that attention backend.
- The stable profile preserves ComfyUI's Dynamic VRAM memory management on supported GPU configurations. It adds `--disable-triton-backend`, `--disable-async-offload`, `--disable-comfy-compiler`, and `--disable-pinned-memory` when supported. Unsupported optional flags are reported and omitted. Conflicting Sage/Flash/split/quad/ComfyKitchen attention, Triton enabling, and memory-transfer flags are rejected, including abbreviations. Ordinary server arguments such as the listen address and port remain available.
- Added an internal **H3 Studio Attention Safety** node selecting PyTorch attention when any of the three modes builds its execution graph. It adds no visible top-level node or new user setting; the five main nodes stay intact. Use the launcher too, because the model attention node does not configure the server's other backends.
- The Windows launcher still uses the existing embedded Python or a `.venv`/`venv` inside ComfyUI. SageAttention is not required, and no system Python fallback is used.
- Retained the low-copy Windows CPU reader that validates tensor metadata and exposes tensors through a read-only file mapping, avoiding another full model copy. It supplies ordinary CPU tensors without direct-file transfer descriptors, retaining dynamic GPU allocation while using RAM transfers instead of the direct aimdo disk-to-GPU reader. It also avoids the PyTorch storage-slicing path involved in the earlier loading failures.
- Loading the Studio custom-node pack at server startup activates this reader by replacing the reader reference in ComfyUI's loading utility for the current process. Other CPU loads through that utility also use it. No installed package, ComfyUI core file, or model file is rewritten.
- Preserved the green settings panel's LoRA controls. The exact non-EMA **Turbo V4 Step 600 pruned** remains the sole default reference/video LoRA at strength **1.0**; other rows are empty. No hidden reference Turbo 8-step application is stacked underneath it.
- Preserved the exact Turbo V4 publisher link and SHA-256-verified download button in the Models node. The reference Turbo 8-step remains an optional alternative, and experimental first-to-last-frame mode retains its own matching Turbo.
- Preserved the video-trim popup and the bundled example's **3 seconds**, **0.8 MP**, and fixed seed **688636457668368**.

[SageAttention issue #386](https://github.com/thu-ml/SageAttention/issues/386) reports integer-index overflow with large, strided attention tensors. [ComfyKitchen issue #136](https://github.com/Comfy-Org/comfy-kitchen/issues/136) reports a separate overflow in Triton INT8 matrix multiplication for large MiniMax H3 workloads. The profile avoids those reported backend paths. These reports do not prove that every observed CUDA failure has either cause; an asynchronous GPU error can first appear during a later copy or cleanup synchronization.

## Install or update

1. Close the existing ComfyUI server. Extract the ZIP and merge the included `ComfyUI` folder into your current ComfyUI folder. Keep both included custom-node folders. The two launcher files must be beside `main.py`.
2. Install **both** `custom_nodes/ComfyUI-H3-Studio/requirements.txt` and `custom_nodes/ComfyUI-H3-Studio-Support/requirements.txt` using ComfyUI's Python. The included Studio requirements specify **safetensors 0.8.0 or newer**. Ensure FFmpeg **and** ffprobe are on PATH; the `imageio-ffmpeg` fallback does not supply ffprobe. See [FFmpeg downloads](https://ffmpeg.org/download.html).
3. On Windows, open `Start-MiniMax-H3-Studio.bat`. For another environment layout, or on Linux/macOS, activate your ComfyUI Python environment and run `python h3_studio_start.py` from the ComfyUI folder.
4. Open the included MiniMax H3 Studio workflow. Use the Models node's filter, publisher links, and download buttons for the weights needed by the selected mode.

From the ComfyUI folder with its Python environment activated:

```sh
python -m pip install -r custom_nodes/ComfyUI-H3-Studio/requirements.txt
python -m pip install -r custom_nodes/ComfyUI-H3-Studio-Support/requirements.txt
```

For Windows portable ComfyUI, replace `python` with `..\python_embeded\python.exe -s`. Restart the server after updating dependencies. If Studio's runtime check reports an older safetensors version or an incompatible startup profile, correct the dependency or startup setting in that server's environment and restart with the included launcher.

A current ComfyUI with native MiniMax H3, SAM3.1, subgraphs, and `--disable-fast-disk` and `--use-pytorch-cross-attention` support is required, along with a compatible PyTorch/CUDA environment. The INT8 ConvRot models' publisher recommends PyTorch with CUDA 13.0; follow the model's requirements and keep ComfyUI's own requirements current. The package does not bundle model weights, ComfyUI, GPU drivers, or media tools. Its custom nodes and launchers do not patch ComfyUI core files, rewrite model files, or modify drivers or system settings. Model terms remain available from each publisher's page.

Downloads occur only when requested with the model download controls, check SHA-256 before installation, and do not replace existing model files. No external SAM3 plugin or Qwen captioner custom-node pack is needed. If **ComfyUI-MiniMax-Safe** is installed, it remains authoritative and the portable support pack defers to it; do not use a partial or unrelated folder under that name.

Turbo V4's [publisher](https://huggingface.co/drbaph/MiniMax-H3-Turbo-Lora-ComfyUI) identifies it as a partial pruned-model conversion with **51 incompatible AdaLN adapter pairs removed**. It should not be assumed to behave identically to the original full-model LoRA. Use one Turbo accelerator at a time. The endpoint mode requires its matching FL2V Turbo 8-step file; the optional reference Turbo 8-step download is not needed with the default V4 selection.

## Example and privacy

The included Barn Owl example opens in Video inpainting with its portrait, source video, character and scene prompts, and SAM3 target **“the man”**. Its settings remain **3 seconds**, **0.8 MP**, and fixed seed **688636457668368**. Choose **Seed behavior > Randomize** for variations; results can take several attempts. A fixed seed does not promise identical results across different hardware or software.

Reference-to-video and first-to-last-frame remain separate modes with their own empty media selections. Both are **experimental and may not work well**. The three mode notes remain independently removable.

Only the supplied Barn Owl saved character and two demo media files are included. Other saved characters from the creator's computer are excluded. Save Character stores an image and description locally; character records live in `ComfyUI/user/default/h3_character_presets` and durable images in `ComfyUI/input/Character_Presets`. Review those folders before sharing your own library. No generated demo output is bundled.

## Tradeoffs and validation

Dynamic VRAM memory management remains available; the Windows CPU reader and launcher profile remove the direct disk-to-GPU transfer path for weights loaded through that reader. RAM use and load times still depend on the model, settings, and available memory, and RAM transfers may be slower than fast-disk transfers. The profile does not guarantee successful generation on every device or with every model and setting. Startup and dependency changes require a fresh ComfyUI server process; a browser refresh alone does not apply them. Close a server that encountered CUDA illegal memory access before starting another run.

The PyTorch-attention backend settings completed two video-inpainting diagnostic runs on **October 2, 2026**: **15 seconds at 0.55 MP** in about **29m 10s**, then **3 seconds at 0.8 MP** in about **4m 45s** after memory cleanup in the same server process. Both used **`CUDA_LAUNCH_BLOCKING=1`**; these are diagnostic timings, **not normal generation-speed measurements**. The outputs contained 360 frames at 544 × 992 and 72 frames at 672 × 1184, respectively, both at 24 fps with audio. Full output decoding passed. These checks preceded installation of the new internal attention safety node and validate the backend settings only.

The exact installed **v1.0.2** package then completed a normal-launcher check on a fresh server: **3 seconds at 0.8 MP**, **8 steps**, in **4m 14s**, with CUDA launch blocking disabled. The runtime log confirmed that the internal H3 attention safety node selected PyTorch attention. The output contained **72 frames at 672 × 1184**, **24 fps**, with audio; full decoding passed. These October 2 checks ran on Windows with an RTX 4090 with 24 GB VRAM and 32 GB system RAM.

Historical checks on **October 1, 2026**, used the previous SageAttention profile: the supplied **0.8 MP**, **8-step** demo completed at **3 seconds** in **2m 49s** and **8 seconds** in **9m 51s**, using the fixed example seed, INT8 ConvRot reference model, and Turbo V4 Step 600 pruned LoRA. Output decoding passed. That machine used Windows, an RTX 4090 with 24 GB VRAM, 32 GB RAM, a roughly 31 GB pagefile, ComfyUI 0.37.0, PyTorch 2.9.1+cu130, and safetensors 0.8.0. These earlier checks are **not v1.0.2 validation** and did not establish stability for longer or repeated runs.

Execution and file-integrity checks do not establish visual quality or support for arbitrary lengths, other hardware, or the experimental modes. Normal-launcher validation covers the three-second case; the fifteen-second and post-cleanup checks used diagnostic synchronization.
