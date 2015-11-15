#!/usr/bin/env python

from env import ABSPATH
import pyneuronjs.module as module

print module.parse_module_id('jquery').group(2)