# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from io import BytesIO
from unittest import TestCase

from PIL import Image

from thumbor.config import Config
from thumbor.context import Context, RequestParameters
from thumbor.engines.pil import Engine
from thumbor.importer import Importer
from thumbor.transformer import Transformer

RAINBOW_COLORS = [
    (255, 0, 0),
    (255, 165, 0),
    (255, 255, 0),
    (0, 128, 0),
    (0, 0, 255),
    (75, 0, 130),
    (238, 130, 238),
    (255, 255, 255),
]


def rainbow_png():
    # A 16x16 transparent PNG with vertical colored bars, as in the issue.
    image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for x in range(16):
        color = RAINBOW_COLORS[x * len(RAINBOW_COLORS) // 16]
        for y in range(16):
            image.putpixel((x, y), (*color, 255))
    buffer = BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def wide_png(size):
    # A solid opaque source, used for the 940x2 cases from the issue.
    buffer = BytesIO()
    Image.new("RGBA", size, (0, 0, 255, 255)).save(buffer, "PNG")
    return buffer.getvalue()


def run_transform(buffer, width, height, fit_in=False):
    cfg = Config(
        SECURITY_KEY="ACME-SEC",
        ENGINE="thumbor.engines.pil",
        LOADER="thumbor.loaders.file_loader",
        STORAGE="thumbor.storages.no_storage",
    )
    importer = Importer(cfg)
    importer.import_modules()
    context = Context(config=cfg, importer=importer)
    context.request = RequestParameters(
        width=width, height=height, unsafe=True, filters="", fit_in=fit_in
    )
    engine = Engine(context)
    engine.load(buffer, ".png")
    context.request.engine = engine
    transformer = Transformer(context)
    transformer.engine = engine
    # Run the same entry point the imaging handler uses. The handler calls
    # transformer.transform() -> do_image_operations() -> img_operation_worker(),
    # which performs the fit-in resize itself; resizing again here with the
    # raw target dimensions would diverge from production.
    transformer.img_operation_worker()
    return engine.image.convert("RGBA")


class ExtremeAspectCropTestCase(TestCase):
    def test_rainbow_png_at_800x20_is_a_visible_strip(self):
        # Before the fix this came back 800x20 with every pixel transparent.
        image = run_transform(rainbow_png(), 800, 20)

        assert image.size == (800, 20)
        opaque = sum(1 for pixel in image.getdata() if pixel[3] > 0)
        assert opaque == 800 * 20

    def test_one_pixel_box_from_wide_source_is_not_empty(self):
        # 940x2 into a 1x1 box used to return a 500 error.
        image = run_transform(wide_png((940, 2)), 1, 1, fit_in=True)

        assert image.size == (1, 1)

    def test_width_only_fit_in_from_wide_source_is_not_empty(self):
        # 940x2 with a width of 100 and no height used to return a 500 error.
        image = run_transform(wide_png((940, 2)), 100, 0, fit_in=True)

        assert image.size == (100, 1)
