from math import ceil, floor
from silence import detect_leading_silence, detect_ending_silence
from vgmstream_file import seg_from_vgmstream
from os import path, makedirs
from glob import iglob
from sys import argv
from snap_to_bpm_lut import SNAP_TO_BGM_LUT


SILENCE_THRESOLD = -36 # dBFS
# For use with BPM estimation in FL Studio
STRIP_START_ONLY = False


def ms_to_samples(ms, frame_rate):
    # This should absolutely return a int, otherwise vgmstream will interpret the number as seconds
    return ceil(ms / 1000 * frame_rate)

def snap_to_bpm(ms, bpm):
    """Snap a given time in milliseconds to the nearest beat based on the specified BPM"""
    if bpm <= 0: return ms
    beat_length = (1 * 60 * 1000) / bpm
    return ceil(ms / beat_length) * beat_length

if len(argv) > 1:
    work_dir = argv[1]
else:
    work_dir = input("work dir : ")
work_dir = path.relpath(work_dir)
out_dir = work_dir

if STRIP_START_ONLY:
    out_dir = path.join(work_dir, "silence_start")
    makedirs(out_dir, exist_ok=True)


for sound_path in iglob(path.join(work_dir, "*")):
    sound_name_parts = path.splitext(path.basename(sound_path))
    if sound_name_parts[1] not in [".m4a", ".mp3"]:
        continue

    sound_name = sound_name_parts[0]
    sound_txtp_path = path.join(out_dir, sound_name + ".txtp")
    if path.exists(sound_txtp_path):
        continue
    else:
        print(sound_path)

    sound_bpm = SNAP_TO_BGM_LUT.get(path.realpath(sound_path), -1)

    sound = seg_from_vgmstream(sound_path)
    lead_trim = ms_to_samples(
        detect_leading_silence(sound, silence_threshold=SILENCE_THRESOLD, chunk_size=1),
        frame_rate=sound.frame_rate
    )
    strip_start_only_here = STRIP_START_ONLY or sound_bpm == -100
    if not strip_start_only_here:
        end_trim = ms_to_samples(
            min(snap_to_bpm(
                detect_ending_silence(sound, silence_threshold=SILENCE_THRESOLD, chunk_size=1),
                bpm=sound_bpm
            ), sound.duration_seconds * 1000),
            frame_rate=sound.frame_rate
        )

    commands = f"#r {lead_trim}"
    if not strip_start_only_here:
        commands += f" #t {end_trim}"
    print(f"\t{commands}")
    with open(sound_txtp_path, "w", encoding="utf-8-sig") as sound_txtp:
        sound_txtp.write("# AUTO-GENERATED with batch_silence_detection.")
        if sound_bpm >= 0:
            sound_txtp.write(f"\n# BPM: {sound_bpm}")
        sound_txtp.write(f"\n")
        sound_txtp.write(path.relpath(sound_path, start=out_dir) + " " + commands)