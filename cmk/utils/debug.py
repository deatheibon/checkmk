#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

debug_mode = False


def enabled():
    # type: () -> bool
    return debug_mode


def disabled():
    # type: () -> bool
    return not debug_mode


def enable():
    # type: () -> None
    global debug_mode
    debug_mode = True


def disable():
    # type: () -> None
    global debug_mode
    debug_mode = False
