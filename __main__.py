from math import ceil, floor
from silence import detect_leading_silence, detect_ending_silence
from vgmstream_file import seg_from_vgmstream
from os import path, makedirs
from glob import iglob
from sys import argv
from snap_to_bpm_lut import SNAP_TO_BGM_LUT


SILENCE_THRESOLD = -36 # dBFS
CHUNK_SIZE = 0.1
# For use with BPM estimation in FL Studio
# This is ONLY MEANT FOR DEBUGGING and drops the txtps to the !!silence_start folder
STRIP_START_ONLY = False
CHECKED_EXTENSIONS = [".m4a", ".mp3"]
# Remove this comment after editing a txtp file to prevent clobbering
TOOL_SIG = "# AUTO-GENERATED with batch_silence_detection."
DETECT_AUTOGENERATED_AND_CLOBBER = False


def ms_to_samples(ms, frame_rate):
    # This should absolutely return a int, otherwise vgmstream will interpret the number as seconds
    return ceil(ms / 1000 * frame_rate)

def snap_to_bpm(ms, bpm, roundover_hack=False):
    """Snap a given time in milliseconds to the nearest beat based on the specified BPM"""
    if bpm <= 0: return ms
    beat_length = 60 / bpm * 1000
    if roundover_hack:
        return ceil(ms / beat_length) * beat_length
    return floor(ms / beat_length) * beat_length

if len(argv) > 1:
    work_dir = argv[1]
else:
    work_dir = input("work dir : ")
work_dir = path.relpath(work_dir)
out_dir = work_dir

if STRIP_START_ONLY:
    out_dir = path.join(work_dir, "!!silence_start")
    makedirs(out_dir, exist_ok=True)


for sound_path in iglob(path.join(work_dir, "*")):
    if path.exists(path.join(out_dir, path.basename(sound_path) + ".bsdt_ignore")):
        continue

    sound_name_parts = path.splitext(path.basename(sound_path))
    if sound_name_parts[1] not in CHECKED_EXTENSIONS:
        continue

    sound_name = sound_name_parts[0]
    sound_txtp_path = path.join(out_dir, sound_name + ".txtp")
    if path.exists(sound_txtp_path):
        if DETECT_AUTOGENERATED_AND_CLOBBER:
            with open(sound_txtp_path, "r", encoding="utf-8-sig") as sound_txtp:
                if TOOL_SIG in sound_txtp.read():
                    print(f"\tClobbering apparently auto-generated {sound_txtp_path}")
                else:
                    continue
        else:
            continue
    print(sound_path)

    sound_bpm = SNAP_TO_BGM_LUT.get(path.realpath(sound_path), -1)
    sound_bpm_roundover_hack = False
    if isinstance(sound_bpm, tuple):
        sound_bpm, sound_bpm_roundover_hack = sound_bpm
    if sound_bpm > 0:
        print(f"\tBPM override: {sound_bpm}")
    strip_start_only_here = STRIP_START_ONLY or sound_bpm == -100
    if strip_start_only_here:
        print(f"\tOnly stripping start")

    sound = seg_from_vgmstream(sound_path)
    lead_trim_ms = detect_leading_silence(sound, silence_threshold=SILENCE_THRESOLD, chunk_size=CHUNK_SIZE)
    lead_trimmed_dur = sound.duration_seconds * 1000 - lead_trim_ms
    lead_trim = ms_to_samples(lead_trim_ms, frame_rate=sound.frame_rate)
    if not strip_start_only_here:
        end_trim_ms = detect_ending_silence(sound[lead_trim_ms:], silence_threshold=SILENCE_THRESOLD, chunk_size=CHUNK_SIZE)
        end_trim_ms = snap_to_bpm(end_trim_ms, bpm=sound_bpm, roundover_hack=sound_bpm_roundover_hack)
        if end_trim_ms > lead_trimmed_dur:
            print(f"\tSnapped end silence to beat, but it's longer than the lead trimmed duration ({lead_trimmed_dur} ms)")  
            end_trim_ms = lead_trimmed_dur
        end_trim_ms = lead_trim_ms + end_trim_ms
        end_trim = ms_to_samples(end_trim_ms, frame_rate=sound.frame_rate)
    if lead_trim == 0 and (not strip_start_only_here or end_trim == sound.duration_seconds * sound.frame_rate):
        print("\tNo silence detected")
        continue

    commands = f"#r {lead_trim}"
    if not strip_start_only_here:
        commands += f" #t {end_trim}"
    print(f"\tStripping config determined: {commands}")
    with open(sound_txtp_path, "w", encoding="utf-8-sig") as sound_txtp:
        sound_txtp.write(TOOL_SIG)
        if sound_bpm >= 0:
            sound_txtp.write(f"\n# BPM set to: {sound_bpm}")
        sound_txtp.write(f"\n")
        sound_txtp.write(path.relpath(sound_path, start=out_dir) + " " + commands)