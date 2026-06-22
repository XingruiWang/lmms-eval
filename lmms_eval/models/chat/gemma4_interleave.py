"""gemma4_interleave — Google Gemma 4 (E2B/E4B) over interleaved doc_to_messages.

Gemma 4 is Google's open multimodal family (text + image + audio + video as
frames). The E2B / E4B checkpoints carry an audio tower; larger checkpoints
(31B, 26B-A4B) are text+image+video only. The HF chat template natively
accepts the same shape as `_interleave_base` produces — `{"type":"audio",
"audio": <path>}`, `{"type":"image","image": <path>}`, `{"type":"text",
"text": "..."}` — so XModBench's full multimedia stem + 4 multimedia options
go through `apply_chat_template` unchanged.

Notes
-----
* Public weights, no HF gated license (verified 2026-05 on
  google/gemma-4-E4B-it).
* Needs ``transformers`` from main (Gemma4 modules merged after 4.57.x).
  Install via ``pip install -U "transformers @ git+https://github.com/
  huggingface/transformers"``.
* The processor exposes ``parse_response`` to strip the new Gemma-4
  thought-tag wrappers and return only the visible reply.

This wrapper is generation-only (single-sample per request, batch=1) which
matches every other XModBench interleave path; multi-sample batching is left
for a future PR.
"""

from __future__ import annotations

from typing import List, Optional, Union

import torch
from accelerate import Accelerator
from loguru import logger as eval_logger

from lmms_eval.api.instance import Instance
from lmms_eval.api.model import lmms
from lmms_eval.api.registry import register_model
from lmms_eval.models.chat._interleave_base import (
    IMAGE_KWARGS,
    VIDEO_KWARGS,
    InterleaveChatMixin,
)

try:
    from transformers import AutoProcessor  # always available
except ImportError as e:  # pragma: no cover
    raise ImportError("transformers is required for gemma4_interleave") from e


def _try_import_gemma4():
    """Defer the Gemma4 class import — only available on transformers main."""
    try:
        from transformers import Gemma4ForConditionalGeneration  # type: ignore
        return Gemma4ForConditionalGeneration
    except ImportError:
        try:
            from transformers import AutoModelForMultimodalLM  # type: ignore
            return AutoModelForMultimodalLM
        except ImportError as e:
            raise ImportError(
                "Gemma 4 requires transformers from main "
                "(`pip install -U \"transformers @ git+https://github.com/huggingface/transformers\"`)."
            ) from e


def _decode_video_to_frames(
    path: str,
    max_frames: int = 16,
    fps: float = 2.0,
    target_frames: int | None = None,
):
    """Pre-decode a video path to a (T, H, W, C) uint8 ndarray.

    Gemma 4's HF video processor defaults to the torchcodec backend and falls
    back to ``torchvision.io.read_video`` — but recent torchvision (>=0.22)
    has dropped ``read_video``, so video samples crash. We sidestep both
    backends by sampling frames here with ``decord`` (which is available in
    every lmms-eval omni env) and handing the already-sampled ndarray to the
    processor; the processor then takes the ``is_valid_video`` array path and
    never touches the missing backends. ``do_sample_frames=False`` is set in
    ``_infer_one`` because we've already sampled.

    When ``target_frames`` is supplied, the result is **exactly** that many
    frames (evenly-spaced sampling, padding the last frame if the source is
    shorter than ``target_frames``). The Gemma 4 video processor stacks all
    videos in a single request via ``torch.stack``, so when XModBench packs
    several videos as options (a2v / t2v), every video MUST decode to the
    same T or the call crashes with a shape mismatch — this caused ~24.5 %
    empty responses on the Lite split before the fix.
    """
    try:
        import decord  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "decord is required for Gemma 4 video inputs in this env "
            "(torchvision.read_video is unavailable)."
        ) from e
    import numpy as np

    def _placeholder(tgt: int | None) -> "np.ndarray":
        t = max(int(tgt) if tgt else 1, 1)
        return np.zeros((t, 16, 16, 3), dtype=np.uint8)

    try:
        vr = decord.VideoReader(path)
        n_total = len(vr)
    except Exception:  # pragma: no cover — unreadable container, emit placeholder
        return _placeholder(target_frames)

    if n_total == 0:
        return _placeholder(target_frames)

    if target_frames is not None and target_frames > 0:
        T = int(target_frames)
        if n_total >= T:
            # Evenly-spaced indices across the full clip → exactly T frames.
            idxs = np.linspace(0, n_total - 1, num=T, dtype=int).tolist()
        else:
            # Sample everything, then pad with the last frame to reach T.
            idxs = list(range(n_total))
        try:
            frames = vr.get_batch(idxs).asnumpy()  # (len(idxs), H, W, C) uint8
        except Exception:  # pragma: no cover
            return _placeholder(target_frames)
        if frames.shape[0] < T:
            pad = np.repeat(frames[-1:], T - frames.shape[0], axis=0)
            frames = np.concatenate([frames, pad], axis=0)
        return frames

    # Legacy path: ~fps-sampled indices, capped by max_frames.
    avg_fps = float(vr.get_avg_fps() or 30.0)
    step = max(1, int(round(avg_fps / max(fps, 0.1))))
    idxs = list(range(0, n_total, step))[:max_frames]
    if not idxs:
        idxs = [0]
    try:
        frames = vr.get_batch(idxs).asnumpy()  # (T, H, W, C) uint8
    except Exception:  # pragma: no cover
        return _placeholder(target_frames)
    return frames


