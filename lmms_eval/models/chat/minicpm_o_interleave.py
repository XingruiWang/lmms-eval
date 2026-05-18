"""minicpm_o_interleave — MiniCPM-o over interleaved doc_to_messages.

See `_interleave_base.InterleaveChatMixin` for the shared rationale and
request loop. MiniCPM-o's `model.chat` takes a single user message whose
`content` is an ordered list mixing PIL images, np audio arrays, extracted
video frames, and text. The stock `minicpm_o` wrapper only attaches one
media object per request; here we build the full interleaved content list
from the task's doc_to_messages so the question stem and all four options
keep their media + order.
"""

import numpy as np
import soundfile as sf
from loguru import logger as eval_logger
from PIL import Image

from lmms_eval.api.registry import register_model
from lmms_eval.models.chat._interleave_base import InterleaveChatMixin
from lmms_eval.models.simple.minicpm_o import MiniCPM_O, encode_video


@register_model("minicpm_o_interleave")
class MiniCPM_O_Interleave(InterleaveChatMixin, MiniCPM_O):
    """MiniCPM-o that consumes interleaved doc_to_messages prompts."""

    def _infer_one(self, messages: list, gen_kwargs: dict) -> str:
        content = []
        has_audio = False
        for msg in messages:
            blocks = msg.get("content")
            if not isinstance(blocks, list):
                continue
            for c in blocks:
                t = c.get("type")
                if t == "text":
                    content.append(c.get("text", ""))
                elif t == "image":
                    content.append(Image.open(c["url"]).convert("RGB"))
                elif t == "video":
                    try:
                        content.extend(encode_video(c["url"], self.max_num_frames))
                    except Exception as e:
                        eval_logger.warning(f"video encode failed {c['url']}: {e}")
                elif t == "audio":
                    arr, srate = sf.read(c["url"], dtype="float32")
                    if arr.ndim > 1:
                        arr = arr.mean(axis=1)
                    content.append(self.resample_audio(np.asarray(arr), srate))
                    has_audio = True

        msgs = [{"role": "user", "content": content}]
        temperature = gen_kwargs.get("temperature", 0)
        chat_kwargs = {
            "msgs": msgs,
            "tokenizer": self.tokenizer,
            "sampling": temperature > 0,
            "max_new_tokens": gen_kwargs.get("max_new_tokens", 512),
        }
        if temperature > 0:
            chat_kwargs["temperature"] = temperature
        if gen_kwargs.get("top_p"):
            chat_kwargs["top_p"] = gen_kwargs["top_p"]
        if has_audio and self.init_audio:
            chat_kwargs["omni_input"] = True

        response = self.model.chat(**chat_kwargs)
        if isinstance(response, tuple):
            return response[0] if response else ""
        if isinstance(response, dict):
            return response.get("text", response.get("response", str(response)))
        return str(response) if response else ""
