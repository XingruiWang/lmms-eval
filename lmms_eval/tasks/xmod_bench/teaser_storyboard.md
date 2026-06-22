# XModBench teaser — storyboard (≈52 s, 1080p, ICLR 2026 palette)

Continuity motifs: the red **≠** device (cross-modal inconsistency),
the 3×3 directional grid, the 5-family color band, no narration —
on-screen text + one real dog-bark SFX hit in the hook.

| # | t (s) | Visual | On-screen text | Notes |
|---|-------|--------|----------------|-------|
| **S1 Hook** | 0–6 | L: real dog photo → `🐕 Dog ✓` (green). R: waveform of the *same* dog barking (1 audio hit) → `"a person talking" ✗` (red). Center slams **🐕 ≠ 🔊**, the ≠ pulses red. | `Which represents a dog?` ×2 → **"A model that knows a dog by sight can't hear one."** | Use a *real* paired sample from XModBench perception (vggss). |
| **S2 6 settings** | 6–14 | The ≠ resolves into a 3×3 grid; rows = source {Audio, Vision, Text}, cols = target; 6 off-diagonal cells light up one by one. | **"6 cross-modal directions"** · A→T A→V T→A T→V V→A V→T | Vision = Image ∪ Video (small subtitle). |
| **S3 5 families** | 14–22 | Grid slides left; a 5-band color stack rises: Perception · Spatial · Temporal · Linguistic · Knowledge, each with a 1-line icon. | **"5 broad task families · 17 subtasks · 61,320 samples"** | Conveys breadth. |
| **S4 Finding 1** | 22–32 | Bars grow per family (real Qwen2.5-Omni Lite): Linguistic **81** … Perception 73 … Knowledge 62 … Spatial **31** … Temporal **19**. Spatial+Temporal bars flash red, drop. | **"Spatial & temporal reasoning collapses — 19% / 31% vs 81%."** | Numbers are real. |
| **S5 Finding 2** | 32–42 | Same concept, two modalities, two different scores; a seesaw tilts (modality **disparity**); arrows A→T vs T→A unequal length (directional **imbalance**). | **"Severe modality disparity & directional imbalance — the same knowledge, unequal across modalities."** | Callback to the ≠. |
| **S6 Insight** | 42–50 | Split: "single-media prompt" (model sees 1 thing, guesses) vs "interleaved prompt" (question + 4 media options together → consistent). The interleaved side turns green. | **"Cross-modal consistency needs interleaved multi-media — not modalities in isolation."** | The paper's core insight / why the eval is interleaved. |
| **S7 Card** | 50–52 | Title card, palette match. | **XModBench** · ICLR 2026 · xingruiwang.github.io/projects/XModBench | Logo / arXiv 2510.15148. |

Render: matplotlib/PIL frames @ 30 fps → ffmpeg `libx264 -pix_fmt yuv420p`,
crossfades via `xfade`, the dog-bark SFX muxed only over S1.
