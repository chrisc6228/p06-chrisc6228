# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from tornado.testing import gen_test

from tests.base import FilterTestCase


class RoundCornerFringeTestCase(FilterTestCase):
    @gen_test
    async def test_transparent_round_corner_edge_is_antialiased_by_alpha(
        self,
    ):
        # With the transparent flag, the anti-aliased pixels on the arc must
        # get partial alpha so they fade into the background. The bug leaves
        # them fully opaque, so the arc has no pixel with 0 < alpha < 255.
        image = await self.get_filtered(
            "source.jpg",
            "thumbor.filters.round_corner",
            "round_corner(50,255,0,0,1)",
            mode="RGBA",
        )

        corner = image.crop((0, 0, 50, 50))
        alphas = {pixel[3] for pixel in corner.getdata()}

        assert any(0 < alpha < 255 for alpha in alphas), (
            "no partially transparent pixels on the rounded edge; "
            f"alpha values in corner: {sorted(alphas)}"
        )
