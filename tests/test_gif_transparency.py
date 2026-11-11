# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from io import BytesIO
from os.path import abspath, dirname, join
from unittest import TestCase

from PIL import Image

from thumbor.config import Config
from thumbor.context import Context
from thumbor.engines.pil import Engine

STORAGE_PATH = abspath(join(dirname(__file__), "fixtures/images"))


class GifTransparencyTestCase(TestCase):
    def get_context(self):
        cfg = Config(
            SECURITY_KEY="ACME-SEC",
            ENGINE="thumbor.engines.pil",
            PILLOW_PRESERVE_INDEXED_MODE=True,
        )
        cfg.LOADER = "thumbor.loaders.file_loader"
        cfg.FILE_LOADER_ROOT_PATH = STORAGE_PATH
        cfg.STORAGE = "thumbor.storages.no_storage"

        return Context(config=cfg)

    def test_resized_palette_png_keeps_transparency_as_gif(self):
        # A palette source with a transparent entry, resized and written as
        # GIF, must still have transparent pixels in the GIF output.
        engine = Engine(self.get_context())
        with open(
            join(STORAGE_PATH, "paletted-transparent.png"), "rb"
        ) as image_file:
            buffer = image_file.read()

        engine.load(buffer, "png")
        assert engine.original_mode == "P"
        engine.resize(200, 150)

        img = Image.open(BytesIO(engine.read(".gif")))
        assert img.format == "GIF"

        transparent_pixels = sum(
            1
            for alpha in img.convert("RGBA").getchannel("A").getdata()
            if alpha == 0
        )
        assert transparent_pixels > 19000
