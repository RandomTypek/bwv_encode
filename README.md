# Video → Binary Waterfall

Static, client-side converter. Drop a video, get a raw file whose bytes are the frames,
with the original audio packed into the upper bytes of each 32-bit sample.

Hosting on GitHub Pages: put `index.html` in the repo root (or `docs/`), enable Pages in
the repo settings, done. No build step, no dependencies beyond Google Fonts.

Companion CLI (ffmpeg + numpy): `bw_encode.py`.

Made with the help of Binary Waterfall: https://github.com/nimaid/binary-waterfall