def _to_gemma4_messages(messages: list, video_kwargs: dict | None = None) -> list:
    """doc_to_messages blocks -> Gemma 4 chat-template format.

    Our `doc_to_messages` emits ``{"type":"image","url": path}`` etc.; Gemma 4
    expects the value key to match the type (``{"type":"image","image": path}``).
    Text blocks are pass-through. Video paths are pre-decoded to a frame
    ndarray (see ``_decode_video_to_frames``).

    When the request contains more than one video, every video is decoded to
    **exactly the same** number of frames. The Gemma 4 video processor
    stacks the per-video tensors via ``torch.stack`` and crashes if T is not
    constant — this previously made XModBench's a2v/t2v configs (which pack
    4 candidate videos) return empty strings ~24 % of the time.
    """
    vk = video_kwargs or {}
    max_frames = int(vk.get("max_frames", 16))
    fps = float(vk.get("fps", 2.0))

    # Count videos across all turns so we can pick a single target T.
    n_videos = 0
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if c.get("type") == "video":
                n_videos += 1

    # Multi-video → enforce a fixed T and cap it down a bit so the context
    # cost stays bounded (8 frames × up to 5 videos = 40 frames worth of
    # 384×384 tiles, well within Gemma 4's window). Single-video → keep the
    # original ~fps-based sampling for max recall.
    target_frames: int | None
    forced = vk.get("_force_target_frames")
    if forced is not None:
        target_frames = int(forced)
    elif n_videos >= 2:
        target_frames = min(max_frames, 8)
    else:
        target_frames = None

    out = []
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            out.append(msg)
            continue
        new_content = []
        for c in content:
            t = c.get("type")
            if t == "text":
                new_content.append({"type": "text", "text": c.get("text", "")})
            elif t == "video":
                src = c.get("url", c.get("video"))
                if isinstance(src, str):
                    src = _decode_video_to_frames(
                        src,
                        max_frames=max_frames,
                        fps=fps,
                        target_frames=target_frames,
                    )
                new_content.append({"type": "video", "video": src})
            elif t in {"image", "audio"}:
                # Gemma 4 accepts a file path, URL, PIL image, or np.array.
                new_content.append({"type": t, t: c.get("url", c.get(t))})
            else:
                new_content.append(c)
        out.append({"role": msg["role"], "content": new_content})
    return out


