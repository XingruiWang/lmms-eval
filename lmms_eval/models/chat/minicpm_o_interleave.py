"""minicpm_o_interleave — MiniCPM-o over interleaved doc_to_messages.

See `_interleave_base.InterleaveChatMixin` for the shared rationale and
request loop. MiniCPM-o's `model.chat` takes a single user message whose
`content` is an ordered list mixing PIL images, np audio arrays, extracted
video frames, and text. The stock `minicpm_o` wrapper only attaches one
media object per request; here we build the full interleaved content list
from the task's doc_to_messages so the question stem and all four options
keep their media + order.
"""

import os
import traceback

import numpy as np
import soundfile as sf
from loguru import logger as eval_logger
from PIL import Image

from lmms_eval.api.registry import register_model
from lmms_eval.models.chat._interleave_base import InterleaveChatMixin
from lmms_eval.models.simple.minicpm_o import MiniCPM_O, encode_video

# Per-item error log for the v2a residual debug pass. The
# InterleaveChatMixin swallows generate-time exceptions and writes "" to
# the samples file, which makes failure modes invisible from the jsonl.
# Append-only so a single file accumulates across runs.
_ERR_LOG_PATH = os.environ.get(
    "MINICPM_INTERLEAVE_ERROR_LOG", "/tmp/minicpm_v2a_errors.log"
)


def _log_error(tag: str, msg: str) -> None:
    try:
        with open(_ERR_LOG_PATH, "a") as f:
            f.write(f"[{tag}] {msg}\n")
    except Exception:  # pragma: no cover — best-effort logging
        pass


