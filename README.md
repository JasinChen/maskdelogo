# maskdelogo

A simple vapoursynth filter to delogo with mask clip (not lgd file).

It is simple but not fast, because it runs with python. In fact, it will be faster if running in C++, but I haven't learned it!😀


Useage:

def delogo(src: vs.VideoNode, mask: vs.VideoNode, predn: bool = False,
           mode: str = 'o', radius_w: int = 3, radius_h: int = 3, stat_method: str = 'common',
           crop_l: int = 0, crop_r: int = 0, crop_t: int = 0, crop_b: int = 0, cycle: int = 1,
           postblur: bool = True, hradius=3, hpasses=3, vradius=3, vpasses=3, first_plane: bool = True,
           force_done: bool = False) -> vs.VideoNode:
    ...



mask: mask clip, format must same as src clip

predn: pre denoise the src (use knlmeansCL). Default False

mode: the method of searching reference pixels. "o" means square, "-" means searching left and right, "|" means searching up and down, "+" means "-" + "|", "*" include oblique line. Default "o"

radius_w, radius_h: searching radius, larger value means more range, but also slower. Default 3, 3

stat_method: "common", the most common color in ref pixels. "mean", average color of ref pixels. "median"， median. Default common
crop_l, crop_r, crop_t, crop_b: pre crop the src clip. Default 0

cycle: searching multi times if it cannot search all logo region. Default 1

postblur: blur the logo region after delogo. Use boxblur filter. Default True

hradius, hpasses, vradius, vpasses: parameter of boxblur.

first_plane: mask’s first plane will be used as the mask for handling all planes. Default True

force_done: raise Exception when any logo pixel not being handled. Default False



Notice: It works in YUV420 clip, other format have not been try.

sample image: 

![Image text](https://github.com/JasinChen/maskdelogo/blob/main/logo-sample.png)

delogo (mode="o", radius_w=3, radius_h=3, cycle=2, postblur=False): 

![Image text](https://github.com/JasinChen/maskdelogo/blob/main/delogo-sample.png)

