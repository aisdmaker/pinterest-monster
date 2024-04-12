import os

import g4f
import gspread
from google.oauth2.service_account import Credentials
from modules.base import Pinterest


class Writer(Pinterest):
    def __init__(self, project_folder):
        super().__init__(project_folder)

    def open_data(self, mode, google_sheet=True, table_id=None):
        if google_sheet:
            # Obtain Google Sheets credentials
            creds = self._get_google_creds()

            # Authorize the connection using gspread
            client = gspread.authorize(creds)

            # Open the Google Sheets table using its key
            table = client.open_by_key(table_id)

            # Choose the appropriate worksheet based on the mode (image or video)
            if mode == self.WRITER_MODE_2:
                worksheet = table.get_worksheet(2)  # Assuming 2 is the index of the image worksheet
            elif mode == self.WRITER_MODE_1 or mode == self.WRITER_MODE_3:
                worksheet = table.get_worksheet(1)  # Assuming 1 is the index of the video worksheet
            else:
                # Raise an error for an invalid mode
                raise ValueError(f"Invalid mode: {mode}. Check the available modes in the base class.")

            # Retrieve all values from the chosen worksheet
            all_values = worksheet.get_all_values()

            # Parse the rows and obtain the data based on the specified mode
            data = self._parse_rows(all_values, mode)
        else:
            # Check if the mode is 'image' or 'video'; otherwise, raise an exception
            if mode == self.WRITER_MODE_2:
                filename = self.IMAGE_PROMPTS_FILE
            elif mode == self.WRITER_MODE_1 or mode == self.WRITER_MODE_3:
                filename = self.VIDEO_PROMPTS_FILE
            else:
                raise ValueError(f"Invalid mode: {mode}. Check the available modes in the base class.")

            # Open the CSV file with the specified filename and retrieve the data
            data = self.open_csv(filename)

        return data

    @staticmethod
    def _parse_rows(rows, mode):
        data = []
        for index, row in enumerate(rows):
            # Skip first iteration
            if index == 0:
                continue

            row_dict = {
                'keyword': row[0],
                'title_prompt': row[1],
                'description_prompt': row[2]
            }
            # Add 'tips_prompt' to the dictionary if the mode is 'image'
            if mode == 'image':
                row_dict['tips_prompt'] = row[3]
            data.append(row_dict)
        return data

    def _get_google_creds(self):
        # Specify the path to the JSON key file
        json_key_path = os.path.join(self.data_path, 'keyfile.json')

        # Define the required OAuth2.0 scopes for Google Sheets API
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        # Create the credentials object based on the JSON key file
        credentials = Credentials.from_service_account_file(json_key_path, scopes=scopes)

        return credentials

    def write_single_prompt(self, prompt):
        # Create a ChatCompletion instance from g4f module using the OpenAI GPT model (gpt_3.5_turbo)
        # to generate content based on the provided prompt.
        # The prompt is set as a user message in the 'messages' parameter.
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_35_turbo,
            messages=[{'role': 'user', 'content': prompt}]
        )

        # Return the generated response
        return response

    def write(self, row, mode):
        # Check if the mode is valid
        if mode not in [self.WRITER_MODE_1, self.WRITER_MODE_2, self.WRITER_MODE_3]:
            raise ValueError(f"Invalid mode: {mode}. Check the available modes in the base class.")

        # Initialize results dictionary with default values
        results = {
            'mode': mode,
            'file_path': '',
            'board_name': '',
            'pin_link': ''
        }

        try:
            # Extract keyword from the row or set it to an empty string if not present
            results['keyword'] = row.get('keyword', '')

            # Write title and log the process
            self._log_message('Writing title...')
            # Extract title prompt
            title_prompt = row.get('title_prompt', '')
            title = self.write_single_prompt(title_prompt)
            results['title'] = title.strip('"') if title else ''

            # Write description and log the process
            self._log_message('Writing description...')
            # Replace 'SELECTED TITLE' in the description prompt with the generated title
            description_prompt = row.get('description_prompt', '') \
                .replace('SELECTED TITLE', title if title else row.get('keyword', ''))
            description = self.write_single_prompt(description_prompt)
            results['description'] = description.strip('"') if description else ''

            if mode == self.WRITER_MODE_2:
                # Write tips for image mode and log the process
                self._log_message('Writing tips...')
                # Replace 'SELECTED TITLE' in the tips prompt with the generated title
                tips_prompt = row.get('tips_prompt', '') \
                    .replace('SELECTED TITLE', title if title else row.get('keyword', ''))
                tips = self.write_single_prompt(tips_prompt)
                results['tips'] = tips.strip('"') if tips else ''
        except Exception as e:
            # Log an error if an exception occurs during writing
            self._log_error(f"Error while writing: ", e)

        # Determine the filename based on the mode and write the results to the corresponding CSV file
        filename = self.GENERATOR_DATA_FILE if mode == self.WRITER_MODE_2 else self.UPLOADING_DATA_FILE
        self.write_csv(results, filename)