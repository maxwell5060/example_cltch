import importlib
import os

APP = os.getenv('APP')
STAGE = os.getenv('STAGE')

CONFIG = {}

globals().update(importlib.import_module(f'settings.{APP}').__dict__)
