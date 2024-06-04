from ctypes import windll, c_int, c_uint, c_ushort, c_char_p, c_buffer, Structure, byref, sizeof, POINTER, create_string_buffer
from ctypes.wintypes import HBITMAP, HDC, HGDIOBJ, DWORD
from PIL import Image
import traceback

# Load libraries
gdi32 = windll.gdi32
user32 = windll.user32

# Define Win32 functions
CreateDC = gdi32.CreateDCA
CreateCompatibleDC = gdi32.CreateCompatibleDC
GetDeviceCaps = gdi32.GetDeviceCaps
CreateCompatibleBitmap = gdi32.CreateCompatibleBitmap
BitBlt = gdi32.BitBlt
SelectObject = gdi32.SelectObject
GetDIBits = gdi32.GetDIBits
DeleteDC = gdi32.DeleteDC
DeleteObject = gdi32.DeleteObject

# Define constants
NULL = 0
HORZRES = 8
VERTRES = 10
SRCCOPY = 13369376
DIB_RGB_COLORS = 0
BI_RGB = 0
ERROR_INVALID_PARAMETER = 87
HGDI_ERROR = HGDIOBJ(-1).value

class BITMAPINFOHEADER(Structure):
    _fields_ = [
        ("biSize", c_uint),
        ("biWidth", c_int),
        ("biHeight", c_int),
        ("biPlanes", c_ushort),
        ("biBitCount", c_ushort),
        ("biCompression", c_uint),
        ("biSizeImage", c_uint),
        ("biXPelsPerMeter", c_int),
        ("biYPelsPerMeter", c_int),
        ("biClrUsed", c_uint),
        ("biClrImportant", c_uint)
    ]

class BITMAPINFO(Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", c_uint * 3)
    ]

def grab_screen(bbox=None):
    try:
        screen = CreateDC(b'DISPLAY', None, None, None)
        assert screen, "Failed to create screen device context"

        screen_copy = CreateCompatibleDC(screen)
        assert screen_copy, "Failed to create compatible device context"

        if bbox:
            left, top, x2, y2 = bbox
            width = x2 - left
            height = y2 - top
        else:
            left = 0
            top = 0
            width = GetDeviceCaps(screen, HORZRES)
            height = GetDeviceCaps(screen, VERTRES)

        bitmap = CreateCompatibleBitmap(screen, width, height)
        assert bitmap, "Failed to create compatible bitmap"

        hobj = SelectObject(screen_copy, bitmap)
        assert hobj != NULL and hobj != HGDI_ERROR, f"Failed to select object into device context: {hobj}"

        result = BitBlt(screen_copy, 0, 0, width, height, screen, left, top, SRCCOPY)
        assert result, "Failed to perform bit-block transfer"

        bitmap_info = BITMAPINFO()
        bitmap_info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
        bitmap_info.bmiHeader.biWidth = width
        bitmap_info.bmiHeader.biHeight = -height  # negative height to create a top-down DIB
        bitmap_info.bmiHeader.biPlanes = 1
        bitmap_info.bmiHeader.biBitCount = 24
        bitmap_info.bmiHeader.biCompression = BI_RGB
        bitmap_info.bmiHeader.biSizeImage = 0
        bitmap_info.bmiHeader.biXPelsPerMeter = 0
        bitmap_info.bmiHeader.biYPelsPerMeter = 0
        bitmap_info.bmiHeader.biClrUsed = 0
        bitmap_info.bmiHeader.biClrImportant = 0

        bitmap_bits = create_string_buffer(width * height * 3)

        got_bits = GetDIBits(screen_copy, bitmap, 0, height, bitmap_bits, byref(bitmap_info), DIB_RGB_COLORS)
        assert got_bits != 0 and got_bits != ERROR_INVALID_PARAMETER, f"Failed to get bitmap bits: {got_bits}"

        image = Image.frombuffer('RGB', (width, height), bitmap_bits, 'raw', 'BGR', 0, 1)
        return image
    except Exception as e:
        print(traceback.format_exc())
        print(e)
    finally:
        if 'bitmap' in locals() and bitmap:
            DeleteObject(bitmap)
        if 'screen_copy' in locals() and screen_copy:
            DeleteDC(screen_copy)
        if 'screen' in locals() and screen:
            DeleteDC(screen)

# Example usage
if __name__ == "__main__":
    bbox = [-1600, 0, 0, 1200]  # Example bounding box for a screen to the left of the primary monitor
    im = grab_screen(bbox)
    if im:
        im.show()
