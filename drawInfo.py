#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# To get a Py3k-like print function
import sys
from _fbink import ffi, lib as FBInk


fbink_cfg = ffi.new("FBInkConfig *")
fbink_cfg.is_centered = True
fbink_cfg.is_halfway = False
fbink_cfg.row = -2
fbink_cfg.is_cleared = True
fbfd = FBInk.fbink_open()

def main():
    try:

        if len(sys.argv) > 1:
            text = f'{sys.argv[1]}'
        else:
            text = 'Generating...'

        FBInk.fbink_init(fbfd, fbink_cfg)
        FBInk.fbink_print(fbfd, text.encode('utf-8'), fbink_cfg)
    finally:
        FBInk.fbink_close(fbfd)


if __name__ == "__main__":
    main()