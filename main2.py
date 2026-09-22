import sys
import subprocess

# -----------------------------
# فحص وتثبيت المكتبات المطلوبة تلقائياً
# -----------------------------
REQUIRED_PACKAGES = {
    "cv2": "opencv-python",
    "numpy": "numpy",
    "kivy": "kivy"
}

for module_name, pip_name in REQUIRED_PACKAGES.items():
    try:
        __import__(module_name)
    except ImportError:
        print(f"جاري تثبيت المكتبة الناقصة: {pip_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        except Exception as e:
            print(f"فشل تثبيت {pip_name}: {e}")

import os
import cv2
import numpy as np

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.utils import platform


# -----------------------------
# المسارات والصلاحيات
# -----------------------------
if platform == "android":
    from android.permissions import request_permissions, Permission

    perms = [
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE
    ]
    # الفحص الآمن لمنع AttributeError في بعض إصدارات الواجهة
    if hasattr(Permission, "MANAGE_EXTERNAL_STORAGE"):
        perms.append(Permission.MANAGE_EXTERNAL_STORAGE)

    request_permissions(perms)
    BASE_DIR = "/storage/emulated/0/DCIM/StampExtractorPro"
else:
    BASE_DIR = os.path.join(os.path.expanduser("~"), "DCIM", "StampExtractorPro")

SOURCE_DIR = os.path.join(BASE_DIR, "SourceFiles")
STAMP_DIR = os.path.join(BASE_DIR, "ExtractedStamps")
RESULT_DIR = os.path.join(BASE_DIR, "StampResults")

os.makedirs(SOURCE_DIR, exist_ok=True)
os.makedirs(STAMP_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)


# -----------------------------
# دوال مساعدة
# -----------------------------
def rotate_image_cv(img, angle_deg: float):
    (h, w) = img.shape[:2]
    if h == 0 or w == 0:
        return img

    center = (w / 2.0, h / 2.0)
    M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)

    cos = abs(M[0, 0])
    sin = abs(M[0, 1])

    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    M[0, 2] += (new_w / 2.0) - center[0]
    M[1, 2] += (new_h / 2.0) - center[1]

    rotated = cv2.warpAffine(
        img, M, (new_w, new_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0)
    )
    return rotated


def ensure_bgr(img):
    if img is None:
        return None
    if len(img.shape) == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


def bgr_to_gray(img_bgr):
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)


def make_stamp_rgba(img_bgr, mask_total_u8):
    """
    mask_total_u8: 0..255 where stamp area=255
    نخرج BGRA بخلفية شفافة (alpha=mask) بتسلسل ألوان صحيح لتفادي انقلاب الألوان في OpenCV
    """
    img_bgr = ensure_bgr(img_bgr)
    b, g, r = cv2.split(img_bgr)
    # alpha = mask (ترتيب BGRA لتوافقه مع cv2.imwrite)
    dst = cv2.merge([b, g, r, mask_total_u8])
    return dst


def clean_mask(mask_u8):
    """
    تنظيف القناع بشكل محافظ:
    - إزالة ضوضاء خفيفة
    - ملء ثقوب بسيطة
    - المحافظة على الشكل دون "اختراع" تفاصيل كبيرة
    """
    if mask_u8 is None:
        return None

    kernel3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    kernel5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    # تنعيم + تقليل بقع صغيرة
    m = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel3, iterations=1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel5, iterations=2)

    # ملء ثقوب عبر تعبئة داخل الحدود
    h, w = m.shape[:2]
    inv = cv2.bitwise_not(m)
    ff = inv.copy()

    # إحاطة بحدود مؤقتة لمنع الفشل إذا لامس القناع نقطة (0,0)
    ff_padded = cv2.copyMakeBorder(ff, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=255)
    mask_ff = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(ff_padded, mask_ff, (0, 0), 0)
    ff = ff_padded[1:-1, 1:-1]

    # بعد floodFill: الأجزاء المحبوسة داخل الحدود تصبح 255 في m2
    filled = cv2.bitwise_not(ff)
    m2 = cv2.bitwise_or(m, filled)
    return m2


