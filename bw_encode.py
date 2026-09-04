#!/usr/bin/env python3
"""
bw_encode.py -- turn any video into a raw file that Binary Waterfall plays back as real frames.

Layout: video frames stored back to back, pixel format "wxxx" (or "rxxxgxxxbxxx" with --color):
    byte 0 = pixel/colour byte, bytes 1-3 = top 3 bytes of a 32-bit audio sample.
Audio is 32-bit stereo; the pixel byte sits in the LSB (~-144 dB), so audio stays clean.
Sample rate is derived so that exactly one video frame scrolls past per 1/fps second.

Requires: ffmpeg in PATH, numpy.

Usage:
    python bw_encode.py bad_apple.mp4 bad_apple.bwv [--width 64 --height 48 --fps 25]

Binary Waterfall settings are printed at the end.
"""
import argparse, subprocess, sys
import numpy as np

def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        sys.exit(p.stderr.decode(errors="replace"))
    return p.stdout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--width", type=int, default=64)
    ap.add_argument("--height", type=int, default=48)
    ap.add_argument("--fps", type=int, default=25, help="use a divisor of 1000 (25, 20, 10) for exact export timing")
    ap.add_argument("--no-flip", action="store_true", help="store frames upright (then turn off Vertical Flip in BW)")
    ap.add_argument("--color", action="store_true", help="RGB (format rxxxgxxxbxxx, 3 words/pixel -> 3x the sample rate)")
    a = ap.parse_args()

    W, H, FPS = a.width, a.height, a.fps
    NB = 3 if a.color else 1         # colour bytes per pixel, each carried by its own 32-bit word
    PX = W * H * NB                  # 32-bit words (= samples) per frame
    CH, SB = 2, 4                    # stereo, 32-bit
    SR = PX * FPS // CH              # samples/sec/channel so that one frame = one 1/FPS period
    if SR * CH != PX * FPS:
        sys.exit("width*height*fps must be divisible by 2")

    vf = f"fps={FPS},scale={W}:{H}:flags=area,format={'rgb24' if a.color else 'gray'}"
    if not a.no_flip:
        vf += ",vflip"               # BW flips vertically by default
    video = run(["ffmpeg", "-v", "error", "-i", a.input, "-vf", vf, "-f", "rawvideo", "-"])
    audio = run(["ffmpeg", "-v", "error", "-i", a.input, "-vn", "-ac", str(CH), "-ar", str(SR),
                 "-f", "s32le", "-"])

    px = np.frombuffer(video, dtype=np.uint8)
    n_frames = len(px) // PX
    px = px[:n_frames * PX]

    au = np.frombuffer(audio, dtype="<i4").astype(np.uint32)
    need = n_frames * PX
    au = np.concatenate([au[:need], np.zeros(max(0, need - len(au)), np.uint32)])

    words = (au & 0xFFFFFF00) | px.astype(np.uint32)   # audio in top 3 bytes, pixel in LSB
    with open(a.output, "wb") as f:
        f.write(words.astype("<u4").tobytes())

    print(f"wrote {a.output}: {n_frames} frames, {n_frames * PX * 4:,} bytes, {n_frames / FPS:.1f} s")
    print("\nBinary Waterfall settings")
    print(f"  Audio : {CH} (stereo), 32-bit, {SR} Hz, volume 100%")
    fmt = "rxxxgxxxbxxx" if a.color else "wxxx"
    print(f"  Video : {W}px x {H}px, color format {fmt}, alignment Frame End, playhead OFF,")
    print(f"          vertical flip {'OFF' if a.no_flip else 'ON'}, horizontal flip OFF")
    print(f"  Player: {FPS} fps  (use the same fps when exporting)")

if __name__ == "__main__":
    main()
