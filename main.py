import os
import sys
import logging
import concurrent.futures
from enum import Enum
from typing import Optional, Tuple, Dict, List, Callable

import cv2
import numpy as np
from PIL import Image as PILImage

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.utils import platform

# -----------------------------------------------------------------------------
# Logging & Storage Setup
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if platform == "android":
    from android.permissions import request_permissions, Permission
    perms = [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
    if hasattr(Permission, "MANAGE_EXTERNAL_STORAGE"):
        perms.append(Permission.MANAGE_EXTERNAL_STORAGE)
    request_permissions(perms)
    BASE_DIR = os.path.join(os.path.expanduser("~"), "DCIM", "StampExtractorPro")
else:
    BASE_DIR = os.path.join(os.path.expanduser("~"), "DCIM", "StampExtractorPro")

STAMP_DIR = os.path.join(BASE_DIR, "ExtractedStamps")
RESULT_DIR = os.path.join(BASE_DIR, "StampResults")

for directory in [STAMP_DIR, RESULT_DIR]:
    os.makedirs(directory, exist_ok=True)


# =============================================================================
# MULTI-LANGUAGE I18N ENGINE (7 LANGUAGES)
# =============================================================================

class Language(Enum):
    AR_EG = "العربية المصرية"
    EN = "English"
    DE = "Deutsch"
    IT = "Italiano"
    FR = "Français"
    RU = "Русский"
    ZH = "简体中文"


TRANSLATIONS: Dict[Language, Dict[str, str]] = {
    Language.AR_EG: {
        "app_title": "مستخرج الأختام الاحترافي - Enterprise AI Pro",
        "status_ready": "جاهز للعمل. اختار صورة الختم والمستند وابدأ.",
        "grid_enable": "تفعيل شبكة المحاذاة",
        "grid_disable": "إخفاء شبكة المحاذاة",
        "reset_pos": "إعادة ضبط المكان",
        "load_stamp": "١. صورة الختم المصدر",
        "load_doc": "٢. صورة المستند الهدف",
        "color_mode": "لون الختم:",
        "opacity": "الشفافية:",
        "intensity": "كثافة الحبر:",
        "export_fmt": "صيغة التصدير:",
        "extract_btn": "استخراج الختم فائق الدقة",
        "export_btn": "توليد المستند النهائي",
        "settings": "الإعدادات",
        "language": "اللغة:",
        "theme": "الثيم:",
        "mode": "النمط:",
        "dark": "داكن (Dark)",
        "light": "فاتح (Light)",
        "ai_assistant": "مساعد الذكاء الاصطناعي",
        "ai_auto_enhance": "تحسين تلقائي ذكي",
        "ai_clean_bg": "تنظيف الورق والظلال",
        "ai_restore_ink": "ترميم حبر الختم الباهت",
        "ai_denoise": "تنقية وإبراز الحواف AI",
        "apply": "تطبيق",
        "close": "إغلاق",
        "ok": "موافق",
        "cancel": "إلغاء",
        "stamp_color_auto": "تلقائي (الكل)",
        "stamp_color_blue": "أزرق",
        "stamp_color_red": "أحمر",
        "stamp_color_green": "أخضر",
        "stamp_color_dark": "أسود / داكن",
    },
    Language.EN: {
        "app_title": "Stamp Extractor Pro - Enterprise AI Pro",
        "status_ready": "System ready. Select source stamp and target document.",
        "grid_enable": "Enable Grid",
        "grid_disable": "Hide Grid",
        "reset_pos": "Reset Position",
        "load_stamp": "1. Source Stamp Image",
        "load_doc": "2. Target Document Image",
        "color_mode": "Color Mode:",
        "opacity": "Opacity:",
        "intensity": "Ink Density:",
        "export_fmt": "Export Format:",
        "extract_btn": "Extract Ultra-Res Stamp",
        "export_btn": "Generate Final Document",
        "settings": "Settings",
        "language": "Language:",
        "theme": "Theme:",
        "mode": "Mode:",
        "dark": "Dark Mode",
        "light": "Light Mode",
        "ai_assistant": "AI Assistant",
        "ai_auto_enhance": "Smart Auto-Enhance",
        "ai_clean_bg": "Clean Paper & Shadows",
        "ai_restore_ink": "Restore Faded Ink",
        "ai_denoise": "AI Denoise & Sharpen",
        "apply": "Apply",
        "close": "Close",
        "ok": "OK",
        "cancel": "Cancel",
        "stamp_color_auto": "Auto (All)",
        "stamp_color_blue": "Blue",
        "stamp_color_red": "Red",
        "stamp_color_green": "Green",
        "stamp_color_dark": "Black / Dark",
    },
    Language.DE: {
        "app_title": "Stempel-Extraktor Pro - Enterprise AI Pro",
        "status_ready": "System bereit. Wählen Sie Quellstempel und Zieldokument.",
        "grid_enable": "Raster aktivieren",
        "grid_disable": "Raster ausblenden",
        "reset_pos": "Position zurücksetzen",
        "load_stamp": "1. Quellstempel-Bild",
        "load_doc": "2. Zieldokument-Bild",
        "color_mode": "Farbmodus:",
        "opacity": "Deckkraft:",
        "intensity": "Tintendichte:",
        "export_fmt": "Exportformat:",
        "extract_btn": "Ultra-Res Stempel extrahieren",
        "export_btn": "Dokument erstellen",
        "settings": "Einstellungen",
        "language": "Sprache:",
        "theme": "Design:",
        "mode": "Modus:",
        "dark": "Dunkel",
        "light": "Hell",
        "ai_assistant": "KI-Assistent",
        "ai_auto_enhance": "Intelligente Auto-Optimierung",
        "ai_clean_bg": "Papier & Schatten reinigen",
        "ai_restore_ink": "Tinte wiederherstellen",
        "ai_denoise": "KI-Entrauschen & Schärfen",
        "apply": "Anwenden",
        "close": "Schließen",
        "ok": "OK",
        "cancel": "Abbrechen",
        "stamp_color_auto": "Auto (Alle)",
        "stamp_color_blue": "Blau",
        "stamp_color_red": "Rot",
        "stamp_color_green": "Grün",
        "stamp_color_dark": "Schwarz / Dunkel",
    },
    Language.IT: {
        "app_title": "Estrattore Timbri Pro - Enterprise AI Pro",
        "status_ready": "Sistema pronto. Seleziona timbro e documento.",
        "grid_enable": "Attiva Griglia",
        "grid_disable": "Nascondi Griglia",
        "reset_pos": "Reimposta Posizione",
        "load_stamp": "1. Immagine Timbro",
        "load_doc": "2. Documento Destinazione",
        "color_mode": "Modalità Colore:",
        "opacity": "Opacità:",
        "intensity": "Densità Inchiostro:",
        "export_fmt": "Formato Esportazione:",
        "extract_btn": "Estrai Timbro Ultra-Res",
        "export_btn": "Genera Documento",
        "settings": "Impostazioni",
        "language": "Lingua:",
        "theme": "Tema:",
        "mode": "Modalità:",
        "dark": "Scuro",
        "light": "Chiaro",
        "ai_assistant": "Assistente AI",
        "ai_auto_enhance": "Miglioramento Auto AI",
        "ai_clean_bg": "Pulisci Carta e Ombre",
        "ai_restore_ink": "Ripristina Inchiostro",
        "ai_denoise": "Riduzione Rumore AI",
        "apply": "Applica",
        "close": "Chiudi",
        "ok": "OK",
        "cancel": "Annulla",
        "stamp_color_auto": "Auto (Tutti)",
        "stamp_color_blue": "Blu",
        "stamp_color_red": "Rosso",
        "stamp_color_green": "Verde",
        "stamp_color_dark": "Nero / Scuro",
    },
    Language.FR: {
        "app_title": "Extracteur de Tampon Pro - Enterprise AI Pro",
        "status_ready": "Système prêt. Sélectionnez le tampon et le document.",
        "grid_enable": "Activer la Grille",
        "grid_disable": "Masquer la Grille",
        "reset_pos": "Réinitialiser Position",
        "load_stamp": "1. Image Tampon Source",
        "load_doc": "2. Image Document Cible",
        "color_mode": "Mode Couleur:",
        "opacity": "Opacité:",
        "intensity": "Densité d'Encre:",
        "export_fmt": "Format d'Exportation:",
        "extract_btn": "Extraire Tampon Ultra-Res",
        "export_btn": "Générer Document",
        "settings": "Paramètres",
        "language": "Langue:",
        "theme": "Thème:",
        "mode": "Mode:",
        "dark": "Sombre",
        "light": "Clair",
        "ai_assistant": "Assistant IA",
        "ai_auto_enhance": "Amélioration Auto IA",
        "ai_clean_bg": "Nettoyer Papier & Ombres",
        "ai_restore_ink": "Restaurer l'Encre",
        "ai_denoise": "Réduction de Bruit IA",
        "apply": "Appliquer",
        "close": "Fermer",
        "ok": "OK",
        "cancel": "Annuler",
        "stamp_color_auto": "Auto (Tous)",
        "stamp_color_blue": "Bleu",
        "stamp_color_red": "Rouge",
        "stamp_color_green": "Vert",
        "stamp_color_dark": "Noir / Sombre",
    },
    Language.RU: {
        "app_title": "Извлекатель Печатей Pro - Enterprise AI Pro",
        "status_ready": "Система готова. Выберите штамп и документ.",
        "grid_enable": "Включить сетку",
        "grid_disable": "Скрыть сетку",
        "reset_pos": "Сбросить позицию",
        "load_stamp": "1. Исходный штамп",
        "load_doc": "2. Целевой документ",
        "color_mode": "Цветовой режим:",
        "opacity": "Прозрачность:",
        "intensity": "Плотность чернил:",
        "export_fmt": "Формат экспорта:",
        "extract_btn": "Извлечь печать Ultra-Res",
        "export_btn": "Создать документ",
        "settings": "Настройки",
        "language": "Язык:",
        "theme": "Тема:",
        "mode": "Режим:",
        "dark": "Тёмный",
        "light": "Светлый",
        "ai_assistant": "ИИ-Помощник",
        "ai_auto_enhance": "Умное авто-улучшение",
        "ai_clean_bg": "Очистка бумаги и теней",
        "ai_restore_ink": "Восстановление чернил",
        "ai_denoise": "ИИ-Подавление шума",
        "apply": "Применить",
        "close": "Закрыть",
        "ok": "ОК",
        "cancel": "Отмена",
        "stamp_color_auto": "Авто (Все)",
        "stamp_color_blue": "Синий",
        "stamp_color_red": "Красный",
        "stamp_color_green": "Зелёный",
        "stamp_color_dark": "Чёрный / Тёмный",
    },
    Language.ZH: {
        "app_title": "印章提取专业版 - Enterprise AI Pro",
        "status_ready": "系统就绪。请选择源印章和目标文档。",
        "grid_enable": "启用网格",
        "grid_disable": "隐藏网格",
        "reset_pos": "重置位置",
        "load_stamp": "1. 源印章图像",
        "load_doc": "2. 目标文档图像",
        "color_mode": "颜色模式:",
        "opacity": "不透明度:",
        "intensity": "墨水密度:",
        "export_fmt": "导出格式:",
        "extract_btn": "提取超清印章",
        "export_btn": "生成最终文档",
        "settings": "设置",
        "language": "语言:",
        "theme": "主题:",
        "mode": "模式:",
        "dark": "暗黑模式",
        "light": "明亮模式",
        "ai_assistant": "AI 助手",
        "ai_auto_enhance": "智能自动增强",
        "ai_clean_bg": "清理阴影与纸张",
        "ai_restore_ink": "修复褪色墨水",
        "ai_denoise": "AI 降噪与锐化",
        "apply": "应用",
        "close": "关闭",
        "ok": "确定",
        "cancel": "取消",
        "stamp_color_auto": "自动 (全部)",
        "stamp_color_blue": "蓝色",
        "stamp_color_red": "红色",
        "stamp_color_green": "绿色",
        "stamp_color_dark": "黑色 / 深色",
    }
}


class I18nEngine:
    _current_lang: Language = Language.AR_EG
    _listeners: List[Callable[[], None]] = []

    @classmethod
    def set_language(cls, lang: Language):
        cls._current_lang = lang
        cls.notify_listeners()

    @classmethod
    def get(cls, key: str) -> str:
        lang_dict = TRANSLATIONS.get(cls._current_lang, TRANSLATIONS[Language.AR_EG])
        return lang_dict.get(key, key)

    @classmethod
    def register_listener(cls, callback: Callable[[], None]):
        if callback not in cls._listeners:
            cls._listeners.append(callback)

    @classmethod
    def notify_listeners(cls):
        for callback in cls._listeners:
            try:
                callback()
            except Exception as e:
                logging.error(f"Error notifying i18n listener: {e}")


# =============================================================================
# THEME ENGINE (6 PALETTES DESIGNED BY GRAPHIC EXPERTS)
# =============================================================================

class ThemeMode(Enum):
    DARK = "Dark"
    LIGHT = "Light"


class ThemeName(Enum):
    DARK_MIDNIGHT = "Midnight Navy (Dark 1)"
    DARK_CYBERPUNK = "Cyberpunk OLED (Dark 2)"
    DARK_EMERALD = "Deep Emerald (Dark 3)"
    LIGHT_SOFT = "Soft Modern (Light 1)"
    LIGHT_SAND = "Warm Sand (Light 2)"
    LIGHT_NORDIC = "Nordic Frost (Light 3)"


THEMES_CONFIG = {
    ThemeName.DARK_MIDNIGHT: {
        "mode": ThemeMode.DARK,
        "bg_root": (0.09, 0.10, 0.14, 1),
        "bg_card": (0.14, 0.15, 0.22, 1),
        "accent_p": (0.28, 0.52, 0.85, 1),
        "accent_s": (0.55, 0.40, 0.82, 1),
        "text_main": (1.0, 1.0, 1.0, 1),
        "text_status": (0.45, 0.72, 1.0, 1),
        "btn_secondary": (0.22, 0.25, 0.35, 1),
    },
    ThemeName.DARK_CYBERPUNK: {
        "mode": ThemeMode.DARK,
        "bg_root": (0.02, 0.02, 0.03, 1),
        "bg_card": (0.08, 0.08, 0.12, 1),
        "accent_p": (0.00, 0.80, 0.80, 1),
        "accent_s": (0.90, 0.20, 0.60, 1),
        "text_main": (0.95, 0.95, 0.98, 1),
        "text_status": (0.00, 0.90, 0.70, 1),
        "btn_secondary": (0.15, 0.15, 0.25, 1),
    },
    ThemeName.DARK_EMERALD: {
        "mode": ThemeMode.DARK,
        "bg_root": (0.06, 0.12, 0.09, 1),
        "bg_card": (0.10, 0.18, 0.14, 1),
        "accent_p": (0.20, 0.60, 0.40, 1),
        "accent_s": (0.80, 0.65, 0.25, 1),
        "text_main": (0.92, 0.96, 0.93, 1),
        "text_status": (0.40, 0.85, 0.60, 1),
        "btn_secondary": (0.15, 0.28, 0.20, 1),
    },
    ThemeName.LIGHT_SOFT: {
        "mode": ThemeMode.LIGHT,
        "bg_root": (0.93, 0.94, 0.96, 1),
        "bg_card": (1.0, 1.0, 1.0, 1),
        "accent_p": (0.22, 0.45, 0.78, 1),
        "accent_s": (0.42, 0.30, 0.68, 1),
        "text_main": (0.15, 0.16, 0.20, 1),
        "text_status": (0.15, 0.35, 0.75, 1),
        "btn_secondary": (0.82, 0.85, 0.90, 1),
    },
    ThemeName.LIGHT_SAND: {
        "mode": ThemeMode.LIGHT,
        "bg_root": (0.95, 0.93, 0.89, 1),
        "bg_card": (1.0, 0.98, 0.95, 1),
        "accent_p": (0.72, 0.45, 0.20, 1),
        "accent_s": (0.50, 0.35, 0.25, 1),
        "text_main": (0.22, 0.18, 0.15, 1),
        "text_status": (0.60, 0.35, 0.10, 1),
        "btn_secondary": (0.88, 0.82, 0.75, 1),
    },
    ThemeName.LIGHT_NORDIC: {
        "mode": ThemeMode.LIGHT,
        "bg_root": (0.90, 0.94, 0.97, 1),
        "bg_card": (0.97, 0.99, 1.0, 1),
        "accent_p": (0.15, 0.55, 0.70, 1),
        "accent_s": (0.30, 0.40, 0.55, 1),
        "text_main": (0.12, 0.18, 0.22, 1),
        "text_status": (0.10, 0.45, 0.60, 1),
        "btn_secondary": (0.80, 0.88, 0.92, 1),
    },
}


class ThemeEngine:
    _current_theme: ThemeName = ThemeName.DARK_MIDNIGHT
    _listeners: List[Callable[[], None]] = []

    @classmethod
    def set_theme(cls, theme: ThemeName):
        cls._current_theme = theme
        cls.notify_listeners()

    @classmethod
    def get_current(cls) -> Dict:
        return THEMES_CONFIG[cls._current_theme]

    @classmethod
    def register_listener(cls, callback: Callable[[], None]):
        if callback not in cls._listeners:
            cls._listeners.append(callback)

    @classmethod
    def notify_listeners(cls):
        for callback in cls._listeners:
            try:
                callback()
            except Exception as e:
                logging.error(f"Error notifying theme listener: {e}")


# =============================================================================
# AUTONOMOUS AI IMAGE ASSISTANT ENGINE (OPENCV/NUMPY COMPUTATIONAL VISION)
# =============================================================================

class AIImageAssistantEngine:
    """
    مساعد الذكاء الاصطناعي المستقل للتعديل على الصور وإصلاح المستندات
    """
    @staticmethod
    def auto_enhance_image(img_bgr: np.ndarray) -> np.ndarray:
        """تحسين التباين والإضاءة الذكي عبر CLAHE وطمس حواف التردد المنخفض"""
        if img_bgr is None:
            return img_bgr
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced_lab = cv2.merge((cl, a, b))
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        return cv2.bilateralFilter(enhanced_bgr, d=5, sigmaColor=50, sigmaSpace=50)

    @staticmethod
    def smart_clean_paper_background(img_bgr: np.ndarray) -> np.ndarray:
        """تنظيف خلفيات المستندات الصفراء والرمادية وتحويلها لأبيض ناصع مع إبراز النصوص"""
        if img_bgr is None:
            return img_bgr
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        smooth = cv2.GaussianBlur(gray, (25, 25), 0)
        division = cv2.divide(gray, smooth, scale=255.0)
        result = cv2.cvtColor(division.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        return result

    @staticmethod
    def restore_faded_stamp_ink(img_bgr: np.ndarray) -> np.ndarray:
        """ترميم وتعميق ألوان حبر الختم الباهت والمتقطع"""
        if img_bgr is None:
            return img_bgr
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s_boosted = cv2.add(s, 40)
        v_boosted = cv2.subtract(v, 15)
        hsv_boosted = cv2.merge((h, s_boosted, v_boosted))
        restored = cv2.cvtColor(hsv_boosted, cv2.COLOR_HSV2BGR)
        return cv2.fastNlMeansDenoisingColored(restored, None, 5, 5, 7, 21)

    @staticmethod
    def ai_denoise_and_sharpen(img_bgr: np.ndarray) -> np.ndarray:
        """إزالة النويز والضجيج الجرافيكي وإبراز حواف الحروف والأختام"""
        if img_bgr is None:
            return img_bgr
        denoised = cv2.fastNlMeansDenoisingColored(img_bgr, None, 7, 7, 7, 21)
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        sharpened = cv2.filter2D(denoised, -1, kernel)
        return sharpened


# =============================================================================
# HIGH-FIDELITY COMPUTER VISION ENGINE (CLAUDE & CHATGPT OPTIMIZED)
# =============================================================================

class HighFidelityStampEngine:
    @staticmethod
    def guided_filter(guide: np.ndarray, src: np.ndarray, radius: int = 4, eps: float = 1e-3) -> np.ndarray:
        guide_32 = guide.astype(np.float32) / 255.0
        src_32 = src.astype(np.float32) / 255.0

        mean_p = cv2.boxFilter(src_32, -1, (radius, radius))
        mean_I = cv2.boxFilter(guide_32, -1, (radius, radius))
        mean_Ip = cv2.boxFilter(guide_32 * src_32, -1, (radius, radius))
        cov_Ip = mean_Ip - mean_I * mean_p

        mean_II = cv2.boxFilter(guide_32 * guide_32, -1, (radius, radius))
        var_I = mean_II - mean_I * mean_I

        a = cov_Ip / (var_I + eps)
        b = mean_p - a * mean_I

        mean_a = cv2.boxFilter(a, -1, (radius, radius))
        mean_b = cv2.boxFilter(b, -1, (radius, radius))

        q = mean_a * guide_32 + mean_b
        return (np.clip(q, 0, 1) * 255.0).astype(np.uint8)

    @classmethod
    def extract_soft_alpha_stamp(
        cls, 
        img_bgr: np.ndarray, 
        color_mode_str: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        sat = hsv[:, :, 1].astype(np.float32) / 255.0
        val = hsv[:, :, 2].astype(np.float32) / 255.0

        if "أزرق" in color_mode_str or "Blue" in color_mode_str or "Blau" in color_mode_str or "Blu" in color_mode_str or "Bleu" in color_mode_str or "Синий" in color_mode_str or "蓝" in color_mode_str:
            color_mask = cv2.inRange(hsv, np.array([85, 30, 20]), np.array([135, 255, 255]))
        elif "أحمر" in color_mode_str or "Red" in color_mode_str or "Rot" in color_mode_str or "Rosso" in color_mode_str or "Rouge" in color_mode_str or "Красный" in color_mode_str or "红" in color_mode_str:
            m1 = cv2.inRange(hsv, np.array([0, 30, 20]), np.array([12, 255, 255]))
            m2 = cv2.inRange(hsv, np.array([155, 30, 20]), np.array([180, 255, 255]))
            color_mask = cv2.bitwise_or(m1, m2)
        elif "أخضر" in color_mode_str or "Green" in color_mode_str or "Grün" in color_mode_str or "Verde" in color_mode_str or "Vert" in color_mode_str or "Зелёный" in color_mode_str or "绿" in color_mode_str:
            color_mask = cv2.inRange(hsv, np.array([35, 30, 20]), np.array([85, 255, 255]))
        elif "أسود" in color_mode_str or "Dark" in color_mode_str or "Schwarz" in color_mode_str or "Nero" in color_mode_str or "Noir" in color_mode_str or "Чёрный" in color_mode_str or "黑" in color_mode_str:
            color_mask = cv2.inRange(val, 0.0, 0.35)
        else:
            chroma = np.sqrt((a_channel.astype(np.float32) - 128)**2 + (b_channel.astype(np.float32) - 128)**2)
            color_mask = np.where((chroma > 12) | (val < 0.4), 255, 0).astype(np.uint8)

        alpha_continuous = (sat * 255.0) * (color_mask.astype(np.float32) / 255.0)
        alpha_continuous = np.clip(alpha_continuous, 0, 255).astype(np.uint8)

        gray_guide = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        refined_alpha = cls.guided_filter(gray_guide, alpha_continuous, radius=3, eps=1e-3)

        return img_bgr, refined_alpha

    @staticmethod
    def process_bgra_composition(
        stamp_bgr: np.ndarray,
        alpha_map: np.ndarray,
        opacity: float = 1.0,
        intensity: float = 1.0
    ) -> np.ndarray:
        adjusted_bgr = cv2.convertScaleAbs(stamp_bgr, alpha=intensity, beta=0) if intensity != 1.0 else stamp_bgr.copy()
        b, g, r = cv2.split(adjusted_bgr)
        final_alpha = (alpha_map.astype(np.float32) * opacity).clip(0, 255).astype(np.uint8)
        return cv2.merge([b, g, r, final_alpha])

    @staticmethod
    def blend_linear_gamma_correct(
        bg_bgr: np.ndarray,
        stamp_bgra: np.ndarray,
        center_xy: Tuple[float, float],
        scale_factor: float = 1.0,
        angle_deg: float = 0.0
    ) -> np.ndarray:
        bg_out = bg_bgr.copy()
        bg_h, bg_w = bg_out.shape[:2]

        sw = int(stamp_bgra.shape[1] * scale_factor)
        sh = int(stamp_bgra.shape[0] * scale_factor)
        if sw <= 0 or sh <= 0:
            return bg_out

        interp = cv2.INTER_AREA if scale_factor < 1.0 else cv2.INTER_LANCZOS4
        stamp_resized = cv2.resize(stamp_bgra, (sw, sh), interpolation=interp)

        if abs(angle_deg) > 0.01:
            h, w = stamp_resized.shape[:2]
            center = (w / 2.0, h / 2.0)
            M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
            cos = abs(M[0, 0])
            sin = abs(M[0, 1])
            nw = int((h * sin) + (w * cos))
            nh = int((h * cos) + (w * sin))
            M[0, 2] += (nw / 2.0) - center[0]
            M[1, 2] += (nh / 2.0) - center[1]
            stamp_resized = cv2.warpAffine(
                stamp_resized, M, (nw, nh),
                flags=cv2.INTER_LANCZOS4,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0, 0)
            )

        sh, sw = stamp_resized.shape[:2]
        cx, cy = int(center_xy[0]), int(center_xy[1])
        x0, y0 = cx - sw // 2, cy - sh // 2

        x1, y1 = max(0, x0), max(0, y0)
        x2, y2 = min(bg_w, x0 + sw), min(bg_h, y0 + sh)

        if x2 <= x1 or y2 <= y1:
            return bg_out

        sx1, sy1 = x1 - x0, y1 - y0
        sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)

        roi_bg = bg_out[y1:y2, x1:x2]
        roi_stamp = stamp_resized[sy1:sy2, sx1:sx2]

        roi_bg_lin = (roi_bg.astype(np.float32) / 255.0) ** 2.2
        stamp_rgb_lin = (roi_stamp[:, :, :3].astype(np.float32) / 255.0) ** 2.2
        alpha = (roi_stamp[:, :, 3].astype(np.float32) / 255.0)[:, :, np.newaxis]

        blended_lin = roi_bg_lin * (1.0 - alpha) + stamp_rgb_lin * alpha
        blended_srgb = (np.clip(blended_lin, 0, 1) ** (1.0 / 2.2)) * 255.0
        bg_out[y1:y2, x1:x2] = blended_srgb.astype(np.uint8)

        return bg_out


def cv2_to_kivy_texture(cv_img: np.ndarray) -> Optional[Texture]:
    if cv_img is None or cv_img.size == 0:
        return None

    if len(cv_img.shape) == 2:
        buf = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGBA)
    elif cv_img.shape[2] == 4:
        buf = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
    else:
        buf = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGBA)

    buf = np.ascontiguousarray(cv2.flip(buf, 0))
    h, w = buf.shape[:2]
    texture = Texture.create(size=(w, h), colorfmt='rgba')
    texture.blit_buffer(buf.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
    return texture


# =============================================================================
# REACTIVE UI COMPONENTS
# =============================================================================

class ThemeableCard(BoxLayout):
    def __init__(self, card_type="card", radius=None, **kwargs):
        super().__init__(**kwargs)
        self.card_type = card_type
        if radius is None:
            radius = [12]
        self.radius = radius

        ThemeEngine.register_listener(self.update_theme_colors)
        with self.canvas.before:
            self.bg_color_inst = Color(0, 0, 0, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
        self.bind(pos=self._update_geometry, size=self._update_geometry)
        self.update_theme_colors()

    def _update_geometry(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def update_theme_colors(self):
        theme = ThemeEngine.get_current()
        if self.card_type == "root":
            c = theme["bg_root"]
        else:
            c = theme["bg_card"]
        self.bg_color_inst.rgba = c


class StyledButton(Button):
    def __init__(self, btn_role="primary", **kwargs):
        super().__init__(**kwargs)
        self.btn_role = btn_role
        self.background_normal = ''
        self.bold = True
        ThemeEngine.register_listener(self.update_theme_colors)
        self.update_theme_colors()

    def update_theme_colors(self):
        theme = ThemeEngine.get_current()
        if self.btn_role == "primary":
            self.background_color = theme["accent_p"]
            self.color = (1, 1, 1, 1)
        elif self.btn_role == "secondary":
            self.background_color = theme["btn_secondary"]
            self.color = theme["text_main"]
        elif self.btn_role == "accent":
            self.background_color = theme["accent_s"]
            self.color = (1, 1, 1, 1)


class EnterpriseWorkspace(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid_enabled = False

        self.bg_image_widget = Image(
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.bg_image_widget)

        self.scatter = Scatter(
            do_rotation=True,
            do_scale=True,
            do_translation=True,
            size_hint=(None, None),
            size=(200, 200),
            auto_bring_to_front=True
        )

        self.stamp_image_widget = Image(
            allow_stretch=True,
            keep_ratio=False,
            size=(200, 200)
        )
        self.scatter.add_widget(self.stamp_image_widget)
        self.add_widget(self.scatter)
        self.scatter.opacity = 0

        self.bind(size=self._draw_grid, pos=self._draw_grid)

    def toggle_grid(self) -> bool:
        self.grid_enabled = not self.grid_enabled
        self._draw_grid()
        return self.grid_enabled

    def _draw_grid(self, *args):
        self.canvas.after.clear()
        if not self.grid_enabled:
            return
        theme = ThemeEngine.get_current()
        with self.canvas.after:
            Color(*theme["accent_p"][:3], 0.3)
            cols, rows = 10, 10
            w_step = self.width / float(cols)
            h_step = self.height / float(rows)
            for i in range(1, cols):
                Line(points=[self.x + i * w_step, self.y, self.x + i * w_step, self.y + self.height], width=1)
            for j in range(1, rows):
                Line(points=[self.x, self.y + j * h_step, self.x + self.width, self.y + j * h_step], width=1)

    def reset_stamp_transform(self):
        if self.scatter:
            self.scatter.rotation = 0
            self.scatter.scale = 1.0
            self.scatter.center = self.center

    def set_stamp_texture(self, texture: Texture, orig_size: Tuple[int, int]):
        sw, sh = orig_size
        max_disp = 220.0
        scale = min(max_disp / float(sw), max_disp / float(sh), 1.0)
        disp_w, disp_h = float(sw) * scale, float(sh) * scale

        self.stamp_image_widget.texture = texture
        self.scatter.size = (disp_w, disp_h)
        self.stamp_image_widget.size = (disp_w, disp_h)
        self.scatter.center = self.center
        self.scatter.opacity = 1

    def calculate_exact_geometry(
        self, 
        orig_bg_w: int, 
        orig_bg_h: int, 
        orig_stamp_w: int, 
        orig_stamp_h: int
    ) -> Optional[Tuple[Tuple[float, float], float, float]]:
        if self.bg_image_widget.texture is None or self.scatter.opacity == 0:
            return None

        norm_w, norm_h = self.bg_image_widget.norm_image_size
        if norm_w <= 0 or norm_h <= 0 or orig_stamp_w <= 0:
            return None

        disp_x = self.bg_image_widget.center_x - (norm_w / 2.0)
        disp_y = self.bg_image_widget.center_y - (norm_h / 2.0)

        rel_x = self.scatter.center_x - disp_x
        rel_y = self.scatter.center_y - disp_y

        scale_x = orig_bg_w / float(norm_w)
        scale_y = orig_bg_h / float(norm_h)

        pixel_cx = rel_x * scale_x
        pixel_cy = (norm_h - rel_y) * scale_y

        scatter_scale = self.scatter.scale
        target_stamp_w = self.scatter.width * scatter_scale * scale_x
        final_scale_factor = target_stamp_w / float(orig_stamp_w)

        angle = -self.scatter.rotation
        return (pixel_cx, pixel_cy), final_scale_factor, angle


# =============================================================================
# SETTINGS & AI POPUP WINDOWS
# =============================================================================

class SettingsPopup(Popup):
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        self.app_ctrl = app_controller
        self.title = I18nEngine.get("settings")
        self.size_hint = (0.85, 0.75)

        layout = ThemeableCard(orientation='vertical', padding=12, spacing=10)

        # Language Selection
        r_lang = BoxLayout(size_hint_y=0.25, spacing=8)
        self.lbl_lang = Label(text=I18nEngine.get("language"), bold=True, size_hint_x=0.3)
        self.spn_lang = Spinner(
            text=I18nEngine._current_lang.value,
            values=[l.value for l in Language],
            size_hint_x=0.7
        )
        self.spn_lang.bind(text=self.on_language_change)
        r_lang.add_widget(self.lbl_lang)
        r_lang.add_widget(self.spn_lang)
        layout.add_widget(r_lang)

        # Theme Mode Selection (Dark / Light)
        r_mode = BoxLayout(size_hint_y=0.25, spacing=8)
        self.lbl_mode = Label(text=I18nEngine.get("mode"), bold=True, size_hint_x=0.3)
        self.spn_mode = Spinner(
            text=ThemeEngine.get_current()["mode"].value,
            values=[ThemeMode.DARK.value, ThemeMode.LIGHT.value],
            size_hint_x=0.7
        )
        self.spn_mode.bind(text=self.on_mode_change)
        r_mode.add_widget(self.lbl_mode)
        r_mode.add_widget(self.spn_mode)
        layout.add_widget(r_mode)

        # Theme Palette Selection (6 Themes)
        r_theme = BoxLayout(size_hint_y=0.25, spacing=8)
        self.lbl_theme = Label(text=I18nEngine.get("theme"), bold=True, size_hint_x=0.3)
        self.spn_theme = Spinner(
            text=ThemeEngine._current_theme.value,
            values=[t.value for t in ThemeName],
            size_hint_x=0.7
        )
        self.spn_theme.bind(text=self.on_theme_change)
        r_theme.add_widget(self.lbl_theme)
        r_theme.add_widget(self.spn_theme)
        layout.add_widget(r_theme)

        # Close Button
        btn_close = StyledButton(text=I18nEngine.get("close"), btn_role="secondary", size_hint_y=0.25)
        btn_close.bind(on_press=self.dismiss)
        layout.add_widget(btn_close)

        self.content = layout

    def on_language_change(self, spinner, text):
        for l in Language:
            if l.value == text:
                I18nEngine.set_language(l)
                self.title = I18nEngine.get("settings")
                self.lbl_lang.text = I18nEngine.get("language")
                self.lbl_mode.text = I18nEngine.get("mode")
                self.lbl_theme.text = I18nEngine.get("theme")
                break

    def on_mode_change(self, spinner, text):
        if text == ThemeMode.DARK.value:
            ThemeEngine.set_theme(ThemeName.DARK_MIDNIGHT)
        else:
            ThemeEngine.set_theme(ThemeName.LIGHT_SOFT)
        self.spn_theme.text = ThemeEngine._current_theme.value

    def on_theme_change(self, spinner, text):
        for t in ThemeName:
            if t.value == text:
                ThemeEngine.set_theme(t)
                self.spn_mode.text = THEMES_CONFIG[t]["mode"].value
                break


class AIAssistantPopup(Popup):
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        self.app_ctrl = app_controller
        self.title = I18nEngine.get("ai_assistant")
        self.size_hint = (0.90, 0.80)

        layout = ThemeableCard(orientation='vertical', padding=12, spacing=10)

        grid = GridLayout(cols=1, spacing=8, size_hint_y=0.8)

        btn_auto = StyledButton(text=I18nEngine.get("ai_auto_enhance"), btn_role="accent")
        btn_auto.bind(on_press=lambda x: self.run_ai("auto"))

        btn_bg = StyledButton(text=I18nEngine.get("ai_clean_bg"), btn_role="primary")
        btn_bg.bind(on_press=lambda x: self.run_ai("clean_bg"))

        btn_ink = StyledButton(text=I18nEngine.get("ai_restore_ink"), btn_role="primary")
        btn_ink.bind(on_press=lambda x: self.run_ai("restore_ink"))

        btn_denoise = StyledButton(text=I18nEngine.get("ai_denoise"), btn_role="accent")
        btn_denoise.bind(on_press=lambda x: self.run_ai("denoise"))

        grid.add_widget(btn_auto)
        grid.add_widget(btn_bg)
        grid.add_widget(btn_ink)
        grid.add_widget(btn_denoise)

        layout.add_widget(grid)

        btn_close = StyledButton(text=I18nEngine.get("close"), btn_role="secondary", size_hint_y=0.2)
        btn_close.bind(on_press=self.dismiss)
        layout.add_widget(btn_close)

        self.content = layout

    def run_ai(self, mode: str):
        self.dismiss()
        self.app_ctrl.execute_ai_enhancement(mode)


# =============================================================================
# MAIN ENTERPRISE APPLICATION CONTROLLER
# =============================================================================

class EnterpriseStampExtractorApp(App):
    def build(self):
        self.title = I18nEngine.get("app_title")

        self.source_path: Optional[str] = None
        self.thumb_path: Optional[str] = None
        self.last_stamp_roi: Optional[np.ndarray] = None
        self.last_alpha_map: Optional[np.ndarray] = None
        self.last_stamp_bgra: Optional[np.ndarray] = None
        self.thumb_bgr: Optional[np.ndarray] = None

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

        root = ThemeableCard(card_type="root", orientation="vertical", padding=10, spacing=8)

        # Header Bar
        header = ThemeableCard(size_hint_y=0.08, padding=6)
        self.status_label = Label(
            text=I18nEngine.get("status_ready"),
            font_size='13sp',
            bold=True
        )
        
        self.btn_ai_nav = StyledButton(
            text=I18nEngine.get("ai_assistant"),
            btn_role="accent",
            size_hint_x=0.25,
            on_press=self.open_ai_popup
        )
        
        self.btn_settings = StyledButton(
            text=I18nEngine.get("settings"),
            btn_role="secondary",
            size_hint_x=0.20,
            on_press=self.open_settings_popup
        )

        header.add_widget(self.status_label)
        header.add_widget(self.btn_ai_nav)
        header.add_widget(self.btn_settings)
        root.add_widget(header)

        # Central Workspace
        self.workspace = EnterpriseWorkspace(size_hint_y=0.52)
        root.add_widget(self.workspace)

        # Toolbar
        quick_bar = BoxLayout(size_hint_y=0.07, spacing=6)
        self.grid_btn = StyledButton(
            text=I18nEngine.get("grid_enable"),
            btn_role="secondary",
            on_press=self.toggle_grid_action
        )
        self.reset_btn = StyledButton(
            text=I18nEngine.get("reset_pos"),
            btn_role="secondary",
            on_press=lambda x: self.workspace.reset_stamp_transform()
        )
        quick_bar.add_widget(self.grid_btn)
        quick_bar.add_widget(self.reset_btn)
        root.add_widget(quick_bar)

        # Main Control Card
        ctrl = ThemeableCard(orientation="vertical", size_hint_y=0.33, padding=8, spacing=6)

        r1 = BoxLayout(size_hint_y=0.25, spacing=6)
        self.btn_load_stamp = StyledButton(text=I18nEngine.get("load_stamp"), btn_role="primary", on_press=self.open_source_popup)
        self.btn_load_doc = StyledButton(text=I18nEngine.get("load_doc"), btn_role="primary", on_press=self.open_thumb_popup)
        r1.add_widget(self.btn_load_stamp)
        r1.add_widget(self.btn_load_doc)

        r2 = GridLayout(cols=6, size_hint_y=0.25, spacing=4)
        self.lbl_color = Label(text=I18nEngine.get("color_mode"), size_hint_x=0.15, bold=True, font_size='12sp')
        
        self.color_spinner = Spinner(
            text=I18nEngine.get("stamp_color_auto"),
            values=[
                I18nEngine.get("stamp_color_auto"),
                I18nEngine.get("stamp_color_blue"),
                I18nEngine.get("stamp_color_red"),
                I18nEngine.get("stamp_color_green"),
                I18nEngine.get("stamp_color_dark")
            ],
            size_hint_x=0.25
        )
        r2.add_widget(self.lbl_color)
        r2.add_widget(self.color_spinner)

        self.lbl_opacity = Label(text=I18nEngine.get("opacity"), size_hint_x=0.12, bold=True, font_size='12sp')
        self.opacity_badge = Label(text="100%", size_hint_x=0.1, bold=True)
        self.opacity_slider = Slider(min=0.1, max=1.0, value=1.0, size_hint_x=0.28)
        self.opacity_slider.bind(value=self.on_slider_change)
        r2.add_widget(self.lbl_opacity)
        r2.add_widget(self.opacity_badge)
        r2.add_widget(self.opacity_slider)

        r3 = GridLayout(cols=6, size_hint_y=0.25, spacing=4)
        self.lbl_intensity = Label(text=I18nEngine.get("intensity"), size_hint_x=0.15, bold=True, font_size='12sp')
        self.intensity_badge = Label(text="100%", size_hint_x=0.1, bold=True)
        self.intensity_slider = Slider(min=0.5, max=2.0, value=1.0, size_hint_x=0.25)
        self.intensity_slider.bind(value=self.on_slider_change)
        r3.add_widget(self.lbl_intensity)
        r3.add_widget(self.intensity_badge)
        r3.add_widget(self.intensity_slider)

        self.lbl_export = Label(text=I18nEngine.get("export_fmt"), size_hint_x=0.15, bold=True, font_size='12sp')
        self.format_spinner = Spinner(
            text="PNG",
            values=["PNG", "JPG", "PDF", "WEBP"],
            size_hint_x=0.25
        )
        r3.add_widget(self.lbl_export)
        r3.add_widget(self.format_spinner)

        r4 = BoxLayout(size_hint_y=0.25, spacing=6)
        self.btn_extract = StyledButton(
            text=I18nEngine.get("extract_btn"),
            btn_role="accent",
            on_press=self.trigger_async_extraction
        )
        self.btn_export = StyledButton(
            text=I18nEngine.get("export_btn"),
            btn_role="primary",
            on_press=self.trigger_async_save
        )
        r4.add_widget(self.btn_extract)
        r4.add_widget(self.btn_export)

        ctrl.add_widget(r1)
        ctrl.add_widget(r2)
        ctrl.add_widget(r3)
        ctrl.add_widget(r4)

        root.add_widget(ctrl)

        # Register i18n & Theme Change Listeners
        I18nEngine.register_listener(self.update_ui_translations)
        ThemeEngine.register_listener(self.update_ui_theme_colors)

        self.update_ui_theme_colors()

        return root

    def update_ui_translations(self):
        self.title = I18nEngine.get("app_title")
        self.btn_settings.text = I18nEngine.get("settings")
        self.btn_ai_nav.text = I18nEngine.get("ai_assistant")
        self.btn_load_stamp.text = I18nEngine.get("load_stamp")
        self.btn_load_doc.text = I18nEngine.get("load_doc")
        self.lbl_color.text = I18nEngine.get("color_mode")
        self.lbl_opacity.text = I18nEngine.get("opacity")
        self.lbl_intensity.text = I18nEngine.get("intensity")
        self.lbl_export.text = I18nEngine.get("export_fmt")
        self.btn_extract.text = I18nEngine.get("extract_btn")
        self.btn_export.text = I18nEngine.get("export_btn")
        self.grid_btn.text = I18nEngine.get("grid_disable") if self.workspace.grid_enabled else I18nEngine.get("grid_enable")
        self.reset_btn.text = I18nEngine.get("reset_pos")
        
        self.color_spinner.values = [
            I18nEngine.get("stamp_color_auto"),
            I18nEngine.get("stamp_color_blue"),
            I18nEngine.get("stamp_color_red"),
            I18nEngine.get("stamp_color_green"),
            I18nEngine.get("stamp_color_dark")
        ]
        self.color_spinner.text = I18nEngine.get("stamp_color_auto")

    def update_ui_theme_colors(self):
        theme = ThemeEngine.get_current()
        self.status_label.color = theme["text_status"]
        self.opacity_badge.color = theme["accent_p"]
        self.intensity_badge.color = theme["accent_s"]

    def set_status(self, text: str):
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', text))

    def toggle_grid_action(self, instance):
        is_on = self.workspace.toggle_grid()
        self.grid_btn.text = I18nEngine.get("grid_disable") if is_on else I18nEngine.get("grid_enable")

    def on_slider_change(self, instance, value):
        self.opacity_badge.text = f"{int(self.opacity_slider.value * 100)}%"
        self.intensity_badge.text = f"{int(self.intensity_slider.value * 100)}%"
        
        Clock.unschedule(self._deferred_preview_update)
        Clock.schedule_once(self._deferred_preview_update, 0.03)

    def _deferred_preview_update(self, dt):
        if self.last_stamp_roi is not None and self.last_alpha_map is not None:
            self.last_stamp_bgra = HighFidelityStampEngine.process_bgra_composition(
                self.last_stamp_roi,
                self.last_alpha_map,
                opacity=self.opacity_slider.value,
                intensity=self.intensity_slider.value
            )
            tex = cv2_to_kivy_texture(self.last_stamp_bgra)
            sh, sw = self.last_stamp_bgra.shape[:2]
            self.workspace.set_stamp_texture(tex, orig_size=(sw, sh))

    def open_settings_popup(self, instance):
        popup = SettingsPopup(app_controller=self)
        popup.open()

    def open_ai_popup(self, instance):
        popup = AIAssistantPopup(app_controller=self)
        popup.open()

    def execute_ai_enhancement(self, mode: str):
        if self.thumb_bgr is None and self.last_stamp_roi is None:
            self.set_status("❌ اختر صورة أولاً للتعديل بواسطة الذكاء الاصطناعي.")
            return

        self.set_status(f"⏳ جاري تشغيل وحدة الذكاء الاصطناعي [{mode}]...")
        self.executor.submit(self._task_ai_processing, mode)

    def _task_ai_processing(self, mode: str):
        try:
            if self.thumb_bgr is not None:
                if mode == "auto":
                    self.thumb_bgr = AIImageAssistantEngine.auto_enhance_image(self.thumb_bgr)
                elif mode == "clean_bg":
                    self.thumb_bgr = AIImageAssistantEngine.smart_clean_paper_background(self.thumb_bgr)
                elif mode == "denoise":
                    self.thumb_bgr = AIImageAssistantEngine.ai_denoise_and_sharpen(self.thumb_bgr)

                tex = cv2_to_kivy_texture(self.thumb_bgr)
                Clock.schedule_once(lambda dt: setattr(self.workspace.bg_image_widget, 'texture', tex))

            if self.last_stamp_roi is not None:
                if mode == "restore_ink":
                    self.last_stamp_roi = AIImageAssistantEngine.restore_faded_stamp_ink(self.last_stamp_roi)
                    self._deferred_preview_update(0)

            self.set_status("✓ تم التطبيق بنجاح بواسطة مساعد الذكاء الاصطناعي!")
        except Exception as e:
            logging.exception("AI Processing Error")
            self.set_status(f"❌ خطأ في معالجة الذكاء الاصطناعي: {str(e)}")

    def open_file_dialog(self, title: str, callback):
        content = BoxLayout(orientation='vertical', spacing=6)
        chooser = FileChooserIconView(path=BASE_DIR, filters=['*.png', '*.jpg', '*.jpeg', '*.webp', '*.bmp'])
        content.add_widget(chooser)

        btns = BoxLayout(size_hint_y=0.15, spacing=6)
        btn_ok = StyledButton(text=I18nEngine.get("ok"), btn_role="primary")
        btn_cancel = StyledButton(text=I18nEngine.get("cancel"), btn_role="secondary")
        btns.add_widget(btn_ok)
        btns.add_widget(btn_cancel)
        content.add_widget(btns)

        popup = Popup(title=title, content=content, size_hint=(0.92, 0.92))

        def on_select(_):
            if chooser.selection:
                callback(chooser.selection[0])
                popup.dismiss()

        btn_ok.bind(on_press=on_select)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def open_source_popup(self, instance):
        self.open_file_dialog(I18nEngine.get("load_stamp"), lambda path: self._set_source_path(path))

    def _set_source_path(self, path: str):
        self.source_path = path
        self.set_status(f"✓ تم اختيار الختم: {os.path.basename(path)}")

    def open_thumb_popup(self, instance):
        self.open_file_dialog(I18nEngine.get("load_doc"), lambda path: self._set_thumb_path(path))

    def _set_thumb_path(self, path: str):
        self.thumb_path = path
        self.thumb_bgr = cv2.imread(path, cv2.IMREAD_COLOR)
        if self.thumb_bgr is not None:
            tex = cv2_to_kivy_texture(self.thumb_bgr)
            self.workspace.bg_image_widget.texture = tex
            self.set_status(f"✓ تم تحميل المستند: {os.path.basename(path)}")

    def trigger_async_extraction(self, instance):
        if not self.source_path:
            self.set_status("❌ اختر صورة الختم أولاً!")
            return

        self.set_status("⏳ جاري استخراج الختم بتقنية Soft Alpha Matting...")
        self.executor.submit(self._task_extract_stamp)

    def _task_extract_stamp(self):
        try:
            img = cv2.imread(self.source_path, cv2.IMREAD_COLOR)
            if img is None:
                self.set_status("❌ تعذر قراءة صورة الختم المصدر.")
                return

            color_str = self.color_spinner.text
            stamp_bgr, alpha_map = HighFidelityStampEngine.extract_soft_alpha_stamp(img, color_str)

            if alpha_map is None or alpha_map.sum() == 0:
                self.set_status("❌ لم يتم العثور على أثر حبر محدد.")
                return

            ys, xs = np.where(alpha_map > 5)
            if len(ys) == 0 or len(xs) == 0:
                self.set_status("❌ مساحة الحبر المستخرجة غير كافية.")
                return

            y0, y1 = int(ys.min()), int(ys.max()) + 1
            x0, x1 = int(xs.min()), int(xs.max()) + 1

            pad = 8
            y0, x0 = max(0, y0 - pad), max(0, x0 - pad)
            y1, x1 = min(img.shape[0], y1 + pad), min(img.shape[1], x1 + pad)

            self.last_stamp_roi = stamp_bgr[y0:y1, x0:x1]
            self.last_alpha_map = alpha_map[y0:y1, x0:x1]

            self.last_stamp_bgra = HighFidelityStampEngine.process_bgra_composition(
                self.last_stamp_roi,
                self.last_alpha_map,
                opacity=self.opacity_slider.value,
                intensity=self.intensity_slider.value
            )

            base_name = os.path.splitext(os.path.basename(self.source_path))[0]
            out_png = os.path.join(STAMP_DIR, f"{base_name}_extracted.png")
            cv2.imwrite(out_png, self.last_stamp_bgra)

            stamp_tex = cv2_to_kivy_texture(self.last_stamp_bgra)
            sh, sw = self.last_stamp_bgra.shape[:2]

            def update_ui(dt):
                self.workspace.set_stamp_texture(stamp_tex, orig_size=(sw, sh))
                self.set_status("✓ تم استخراج الختم بنجاح مطابق للأصل!")

            Clock.schedule_once(update_ui)

        except Exception as e:
            logging.exception("Extraction Error")
            self.set_status(f"❌ خطأ أثناء الاستخراج: {str(e)}")

    def trigger_async_save(self, instance):
        if self.thumb_bgr is None or self.last_stamp_bgra is None:
            self.set_status("❌ يرجى استخراج الختم واختيار صورة المستند أولاً!")
            return

        bg_h, bg_w = self.thumb_bgr.shape[:2]
        st_h, st_w = self.last_stamp_bgra.shape[:2]

        transform_data = self.workspace.calculate_exact_geometry(bg_w, bg_h, st_w, st_h)
        if transform_data is None:
            self.set_status("❌ تعذر تحديد موقع الختم بالنسبة للمستند.")
            return

        self.set_status("⏳ جاري دمج الختم في الفضاء الخطي عالي الدقة...")
        self.executor.submit(self._task_save_result, transform_data)

    def _task_save_result(self, transform_data):
        try:
            center_xy, scale_factor, angle = transform_data

            result_bgr = HighFidelityStampEngine.blend_linear_gamma_correct(
                self.thumb_bgr,
                self.last_stamp_bgra,
                center_xy=center_xy,
                scale_factor=scale_factor,
                angle_deg=angle
            )

            fmt = self.format_spinner.text.lower()
            base_thumb = os.path.splitext(os.path.basename(self.thumb_path))[0]
            out_path = os.path.join(RESULT_DIR, f"{base_thumb}_result.{fmt}")

            if fmt in ["png", "webp"]:
                cv2.imwrite(out_path, result_bgr)
            elif fmt in ["jpg", "jpeg"]:
                cv2.imwrite(out_path, result_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 98])
            elif fmt == "pdf":
                rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
                pil_img = PILImage.fromarray(rgb)
                pil_img.save(out_path, "PDF", resolution=150.0)

            self.set_status(f"✓ تم التصدير بنجاح:\n{out_path}")

        except Exception as e:
            logging.exception("Export Error")
            self.set_status(f"❌ خطأ أثناء الحفظ: {str(e)}")

    def on_stop(self):
        self.executor.shutdown(wait=False)


if __name__ == "__main__":
    EnterpriseStampExtractorApp().run()
