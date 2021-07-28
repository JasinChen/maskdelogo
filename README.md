# maskdelogo

A simple vapoursynth filter to delogo with mask clip (not lgd file).

It is simple but not fast, because it runs with python. In fact, it will be faster if run in C++, but I haven't learned it!😀

Useage:


def delogo(src: vs.VideoNode, mask: vs.VideoNode, predn: bool = False,
           mode: str = 'o', radius_w: int = 3, radius_h: int = 3, stat_method: str = 'common',
           crop_l: int = 0, crop_r: int = 0, crop_t: int = 0, crop_b: int = 0, cycle: int = 1,
           postblur: bool = True, hradius=3, hpasses=3, vradius=3, vpasses=3, first_plane: bool = True,
           force_done: bool = False) -> vs.VideoNode:
