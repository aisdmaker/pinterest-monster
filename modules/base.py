import csv
import os
import random
from time import sleep


class Pinterest:
    UPLOADING_DATA_FILE = 'uploading_data.csv'
    GENERATOR_DATA_FILE = 'generator_data.csv'
    IMAGE_PROMPTS_FILE = 'image_prompts.csv'
    VIDEO_PROMPTS_FILE = 'video_prompts.csv'
    UPLOADED_FILE = 'uploaded.csv'
    BOARDS_FILE = 'boards.csv'
    CREATED_BOARDS_FILE = 'created_boards.csv'

    WRITER_MODE_1 = 'video'
    WRITER_MODE_2 = 'image'
    WRITER_MODE_3 = 'own_image'

    GENERATOR_MODE_1 = 'template_1'
    GENERATOR_MODE_2 = 'template_2'

    UPLOADER_MODE_1 = 'requests'
    UPLOADER_MODE_2 = 'selenium'

    def __init__(self, project_folder):
        self.project_path = os.path.join(os.path.abspath('projects'), project_folder)
        self.prompts_path = os.path.join(self.project_path, 'prompts')
        self.pinned_path = os.path.join(self.project_path, 'pinned')
        self.data_path = os.path.abspath('data')

        # Ensure that the folders exist
        os.makedirs(self.project_path, exist_ok=True)
        os.makedirs(self.prompts_path, exist_ok=True)
        os.makedirs(self.pinned_path, exist_ok=True)
        os.makedirs(self.data_path, exist_ok=True)

    def open_csv(self, filename):
        # Get the path to the data file
        data_file_path = self._get_data_file_path(filename)

        # Check if the file exists
        if not os.path.exists(data_file_path):
            raise FileNotFoundError(f"File {filename} not found: {data_file_path}")

        # Check the delimiter used in the CSV file
        delimiter = self._check_csv_delimiter(data_file_path)

        # Initialize an empty list to store the result
        result = []

        # Open the CSV file for reading
        with open(data_file_path, 'r', encoding='utf-8', newline='') as data:
            # Read the heading (first row) from the CSV file
            heading = next(data)

            # Create a CSV reader object with the specified delimiter
            reader = csv.reader(data, delimiter=delimiter)

            # Iterate over each row in the CSV file
            for row in reader:
                # Create a dictionary based on the row contents, depending on the filename
                if filename == self.VIDEO_PROMPTS_FILE:
                    row_dict = {
                        'keyword': row[0],
                        'title_prompt': row[1],
                        'description_prompt': row[2]
                    }
                    result.append(row_dict)
                elif filename == self.IMAGE_PROMPTS_FILE:
                    row_dict = {
                        'keyword': row[0],
                        'title_prompt': row[1],
                        'description_prompt': row[2],
                        'tips_prompt': row[3]
                    }
                    result.append(row_dict)
                elif filename == self.GENERATOR_DATA_FILE:
                    row_dict = {
                        'mode': row[0],
                        'keyword': row[1],
                        'title': row[2],
                        'description': row[3],
                        'tips': row[4]
                    }
                    result.append(row_dict)
                elif filename == self.UPLOADING_DATA_FILE:
                    row_dict = {
                        'mode': row[0],
                        'keyword': row[1],
                        'title': row[2],
                        'description': row[3],
                        'file_path': row[4],
                        'board_name': row[5],
                        'pin_link': row[6],
                    }
                    result.append(row_dict)
                elif filename == self.BOARDS_FILE:
                    row_dict = {
                        'board_name': row[0],
                        'board_description': row[1]
                    }
                    result.append(row_dict)
                else:
                    raise ValueError(f"Invalid filename: {filename}. Check the available file names in the base class.")

        # Return the list of dictionaries representing the CSV data
        return result

    def write_csv(self, data, filename):
        # Get the full path for the data file
        data_file_path = self._get_data_file_path(filename)

        file_exists = os.path.isfile(data_file_path)
        file_empty = os.path.exists(data_file_path) and os.stat(data_file_path).st_size == 0

        header = []
        if filename == self.UPLOADING_DATA_FILE or filename == self.UPLOADED_FILE:
            header = ['mode', 'keyword', 'title', 'description', 'file_path', 'board_name', 'pin_link']
        elif filename == self.GENERATOR_DATA_FILE:
            header = ['mode', 'keyword', 'title', 'description', 'tips', 'file_path', 'board_name', 'pin_link']
        elif filename == self.CREATED_BOARDS_FILE:
            header = ['board_name', 'board_id']

        # Write the header if the file is empty
        if not file_exists or file_empty:
            self._write_header(data_file_path, header)

        # Open the data file for appending and write the data using the DictWriter
        with open(data_file_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=header, delimiter=';')
            writer.writerow(data)

        # Log a success message after writing the data
        self._log_message(f'Data has been successfully written to {filename}.\n')

    @staticmethod
    def _write_header(file_path, header):
        with open(file_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(header)

    @staticmethod
    def _check_csv_delimiter(file_path):
        # Open the file in read mode
        with open(file_path, 'r') as file:
            # Read the first line and remove leading/trailing whitespaces
            first_line = file.readline().strip()

            # Check for the presence of a comma (',') as the delimiter
            if ',' in first_line:
                return ','
            # Check for the presence of a semicolon (';') as the delimiter
            elif ';' in first_line:
                return ';'
            # If neither comma nor semicolon is found, default to comma
            else:
                return ','

    def _get_data_file_path(self, filename):
        if filename in [self.VIDEO_PROMPTS_FILE, self.IMAGE_PROMPTS_FILE]:
            # If the filename corresponds to prompts, return the path within the prompts directory
            return os.path.join(self.project_path, self.prompts_path, filename)
        else:
            # Otherwise, return the path within the project directory
            return os.path.join(self.project_path, filename)

    @staticmethod
    def _log_message(message):
        # Instead of print, it's better to use logging mechanisms
        print(message)

    @staticmethod
    def _log_error(message, error):
        # ANSI escape codes for red color and reset
        red_color = "\033[91m"
        reset_color = "\033[0m"

        # Print the error message in red color
        print(f'{red_color}{message}{reset_color}\n{error}\n')

    @staticmethod
    def _random_delay(min_timeout, max_timeout, no_print=False):
        time_out = random.uniform(min_timeout, max_timeout)
        if not no_print:
            print(f'\nTimeout {time_out} seconds...\n')
        sleep(time_out)
