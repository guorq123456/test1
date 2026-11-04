import sys, time
from faster_whisper import WhisperModel
S = sys.argv[1]; size = sys.argv[2]
t = time.time()
m = WhisperModel(size, device="cpu", compute_type="int8", cpu_threads=4)
segs, info = m.transcribe(f"{S}/audio.wav", language="zh", beam_size=1, vad_filter=True,
                          initial_prompt="以下是普通话视频的字幕，内容关于强化学习、皇室战争、模拟器、PPO。")
with open(f"{S}/transcript_{size}.txt", "w") as f:
    for s in segs:
        line = f"[{int(s.start//60):02d}:{int(s.start%60):02d}] {s.text}"
        print(line, file=f, flush=True)
print("done", time.time() - t)
