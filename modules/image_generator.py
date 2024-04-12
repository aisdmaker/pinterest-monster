import datetime
import os
import random
import re

from PIL import Image, ImageDraw, ImageFont, ImageColor

from modules.base import Pinterest
from modules.settings import Template1Settings, Template2Settings


class BaseImageGenerator(Pinterest):
    TEMPLATES = ['template_1', 'template_2']
    SUBFOLDERS = ['fonts']

    def __init__(self, project_folder, template, width=1000, height=1500, image_format='png', dpi=(72, 72),
                 save=True, show=True, write_uploading_data=False):
        super().__init__(project_folder)
        self.template = template
        self.width = width
        self.height = height
        self.image_format = image_format
        self.dpi = dpi
        self.save = save
        self.show = show
        self.write_uploading_data = write_uploading_data

        self.project_assets_path = os.path.join(self.project_path, 'assets')
        self.backgrounds_path = os.path.join(self.project_assets_path, 'backgrounds')
        self.save_image_path = os.path.join(self.project_path, 'images')

        os.makedirs(self.backgrounds_path, exist_ok=True)
        os.makedirs(self.save_image_path, exist_ok=True)

        self.assets_path = os.path.join(self.data_path, 'image_assets')

        for template in self.TEMPLATES:
            template_path = os.path.join(self.assets_path, template)
            setattr(self, template, template_path)

            for subfolder in self.SUBFOLDERS:
                subfolder_path = os.path.join(template_path, subfolder)
                setattr(self, f'{template}_{subfolder}_path', subfolder_path)
                os.makedirs(subfolder_path, exist_ok=True)

        self.settings = self._get_template_settings()

        self.canvas = Image.new("RGBA", (self.width, self.height))

    def _get_template_settings(self):
        if self.template == self.GENERATOR_MODE_1:
            return Template1Settings()
        elif self.template == self.GENERATOR_MODE_2:
            return Template2Settings()
        else:
            raise ValueError(f"Invalid template mode: {self.template}")

    def _fill_background(self, color):
        # Create a drawing object to draw on the canvas
        draw = ImageDraw.Draw(self.canvas)
        # Get the width and height of the canvas
        width, height = self.canvas.size
        # Draw a filled rectangle covering the entire canvas with the specified color
        draw.rectangle((0, 0, width, height), fill=color)

    @staticmethod
    def _get_background_files(folder_path):
        return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))
                and f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    def _add_gradient(self, gradient_color):
        # Create a new RGBA image with the specified gradient color
        gradient = Image.new('RGBA', (self.width, self.height), gradient_color)

        # Generate an alpha gradient with a linear gradient
        alpha = Image.linear_gradient('L').rotate(self.settings.gradient_direction).resize((self.width, self.height))

        # Apply the alpha gradient to the gradient image
        gradient.putalpha(alpha)

        # Composite the gradient onto the canvas
        self.canvas.alpha_composite(gradient)

    def _draw_background(self):
        if self.settings.overlay_bg:
            # Get a list of files from the specified folder
            bg_files = self._get_background_files(self.backgrounds_path)

            if bg_files:
                # Choose a random image from the list of files
                bg_image_path = os.path.join(self.backgrounds_path, random.choice(bg_files))

                # Open the image and convert it to RGBA mode
                bg_image = Image.open(bg_image_path).convert('RGBA')

                # Resize the background image if the option is enabled
                if self.settings.resize_bg:
                    # Define the desired width for the image
                    resized_width = self.width
                    # Calculate the corresponding height to maintain aspect ratio
                    resized_height = int((resized_width / bg_image.width) * bg_image.height)
                    # Resize the image
                    bg_image_resized = bg_image.resize((resized_width, resized_height))
                    # Paste the resized image onto the canvas
                    self.canvas.paste(bg_image_resized, (0, 0))
                else:
                    # Paste the original image onto the canvas
                    self.canvas.paste(bg_image, (0, 0))

                if self.settings.gradient:
                    if self.settings.random_bg_color:
                        # If random background color is enabled, choose a random color from the list
                        random_color = random.choice(self.settings.random_colors)
                        self._add_gradient(random_color)
                    else:
                        # If random background color is disabled, use the specified background color
                        self._add_gradient(self.settings.bg_color)

                return self._contains_light(bg_image_path)
        else:
            if self.settings.random_bg_color:
                random_color = random.choice(self.settings.random_colors)

                self._fill_background(random_color)
            else:
                self._fill_background(self.settings.bg_color)

    @staticmethod
    def _contains_light(filename):
        base_name = os.path.basename(filename)
        return 'light' in base_name.lower()

    @staticmethod
    def _wrap_text(text, font, max_width):
        lines = []  # List to store the wrapped lines of text
        words = text.split()  # Split the input text into words
        current_line = words[0]  # Initialize the current line with the first word

        # Iterate over the remaining words
        for word in words[1:]:
            test_line = current_line + " " + word  # Append the next word to the current line
            bbox = font.getbbox(test_line)  # Get the bounding box of the test line

            # Check if the width of the test line exceeds the maximum width
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line  # If within limit, update the current line
            else:
                lines.append(current_line)  # If exceeds, add the current line to the list
                current_line = word  # Start a new line with the current word

        lines.append(current_line)  # Add the last line to the list
        return '\n'.join(lines)  # Join the wrapped lines with line breaks and return as a single string

    @staticmethod
    def _color_with_alpha(color, alpha):
        r, g, b = ImageColor.getrgb(color)
        return r, g, b, alpha

    def _add_footer_with_text(self, text, font_path):
        # Create a transparent canvas
        transparent_canvas = Image.new('RGBA', self.canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(transparent_canvas)

        # Load the font
        font = ImageFont.truetype(font_path, self.settings.footer_font_size)

        # Determine the dimensions of the image
        image_width, image_height = self.canvas.size

        # Dimensions of the footer bar
        bar_width = image_width
        bar_start_y = image_height - self.settings.footer_height

        # Convert footer fill color to RGBA format with transparency
        footer_fill_color = self._color_with_alpha(self.settings.footer_fill_color, self.settings.footer_opacity)

        # Draw the footer bar
        draw.rectangle((0, bar_start_y, bar_width, image_height), fill=footer_fill_color)

        # Determine the dimensions of the text
        text_bbox = font.getbbox(text)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        # Calculate coordinates to center the text inside the footer bar
        text_x = (bar_width - text_width) // 2
        text_y = bar_start_y + (self.settings.footer_height - text_height) // 2

        # Draw the text
        draw.text((text_x, text_y + self.settings.footer_text_y_offset), text, font=font,
                  fill=self.settings.footer_text_color)

        self.canvas.alpha_composite(transparent_canvas)

    @staticmethod
    def _get_footer_text(file_path, default_text):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Read the first line from the file
                line = file.readline().strip()

                # If the line is not empty, return it
                if line:
                    return line
                # If the line is empty, return the default value
                else:
                    return default_text
        except FileNotFoundError:
            # If the file is not found, return the default value
            return default_text

    def _get_file_path(self, image_number):
        # Get the current timestamp in the specified format
        current_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

        # Create a filename incorporating the image number and current timestamp
        filename = f'{image_number}_{current_time}.{self.image_format}'

        # Generate the full file path by joining the save image path and filename
        file_path = os.path.join(self.save_image_path, filename)

        # Return the complete file path
        return file_path

    def save_image(self, file_path, image_number):
        # Save the canvas as an image file with the specified DPI
        self.canvas.save(file_path, dpi=self.dpi)

        # Log a success message indicating that the image was saved
        self._log_message(f'{image_number} Image successfully saved')

    @staticmethod
    def _get_uploading_data(data, file_path):
        uploading_data = {
            'mode': data.get('mode', ''),
            'keyword': data.get('keyword', ''),
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'file_path': file_path,
            'board_name': '',
            'pin_link': '',
        }
        return uploading_data

    def generate_image(self, data, image_number):
        raise NotImplementedError("Subclasses must implement the generate_image method")


class Template1ImageGenerator(BaseImageGenerator):
    def __init__(self, project_folder, width=1000, height=1500, image_format='png', dpi=(72, 72),
                 save=True, show=True, write_uploading_data=False):
        template = self.GENERATOR_MODE_1
        super().__init__(project_folder, template, width, height, image_format, dpi, save, show, write_uploading_data)

    def _draw_title(self, title_text, font_path, contains_light):
        # Create a drawing object
        draw = ImageDraw.Draw(self.canvas)

        # Load the font
        font = ImageFont.truetype(font_path, self.settings.title_font_size)

        # Wrap the text to fit within the maximum width
        wrapped_text = self._wrap_text(title_text, font, self.settings.title_max_width)

        # Calculate the bounding box for the multiline text
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=self.settings.title_line_spacing)

        # Calculate the width and height of the text
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Determine the starting position for center alignment
        start_y = self.settings.title_margin_from_top
        start_x = (self.width - text_width) // 2

        # Set the title text color
        if self.settings.overlay_bg:
            # If overlay background is enabled, determine title text color based on image brightness
            # If the image is light, use the dark title text color; otherwise, use the default title text color
            title_fill_color = self.settings.title_text_color_dark if contains_light else self.settings.title_text_color_default
        else:
            # If overlay background is disabled, use the default title text color
            title_fill_color = self.settings.title_text_color_default

        # Draw the text onto the canvas

        draw.text((start_x, start_y), wrapped_text, font=font, fill=title_fill_color,
                  spacing=self.settings.title_line_spacing, align='center')

        return text_height

    def _draw_text_with_rectangle(self, text_lines, font_path, title_text_height):
        # Load fonts for tips text and numbers
        tips_font = ImageFont.truetype(font_path, self.settings.tips_font_size)
        number_font = ImageFont.truetype(font_path, self.settings.tips_number_font_size)

        # Wrap text lines to fit within the maximum text width
        text_lines = [self._wrap_text(line, tips_font, self.settings.tips_max_text_width) for line in text_lines]

        # Calculate the maximum width of the text block
        max_text_width = max(
            tips_font.getbbox(elem)[2] - tips_font.getbbox(elem)[0]
            for line in text_lines[:self.settings.tips_count]
            for elem in line.splitlines()
        )

        # Determine the starting Y position for drawing text
        start_y = self.settings.title_margin_from_top + title_text_height + self.settings.tips_top_margin

        # Draw each text line with its respective rectangle and circle
        for line_number, line in enumerate(text_lines[:self.settings.tips_count], start=1):
            # Create a transparent canvas
            transparent_canvas = Image.new('RGBA', self.canvas.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(transparent_canvas)

            # Calculate the bounding box for multiline text using the multiline_textbbox method
            bbox = draw.multiline_textbbox((0, 0), line, font=tips_font, spacing=self.settings.tips_line_spacing)

            # Calculate the width and height of the text by subtracting corresponding coordinates from bbox
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Calculate the height of the rectangle by adding top and bottom paddings to the text height
            rectangle_height = text_height + self.settings.rectangle_top_padding + self.settings.rectangle_bottom_padding
            # Calculate the width of the rectangle by adding left and right paddings to the maximum text width
            rectangle_width = max_text_width + 2 * self.settings.rectangle_horizontal_padding

            # Determine the starting X position for the rectangle,
            # aligning it to the center relative to the image and adding offset
            start_x_rectangle = (self.width - rectangle_width) // 2 + self.settings.tips_block_x_offset
            # Determine the starting X position for the text inside the rectangle,
            # aligning it to the center relative to the image and adding offset
            start_x_text = (self.width - max_text_width) // 2 + self.settings.tips_block_x_offset

            # Convert the rectangle fill color to RGBA format with transparency
            rectangle_fill_color = self._color_with_alpha(self.settings.rectangle_fill_color,
                                                          self.settings.rectangle_opacity)

            # Draw the rectangle with specified parameters
            draw.rounded_rectangle((start_x_rectangle,
                                    start_y - self.settings.rectangle_top_padding,
                                    start_x_rectangle + rectangle_width,
                                    start_y + rectangle_height),
                                   fill=rectangle_fill_color,
                                   outline=self.settings.rectangle_outline, width=self.settings.rectangle_outline_width,
                                   radius=self.settings.rectangle_corner_radius)

            # Draw the text inside the rectangle
            draw.text((start_x_text, start_y), line, font=tips_font, fill=self.settings.tips_text_color,
                      spacing=self.settings.tips_line_spacing)

            # Determine the coordinates for the circle with the number
            circle_x = start_x_text + self.settings.circle_x_offset
            circle_y = start_y + \
                       (rectangle_height - self.settings.rectangle_top_padding) // 2 + self.settings.circle_y_offset

            # Convert the circle fill color to RGBA format with transparency
            circle_fill_color = self._color_with_alpha(self.settings.circle_fill_color, self.settings.circle_opacity)

            # Draw the circle
            draw.ellipse((circle_x - self.settings.circle_radius,
                          circle_y - self.settings.circle_radius,
                          circle_x + self.settings.circle_radius,
                          circle_y + self.settings.circle_radius),
                         fill=circle_fill_color, outline=self.settings.circle_outline,
                         width=self.settings.circle_outline_width)

            # Draw the number inside the circle
            draw.text((circle_x + self.settings.circle_text_x_offset, circle_y + self.settings.circle_text_y_offset),
                      str(line_number), anchor='mm', font=number_font, fill=self.settings.circle_text_color)

            # Update the starting Y position for the next text block
            start_y += text_height + self.settings.margin_between_tips

            self.canvas.alpha_composite(transparent_canvas)

    @staticmethod
    def _prepare_tips(text):
        # Split the text into lines and remove empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Initialize a list to store the items
        items = []

        for line in lines:
            # Use regular expression to extract items
            match = re.match(r'^\d+\.\s(.+?)[.;]*$', line)
            if match:
                item = match.group(1)
                items.append(item)

        return items

    def generate_image(self, data, image_number):
        title = data.get('title', '').upper()
        tips = self._prepare_tips(data.get('tips', ''))

        title_font_path = os.path.join(self.template_1_fonts_path, 'title_font.ttf')
        tips_font_path = os.path.join(self.template_1_fonts_path, 'tips_font.ttf')
        footer_font_path = os.path.join(self.template_1_fonts_path, 'footer_font.ttf')

        contains_light = self._draw_background()

        text_height = self._draw_title(title, title_font_path, contains_light)

        self._draw_text_with_rectangle(tips, tips_font_path, text_height)

        if self.settings.footer:
            footer_text_path = os.path.join(self.project_path, 'footer_text.txt')
            footer_text = self._get_footer_text(footer_text_path, self.settings.footer_text)
            self._add_footer_with_text(footer_text, footer_font_path)

        if self.show:
            self.canvas.show()

        if self.save:
            file_path = self._get_file_path(image_number)
            self.save_image(file_path, image_number)

            if self.write_uploading_data:
                uploading_data = self._get_uploading_data(data, file_path)
                self.write_csv(uploading_data, self.UPLOADING_DATA_FILE)


class Template2ImageGenerator(BaseImageGenerator):
    def __init__(self, project_folder, width=1000, height=1500, image_format='png', dpi=(72, 72),
                 save=True, show=True, write_uploading_data=False):
        template = self.GENERATOR_MODE_2
        super().__init__(project_folder, template, width, height, image_format, dpi, save, show, write_uploading_data)

    def _draw_title(self, title_text, font_path, font_2_path):
        # Create a transparent canvas
        transparent_canvas = Image.new('RGBA', self.canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(transparent_canvas)

        # Load fonts
        font = ImageFont.truetype(font_path, self.settings.title_font_size)
        font_2 = ImageFont.truetype(font_2_path, self.settings.another_text_font_size)

        # Get image dimensions
        image_width, image_height = self.canvas.size

        # Wrap the text and calculate the bounding box for the multiline text
        wrapped_text = self._wrap_text(title_text, font, self.settings.title_max_width).title()
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=self.settings.title_line_spacing)

        # Calculate the width and total height of the text
        total_text_width = bbox[2] - bbox[0]
        total_text_height = bbox[3] - bbox[1]

        # Split text into lines for formatting
        lines = wrapped_text.split('\n')

        # Divide text into sections
        if len(lines) >= self.settings.strings_with_another_font:
            first_text = '\n'.join(lines[:-self.settings.strings_with_another_font])
            second_text = '\n'.join(lines[-self.settings.strings_with_another_font:])
        else:
            first_text = wrapped_text
            second_text = ""

        # Calculate bounding boxes and heights for the first and second texts
        first_text_bbox = draw.multiline_textbbox((0, 0), first_text, font=font,
                                                  spacing=self.settings.title_line_spacing)
        first_text_height = first_text_bbox[3] - first_text_bbox[1]
        first_text_width = first_text_bbox[2] - first_text_bbox[0]

        second_text_bbox = draw.multiline_textbbox((0, 0), second_text, font=font_2,
                                                   spacing=self.settings.another_text_line_spacing)
        second_text_height = second_text_bbox[3] - second_text_bbox[1]
        second_text_width = second_text_bbox[2] - second_text_bbox[0]

        # Adjust total text height if another font is True
        if self.settings.another_font:
            total_text_height = first_text_height + second_text_height

        # Calculate starting positions for text and rectangle
        start_y = (image_height - total_text_height) // 2 + self.settings.title_y_offset
        start_x = (image_width - total_text_width) // 2

        # Adjust rectangle height based on text and padding
        if self.settings.another_font:
            rectangle_height = total_text_height + self.settings.rectangle_top_padding + \
                               self.settings.rectangle_bottom_padding + self.settings.another_text_top_padding
        else:
            rectangle_height = total_text_height + self.settings.rectangle_top_padding + \
                               self.settings.rectangle_bottom_padding
        rectangle_width = total_text_width + 2 * self.settings.rectangle_horizontal_padding

        # Calculate coordinates for the rectangle
        rectangle_x = start_x - self.settings.rectangle_horizontal_padding
        rectangle_y = start_y - self.settings.rectangle_top_padding

        # Convert rectangle fill color to RGBA format with transparency
        rectangle_fill_color = self._color_with_alpha(self.settings.rectangle_fill_color,
                                                      self.settings.rectangle_opacity)

        # Draw the rectangle under the text
        draw.rounded_rectangle(
            (rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height),
            fill=rectangle_fill_color, outline=self.settings.rectangle_outline,
            width=self.settings.rectangle_outline_width, radius=self.settings.rectangle_corner_radius)

        if self.settings.another_font:
            start_x = (image_width - first_text_width) // 2

        # Draw the first text
        draw.text((start_x, start_y), wrapped_text if not self.settings.another_font else first_text, font=font,
                  fill=self.settings.title_text_color, align='center', spacing=self.settings.title_line_spacing)

        # Draw the second text if another font is True
        if self.settings.another_font:
            start_y += first_text_height + self.settings.another_text_top_padding
            start_x = (image_width - second_text_width) // 2

            draw.text((start_x, start_y), second_text, font=font_2,
                      fill=self.settings.another_text_color, align='center',
                      spacing=self.settings.another_text_line_spacing)

        self.canvas.alpha_composite(transparent_canvas)

    def generate_image(self, data, image_number):
        title = data.get('title', '')

        title_font_path = os.path.join(self.template_2_fonts_path, 'title_font.ttf')
        title_2_font_path = os.path.join(self.template_2_fonts_path, 'title_2_font.ttf')
        footer_font_path = os.path.join(self.template_2_fonts_path, 'footer_font.ttf')

        self._draw_background()

        self._draw_title(title, title_font_path, title_2_font_path)

        if self.settings.footer:
            footer_text_path = os.path.join(self.project_path, 'footer_text.txt')
            footer_text = self._get_footer_text(footer_text_path, self.settings.footer_text)
            self._add_footer_with_text(footer_text, footer_font_path)

        if self.show:
            self.canvas.show()

        if self.save:
            file_path = self._get_file_path(image_number)
            self.save_image(file_path, image_number)

            if self.write_uploading_data:
                uploading_data = self._get_uploading_data(data, file_path)
                self.write_csv(uploading_data, self.UPLOADING_DATA_FILE)
