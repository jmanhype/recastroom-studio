# Synthetic E2E fixtures

`synthetic_source.mp4` is a 2.041667-second, 640×240, 24 fps H264 video with a
synthetic 440 Hz AAC audio track. `synthetic_reference.png` is a one-frame
synthetic PNG. Both are generated entirely from ffmpeg `testsrc2`; they contain
no human likeness, third-party content, or recorded performance.

`word_timings.json` contains synthetic timing intervals matching this source.

Deterministic source-generation command:

```sh
ffmpeg -y -bitexact -f lavfi -i 'testsrc2=size=640x240:rate=24' \
  -f lavfi -i 'sine=frequency=440:sample_rate=48000' -t 2.04 \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -preset veryfast -crf 28 \
  -pix_fmt yuv420p -x264-params 'bframes=0' -c:a aac -b:a 64k \
  -ar 48000 -movflags +faststart tests/fixtures/synthetic_source.mp4
```
