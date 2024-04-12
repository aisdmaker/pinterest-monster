import csv
import os


class AccountManager:
    def __init__(self):
        self.accounts_file_path = os.path.join(os.path.abspath('data'), 'accounts.csv')
        os.makedirs(os.path.dirname(self.accounts_file_path), exist_ok=True)

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

    def get_accounts(self):
        # Check if the data file exists
        if not os.path.exists(self.accounts_file_path):
            raise FileNotFoundError(f"File 'accounts.csv' not found")

        # Determine the CSV delimiter by checking the file
        delimiter = self._check_csv_delimiter(self.accounts_file_path)

        # Initialize an empty list to store the result
        result = []

        # Open the data file and read its content
        with open(self.accounts_file_path, "r", encoding="utf-8", newline="") as data:
            # Read the header (first line) of the CSV file
            heading = next(data)

            # Create a CSV reader object with the specified delimiter
            reader = csv.reader(data, delimiter=delimiter)

            # Iterate over each row in the CSV file
            for row in reader:
                # Check if the value in the first column (index 0) is '1'
                if row[0].strip() == '1':
                    # Create a dictionary with 'email', 'password', and 'proxy' keys
                    row_dict = {
                        'email': row[1],
                        'password': row[2],
                        'username': row[3],
                        'useragent': row[4],
                        'proxy': row[5],
                        'project_folder': row[6],
                        'random_boards': row[7],
                        'global_link': row[8],
                    }
                    # Append the dictionary to the result list
                    result.append(row_dict)

        # Check if any accounts were found; raise an exception if none are present
        if not result:
            raise Exception('No accounts in operation')

        # Print the number of accounts in operation
        print(f'{len(result)} accounts in work')

        # Return the list of dictionaries representing the selected accounts
        return result
