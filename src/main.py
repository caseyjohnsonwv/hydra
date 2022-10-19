import argparse
import pathlib
from random import randint, random, choice
import moviepy.editor as mpe

DIMENSIONS = (1080, 1920)
THREAD_COUNT = 8
FPS = 30

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--audio', help='Audio file for video montage.')
parser.add_argument('-t', '--tempo', help='BPM of audio file.')
parser.add_argument('-d', '--directory', help='Parent directory containing all video clips. This is NOT explored recursively.')
parser.add_argument('-o', '--output', help='Path to place final output.mp4 video file.')
parser.add_argument('--randomize', default=False, action=argparse.BooleanOptionalAction, help='Option to randomize order of clips.')
parser.add_argument('--max-length', default=None, help='Maximum length of the video, in seconds.')
parser.add_argument('--max-clips', default=None, help='Maximum number of clips to be used in the video.')
ARGS = parser.parse_args()

# convert tempo to length of time in seconds
sbp = 1 / (int(ARGS.tempo) / 60)

# list clips in directory
dir = pathlib.Path(ARGS.directory)
clips = []
for f in dir.iterdir():
    if f.suffix == '.mp4':
        clips.append(dir.joinpath(f.name).as_posix())

print(f"Selecting clips from {len(clips)} files in {dir.as_posix()}.")

# select clips
total_time = 0
edit_list = []
while len(clips) > 0:
    # stop editing if needed
    if (ARGS.max_length and total_time >= int(ARGS.max_length)) or (ARGS.max_clips and len(edit_list) >= int(ARGS.max_clips)):
        break
    # choose clip
    if ARGS.randomize:
        clip = choice(clips)
    else:
        clip = clips[0]
    clips.remove(clip)
    with mpe.VideoFileClip(filename=clip) as f:
        # quick and dirty - pick length for clip, but ensure length we pick is valid
        max_clip_beats = min(f.duration / sbp // 2, 4)
        if max_clip_beats < 2:
            continue
        num_beats = randint(1, max_clip_beats) * 2
        target_length = sbp * num_beats
        if target_length > f.duration:
            continue
        # save list of tuples containing (clip file, start timestamp, end timestamp)
        start_ts = random() * (f.duration - target_length)
        end_ts = start_ts + target_length
        total_time += target_length
        clip_selection = (clip, start_ts, end_ts)
        edit_list.append(clip_selection)

print(f"Now editing {len(edit_list)} clips - this may take a moment.")

final_clips = []
for clip, start_ts, end_ts in edit_list:
    print(f"{clip} ({start_ts:.1f} -> {end_ts:.1f})")
    f = mpe.VideoFileClip(filename=clip)
    new_f = f.resize(DIMENSIONS).subclip(start_ts, end_ts)
    final_clips.append(new_f)
output = mpe.concatenate_videoclips(final_clips)
out_path = pathlib.Path(ARGS.output).joinpath('output.mp4').as_posix()

print(f"Overwriting audio of output file.")

f = mpe.AudioFileClip(filename=ARGS.audio)
audio_clip = f.subclip(0, output.duration)
output = output.set_audio(audio_clip)
assert isinstance(output, mpe.VideoClip)
output.write_videofile(out_path, threads=THREAD_COUNT, fps=FPS)