@register_model("gemma4_interleave")
class Gemma4Interleave(InterleaveChatMixin, lmms):
    """Google Gemma 4 over interleaved (text+image+audio+video-frames) prompts.

    Public default checkpoint: ``google/gemma-4-E4B-it`` (audio-capable, 4.5B
    effective params). For text+image+video only, use ``google/gemma-4-31B-it``
    or ``google/gemma-4-26B-A4B-it``.
    """

    is_simple = False
    # XModBench v2a / a2v carry up to 5 media per item; keep the shared caps.
    video_kwargs = VIDEO_KWARGS
    image_kwargs = IMAGE_KWARGS

    def __init__(
        self,
        pretrained: str = "google/gemma-4-E4B-it",
        device: Optional[str] = "cuda",
        device_map: Optional[str] = "auto",
        batch_size: Optional[Union[int, str]] = 1,
        torch_dtype: str = "bfloat16",
        attn_implementation: Optional[str] = None,
        system_prompt: Optional[str] = "You are a helpful assistant.",
        use_cache: bool = True,
        max_new_tokens: int = 512,
        **kwargs,
    ) -> None:
        super().__init__()
        # Accept-but-ignore any lmms-eval-passed kwargs we don't use yet.
        if kwargs:
            eval_logger.debug(f"Gemma4Interleave ignoring kwargs: {list(kwargs)}")

        accel = Accelerator()
        if accel.num_processes > 1:
            self._device = torch.device(f"cuda:{accel.local_process_index}")
            self.device_map = f"cuda:{accel.local_process_index}"
        else:
            self._device = torch.device(device)
            self.device_map = device_map if device_map else device

        dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16,
                 "float32": torch.float32}.get(torch_dtype, torch.bfloat16)
        model_kwargs = {"dtype": dtype, "device_map": self.device_map}
        if attn_implementation is not None:
            model_kwargs["attn_implementation"] = attn_implementation

        ModelCls = _try_import_gemma4()
        eval_logger.info(f"Loading Gemma 4: {pretrained}  ({ModelCls.__name__})")
        self._model = ModelCls.from_pretrained(pretrained, **model_kwargs).eval()
        self.processor = AutoProcessor.from_pretrained(pretrained)
        self._tokenizer = getattr(self.processor, "tokenizer", None)

        self._config = self._model.config
        self.system_prompt = system_prompt
        self.use_cache = use_cache
        self.batch_size_per_gpu = int(batch_size)
        self._max_new_tokens = max_new_tokens
        self.accelerator = accel
        self._rank = accel.process_index
        self._world_size = accel.num_processes

    # --- lmms boilerplate (required) ---
    @property
    def model(self):
        return self._model

    @property
    def tokenizer(self):
        return self._tokenizer

    @property
    def device(self):
        return self._device

    @property
    def rank(self):
        return self._rank

    @property
    def world_size(self):
        return self._world_size

    @property
    def batch_size(self):
        return self.batch_size_per_gpu

    def loglikelihood(self, requests):  # pragma: no cover
        raise NotImplementedError("Gemma4Interleave is generation-only.")

    def generate_until_multi_round(self, requests):  # pragma: no cover
        raise NotImplementedError("TODO: Implement multi-round generation")

    # --- the only model-specific step ---
    def _infer_one(self, messages: list, gen_kwargs: dict) -> str:
        try:
            return self._infer_one_impl(messages, gen_kwargs, target_frames=None)
        except RuntimeError as e:
            # CUDA OOM or unexpected processor stack failure → retry once
            # with fewer frames per video, then fall back to "" so the run
            # doesn't crash mid-sample.
            msg = str(e).lower()
            if "out of memory" in msg or "stack expects" in msg:
                eval_logger.warning(
                    f"Gemma4Interleave: retrying with target_frames=4 after {type(e).__name__}: {e}"
                )
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass
                try:
                    return self._infer_one_impl(messages, gen_kwargs, target_frames=4)
                except Exception as e2:  # pragma: no cover
                    eval_logger.warning(f"Gemma4Interleave: giving up after retry ({e2}); returning ''")
                    return ""
            eval_logger.warning(f"Gemma4Interleave: unhandled error, returning '': {e}")
            return ""
        except Exception as e:  # pragma: no cover
            eval_logger.warning(f"Gemma4Interleave: unexpected error, returning '': {e}")
            return ""

    def _infer_one_impl(self, messages: list, gen_kwargs: dict, target_frames: int | None = None) -> str:
        if self.system_prompt:
            messages = [{"role": "system",
                         "content": [{"type": "text", "text": self.system_prompt}]}] + list(messages)
        vk = dict(self.video_kwargs or {})
        if target_frames is not None:
            vk["_force_target_frames"] = int(target_frames)
        hf_messages = _to_gemma4_messages(messages, video_kwargs=vk)

        inputs = self.processor.apply_chat_template(
            hf_messages,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            add_generation_prompt=True,
            video_load_backend=None,
            do_sample_frames=False,
        )
        # apply_chat_template returns a BatchEncoding; move to device + dtype.
        inputs = inputs.to(self._model.device)
        if hasattr(inputs, "input_ids"):
            input_len = inputs["input_ids"].shape[-1]
        else:
            input_len = inputs[next(iter(inputs))].shape[-1]

        gen_kwargs.setdefault("max_new_tokens", self._max_new_tokens)
        gen_kwargs.setdefault("temperature", 0)
        gen_kwargs.setdefault("top_p", None)
        gen_kwargs.setdefault("num_beams", 1)

        with torch.inference_mode():
            out = self._model.generate(
                **inputs,
                do_sample=gen_kwargs["temperature"] > 0,
                temperature=gen_kwargs["temperature"] or None,
                top_p=gen_kwargs["top_p"],
                num_beams=gen_kwargs["num_beams"],
                max_new_tokens=gen_kwargs["max_new_tokens"],
                use_cache=self.use_cache,
            )

        # Decode only the freshly generated tokens.
        gen_ids = out[0][input_len:]
        # Plain decoded text, always available as a safe fallback.
        plain = self.processor.decode(gen_ids, skip_special_tokens=True).strip()
        text_with_special = self.processor.decode(gen_ids, skip_special_tokens=False)
        # Gemma 4 introduces a structured response; the processor exposes
        # parse_response() to strip the wrappers. If parsing yields an empty
        # string (e.g. the schema didn't match a short letter-only answer),
        # prefer the plain decoded text so downstream MCQ filters still see
        # the option letter.
        parse = getattr(self.processor, "parse_response", None)
        parsed_text = None
        if callable(parse):
            try:
                parsed = parse(text_with_special)
                if isinstance(parsed, dict):
                    parsed_text = str(parsed.get("text", parsed.get("content", ""))).strip()
                else:
                    parsed_text = str(parsed).strip()
            except Exception:  # pragma: no cover
                parsed_text = None
        if parsed_text:
            return parsed_text
        return plain
