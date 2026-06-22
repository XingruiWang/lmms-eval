"""gemini_genai_api — Gemini via the new ``google.genai`` (>=1.0) SDK.

Why this exists
---------------
The legacy ``google.generativeai`` SDK (used by ``gemini_api.py``) does not
correctly route requests to Gemini 3.x model names; calls succeed but the
model returns empty text on ~60–80% of XModBench items (verified in the
2026-05 smoke). The new ``google.genai`` SDK fixes the routing and exposes
the same multimodal contract (``Part.from_uri`` for uploaded files, inline
``Part.from_bytes`` for images, ``client.models.generate_content``).

This file mirrors the ``gemini_api`` wrapper's external interface so existing
launcher scripts can swap ``--model gemini_api`` for ``--model gemini_genai_api``
without further changes. The interleave path (``<media_N>`` placeholders) is
preserved verbatim.
"""

from __future__ import annotations

import io
import json
import os
import pathlib
import re
import time
from typing import List

from accelerate import Accelerator, DistributedType
from loguru import logger as eval_logger
from PIL import Image
from tqdm import tqdm

from lmms_eval.api.instance import GenerationResult, Instance, TokenCounts
from lmms_eval.api.model import lmms
from lmms_eval.api.registry import register_model
from lmms_eval.models.model_utils.usage_metrics import is_budget_exceeded, log_usage

try:
    from google import genai
    from google.genai import types as gtypes
except Exception as e:  # pragma: no cover
    eval_logger.error(f"Failed to import google.genai: {e}")
    genai = None
    gtypes = None

try:
    import soundfile as sf
except Exception as e:
    eval_logger.warning(f"Error importing soundfile, audio inputs will fail: {e}")
    sf = None


NUM_SECONDS_TO_SLEEP = 30


