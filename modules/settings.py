from dataclasses import dataclass
from typing import Tuple


@dataclass
class Template1Settings:
    bg_color: str = '#8194b0'
    random_bg_color: bool = True
    random_colors: Tuple[str] = ('#040038', '#8142f6', '#4395b1')
    overlay_bg: bool = False
    resize_bg: bool = False

    title_font_size: int = 75
    title_max_width: int = 900
    title_text_color_default: str = 'white'
    title_text_color_dark: str = '#323232'
    title_line_spacing: int = 15
    title_margin_from_top: int = 50

    gradient: bool = False
    gradient_direction: int = 360  # 180 - from top to bottom, 360 - from bottom to top

    tips_count: int = 4
    tips_font_size: int = 36
    tips_top_margin: int = 120
    tips_max_text_width: int = 700
    tips_left_margin: int = 150

    rectangle_top_padding: int = 20
    rectangle_bottom_padding: int = 20
    rectangle_horizontal_padding: int = 30
    rectangle_fill_color: str = 'white'
    rectangle_opacity: int = 255  # Transparency value (0 - fully transparent, 255 - opaque)
    rectangle_corner_radius: int = 20
    rectangle_outline: str = 'grey'
    rectangle_outline_width: int = 0
    tips_text_color: str = '#323232'
    tips_line_spacing: int = 10
    margin_between_tips: int = 110
    tips_block_x_offset: int = 20

    circle_radius: int = 40
    circle_x_offset: int = -55
    circle_y_offset: int = 0
    circle_fill_color: str = '#b7abe9'
    circle_opacity: int = 255  # Transparency value (0 - fully transparent, 255 - opaque)
    circle_outline: str = 'grey'
    circle_outline_width: int = 0
    tips_number_font_size: int = 40
    circle_text_color: str = 'white'
    circle_text_x_offset: int = 0
    circle_text_y_offset: int = 0

    footer: bool = True
    footer_text: str = 'website.com'
    footer_font_size: int = 40
    footer_height: int = 100
    footer_fill_color: str = '#475b75'
    footer_opacity: int = 255  # Transparency value (0 - fully transparent, 255 - opaque)
    footer_text_color: str = 'white'
    footer_text_y_offset: int = 0


@dataclass
class Template2Settings:
    bg_color: str = '#7c95b3'
    random_bg_color: bool = True
    random_colors: Tuple[str] = ('#7ff3b6', '#e684a5', '#b5abe4', '#26364f')
    overlay_bg: bool = True
    resize_bg: bool = False

    gradient: bool = False
    gradient_direction: int = 360  # 180 - from top to bottom, 360 - from bottom to top

    title_font_size: int = 90
    title_text_color: str = '#323232'
    title_line_spacing: int = 20
    title_max_width: int = 550
    title_y_offset: int = -100

    another_font: bool = True
    strings_with_another_font: int = 2
    another_text_top_padding: int = 40
    another_text_font_size: int = 100
    another_text_color: str = '#876ac7'
    another_text_line_spacing: int = 0

    rectangle_top_padding: int = 50
    rectangle_bottom_padding: int = 60
    rectangle_horizontal_padding: int = 50
    rectangle_fill_color: str = 'white'
    rectangle_opacity: int = 255  # Transparency value (0 - fully transparent, 255 - opaque)
    rectangle_outline: str = 'black'
    rectangle_outline_width: int = 5
    rectangle_corner_radius: int = 0

    footer: bool = True
    footer_text: str = 'website.com'
    footer_font_size: int = 40
    footer_height: int = 100
    footer_fill_color: str = '#b7abe9'
    footer_opacity: int = 255  # Transparency value (0 - fully transparent, 255 - opaque)
    footer_text_color: str = 'white'
    footer_text_y_offset: int = 0
