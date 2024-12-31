from math import ceil
from silence import detect_leading_silence, detect_ending_silence
from vgmstream_file import seg_from_vgmstream
from os import path
from glob import iglob
from sys import argv


SILENCE_THRESOLD = -40 # dBFS


if len(argv) > 1:
    work_dir = argv[1]
else:
    work_dir = input("work dir : ")
work_dir = path.relpath(work_dir)


for sound_path in iglob(path.join(work_dir, "*")):
    sound_nameparts = path.splitext(sound_path)
    if sound_nameparts[1] not in [".m4a", ".mp3"]:
        continue
    print(sound_path)

    sound_name = sound_nameparts[0]
    sound_txtp_path = sound_name + ".txtp"
    if path.exists(sound_txtp_path):
        print(f"\t{sound_txtp_path} already exists")
        continue

    sound = seg_from_vgmstream(sound_path)
    def ms_to_samples(ms):
        return ceil(ms / 1000 * sound.frame_rate)
    lead_trim = ms_to_samples(detect_leading_silence(sound, silence_threshold=SILENCE_THRESOLD, chunk_size=1))
    end_trim = ms_to_samples(detect_ending_silence(sound, silence_threshold=SILENCE_THRESOLD, chunk_size=1))

    commands = f"#r {lead_trim} #t {end_trim}"
    print(f"\t{commands}")
    with open(sound_txtp_path, "w", encoding="utf-8-sig") as sound_txtp:
        sound_txtp.write(path.relpath(sound_path, start=work_dir) + " " + commands)