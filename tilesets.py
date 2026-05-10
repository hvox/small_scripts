from __future__ import annotations
from itertools import islice
from typing import NamedTuple, TypeVar, Type, Any
from pathlib import Path
from functools import reduce
import PIL.Image

T = TypeVar("T")
Color = tuple[int, int, int, int]


class TilesetMetaclass(type):
    def __init__(cls, *_):
        cls.supported_tiles = {x for row in cls.order for x in row if x >= 0}
        cls.supported_tiles_list = list(sorted(cls.supported_tiles))

    def __in__(cls: Type, item) -> bool:
        return item in cls.supported_tiles

    def __iter__(cls):
        yield from cls.supported_tiles_list


class Tileset(metaclass=TilesetMetaclass):
    w: int
    h: int
    tiles: dict[int, Tile]
    order: list[list[int]] = []

    def __init__(self, w: int, h: int, tiles: dict[int, Tile]):
        self.w = w
        self.h = h
        self.tiles = tiles

    def __iter__(self):
        yield from (self.w, self.h, self.tiles)

    @classmethod
    def load(cls: Type, path: Path) -> Tileset:
        if cls is Tileset:
            suffix = path.stem.rsplit(".", 1)[-1].lower() if "." in path.stem else ""
            loader = {
                "blob": BlobTileset,
                "wang": WangTileset,
                "miniblob": MiniblobTileset,
                "form": FormTileset,
            }[suffix]
            return loader.load(path)
        cols, rows = len(cls.order[0]), len(cls.order)
        w, h, tiles = Tile.load(path, cols, rows)
        tileset = {cls.order[i // cols][i % cols]: t for i, t in enumerate(tiles)}
        return cls(w, h, {i: tile for i, tile in tileset.items() if i >= 0})

    def save(self, path: Path):
        cols, rows = len(self.order[0]), len(self.order)
        w, h, tiles = self
        image = PIL.Image.new(mode="RGBA", size=(w * cols, h * rows))
        for x, y, tile in (
            (x, y, t)
            for y, row in enumerate(self.order)
            for x, t in enumerate(row)
            if t >= 0
        ):
            for j, pixel in enumerate(self.tiles[tile].pixels):
                pixel_x = x * w + j % w
                pixel_y = y * h - j // w + h - 1
                image.putpixel((pixel_x, pixel_y), pixel)
        image.save(path)

    def to_blob(self) -> BlobTileset:
        return self.lossy_convert_to(BlobTileset)

    def to_miniblob(self) -> MiniblobTileset:
        return self.lossy_convert_to(MiniblobTileset)

    def lossy_convert_to(self, tileset_class: Type[T]) -> T:
        if isinstance(self, tileset_class):
            return self
        tiles = self.to_blob().tiles
        cls: Any = tileset_class
        tiles = {t: tiles[t & 0xFF] for t in cls}
        return cls(self.w, self.h, tiles)

    def __str__(self):
        w, h, _ = self
        cls = self.__class__.__name__.removesuffix("Tileset")
        ref = hex(id(self))[2:]
        return f"{cls}:{w}:{h}:{ref}"


def lists(hex: str) -> list[list[int]]:
    rows = hex.replace(" ", "").replace("\n", "").split(":")
    lsts = [[int(row[i : i + 2], 16) for i in range(0, len(row), 2)] for row in rows]
    return lsts


class BlobTileset(Tileset):
    order = lists(
        "-1121e1f1b1a0a:0252defb7a5a4a:565bda68505e4b:d27e5f0b16df6b:42d6ff7fdbfa6a:40d0f8fe7b5848:001018d87808-1"
    )
    pass


class MiniblobTileset(Tileset):
    order = lists("02-1161fdf7f0b:4200d0f8feff6b:40101808d6fb68")

    def to_blob(self) -> BlobTileset:
        tiles = dict(self.tiles)
        for tile in BlobTileset:
            if tile not in MiniblobTileset:
                parts: Any = [
                    (foreground, back)
                    for foreground in list(sorted(MiniblobTileset))
                    for back in list(sorted(MiniblobTileset))
                    if foreground | back == tile
                ] or [
                    (t1, t2, t3)
                    for t1 in list(sorted(MiniblobTileset))
                    for t2 in list(sorted(MiniblobTileset))
                    for t3 in list(sorted(MiniblobTileset))
                    if t1 | t2 | t3 == tile
                ]
                parts = max(
                    parts, key=(lambda p: tuple((bin(x).count("1"), -x) for x in p))
                )
                tiles[tile] = reduce(Tile.blend, [tiles[tile] for tile in parts])
        return BlobTileset(self.w, self.h, tiles)


class WangTileset(Tileset):
    order = lists("02121a0a:42525a4a:40505848:00101808")

    def to_blob(self) -> BlobTileset:
        tiles = dict(self.tiles)
        for tile in (tile for tile in BlobTileset if tile not in WangTileset):
            tiles[tile] = tiles[tile & 90]
        return BlobTileset(self.w, self.h, tiles)


class FormTileset(Tileset):
    order = [[22, 11], [208, 104]]

    def to_blob(self) -> BlobTileset:
        tiles = dict(self.tiles)
        (t1, t2), (t5, t6) = tiles[22].split()
        (t3, t4), (t7, t8) = tiles[11].split()
        (t9, t10), (t13, t14) = tiles[208].split()
        (t11, t12), (t15, t16) = tiles[104].split()
        no = Tile(0, 0, [])
        parts = {
            1: [no, t4, no, no],
            2: [t1, no, no, no],
            3: [t3, t2, no, no],
            4: [no, no, no, t16],
            5: [no, t12, no, t8],
            7: [no, t2.blend(t12), no, no],  # TODO: join two edges into corner
            8: [no, no, t13, no],
            10: [t9, no, t5, no],
            11: [t3.blend(t9), no, no, no],  # TODO: corner
            12: [no, no, t15, t14],
            13: [no, no, no, t14.blend(t8)],  # TODO: corner
            14: [no, no, t15.blend(t5), no],  # TODO:corner
            15: [t11, t10, t7, t6],
        }
        for t in BlobTileset:
            if t not in tiles:
                tiles[t] = Tile.join(
                    (
                        (
                            parts[bit(t, 4) + 2 + 4 * bit(t, 6) + 8 * bit(t, 7)][0],
                            parts[1 + 2 * bit(t, 5) + 4 * bit(t, 7) + 8 * bit(t, 8)][1],
                        ),
                        (
                            parts[bit(t, 1) + 2 * bit(t, 2) + 4 * bit(t, 4) + 8][2],
                            parts[bit(t, 2) + 2 * bit(t, 3) + 4 + 8 * bit(t, 5)][3],
                        ),
                    )
                )
        return BlobTileset(self.w, self.h, tiles)


class Tile(NamedTuple):
    width: int
    height: int
    pixels: list[Color]

    def blend(self: Tile, other: Tile):
        assert self.width == other.width and self.height == other.height
        pixels = [
            blend_rgba(color1, color2)
            for color1, color2 in zip(self.pixels, other.pixels)
        ]
        return Tile(self.width, self.height, pixels)

    def split(self: Tile):
        w1 = self.width // 2
        w2 = self.width - w1
        h1 = self.height // 2
        h2 = self.height - h1
        tiles = []
        for x0, y0, w, h in [
            (0, 0, w1, h1),
            (w1, 0, w2, h1),
            (0, h1, w1, h2),
            (w1, h1, w2, h2),
        ]:
            pixels = [
                self.pixels[x + y * (w1 + w2)]
                for y in range(y0, y0 + h)
                for x in range(x0, x0 + w)
            ]
            tiles.append(Tile(w, h, pixels))
        return ((tiles[2], tiles[3]), (tiles[0], tiles[1]))

    @staticmethod
    def join(tiles: tuple[tuple[Tile, Tile], tuple[Tile, Tile]]):
        pixels = [
            pixel
            for t1, t2 in reversed(tiles)
            for row1, row2 in zip(
                chunked(t1.pixels, t1.width), chunked(t2.pixels, t2.width)
            )
            for pixel in (row1 + row2)
        ]
        assert all(tile.height != 0 for r in tiles for tile in r)
        width = tiles[0][0].width + tiles[0][1].width
        height = tiles[0][0].height + tiles[1][0].height
        return Tile(width, height, pixels)

    @staticmethod
    def load(path: Path, cols: int, rows: int) -> tuple[int, int, list[Tile]]:
        img = PIL.Image.open(path).convert("RGBA")
        img_pixels = img.load()
        w = img.size[0] // cols
        h = img.size[1] // rows
        tiles = [
            [
                img_pixels[x, y]
                for y in reversed(range(tile_y * h, (tile_y + 1) * h))
                for x in range(tile_x * w, (tile_x + 1) * w)
            ]
            for tile_y in range(rows)
            for tile_x in range(cols)
        ]
        return w, h, [Tile(w, h, pixels) for pixels in tiles]


def blend_rgba(foreground: Color, background: Color) -> Color:
    r1, g1, b1, a1 = background
    r2, g2, b2, a2 = foreground
    alpha = 255 - (255 - a1) * (255 - a2) // 255
    red = (r1 * (255 - a2) + r2 * a2) // 255
    green = (g1 * (255 - a2) + g2 * a2) // 255
    blue = (b1 * (255 - a2) + b2 * a2) // 255
    return (red, green, blue, alpha)


def bytelist(hex: str) -> list[int]:
    return list(bytes.fromhex(hex))


def list_repr(lists: list[list[int]]) -> str:
    items = ":".join("".join(f"{x:02x}" for x in lst) for lst in lists)
    return f"lists('{items}')"


def chunked(iterable, n: int):
    it = iter(iterable)
    while chunk := list(islice(it, n)):
        yield chunk


def bit(mask: int, index: int) -> int:
    return (mask >> (index - 1)) & 1


def get_order(tileset_path, ordered_path):
    w, h, tileset = Tileset.load(Path(tileset_path))
    img = PIL.Image.open(Path(ordered_path)).convert("RGBA")
    cols, rows = img.size
    cols //= w
    rows //= h
    _, _, tiles = Tile.load(Path(ordered_path), cols, rows)
    order = [
        [
            next((i for i, t in tileset.items() if t == tiles[x + y * cols]), -1)
            for x in range(cols)
        ]
        for y in range(rows)
    ]
    return order


# print(list_repr(get_order("/home/ulad/Desktop/tileset.blob.png", "/home/ulad/Desktop/tileset.png")))

tileset = Tileset.load(Path("/home/ulad/Desktop/tileset.form.png"))
print(tileset)
tileset.to_blob().save(Path("/home/ulad/Desktop/out.png"))
