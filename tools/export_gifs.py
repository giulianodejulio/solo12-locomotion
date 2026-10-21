"""Export compact positive-axis clips from the recorded teleop sequence."""
from pathlib import Path
from PIL import Image


def main():
    root = Path('paper/checks')
    source = Image.open(root/'teleop_demo_full_velocity_sequence.gif')
    clips = [('vx', 2., 15.), ('vy', 28., 39.), ('wz', 50., 59.5)]
    for name, start, end in clips:
        frames = []
        # One second at zero followed by the ramp and complete stop segment.
        indices = list(range(round((start-1)*20), round(end*20), 3))
        for index in indices:
            source.seek(index)
            frame = source.convert('RGB').resize((360,240), Image.Resampling.LANCZOS)
            frames.append(frame.quantize(colors=32, dither=Image.Dither.NONE))
        output = root/f'teleop_{name}_max_stop.gif'
        frames[0].save(output, save_all=True, append_images=frames[1:],
                       duration=150, loop=0, optimize=True)
        print(f'{output}: {output.stat().st_size/1024:.0f} KiB', flush=True)


if __name__ == '__main__':
    main()