@register_model("gemini_genai_api")
class GeminiGenAIAPI(lmms):
    """Gemini wrapper on the new ``google.genai`` SDK (>=1.0)."""

    def __init__(
        self,
        model_version: str = "gemini-3.1-pro-preview",
        timeout: int = 120,
        interleave: bool = False,
        **kwargs,
    ) -> None:
        super().__init__()
        if genai is None:
            raise RuntimeError(
                "google.genai is not installed. `pip install google-genai`."
            )
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY / GEMINI_API_KEY env var is required.")

        self.model_version = model_version
        self.timeout = timeout
        self.interleave = interleave
        self.client = genai.Client(api_key=api_key)
        # Used by older lmms-eval APIs that check ``self.model``.
        self.model = self.client

        accel = Accelerator()
        if accel.num_processes > 1:
            assert accel.distributed_type in [
                DistributedType.FSDP,
                DistributedType.MULTI_GPU,
                DistributedType.DEEPSPEED,
            ], "Unsupported distributed type."
        self.accelerator = accel
        self._rank = accel.local_process_index
        self._world_size = accel.num_processes
        self.device = accel.device

        # Uploaded file objects we should remove on free_video().
        self.uploaded_files = []

        # Per-item resume cache. lmms-eval's built-in CacheHook.add_partial
        # is a no-op, and JSONL is only flushed at end-of-config; a single
        # transient 503 mid-run therefore wastes the entire 1k-item config.
        # Persist each successful response as a sidecar JSONL keyed by
        # (task, doc_id) so a restart skips items we already paid for.
        # Cache lives under ~/.cache/lmms_eval_genai_resume/<model>/<task>.jsonl
        # by default; override with GEMINI_RESUME_DIR.
        self.resume_dir = pathlib.Path(
            os.environ.get(
                "GEMINI_RESUME_DIR",
                os.path.expanduser("~/.cache/lmms_eval_genai_resume"),
            )
        ) / model_version.replace("/", "_")
        self.resume_dir.mkdir(parents=True, exist_ok=True)
        self.resume_cache: dict[tuple, dict] = {}
        for f in self.resume_dir.glob("*.jsonl"):
            task = f.stem
            for line in f.open():
                try:
                    r = json.loads(line)
                    self.resume_cache[(task, r["doc_id"])] = r
                except Exception:
                    continue
        if self.resume_cache:
            eval_logger.info(
                f"GeminiGenAIAPI resume cache: loaded {len(self.resume_cache)} "
                f"items from {self.resume_dir}"
            )

    # ------- helpers (mirror gemini_api.py) -------
    def free_video(self):
        for f in self.uploaded_files:
            try:
                self.client.files.delete(name=f.name)
            except Exception:
                pass
        self.uploaded_files = []

    def flatten(self, x):
        out = []
        for i in x:
            for j in i:
                out.append(j)
        return out

    def _upload(self, path: str, mime: str):
        # Google's media-upload endpoint also returns 503 / 500 / 429 under
        # load; an unretried throw here aborts the *entire* lmms-eval task
        # (verified during the 2026-05-19 3.1-pro outage: a2t lost at
        # 832/1000, a2v at 24/1000). Retry uploads with the same 30 s back-off
        # as generate so transient outages no longer waste a full config.
        last_err = None
        f = None
        for attempt in range(5):
            try:
                f = self.client.files.upload(file=path, config={"mime_type": mime})
                break
            except Exception as e:
                last_err = e
                eval_logger.info(
                    f"files.upload attempt {attempt + 1}/5 failed: {str(e)[:160]}"
                )
                if attempt < 4:
                    time.sleep(NUM_SECONDS_TO_SLEEP)
        if f is None:
            raise last_err  # 5 failures → bubble so caller marks this item empty
        # Polling files.get can also fail transiently → tolerant retry.
        # Drop poll interval to 0.5 s (most uploads ACTIVE on first poll); the
        # old 2-s default was costing ~2 s/item × 6000 = ~3 h on 3.1-pro Lite.
        for _ in range(60):
            try:
                info = self.client.files.get(name=f.name)
            except Exception:
                time.sleep(0.5)
                continue
            state = getattr(info.state, "name", str(info.state))
            if state == "ACTIVE":
                f = info
                break
            time.sleep(0.5)
        self.uploaded_files.append(f)
        return f

    def encode_audio(self, audio):
        """audio is a {array, sampling_rate} dict from doc_to_visual."""
        if sf is None:
            raise RuntimeError("soundfile not installed")
        # genai.files.upload needs a path; write to a temp wav.
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            sf.write(tf.name, audio["array"], audio["sampling_rate"], format="WAV")
            return self._upload(tf.name, "audio/wav")

    def encode_video(self, path: str):
        return self._upload(path, "video/mp4")

    def convert_modality(self, items):
        out = []
        for it in items:
            if isinstance(it, dict) and "sampling_rate" in it:
                out.append(self.encode_audio(it))
            elif isinstance(it, str):  # path -> video
                try:
                    out.append(self.encode_video(it))
                except Exception as e:
                    eval_logger.error(f"video upload failed: {e}")
                    out.append(None)
            elif isinstance(it, Image.Image):
                out.append(it)
            else:
                out.append(it)
        return out

    def construct_interleaved_input(self, content: str, media: list):
        """Same <media_N> parser as gemini_api.py."""
        pattern = r"<media_(\d+)>"
        parts = re.split(pattern, content)
        result = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                if part == "":
                    continue
                result.append(part)
            else:
                result.append(media[int(part)])
        return result

    def loglikelihood(self, requests):  # pragma: no cover
        raise NotImplementedError("Gemini API is generation-only.")

    def generate_until_multi_round(self, requests):  # pragma: no cover
        # XModBench is single-turn; fall through to generate_until.
        return self.generate_until(requests)

    # ------- main loop -------
    def generate_until(self, requests) -> List[GenerationResult]:
        res = []
        pbar = tqdm(total=len(requests), disable=(self.rank != 0), desc="Model Responding")

        for contexts, gen_kwargs, doc_to_visual, doc_id, task, split in [r.args for r in requests]:
            # Resume: skip items already cached on disk from a prior crashed
            # run. The cache is keyed by (task, doc_id) so the same lite task
            # picks up exactly where it stopped.
            key = (task, doc_id)
            cached = self.resume_cache.get(key)
            if cached is not None:
                res.append(GenerationResult(text=cached.get("text", ""), token_counts=None))
                pbar.update(1)
                continue
            if is_budget_exceeded():
                res.append(GenerationResult(text="", token_counts=None))
                pbar.update(1)
                continue
            # Gemini 3.x is a thinking model; ~12+ tokens of every reply go to
            # internal reasoning before any visible text. XModBench's task yaml
            # ships max_new_tokens=16, which leaves 0 tokens for visible text
            # (finish_reason=MAX_TOKENS, empty resp.text). Override anything
            # below 4096 with 4096 to give the thinking budget enough headroom.
            mnt = gen_kwargs.get("max_new_tokens", 1024) or 1024
            gen_kwargs["max_new_tokens"] = max(mnt, 4096)
            gen_kwargs.setdefault("temperature", 0)

            visuals = [doc_to_visual(self.task_dict[task][split][doc_id])]
            visuals = self.flatten(visuals)
            visuals = self.convert_modality(visuals)

            if self.interleave:
                message = self.construct_interleaved_input(contexts, visuals)
            else:
                message = [contexts] + visuals
            # Drop any failed uploads (None entries).
            message = [m for m in message if m is not None]

            cfg = gtypes.GenerateContentConfig(
                max_output_tokens=gen_kwargs["max_new_tokens"],
                temperature=gen_kwargs["temperature"],
                # New SDK exposes BLOCK_NONE via string thresholds.
                safety_settings=[
                    gtypes.SafetySetting(category=c, threshold="BLOCK_NONE")
                    for c in (
                        "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "HARM_CATEGORY_HATE_SPEECH",
                        "HARM_CATEGORY_HARASSMENT",
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    )
                ],
            )

            text_out = ""
            token_counts = None
            for attempt in range(5):
                try:
                    resp = self.client.models.generate_content(
                        model=self.model_version,
                        contents=message,
                        config=cfg,
                    )
                    text_out = resp.text or ""
                    um = getattr(resp, "usage_metadata", None)
                    if um is not None:
                        in_tok = getattr(um, "prompt_token_count", 0) or 0
                        out_tok = getattr(um, "candidates_token_count", 0) or 0
                        log_usage(
                            model_name=self.model_version,
                            task_name=task,
                            input_tokens=in_tok,
                            output_tokens=out_tok,
                            reasoning_tokens=getattr(um, "thoughts_token_count", 0) or 0,
                            source="model",
                        )
                        token_counts = TokenCounts(input_tokens=in_tok, output_tokens=out_tok)
                    break
                except Exception as e:
                    msg = str(e)
                    eval_logger.info(f"attempt {attempt + 1}/5 failed: {msg[:200]}")
                    if attempt < 4:
                        time.sleep(NUM_SECONDS_TO_SLEEP)
                    else:
                        text_out = ""

            # Persist this item to the resume sidecar BEFORE pbar.update so a
            # 503 / Ctrl-C between items never loses it.
            try:
                sidecar = self.resume_dir / f"{task}.jsonl"
                with sidecar.open("a") as fp:
                    fp.write(json.dumps({
                        "doc_id": doc_id,
                        "task": task,
                        "text": text_out,
                        "ts": time.time(),
                    }) + "\n")
                self.resume_cache[key] = {"text": text_out}
            except Exception as e:  # cache writes must never break the run
                eval_logger.warning(f"resume cache write failed: {e}")

            res.append(GenerationResult(text=text_out, token_counts=token_counts))
            pbar.update(1)
            self.free_video()  # release uploaded media each item

        return res
