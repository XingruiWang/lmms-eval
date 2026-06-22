"""echoink_interleave — EchoInk-R1-7B over interleaved doc_to_messages.

EchoInk-R1-7B (https://huggingface.co/harryhsing/EchoInk-R1-7B) is an RL
fine-tune of Qwen2.5-Omni-7B that produces <think>...</think><answer>X</answer>
style reasoning traces. Architecturally it is identical to Qwen2.5-Omni
(Qwen2_5OmniForConditionalGeneration + Qwen2_5OmniProcessor), but inference
differs in three ways relative to the base Qwen wrapper:

  1. NO system prompt. The RL training script wraps everything in a single
     user turn; injecting "You are Qwen, a virtual human ..." degrades the
     reasoning template.
  2. The question text is wrapped with EchoInk's QUESTION_TEMPLATE +
     multiple-choice TYPE_TEMPLATE, instructing the model to emit
     <answer>LETTER</answer>.
  3. Generation matches EchoInk's training: do_sample=True, top_p=0.95,
     temperature=1, with enough new tokens for the reasoning trace
     (lmms-eval xmod_bench's default 16 is too short).

The answer extractor preferentially reads the <answer>...</answer> tag and
falls back to a bare A-D letter so XModBench's process_results can still
classify the response.

See `_interleave_base.InterleaveChatMixin` for the shared request loop.
"""

import re

from loguru import logger as eval_logger

from lmms_eval.api.registry import register_model
from lmms_eval.models.chat._interleave_base import (
    IMAGE_KWARGS,
    VIDEO_KWARGS,
    InterleaveChatMixin,
)
from lmms_eval.models.simple.qwen2_5_omni import Qwen2_5_Omni

try:
    from qwen_omni_utils import process_mm_info
except ImportError:
    eval_logger.warning("Failed to import qwen_omni_utils; install via `pip install qwen-omni-utils[decord]`")


# EchoInk-R1 RL-variant prompt template (from
# HarryHsing/EchoInk src/omniInstruct-v1_eval_valid.py).
ECHOINK_QUESTION_TEMPLATE = (
    "{Question}\n"
    "Please think about this question as if you were a human pondering deeply. "
    "Make sure to carefully consider both the visual and audio information before answering. "
    "Engage in an internal dialogue using expressions such as 'let me think', 'wait', 'Hmm', "
    "'oh, I see', 'let's break it down', etc, or other natural language thought expressions. "
    "It's encouraged to include self-reflection or verification in the reasoning process. "
    "Provide your detailed reasoning between the <think> </think> tags, and then give your "
    "final answer between the <answer> </answer> tags."
)
ECHOINK_MCQ_SUFFIX = (
    " Please provide only the single option letter (e.g., A, B, C, D, etc.) "
    "within the <answer> </answer> tags."
)

# Pattern for the canonical EchoInk answer payload.
_ANSWER_TAG_RE = re.compile(r"<answer>\s*([A-D])\s*</answer>", re.I)
_BARE_LETTER_RE = re.compile(r"\b([A-D])\b")


def _to_qwen_messages(messages: list, image_kwargs=None, video_kwargs=None) -> list:
    """doc_to_messages blocks -> Qwen-Omni native format with size/frame caps.

    Mirrors qwen2_5_omni_interleave._to_qwen_messages exactly so EchoInk
    consumes the same interleaved XModBench prompt structure.
    """
    image_kwargs = IMAGE_KWARGS if image_kwargs is None else image_kwargs
    video_kwargs = VIDEO_KWARGS if video_kwargs is None else video_kwargs
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
            elif t == "image":
                new_content.append({"type": "image", "image": c["url"], **image_kwargs})
            elif t == "video":
                new_content.append({"type": "video", "video": c["url"], **video_kwargs})
            elif t == "audio":
                new_content.append({"type": "audio", "audio": c["url"]})
            else:
                new_content.append(c)
        out.append({"role": msg["role"], "content": new_content})
    return out


def _wrap_with_echoink_template(messages: list) -> list:
    """Apply EchoInk's QUESTION_TEMPLATE + MCQ suffix to the user text.

    XModBench's doc_to_messages produces a single user turn whose content is
    a list of multimedia + text blocks (question, "A: ", optA, "B: ",
    optB, ..., post_prompt). EchoInk's training format expects a single
    free-text question (with the answer options already inlined) wrapped in
    its reasoning template.

    Strategy: collapse the trailing text blocks (question + options + the
    post_prompt) into one concatenated string, replace lmms-eval's
    "Answer with the option's letter ..." post-prompt with EchoInk's
    template-wrapped version. Media blocks are preserved in order.
    """
    out_messages = []
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            out_messages.append(msg)
            continue

        media_blocks = []
        text_parts = []
        for c in content:
            if c.get("type") == "text":
                text_parts.append(c.get("text", ""))
            else:
                media_blocks.append(c)

        raw_text = "".join(text_parts).strip()
        # Drop lmms-eval's bare "Answer with the option's letter ..." line if
        # present — EchoInk supplies its own MCQ instruction.
        raw_text = re.sub(
            r"\s*Answer with the option'?s? letter[^\n]*$",
            "",
            raw_text,
            flags=re.I,
        ).strip()

        wrapped = ECHOINK_QUESTION_TEMPLATE.format(Question=raw_text) + ECHOINK_MCQ_SUFFIX

        new_content = list(media_blocks) + [{"type": "text", "text": wrapped}]
        out_messages.append({"role": msg.get("role", "user"), "content": new_content})
    return out_messages


