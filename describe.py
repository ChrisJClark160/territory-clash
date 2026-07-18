"""Generate upload packaging from a battle's metadata sidecar.

Titles, the pinned comment and the description are written from what
actually happened in the battle (photo finish / comeback / blowout /
256-moment), never a generic template - the sidecar is the story.

Called by render.py after the sidecar is written; also usable standalone:
    python describe.py output/batch/cats_vs_dogs.json
"""

import json
import os
import sys

# Priority order: the rarest/strongest story wins the title.
MAX_VALUE = 256


def _story(meta):
    a, b = meta["teams"]
    winner = meta["winner"]
    loser = b if winner == a else a
    diff = abs(meta["final_score"][0] - meta["final_score"][1])
    if winner == "DRAW":
        return f"{a} vs {b} ended in a PERFECT TIE - watch it happen"
    if meta["biggest_power"] >= MAX_VALUE:
        kind = "burst" if meta["biggest_event"] == "burst" else "charged shot"
        return f"A {MAX_VALUE} {kind} decided {a} vs {b} 😱"
    if diff <= 4:
        return f"{a} vs {b} - decided by the FINAL tiles!"
    if meta["max_swing"] >= 25:
        return f"{winner} came back from the DEAD against {loser}"
    if diff >= 30:
        return f"{winner} DESTROYED {loser}... or did they?"
    if meta["lead_changes"] >= 2:
        return f"{a} vs {b} - {meta['lead_changes']} lead changes, one winner"
    return f"{a} vs {b} - who takes the territory?"


def describe(meta, music=None):
    """Return (title, pinned_comment, description)."""
    a, b = meta["teams"]
    title = _story(meta)

    pinned = f"Team {a} or Team {b}? Pick your side 👇"

    stats = []
    if meta["lead_changes"]:
        stats.append(f"{meta['lead_changes']} lead changes")
    if meta["biggest_power"] > 1:
        kind = "burst" if meta["biggest_event"] == "burst" else "charged shot"
        stats.append(f"biggest hit {meta['biggest_power']} ({kind})")
    stats.append(f"final score {meta['final_score'][0]}-{meta['final_score'][1]}")

    lines = [
        f"{a} vs {b} - territory battle. {', '.join(stats).capitalize()}.",
        "",
        "Every ball flips tiles to its colour. Green pads multiply a ball's "
        "power, red pads cash it in as a burst or a charged shot. "
        "Most territory when the timer ends wins.",
        "",
        "Who did you back? Pick your side in the comments 👇",
        "New battle every day.",
    ]
    if music:
        lines += ["", f"Music: {os.path.splitext(music)[0]} (NoCopyrightSounds)"]
    tags = ["#Shorts", "#battle", "#satisfying", "#simulation",
            f"#{a.lower().replace(' ', '')}", f"#{b.lower().replace(' ', '')}"]
    lines += ["", " ".join(tags)]
    return title, pinned, "\n".join(lines)


def write_for(meta, mp4_path, music=None):
    """Write <name>.txt next to the MP4; returns the path."""
    title, pinned, description = describe(meta, music=music)
    txt_path = os.path.splitext(mp4_path)[0] + ".txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"TITLE: {title}\n\nPINNED COMMENT: {pinned}\n\n"
                f"DESCRIPTION:\n{description}\n")
    return txt_path


if __name__ == "__main__":
    for meta_path in sys.argv[1:]:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        mp4 = os.path.splitext(meta_path)[0] + ".mp4"
        print(write_for(meta, mp4))
