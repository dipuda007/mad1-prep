"""Generate icon.ico (green badge + white mountain) for the exe. Needs Pillow."""
from PIL import Image, ImageDraw

sizes = [256, 128, 64, 48, 32, 16]
imgs = []
for s in sizes:
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = s // 8
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=(20, 83, 45, 255))
    # mountain: big peak + small peak + snow cap
    m = s / 256.0
    d.polygon([(40 * m, 200 * m), (128 * m, 60 * m), (216 * m, 200 * m)], fill=(255, 255, 255, 255))
    d.polygon([(30 * m, 200 * m), (78 * m, 130 * m), (126 * m, 200 * m)], fill=(74, 222, 128, 255))
    d.polygon([(110 * m, 88 * m), (128 * m, 60 * m), (146 * m, 88 * m)], fill=(74, 222, 128, 255))
    imgs.append(img)

imgs[0].save("icon.ico", sizes=[(s, s) for s in sizes], append_images=imgs[1:])
print("icon.ico written")