def _extract_echoink_answer(reply: str) -> str:
    """Pull a letter (A-D) out of an EchoInk reply.

    Preference order:
      1. <answer>X</answer> (canonical RL output)
      2. last bare A-D token (fallback)
      3. raw reply (let the task parser try)
    """
    if not reply:
        return ""
    # Strip a leading "assistant\n" prefix if the decoder preserved it.
    if "\nassistant" in reply:
        reply = reply.split("\nassistant", 1)[1].strip()

    m = _ANSWER_TAG_RE.search(reply)
    if m:
        return m.group(1).upper()

    # Take the LAST bare letter so chain-of-thought "let me think A vs B" is
    # not mis-extracted from the reasoning prefix.
    matches = list(_BARE_LETTER_RE.finditer(reply))
    if matches:
        return matches[-1].group(1).upper()

    return reply.strip()


@register_model("echoink_interleave")
class EchoInkInterleave(InterleaveChatMixin, Qwen2_5_Omni):
    """EchoInk-R1-7B consuming interleaved doc_to_messages prompts.

    Inherits weight loading from the simple Qwen2_5_Omni wrapper (same
    architecture). Overrides only the messages -> output step.
    """

    def __init__(
        self,
        pretrained: str = "harryhsing/EchoInk-R1-7B",
        # EchoInk-R1 training: do_sample=True, top_p=0.95, temperature=1.
        # Keep deterministic-by-default here; users can pass temperature>0
        # via generation_kwargs if they want to match training exactly.
        system_prompt: str = "",  # RL variant uses NO system prompt.
        **kwargs,
    ) -> None:
        super().__init__(pretrained=pretrained, system_prompt=system_prompt, **kwargs)
        # Reload processor from EchoInk repo (it ships its own chat template
        # + preprocessor_config that match the RL-trained model). The simple
        # Qwen2_5_Omni __init__ hardcodes the upstream Qwen processor; that
        # template injects a system prompt EchoInk wasn't trained on.
        try:
            from transformers import Qwen2_5OmniProcessor
            self.processor = Qwen2_5OmniProcessor.from_pretrained(pretrained)
            self._tokenizer = self.processor.tokenizer
        except Exception as exc:  # pragma: no cover
            eval_logger.warning(
                f"Failed to reload EchoInk processor from {pretrained}: {exc}. "
                "Falling back to base Qwen2.5-Omni processor."
            )

    def _infer_one(self, messages: list, gen_kwargs: dict) -> str:
        # 1) wrap text with EchoInk reasoning template
        messages = _wrap_with_echoink_template(messages)
        # 2) convert to Qwen-Omni native format (with media caps)
        hf_messages = _to_qwen_messages(messages, self.image_kwargs, self.video_kwargs)

        # EchoInk training did NOT mix audio into video tracks (separate
        # audio + video blocks for AVQA). Keep them separate.
        use_audio_in_video = False

        text = self.processor.apply_chat_template(hf_messages, add_generation_prompt=True, tokenize=False)
        audios, images, videos = process_mm_info(hf_messages, use_audio_in_video=use_audio_in_video)
        inputs = self.processor(
            text=text,
            audio=audios,
            images=images,
            videos=videos,
            return_tensors="pt",
            padding=True,
            use_audio_in_video=use_audio_in_video,
        )
        # Use self._model directly (not the `model` property): in some envs
        # (qwenomni3) `Accelerator.unwrap_model` eagerly imports deepspeed,
        # which fails when CUDA_HOME is unset and silently empties the reply.
        _m = self._model
        if self.device_map == "auto":
            inputs = inputs.to("cuda").to(_m.dtype)
        else:
            inputs = inputs.to(_m.device).to(_m.dtype)

        # EchoInk needs space for <think>...</think><answer>X</answer>.
        # lmms-eval's xmod_bench default is max_new_tokens=16 which truncates
        # the trace before the answer tag closes.
        if gen_kwargs.get("max_new_tokens", 16) < 512:
            gen_kwargs = dict(gen_kwargs)
            gen_kwargs["max_new_tokens"] = 1024
        gen_kwargs.setdefault("temperature", 0)
        gen_kwargs.setdefault("top_p", None)
        gen_kwargs.setdefault("num_beams", 1)

        cont = _m.generate(
            **inputs,
            return_audio=False,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
            do_sample=gen_kwargs["temperature"] > 0,
            temperature=gen_kwargs["temperature"] if gen_kwargs["temperature"] > 0 else None,
            top_p=gen_kwargs["top_p"],
            num_beams=gen_kwargs["num_beams"],
            max_new_tokens=gen_kwargs["max_new_tokens"],
            use_cache=self.use_cache,
            use_audio_in_video=use_audio_in_video,
            thinker_do_sample=False,
        )
        if isinstance(cont, tuple):
            cont = cont[0]
        # Decode the full sequence (see qwen2_5_omni_interleave for why we
        # don't trim by input_ids length on multimodal inputs).
        full = self.processor.batch_decode(cont, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        reply = full.split("assistant\n")[-1].strip()

        # EchoInk outputs <think>...</think><answer>X</answer>. XModBench's
        # process_results parses letters from the response — collapse the
        # trace to just the extracted letter so the task scorer doesn't get
        # confused by think-tag reasoning that happens to contain other
        # letters (e.g. "let's check option A vs C... <answer>B</answer>").
        letter = _extract_echoink_answer(reply)
        if letter and letter in ("A", "B", "C", "D"):
            return letter
        return reply