def multi_color_stamp_mask(img_bgr):
    """
    قناع متعدد الألوان (أزرق/أحمر/أخضر + أسود/داكن) بشكل عام يناسب الأختام متعددة الأحجام والأشكال.
    """
    img_bgr = ensure_bgr(img_bgr)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    gray = bgr_to_gray(img_bgr)

    # --- الأزرق ---
    lower_blue = np.array([85, 45, 35])
    upper_blue = np.array([135, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    # --- الأخضر ---
    lower_green = np.array([35, 40, 35])
    upper_green = np.array([90, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)

    # --- الأحمر ---
    lower_red1 = np.array([0, 45, 35])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 45, 35])
    upper_red2 = np.array([180, 255, 255])
    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    # --- الأسود/الداكن ---
    v = hsv[:, :, 2]
    mask_dark_v = cv2.inRange(v, 0, 70)
    _, mask_dark_gray = cv2.threshold(gray, 70, 255, cv2.THRESH_BINARY_INV)
    mask_dark = cv2.bitwise_or(mask_dark_v, mask_dark_gray)

    # ندمج الأقنعة
    mask_total = cv2.bitwise_or(mask_blue, mask_green)
    mask_total = cv2.bitwise_or(mask_total, mask_red)
    mask_total = cv2.bitwise_or(mask_total, mask_dark)

    # تحسين عام محافظ
    mask_total = clean_mask(mask_total)

    contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        areas = [cv2.contourArea(c) for c in contours]
        if len(areas) > 0:
            max_area = max(areas)
            keep = []
            for c, a in zip(contours, areas):
                if a >= max_area * 0.12:
                    keep.append(c)
            if keep:
                new_mask = np.zeros_like(mask_total)
                cv2.drawContours(new_mask, keep, -1, 255, thickness=-1)
                mask_total = new_mask

    mask_total_u8 = np.where(mask_total > 0, 255, 0).astype(np.uint8)
    return mask_total_u8


def stamp_quality_metric(mask_u8, gray_bgr):
    """
    مقياس بسيط للحِدّة/الوضوح داخل منطقة الختم.
    """
    if mask_u8 is None or mask_u8.sum() == 0:
        return 0.0

    roi = gray_bgr.copy()
    roi[mask_u8 == 0] = 0

    gx = cv2.Sobel(roi, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(roi, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    mag_mean = float(mag[mask_u8 > 0].mean())

    vals = roi[mask_u8 > 0].astype(np.float32)
    if vals.size == 0:
        return 0.0
    std = float(vals.std())
    metric = mag_mean / (1.0 + std * 0.08)
    return metric


def mild_preserve_enhancement(stamp_bgr, mask_u8):
    """
    تحسين محافظ جدًا داخل منطقة الختم فقط.
    """
    stamp_bgr = ensure_bgr(stamp_bgr)
    if mask_u8 is None or mask_u8.sum() == 0:
        return stamp_bgr

    roi_mask = mask_u8
    alpha = cv2.GaussianBlur(stamp_bgr, (0, 0), 1.2)
    sharp = cv2.addWeighted(stamp_bgr, 1.25, alpha, -0.25, 0)

    den = cv2.bilateralFilter(sharp, d=7, sigmaColor=40, sigmaSpace=40)

    out = stamp_bgr.copy()
    out[roi_mask > 0] = den[roi_mask > 0]
    return out


def overlay_stamp_on_thumb(thumb_bgr, stamp_bgr, stamp_mask_u8, top_left_xy, out_size=None):
    """
    دمج الختم مع الإبهام بالشفافية المطلوبة.
    """
    thumb_bgr = ensure_bgr(thumb_bgr)
    stamp_bgr = ensure_bgr(stamp_bgr)
    if out_size is None:
        out_size = thumb_bgr.shape[:2][::-1]

    x, y = top_left_xy
    tw, th = out_size

    out = thumb_bgr.copy()
    sh, sw = stamp_bgr.shape[:2]
    if sh == 0 or sw == 0:
        return out

    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(tw, x + sw)
    y1 = min(th, y + sh)

    if x1 <= x0 or y1 <= y0:
        return out

    sx0 = x0 - x
    sy0 = y0 - y
    sx1 = sx0 + (x1 - x0)
    sy1 = sy0 + (y1 - y0)

    roi_thumb = out[y0:y1, x0:x1]
    roi_stamp = stamp_bgr[sy0:sy1, sx0:sx1]
    roi_mask = stamp_mask_u8[sy0:sy1, sx0:sx1]

    a = roi_mask.astype(np.float32) / 255.0
    a3 = np.dstack([a, a, a])

    blended = (roi_thumb.astype(np.float32) * (1.0 - a3) + roi_stamp.astype(np.float32) * a3)
    out[y0:y1, x0:x1] = blended.astype(np.uint8)
    return out


# -----------------------------
# تطبيق Kivy
# -----------------------------
class StampExtractorApp(App):
    def build(self):
        self.title = "Stamp Extractor Pro"

        root = BoxLayout(orientation="vertical", padding=12, spacing=10)

        root.add_widget(Label(
            text="مستخرج الأختام الذكي",
            font_size=20,
            size_hint_y=0.08
        ))

        self.status_label = Label(
            text="جاهز. اختر صورة لاستخراج الختم.",
            size_hint_y=0.08,
            halign="center",
            valign="middle"
        )
        root.add_widget(self.status_label)

        btn_row1 = BoxLayout(size_hint_y=0.10, spacing=8)
        self.btn_select_source = Button(text="اختر ملف (صورة)", on_press=self.open_source_popup)
        self.btn_select_thumb = Button(text="اختر صورة الإبهام", on_press=self.open_thumb_popup)
        btn_row1.add_widget(self.btn_select_source)
        btn_row1.add_widget(self.btn_select_thumb)
        root.add_widget(btn_row1)

        root.add_widget(Label(text="تدوير الختم (قبل الاستخراج):", size_hint_y=0.05))
        self.rotation_slider = Slider(min=0, max=360, value=0, step=1, size_hint_y=0.08)
        root.add_widget(self.rotation_slider)

        root.add_widget(Label(text="مكان ولحظة الدمج على الإبهام:", size_hint_y=0.05))

        self.scale_slider = Slider(min=10, max=250, value=120, step=1, size_hint_y=0.08)
        root.add_widget(Label(text="تكبير/تصغير الختم (%):", size_hint_y=0.05))
        root.add_widget(self.scale_slider)

        self.posx_slider = Slider(min=0, max=100, value=50, step=1, size_hint_y=0.08)
        root.add_widget(Label(text="X (مركز الدمج):", size_hint_y=0.05))
        root.add_widget(self.posx_slider)

        self.posy_slider = Slider(min=0, max=100, value=52, step=1, size_hint_y=0.08)
        root.add_widget(Label(text="Y (مركز الدمج):", size_hint_y=0.05))
        root.add_widget(self.posy_slider)

        btn_row2 = BoxLayout(size_hint_y=0.12, spacing=8)
        self.btn_extract = Button(text="استخراج الختم (PNG شفاف)", on_press=self.extract_stamp_from_source)
        self.btn_apply = Button(text="نقل الأثر إلى الإبهام", on_press=self.apply_stamp_to_thumb)
        btn_row2.add_widget(self.btn_extract)
        btn_row2.add_widget(self.btn_apply)
        root.add_widget(btn_row2)

        self.info_label = Label(
            text="—",
            size_hint_y=0.20,
            halign="left",
            valign="top"
        )
        root.add_widget(self.info_label)

        self.source_path = None
        self.thumb_path = None
        self.last_stamp_path = None
        self.last_stamp_bgr = None
        self.last_stamp_mask = None

        return root

    def _set_status(self, text):
        self.status_label.text = text
        self.info_label.text = text if text else "—"

    def open_source_popup(self, instance):
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserIconView()
        file_chooser.filters = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp', '*.tif', '*.tiff']
        content.add_widget(file_chooser)

        btn_layout = BoxLayout(size_hint_y=0.2)
        btn_select = Button(text="تأكيد الاختيار")
        btn_cancel = Button(text="إلغاء")
        btn_layout.add_widget(btn_select)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)

        popup = Popup(title="اختر صورة المصدر (الختم)", content=content, size_hint=(0.92, 0.92))

        def select_path(_):
            if file_chooser.selection:
                self.source_path = file_chooser.selection[0]
                self._set_status(f"✓ تم تحديد المصدر:\n{os.path.basename(self.source_path)}")
                popup.dismiss()

        btn_select.bind(on_press=select_path)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def open_thumb_popup(self, instance):
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserIconView()
        file_chooser.filters = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp', '*.tif', '*.tiff']
        content.add_widget(file_chooser)

        btn_layout = BoxLayout(size_hint_y=0.2)
        btn_select = Button(text="تأكيد الاختيار")
        btn_cancel = Button(text="إلغاء")
        btn_layout.add_widget(btn_select)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)

        popup = Popup(title="اختر صورة الإبهام (بدون اختام)", content=content, size_hint=(0.92, 0.92))

        def select_path(_):
            if file_chooser.selection:
                self.thumb_path = file_chooser.selection[0]
                self._set_status(f"✓ تم تحديد الإبهام:\n{os.path.basename(self.thumb_path)}")
                popup.dismiss()

        btn_select.bind(on_press=select_path)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def extract_stamp_from_source(self, instance=None):
        if not self.source_path:
            self._set_status("❌ لم يتم تحديد ملف المصدر بعد.")
            return

        try:
            self._set_status("⏳ جاري استخراج الختم...")

            img = cv2.imread(self.source_path, cv2.IMREAD_COLOR)
            if img is None:
                self._set_status("❌ فشل قراءة الصورة.")
                return

            angle = float(self.rotation_slider.value)
            if abs(angle) > 0.01:
                img = rotate_image_cv(img, angle)

            mask_total = multi_color_stamp_mask(img)

            if mask_total is None or mask_total.sum() == 0:
                self._set_status("❌ لم يتم العثور على ختم واضح. جرّب تدوير مختلف أو صورة أوضح.")
                return

            ys, xs = np.where(mask_total > 0)
            y0, y1 = int(ys.min()), int(ys.max()) + 1
            x0, x1 = int(xs.min()), int(xs.max()) + 1

            pad = 8
            y0 = max(0, y0 - pad)
            x0 = max(0, x0 - pad)
            y1 = min(img.shape[0], y1 + pad)
            x1 = min(img.shape[1], x1 + pad)

            stamp_roi = img[y0:y1, x0:x1]
            mask_roi = mask_total[y0:y1, x0:x1]

            gray_roi = bgr_to_gray(stamp_roi)
            metric = stamp_quality_metric(mask_roi, gray_roi)

            if metric < 3.2:
                stamp_roi = mild_preserve_enhancement(stamp_roi, mask_roi)

            stamp_rgba = make_stamp_rgba(stamp_roi, mask_roi)

            base_name = os.path.splitext(os.path.basename(self.source_path))[0]
            output_dir = os.path.join(STAMP_DIR, base_name)
            os.makedirs(output_dir, exist_ok=True)

            output_path = os.path.join(output_dir, "extracted_stamp.png")
            cv2.imwrite(output_path, stamp_rgba)

            self.last_stamp_path = output_path
            self.last_stamp_bgr = stamp_roi
            self.last_stamp_mask = mask_roi

            self._set_status(f"✓ تم استخراج الختم وحفظه:\n{output_path}")

        except Exception as e:
            self._set_status(f"❌ خطأ أثناء الاستخراج: {str(e)}")

    def apply_stamp_to_thumb(self, instance=None):
        if not self.thumb_path:
            self._set_status("❌ لم يتم تحديد صورة الإبهام بعد.")
            return

        if self.last_stamp_bgr is None or self.last_stamp_mask is None:
            self._set_status("❌ لم يتم استخراج ختم بعد. اضغط استخراج أولاً.")
            return

        try:
            self._set_status("⏳ جاري نقل الأثر على الإبهام...")

            thumb = cv2.imread(self.thumb_path, cv2.IMREAD_COLOR)
            if thumb is None:
                self._set_status("❌ فشل قراءة صورة الإبهام.")
                return

            thumb_bgr = ensure_bgr(thumb)
            stamp_bgr = self.last_stamp_bgr
            stamp_mask = self.last_stamp_mask

            if stamp_bgr is None or stamp_mask is None:
                self._set_status("❌ بيانات الختم غير متاحة.")
                return

            scale_percent = float(self.scale_slider.value)
            th, tw = thumb_bgr.shape[:2]
            sh, sw = stamp_bgr.shape[:2]

            target_w = int(tw * 0.30 * (scale_percent / 120.0))
            if target_w <= 0:
                target_w = sw

            target_h = int(sh * (target_w / float(sw + 1e-9)))
            target_h = max(1, target_h)

            stamp_resized = cv2.resize(stamp_bgr, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
            mask_resized = cv2.resize(stamp_mask, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
            mask_resized = np.where(mask_resized > 0, 255, 0).astype(np.uint8)

            cx = int((self.posx_slider.value / 100.0) * tw)
            cy = int((self.posy_slider.value / 100.0) * th)

            top_left = (cx - target_w // 2, cy - target_h // 2)

            out = overlay_stamp_on_thumb(thumb_bgr, stamp_resized, mask_resized, top_left_xy=top_left, out_size=(tw, th))

            base_name = os.path.splitext(os.path.basename(self.thumb_path))[0]
            src_stamp_name = os.path.splitext(os.path.basename(self.last_stamp_path))[0] if self.last_stamp_path else "stamp"

            output_path = os.path.join(RESULT_DIR, f"{base_name}__{src_stamp_name}__applied.png")
            cv2.imwrite(output_path, out)

            self._set_status(f"✓ تم نقل الأثر وحفظ النتيجة:\n{output_path}")

        except Exception as e:
            self._set_status(f"❌ خطأ أثناء النقل: {str(e)}")


if __name__ == "__main__":
    StampExtractorApp().run()
