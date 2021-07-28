import vapoursynth as vs
import itertools
import statistics
from collections import Counter
import functools


core = vs.core


def _delogo(n: int, f: list[vs.VideoFrame, vs.VideoFrame], cycle: int, mode: str, radius_w: int, radius_h: int,
            stat_method: str, force_done: bool) -> vs.VideoFrame:
    clip_f: vs.VideoFrame = f[0].copy()
    mask_f: vs.VideoFrame = f[1].copy()
    colors = []
    _format: vs.Format = clip_f.format
    failed_color = 1 << _format.bits_per_sample - 1
    complete_point = []
    for plane in range(clip_f.format.num_planes):
        mask_array = mask_f.get_write_array(plane)
        clip_array = clip_f.get_write_array(plane)
        height, width = clip_array.shape
        for time in range(cycle):
            complete_point.clear()
            for y in range(0, height):
                for x in range(0, width):
                    if mask_array[y, x] != 0:
                        colors.clear()
                        range_x = range(max(0, x - radius_w - time), min(x + radius_w + time, width))
                        range_y = range(max(0, y - radius_h - time), min(y + radius_h + time, height))
                        if mode == 'o':
                            points = itertools.product(range_x, range_y)
                        else:
                            points = []
                            if mode != '-':
                                points.extend([(x, _y) for _y in range_y])
                            if mode != '|':
                                points.extend([(_x, y) for _x in range_x])
                            if mode == '*':
                                points.extend([(_x, _y) for _x, _y in zip(range(x, min(x + radius_w + time, width)),
                                                                          range(y, min(y + radius_h + time, height)))])
                                points.extend([(_x, _y) for _x, _y in zip(range(max(0, x - radius_w - time), x, -1),
                                                                          range(y, min(y + radius_h + time, height)))])
                                points.extend([(_x, _y) for _x, _y in zip(range(x, min(x + radius_w + time, width)),
                                                                          range(max(0, y - radius_h - time), y, -1))])
                                points.extend([(_x, _y) for _x, _y in zip(range(max(0, x - radius_w - time), x, -1),
                                                                          range(max(0, y - radius_h - time), y, -1))])

                        for offset_x, offset_y in points:
                            if mask_array[offset_y, offset_x] == 0:
                                colors.append(clip_array[offset_y, offset_x])
                        if colors:
                            complete_point.append((x, y))
                            if stat_method == 'mean':
                                color = int(statistics.mean(colors))
                            elif stat_method == 'median':
                                color = int(statistics.median(colors))
                            else:
                                color = Counter(colors).most_common(1)[0][0]
                            clip_array[y, x] = color
                        else:
                            clip_array[y, x] = failed_color
            for x, y in complete_point:
                mask_array[y, x] = 0
        if force_done:
            for width in mask_array:
                for height in width:
                    if height > 0:
                        raise ValueError(f'the plane {plane} is not done')
    return clip_f


def delogo(src: vs.VideoNode, mask: vs.VideoNode, predn: bool = False,
           mode: str = 'o', radius_w: int = 3, radius_h: int = 3, stat_method: str = 'common',
           crop_l: int = 0, crop_r: int = 0, crop_t: int = 0, crop_b: int = 0, cycle: int = 1,
           postblur: bool = True, hradius=3, hpasses=3, vradius=3, vpasses=3, first_plane: bool = True,
           force_done: bool = False) -> vs.VideoNode:
    
    if not isinstance(src, vs.VideoNode):
        raise TypeError('src must be a clip')
    if not isinstance(mask, vs.VideoNode):
        raise TypeError('mask must be a clip')
    if radius_w <= 0:
        raise ValueError('radius_w must bigger than 0')
    if radius_h <= 0:
        raise ValueError('radius_h must bigger than 0')
    if stat_method not in ('common', 'mean', 'median'):
        raise ValueError('stat_method must be common, mean or median')
    if mode not in ('o', '+', '-', '|', '*'):
        raise ValueError('mode must be o, +, -, | or *')

    if first_plane:
        _format: vs.Format = src.format
        color_family = _format.color_family
        if color_family == vs.GRAY:
            mask = core.std.ShufflePlanes(mask, 0, vs.GRAY)
        else:
            mask = core.std.ShufflePlanes(mask, [0, 0, 0], color_family)
            _mask_uv = mask[:]

            if _format.subsampling_h > 0:
                _mask_uv = core.resize.Point(_mask_uv, height=mask.height // (_format.subsampling_h * 2))
            if _format.subsampling_w > 0:
                _mask_uv = core.resize.Point(_mask_uv, width=mask.width // (_format.subsampling_w * 2))
            mask = core.std.ShufflePlanes([mask, _mask_uv, _mask_uv], [0, 1, 2], color_family)

    if predn:
        predn_clip = core.knlm.KNLMeansCL(src, a=2, h=1.5)
    else:
        predn_clip = src
    croped_clip = core.std.Crop(predn_clip, left=crop_l, right=crop_r, top=crop_t, bottom=crop_b)
    mask = core.std.Crop(mask, left=crop_l, right=crop_r, top=crop_t, bottom=crop_b)
    func = functools.partial(_delogo, mode=mode, radius_h=radius_h, radius_w=radius_w,
                             stat_method=stat_method, cycle=cycle, force_done=force_done)
    delogoed_clip = core.std.ModifyFrame(croped_clip,
                                         clips=[croped_clip, mask],
                                         selector=func)
    if postblur:
        delogoed_clip = core.std.BoxBlur(delogoed_clip, planes=[0, 1, 2],
                                         hradius=hradius, hpasses=hpasses, vradius=vradius, vpasses=vpasses)

    delogoed_clip = core.std.MaskedMerge(croped_clip, delogoed_clip, mask)
    if postblur:
        delogoed_clip = core.std.BoxBlur(delogoed_clip, planes=[0, 1, 2], hradius=1, hpasses=1, vradius=1, vpasses=1)

    height = src.height
    width = src.width
    if crop_b:
        delogoed_clip = core.std.StackVertical(
            [delogoed_clip, core.std.Crop(src, left=crop_l, right=crop_r, top=height - crop_b)])
    if crop_t:
        delogoed_clip = core.std.StackVertical(
            [core.std.Crop(src, left=crop_l, right=crop_r, bottom=height - crop_t), delogoed_clip])
    if crop_l:
        delogoed_clip = core.std.StackHorizontal([core.std.Crop(src, right=width - crop_l), delogoed_clip])
    if crop_r:
        delogoed_clip = core.std.StackHorizontal([delogoed_clip, core.std.Crop(src, left=width - crop_r)])

    return delogoed_clip
