# Lapis Break

Full-colour **Python 3** neon vertical billiards for **ElbowOS**.
Cue a glowing rack on a lapis felt table, ricochet off gold rails, and sink prism balls.

Featured: [https://x.com/ElbowOS](https://x.com/ElbowOS)

Reel MP4 (9:16, 15s): [Google Drive](https://drive.google.com/file/d/1SNAHokz1TnkocLYvtpG0VG0h6RN_bl43/view)

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 lapis_break.py --play
```

Drag to aim the cue, click to break. Esc quits.

## Record a 9:16 reel

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 lapis_break.py
```

Writes `/home/workdir/artifacts/LAPIS_BREAK_ElbowOS.mp4` (1080x1920, 30fps, H.264).

Original arcade table — not a clone of prior ElbowOS packs.
