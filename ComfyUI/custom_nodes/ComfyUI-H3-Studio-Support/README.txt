H3 Studio portable support

Copy this folder into ComfyUI/custom_nodes next to ComfyUI-H3-Studio.
Install requirements.txt using ComfyUI's Python, then restart ComfyUI.
Use a current ComfyUI build with native MiniMax H3, SAM3.1 and subgraphs.
The INT8 ConvRot models require a compatible PyTorch/CUDA build; the publisher
recommends PyTorch with CUDA 13.0. Keep ComfyUI's own requirements current.

Video loading needs FFmpeg AND ffprobe available on PATH. FFmpeg.org lists
platform packages: https://ffmpeg.org/download.html
The imageio-ffmpeg fallback supplies FFmpeg only, not ffprobe.
The support pack never downloads tools or models automatically.

No QwenVL captioner or external SAM3 plugin is needed. The workflow uses the
native SAM3.1 checkpoint and the H3 conditioning encoder listed in its downloader.
The six support nodes retain the original memory, trim, masking and cache code.
Only tool lookup and temporary-file locations were adapted for other computers.

Saved characters use ComfyUI/user/default/h3_character_presets and durable images
under ComfyUI/input/Character_Presets. No personal library is included here.
If ComfyUI-MiniMax-Safe is present, this pack defers to it to avoid duplicate
node names and duplicate character-library routes. Do not install a partial or
unrelated folder under that name.
