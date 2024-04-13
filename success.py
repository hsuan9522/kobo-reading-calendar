#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# To get a Py3k-like print function
from __future__ import print_function
from datetime import datetime
from _fbink import ffi, lib as FBInk
from PIL import Image, ImageDraw, ImageFont


fbink_cfg = ffi.new("FBInkConfig *")
fbink_cfg.is_centered = True
fbink_cfg.is_halfway = False
fbink_cfg.row = -2

fbfd = FBInk.fbink_open()
def main():
    try:
        FBInk.fbink_init(fbfd, fbink_cfg)
        FBInk.fbink_print(fbfd, b"Success!!", fbink_cfg)
    finally:
        FBInk.fbink_close(fbfd)


if __name__ == "__main__":
    main()