@register_model("minicpm_o_interleave")
class MiniCPM_O_Interleave(InterleaveChatMixin, MiniCPM_O):
    """MiniCPM-o that consumes interleaved doc_to_messages prompts."""

    # XModBench packs media in the question stem *and* all 4 options, so a
    # single prompt can carry 5 images/videos. At full resolution MiniCPM-o's
    # slicing vision encoder OOMs a 24 GB card and the request is caught as
    # empty. Cap the long side and the per-clip frame count so 5 media fit.
    OPT_MAX_SIDE = 336
    OPT_MAX_FRAMES = 6
    OPT_MAX_AUDIO_SEC = 30  # cap option-audio length (long songs OOM the 4-audio configs)

    # Total audio budget across ALL audio blocks in a single prompt. The
    # per-audio cap (OPT_MAX_AUDIO_SEC) is not enough on its own: in the v2a
    # config (1 image stem + 4 audio options) the per-option 30 s clips sum
    # to 120 s, and the audio encoder + projector pipeline OOMs / hits a
    # placeholder mismatch on every single movie_matching and
    # singer_identification item (100/105 of the 1k-Lite empties; the
    # remaining 5 are speech items with ~80 s total). We trim each audio
    # proportionally so the sum stays under this budget. The previous 60 s
    # value still OOM'd at lm_head because MiniCPM-o's chat() defaults to
    # num_beams=3, tripling the KV-cache footprint over the long audio-
    # token sequence; we now force num_beams=1 below (see _generate) and
    # can keep this comfortable.
    TOTAL_AUDIO_BUDGET_SEC = 48

    # On the first attempt failing for any reason, retry once with a
    # tightened budget before falling back to empty. These are applied in
    # _infer_one_with_retry.
    RETRY_TOTAL_AUDIO_BUDGET_SEC = 24
    RETRY_OPT_MAX_AUDIO_SEC = 8
    RETRY_OPT_MAX_SIDE = 280
    RETRY_OPT_MAX_FRAMES = 4

    # MiniCPM-o's processor counts audio placeholders **per individual audio**
    # (see processing_minicpmo.get_audio_placeholder), but `audio_feature_extract`
    # hstacks every audio that shares the same `audio_parts` index — and the chat
    # API gives all audios in a single user message the SAME part index. So in
    # the v2a config (1 stem video + 4 option audios → 4 audios merged into one
    # block), the sum of per-audio placeholders no longer equals the merged
    # block's `feature_lens_after_pooling`, and ~4.5% of items crash with
    # "tensor (N) must match (N-1) at non-singleton dim 0".
    #
    # The placeholder formula is `(((ceil(L/hop) - 1)//2 + 1) - pool)//pool + 1`
    # with hop=160 and pool=2. Whenever L is a multiple of 640 (= hop*2*pool =
    # 40 ms at 16 kHz) the integer flooring vanishes and placeholders are
    # additive under concatenation: sum_i out(L_i) == out(sum_i L_i). Trimming
    # each resampled audio down to floor(L/640)*640 samples therefore guarantees
    # the merged block's token count matches the sum of per-audio placeholders.
    AUDIO_ALIGN_SAMPLES = 640  # = hop_length(160) * cnn_stride(2) * pool_step(2)

    def _shrink(self, img, max_side: int | None = None):
        max_side = max_side or self.OPT_MAX_SIDE
        w, h = img.size
        m = max(w, h)
        if m > max_side:
            s = max_side / m
            img = img.resize((max(1, int(w * s)), max(1, int(h * s))))
        return img

    def _align_audio(self, audio: np.ndarray) -> np.ndarray:
        """Trim a 16-kHz mono audio np.array down to a multiple of 640 samples.

        See AUDIO_ALIGN_SAMPLES for the derivation. This must be applied
        AFTER resampling so the hop/pool/cnn alignment math is valid.
        """
        if not isinstance(audio, np.ndarray):
            return audio
        n = audio.shape[-1]
        n_aligned = (n // self.AUDIO_ALIGN_SAMPLES) * self.AUDIO_ALIGN_SAMPLES
        if n_aligned == 0:
            # Audio is shorter than 40 ms — pad to one frame so it still produces
            # a valid (and matching) placeholder block.
            pad = self.AUDIO_ALIGN_SAMPLES - n
            return np.pad(audio, (0, pad), mode="constant").astype(np.float32, copy=False)
        if n_aligned == n:
            return audio
        return audio[..., :n_aligned]

    def _build_content(
        self,
        messages: list,
        *,
        max_side: int,
        max_frames: int,
        per_audio_sec: float,
        total_audio_budget_sec: float,
    ) -> tuple[list, bool, dict]:
        """Materialize doc_to_messages into the flat list MiniCPM-o expects.

        Returns (content, has_audio, debug_info). debug_info captures the
        media-count signature we log on failure.
        """
        # First pass: load every audio so we know the total length, then
        # decide per-audio trims that keep `sum(durations) <= budget`.
        raw_audios: list[np.ndarray] = []
        for msg in messages:
            blocks = msg.get("content")
            if not isinstance(blocks, list):
                continue
            for c in blocks:
                if c.get("type") != "audio":
                    continue
                arr, srate = sf.read(c["url"], dtype="float32")
                if arr.ndim > 1:
                    arr = arr.mean(axis=1)
                cap = int(per_audio_sec * srate)
                if arr.shape[0] > cap:
                    arr = arr[:cap]
                # Resample to model rate ONCE so the budget below is in a
                # single sample-rate space.
                resampled = self.resample_audio(np.asarray(arr), srate)
                raw_audios.append(resampled)

        # Target sample-rate (post-resample). Assume all resampled audios
        # share the same rate; use the configured audio sample rate. The
        # base wrapper sets self.audio_sample_rate; fall back to 16000.
        target_sr = int(getattr(self, "audio_sample_rate", 16000) or 16000)
        total_samples = sum(a.shape[-1] for a in raw_audios)
        budget_samples = int(total_audio_budget_sec * target_sr)
        if raw_audios and total_samples > budget_samples:
            # Proportional trim: each audio keeps the same fraction of the
            # over-budget total. Distribute at least 1 align-step per audio.
            min_per = self.AUDIO_ALIGN_SAMPLES
            scale = budget_samples / total_samples
            trimmed = []
            for a in raw_audios:
                keep = max(min_per, int(a.shape[-1] * scale))
                trimmed.append(a[..., :keep])
            raw_audios = trimmed

        # Second pass: build the final content list, drawing trimmed audios
        # in order.
        audio_iter = iter(raw_audios)
        content: list = []
        has_audio = False
        n_image = n_video = n_audio = 0
        for msg in messages:
            blocks = msg.get("content")
            if not isinstance(blocks, list):
                continue
            for c in blocks:
                t = c.get("type")
                if t == "text":
                    content.append(c.get("text", ""))
                elif t == "image":
                    content.append(
                        self._shrink(Image.open(c["url"]).convert("RGB"), max_side=max_side)
                    )
                    n_image += 1
                elif t == "video":
                    try:
                        nf = min(self.max_num_frames, max_frames)
                        content.extend(
                            self._shrink(f, max_side=max_side) for f in encode_video(c["url"], nf)
                        )
                        n_video += 1
                    except Exception as e:
                        eval_logger.warning(f"video encode failed {c['url']}: {e}")
                elif t == "audio":
                    arr = next(audio_iter)
                    content.append(self._align_audio(arr))
                    has_audio = True
                    n_audio += 1

        dbg = {
            "n_image": n_image,
            "n_video": n_video,
            "n_audio": n_audio,
            "total_audio_sec": round(
                sum(a.shape[-1] for a in raw_audios) / max(target_sr, 1), 2
            ),
            "max_side": max_side,
        }
        return content, has_audio, dbg

    def _generate(self, messages: list, gen_kwargs: dict, *, attempt: str) -> str:
        if attempt == "retry":
            content, has_audio, dbg = self._build_content(
                messages,
                max_side=self.RETRY_OPT_MAX_SIDE,
                max_frames=self.RETRY_OPT_MAX_FRAMES,
                per_audio_sec=self.RETRY_OPT_MAX_AUDIO_SEC,
                total_audio_budget_sec=self.RETRY_TOTAL_AUDIO_BUDGET_SEC,
            )
        else:
            content, has_audio, dbg = self._build_content(
                messages,
                max_side=self.OPT_MAX_SIDE,
                max_frames=self.OPT_MAX_FRAMES,
                per_audio_sec=self.OPT_MAX_AUDIO_SEC,
                total_audio_budget_sec=self.TOTAL_AUDIO_BUDGET_SEC,
            )

        msgs = [{"role": "user", "content": content}]
        temperature = gen_kwargs.get("temperature", 0)
        chat_kwargs = {
            "msgs": msgs,
            "tokenizer": self.tokenizer,
            "sampling": temperature > 0,
            "max_new_tokens": gen_kwargs.get("max_new_tokens", 512),
            # MiniCPM-o's chat() defaults to num_beams=3 internally (see
            # modeling_minicpmo.py line ~992). With 4×audio in a v2a item the
            # KV cache for beam=3 hits 5+ GB at lm_head and OOMs on a 24 GB
            # card — that was the dominant failure mode for the 105 empty
            # responses in the post-Approach-A run. The XModBench task
            # config already sets num_beams=1, but lmms-eval's generate_until
            # path doesn't forward num_beams into the MiniCPM-o chat call.
            # Force it here. greedy is fine for an A/B/C/D classification
            # task; quality on the working items is unchanged at 200-sample
            # smoke.
            "num_beams": int(gen_kwargs.get("num_beams", 1) or 1),
        }
        if temperature > 0:
            chat_kwargs["temperature"] = temperature
        if gen_kwargs.get("top_p"):
            chat_kwargs["top_p"] = gen_kwargs["top_p"]
        if has_audio and self.init_audio:
            chat_kwargs["omni_input"] = True

        try:
            response = self.model.chat(**chat_kwargs)
        except Exception:
            # Attach the media-count signature so the appended log entry is
            # actionable without re-running.
            _log_error(
                f"chat-fail/{attempt}",
                f"dbg={dbg} | {traceback.format_exc().splitlines()[-1]}",
            )
            raise

        if isinstance(response, tuple):
            return response[0] if response else ""
        if isinstance(response, dict):
            return response.get("text", response.get("response", str(response)))
        return str(response) if response else ""

    def _infer_one(self, messages: list, gen_kwargs: dict) -> str:
        try:
            return self._generate(messages, gen_kwargs, attempt="primary")
        except Exception as primary_exc:
            # Free any half-allocated CUDA tensors before the retry so the
            # smaller budget actually has room to run.
            try:
                import torch

                torch.cuda.empty_cache()
            except Exception:
                pass
            try:
                out = self._generate(messages, gen_kwargs, attempt="retry")
                _log_error(
                    "recovered",
                    f"primary={type(primary_exc).__name__}: {primary_exc}",
                )
                return out
            except Exception as retry_exc:
                _log_error(
                    "gave-up",
                    f"primary={type(primary_exc).__name__}: {primary_exc} | "
                    f"retry={type(retry_exc).__name__}: {retry_exc}",
                )
                # Propagate so the mixin's outer except records it normally.
                raise retry_exc
