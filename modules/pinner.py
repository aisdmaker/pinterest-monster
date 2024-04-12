import csv
import json
import mimetypes
import os
import random
import shutil
import uuid
from datetime import datetime
from time import sleep

from modules.base import Pinterest
from py3pin.Pinterest import Pinterest as Py3Pin
import undetected_chromedriver as uc
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from moviepy.editor import VideoFileClip
from requests_toolbelt import MultipartEncoder

PIN_IDEA_RESOURCE_CREATE = 'https://www.pinterest.com/resource/ApiResource/create/'
UPLOAD_VIDEO_FILE = 'https://pinterest-media-upload.s3-accelerate.amazonaws.com/'
UPLOAD_IMAGE_FILE = 'https://u.pinimg.com/'
VIP_RESOURCE = 'https://www.pinterest.com/resource/VIPResource/get/'
STORY_PIN_RESOURCE_CREATE = 'https://www.pinterest.com/resource/StoryPinResource/create/'


class PinnerBase(Pinterest):
    LOGIN_URL = 'https://pinterest.com/login'
    UPLOAD_URL = 'https://www.pinterest.com/pin-creation-tool/'

    def __init__(self, project_folder, email):
        super().__init__(project_folder)

        self.email = email
        self.cookies_path = os.path.join(self.data_path, 'cookies')
        self.py3pin_cookies_file_path = os.path.join(self.cookies_path, self.email)
        self.cookies_file_path = os.path.join(self.cookies_path, f'{self.email}.json')

        os.makedirs(self.cookies_path, exist_ok=True)

    @staticmethod
    def _cookies_exist(cookies_file_path):
        return os.path.isfile(cookies_file_path)

    def _load_cookies(self):
        with open(self.cookies_file_path, 'r') as f:
            cookies = json.load(f)
        return cookies

    def _save_cookies(self, cookies):
        with open(self.cookies_file_path, 'w') as f:
            json.dump(cookies, f)

    def _set_driver(self, useragent, proxy, headless):
        chrome_options = uc.ChromeOptions()
        chrome_options.headless = headless
        chrome_options.add_argument('--lang=en')

        chrome_options.add_experimental_option("prefs", {"credentials_enable_service": False})

        if useragent:
            chrome_options.add_argument(f'user-agent={useragent}')

        if proxy and self._format_proxy(proxy):
            proxy_options = {
                'proxy': {
                    'http': proxy,
                    'https': proxy,
                    'no_proxy': 'localhost:127.0.0.1'
                }
            }
        else:
            proxy_options = None

        driver = uc.Chrome(options=chrome_options, seleniumwire_options=proxy_options)

        return driver

    def _format_proxy(self, proxy_string):
        try:
            # Splitting the proxy string into parts
            parts = proxy_string.split(":")

            # Checking if the proxy string starts with the correct scheme
            if not proxy_string.lower().startswith("http://") and not proxy_string.lower().startswith("socks5://"):
                self._log_message('Incorrect proxy scheme. It should be http or socks5.')
                return None

            # Checking the format of the proxy string
            if len(parts) not in (4, 3):
                self._log_message(
                    'Incorrect proxy format. Use the format: http://username:password@proxy_ip:proxy_port')
                return None

            # Checking username and password
            if len(parts) == 4:
                if "@" not in parts[2]:
                    self._log_message(
                        'Incorrect proxy format. Use the format: http://username:password@proxy_ip:proxy_port')
                    return None

            # Determining the proxy type and creating a dictionary
            proxy_type = parts[0].lower()
            proxy_dict = {proxy_type: proxy_string}

            return proxy_dict
        except Exception as e:
            self._log_error(f"Error while forming proxy dictionary: ", e)
            return None

    def _validate_upload_data(self, uploading_data, pins):
        # Check if the number of pins specified exceeds the number of rows in the data table
        if len(uploading_data) < pins:
            # Adjust the number of pins to the available rows
            pins = len(uploading_data)
            self._log_message(f'The specified number of Pins exceeds the number of rows in the data table.\n'
                              f'{pins} Pins will be pinned.\n')
        # Return the validated uploading_data list with the specified number of pins
        return uploading_data[:pins]

    @staticmethod
    def _get_random_board(boards_str):
        boards = [board.strip() for board in boards_str.split(',')]

        if boards:
            random_board = random.choice(boards)
            return random_board
        else:
            return None

    def _create_uploading_data(self, data, random_boards, global_link):
        random_board = self._get_random_board(random_boards)

        return UploadingData(
            file_path=data.get('file_path', ''),
            board_name=random_board if random_board else data.get('board_name', ''),
            hashtag=data.get('keyword', ''),
            pin_title=data.get('title', ''),
            pin_description=data.get('description', ''),
            pin_link=global_link if global_link else data.get('pin_link', ''),
            mode=data.get('mode', ''),
            keyword=data.get('keyword', '')
        )

    def _prepare_emoji(self, input_string):
        filename = os.path.join(self.project_path, 'emoji.txt')
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as emoji_file:
                emoji_file.write('')
            return input_string

        with open(filename, 'r', encoding='utf-8') as emoji_file:
            emoji_list = emoji_file.read().splitlines()

        if emoji_list:
            random_emoji = random.choice(emoji_list)
            return f"{random_emoji} {input_string}"
        else:
            return input_string

    def _after_success_pin(self, file_path):
        # Form paths to the input and output files
        input_file = os.path.join(self.project_path, self.UPLOADING_DATA_FILE)
        output_file = os.path.join(self.project_path, self.UPLOADED_FILE)

        # Find the row and write it to the uploaded_data.csv file, get the list of remaining rows
        rows_to_save = self._process_csv(file_path, input_file, output_file)

        # Update the uploading_data.csv file by writing the remaining rows to it
        self._save_csv(rows_to_save, input_file)
        self._log_message('The uploaded Pin data has been moved to the uploaded.csv file.')

        # Move the uploaded file to the pinned folder
        self._move_uploaded_file(file_path)

    def _process_csv(self, file_path, input_file, output_file):
        rows_to_save = []

        delimiter = self._check_csv_delimiter(input_file)

        with open(input_file, 'r', newline="") as file:
            reader = csv.reader(file, delimiter=delimiter)
            headers = next(reader)
            rows_to_save.append(headers)

            for row in reader:
                if row[4] == file_path:
                    with open(output_file, 'a', newline='') as out_file:
                        writer = csv.writer(out_file, delimiter=';')
                        writer.writerow(row)

                    # or
                    # self.write_csv(row, self.UPLOADED_FILE)
                else:
                    rows_to_save.append(row)

        return rows_to_save

    @staticmethod
    def _save_csv(rows_to_save, input_file):
        with open(input_file, 'w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerows(rows_to_save)

    def _move_uploaded_file(self, file_path):
        destination_file_path = os.path.join(self.pinned_path, os.path.basename(file_path))
        if os.path.exists(destination_file_path):
            os.remove(destination_file_path)
        shutil.move(file_path, self.pinned_path)


class RequestsPinner(PinnerBase, Py3Pin):
    def __init__(self, project_folder='', email='', password='', username='', useragent=None, random_boards='',
                 global_link='', proxy=None):
        super().__init__(project_folder, email)

        formatted_proxy = self._format_proxy(proxy) if proxy else None
        Py3Pin.__init__(self, email=email, password=password, username=username,
                        user_agent=useragent if useragent else None,
                        proxies=formatted_proxy, cred_root='data/cookies')

        self.email = email
        self.username = username
        self.proxy = proxy
        self.useragent = useragent
        self.random_boards = random_boards
        self.global_link = global_link

        self.temp_folder_path = os.path.join(self.project_path, 'temp')
        os.makedirs(self.temp_folder_path, exist_ok=True)

    def _update_cookies(self, cookies):
        self.http.cookies.clear()
        for cookie in cookies:
            self.http.cookies.set(cookie["name"], cookie["value"])

        self.registry.update_all(self.http.cookies.get_dict())

    def login(self, headless=True, wait_time=15, proxy=None, lang="en"):
        if not self._cookies_exist(self.py3pin_cookies_file_path):
            self._log_message('No cookies found. Performing manual login...')
            driver = self._set_driver(self.useragent, self.proxy, headless)

            try:
                # Initialize WebDriverWait
                wait = WebDriverWait(driver, wait_time)

                # Navigate to the login URL
                driver.get(self.LOGIN_URL)

                # Find and input email
                input_email = wait.until(EC.element_to_be_clickable((By.ID, 'email')))
                input_email.send_keys(self.email)

                # Find and input password
                input_password = driver.find_element(By.ID, 'password')
                input_password.send_keys(self.password)

                # Click the login button
                login_button = driver.find_element(By.CSS_SELECTOR, "button.red.SignupButton.active")
                login_button.click()

                # Wait for email input to become invisible, indicating successful login
                wait.until(EC.invisibility_of_element_located((By.ID, 'email')))

                # Navigate to the upload URL
                driver.get(self.UPLOAD_URL)

                # Get cookies after successful login
                cookies = driver.get_cookies()

                # Save cookies to file
                self._save_cookies(cookies)

                # Update stored cookies
                self._update_cookies(cookies)

                self._log_message('Successful login to the account. Cookies saved.')
            except Exception as e:
                # Handle login errors
                self._log_error(f"Login error: ", e)
            finally:
                # Close the browser window
                driver.close()

    @staticmethod
    def _get_video_info(file_path):
        # Open the video file
        clip = VideoFileClip(file_path)

        # Get the duration of the video in milliseconds
        duration_ms = clip.duration * 1000

        # Get the width and height of the video
        width = clip.size[0]
        height = clip.size[1]

        # Close the video file
        clip.close()

        # Return the video duration, width, and height
        return int(duration_ms), width, height

    @staticmethod
    def _generate_uuid():
        # Generate a random UUID
        generated_uuid = uuid.uuid4()
        # Formatting the UUID into the desired format
        formatted_uuid = '-'.join(
            [str(generated_uuid)[:8], str(generated_uuid)[9:13], str(generated_uuid)[14:18], str(generated_uuid)[19:23],
             str(generated_uuid)[24:]])
        return formatted_uuid

    @staticmethod
    def _capture_first_frame(video_path, output_path):
        # Get the current time in timestamp format
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        # Load the video
        video_clip = VideoFileClip(video_path)

        # Get the first frame
        first_frame = video_clip.get_frame(0)

        # Save the first frame to the specified folder with a timestamp label in the filename
        output_file_path = f"{output_path}/first_frame_{timestamp}.png"
        first_frame_image = video_clip.to_ImageClip(t=0)
        first_frame_image.save_frame(output_file_path)

        # Close the video clip
        video_clip.close()

        return output_file_path

    @staticmethod
    def _delete_file(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error deleting file '{file_path}': {e}")

    @staticmethod
    def _calculate_canvas_aspect_ratio(width, height):
        return width / height

    def _register_media_upload_batch(self, mode, uuid_1, uuid_2=None, duration=None):
        if mode == 'video':
            media_info_list = '[{"id":"' + uuid_1 + '","media_type":"video-story-pin","upload_aux_data":{"clips":[{"durationMs":' + str(duration) + ',"isFromImage":false,"startTimestampMs":-1}]}}]'
        else:
            media_info_list = '[{"id":"' + uuid_1 + '","media_type":"image-story-pin"},{"id":"' + uuid_2 + '","media_type":"image-story-pin"}]'

        data = {
            "source_url": "/pin-creation-tool/",
            "data": json.dumps({
                "options": {
                    "url": "/v3/media/uploads/register/batch/",
                    "data": {
                        "media_info_list": media_info_list
                    }
                },
                "context": {}
            })
        }

        return self.post(url=PIN_IDEA_RESOURCE_CREATE, data=data)

    @staticmethod
    def _extract_data_from_response(json_response, file_uuid):
        # Extracting upload data corresponding to the specified file_uuid from the JSON response
        upload_data = json_response['resource_response']['data'].get(file_uuid, {})

        # Extracting required parameters from the upload_data dictionary
        extracted_data = {
            'x-amz-date': upload_data.get('upload_parameters', {})['x-amz-date'],
            'x-amz-signature': upload_data.get('upload_parameters', {})['x-amz-signature'],
            'x-amz-security-token': upload_data.get('upload_parameters', {})['x-amz-security-token'],
            'x-amz-algorithm': upload_data.get('upload_parameters', {})['x-amz-algorithm'],
            'key': upload_data.get('upload_parameters', {})['key'],
            'policy': upload_data.get('upload_parameters', {})['policy'],
            'x-amz-credential': upload_data.get('upload_parameters', {})['x-amz-credential'],
            'Content-Type': 'multipart/form-data',
        }

        # Returning the extracted data dictionary
        return extracted_data

    def _pinterest_media_upload(self, mode, file_path, data):
        # Extracting the file name from the file path
        file_name = os.path.basename(file_path)
        # Guessing the MIME type of the file
        mime_type = mimetypes.guess_type(file_path)[0]

        # Opening the file in binary mode
        with open(file_path, 'rb') as file:
            # Creating a MultipartEncoder object with the specified boundary parameter
            form_data = MultipartEncoder(
                fields={
                    **data,
                    "file": (file_name, file, mime_type),  # Adding the file as a field
                }
            )

            # Constructing the headers for the request
            headers = {
                'Accept': '*/*',
                "Content-Length": str(form_data.len),
                "Content-Type": form_data.content_type,
            }

            # Adding host header for video mode
            if mode == 'video':
                headers["Host"] = "pinterest-media-upload.s3-accelerate.amazonaws.com"

            # Making a POST request with the constructed data and headers
            return self.post(url=UPLOAD_VIDEO_FILE if mode == 'video' else UPLOAD_IMAGE_FILE,
                             data=form_data, headers=headers)

    def _confirm_uploading(self, upload_id):
        options = {
            "upload_ids": [upload_id],
        }

        source_url = '/pin-creation-tool/'

        url = self.req_builder.buildGet(url=VIP_RESOURCE, options=options, source_url=source_url)

        return self.get(url=url).json()

    def _post_video_pin(self, board_id='', title='', description='', link='', video_upload_id=None,
                        video_signature=None, image_signature=None, video_width=None, video_height=None,
                        canvas_aspect_ratio=None):
        data = {
            "source_url": "/pin-creation-tool/",
            "data": json.dumps({
                "options": {
                    "allow_shopping_rec": True,
                    "board_id": board_id,
                    "description": description,
                    "is_comments_allowed": True,
                    "is_removable": False,
                    "is_unified_builder": True,
                    "link": link,
                    "orbac_subject_id": "",
                    "story_pin": '{"metadata":{"pin_title":"' + title + '","pin_image_signature":"' + str(
                        image_signature) + '","canvas_aspect_ratio":' + str(
                        canvas_aspect_ratio) + ',"diy_data":null,"recipe_data":null,"template_type":null},"pages":[{"blocks":[{"block_style":{"height":100,"width":100,"x_coord":0,"y_coord":0},"tracking_id":"' + str(
                        video_upload_id) + '","video_signature":"' + str(
                        video_signature) + '","type":3}],"clips":[{"clip_type":1,"end_time_ms":-1,"is_converted_from_image":false,"source_media_height":' + str(
                        video_height) + ',"source_media_width":' + str(
                        video_width) + ',"start_time_ms":-1}],"layout":0,"style":{"background_color":"#FFFFFF"}}]}',
                    "user_mention_tags": "[]"
                },
                "context": {}
            })
        }

        return self.post(url=STORY_PIN_RESOURCE_CREATE, data=data)

    def upload_video_pin(self, file_path, board_id, title, description, link, timeout=(0, 3)):
        delay_min, delay_max = timeout

        video_duration, video_width, video_height = self._get_video_info(file_path)
        canvas_aspect_ratio = self._calculate_canvas_aspect_ratio(video_width, video_height)

        video_uuid = self._generate_uuid()

        response = self._register_media_upload_batch('video', video_uuid, duration=video_duration)
        # print(response.json())
        self._random_delay(delay_min, delay_max, True)

        uploading_data = self._extract_data_from_response(response.json(), video_uuid)

        media_upload_response = self._pinterest_media_upload('video', file_path, uploading_data)
        # print(media_upload_response)
        self._random_delay(delay_min, delay_max, True)

        video_signature = media_upload_response.headers.get('Etag').strip().replace('"', '')
        video_upload_id = uploading_data['key'].split(':')[-1]

        confirm_uploading_data = self._confirm_uploading(video_upload_id)
        # print(confirm_uploading_data)
        self._random_delay(delay_min, delay_max, True)

        image_uuid_1 = self._generate_uuid()
        image_uuid_2 = self._generate_uuid()
        image_batch_response = self._register_media_upload_batch('image', image_uuid_1, image_uuid_2)
        # print(image_batch_response.json())
        self._random_delay(delay_min, delay_max, True)

        image_uploading_data = self._extract_data_from_response(image_batch_response.json(), image_uuid_2)

        image_file_path = self._capture_first_frame(file_path, self.temp_folder_path)

        image_media_upload_response = self._pinterest_media_upload('image', image_file_path, image_uploading_data)
        image_signature = image_media_upload_response.headers.get('Etag').strip().replace('"', '')
        # print(image_media_upload_response)
        self._random_delay(delay_min, delay_max, True)

        self._delete_file(image_file_path)

        pin_response = self._post_video_pin(board_id, title, description, link,
                                            video_upload_id, video_signature, image_signature,
                                            video_width, video_height, canvas_aspect_ratio)
        # print(pin_response.json())

    @staticmethod
    def _is_digit_string(s):
        return s.isdigit()

    @staticmethod
    def _get_board_id(boards, board_name):
        for board in boards:
            if board['name'] == board_name:
                return board['id']

        return False

    def upload(self, uploading_data, pins=10, shuffle=False, timeout=(3, 8), emoji=True, move_data_after_upload=True):
        # If shuffle is True, shuffle the uploading_data list
        if shuffle:
            random.shuffle(uploading_data)

        # Validate the uploading_data list and limit the number of pins if necessary
        uploading_data = self._validate_upload_data(uploading_data, pins)

        # Get a list of boards
        boards = []
        try:
            boards = self.boards_all(username=self.username)
            self._log_message(f'Found {len(boards)} boards.\n')
        except Exception as e:
            self._log_error('An error occurred while getting the boards.', e)

        # Iterate over the uploading_data list
        for i, elem in enumerate(uploading_data, start=1):
            # Create pin data from the current element
            pin_data = self._create_uploading_data(elem, self.random_boards, self.global_link)

            # Get the board name
            board = pin_data.board_name

            # If the board name is not a digit string, get the board ID
            if not self._is_digit_string(board):
                board = self._get_board_id(boards, board)

            # If no board ID is found, log an error message and continue to the next element
            if not board:
                self._log_message(f"No ID obtained for the board '{pin_data.board_name}'\n")
                continue

            # Check if the file path ends with a video extension
            if pin_data.file_path.endswith(('.mp4', '.mov', '.m4v')):
                try:
                    # Upload a video pin
                    self.upload_video_pin(file_path=pin_data.file_path,
                                          board_id=board,
                                          title=self._prepare_emoji(
                                              pin_data.pin_title) if emoji else pin_data.pin_title,
                                          description=self._prepare_emoji(
                                              pin_data.pin_description) if emoji else pin_data.pin_description,
                                          link=pin_data.pin_link)
                    self._log_message(f'{i} Video pin created')

                    # Move data after successful upload if enabled
                    if move_data_after_upload:
                        self._after_success_pin(pin_data.file_path)
                except Exception as e:
                    # Log an error if video pin creation fails
                    self._log_error('An error occurred while creating video pin.', e)
            else:
                try:
                    # Upload an image pin
                    self.upload_pin(board_id=board,
                                    image_file=pin_data.file_path,
                                    description=self._prepare_emoji(
                                        pin_data.pin_description) if emoji else pin_data.pin_description,
                                    title=self._prepare_emoji(pin_data.pin_title) if emoji else pin_data.pin_title,
                                    link=pin_data.pin_link)
                    self._log_message(f'{i} Image pin created')

                    # Move data after successful upload if enabled
                    if move_data_after_upload:
                        self._after_success_pin(pin_data.file_path)
                except Exception as e:
                    # Log an error if image pin creation fails
                    self._log_error('An error occurred while creating image pin.', e)

            # Add a random delay between pin uploads
            if i != len(uploading_data):
                delay_min, delay_max = timeout
                self._random_delay(delay_min, delay_max)

    def create_boards(self, boards_data, timeout=(3, 8)):
        # Obtain the list of existing boards and their names
        existing_boards = self.boards_all(username=self.username)
        existing_board_names = [board['name'] for board in existing_boards]

        self._log_message(f'Found {len(existing_boards)} boards\n')
        self._log_message(f'Creating boards on account "{self.username}"\n')

        created_boards = []
        for index, board in enumerate(boards_data, start=1):
            # Create a BoardData object
            bdata = BoardData(
                board_name=board.get('board_name', ''),
                board_description=board.get('board_description', '')
            )

            # Check if a board with the same name already exists
            if bdata.board_name in existing_board_names:
                self._log_message(f'A board named {bdata.board_name} has already been created\n')
                continue

            try:
                # Attempt to create a board
                board_response = self.create_board(
                    name=bdata.board_name,
                    description=bdata.board_description,
                )
                self._log_message(f'Created a board with the name {bdata.board_name}')

                response_data = json.loads(board_response.content)

                board_id = response_data["resource_response"]["data"]["id"]
                board_name = response_data["resource_response"]["data"]["name"]

                created_boards.append({"board_name": board_name, "board_id": board_id})
            except Exception as e:
                # Handle error when creating the board
                self._log_error('An error occurred while creating the board.', e)
                continue

            # Introduce a random delay between board creations
            if index != len(boards_data):
                delay_min, delay_max = timeout
                self._random_delay(delay_min, delay_max)

        return created_boards


class SeleniumPinner(PinnerBase):
    def __init__(self, project_folder='', email='', password='', username='',
                 useragent=None, random_boards='', global_link='', proxy=None, headless=False):
        super().__init__(project_folder, email)
        self.email = email
        self.password = password
        self.random_boards = random_boards
        self.global_link = global_link
        self.driver = self._set_driver(useragent, proxy, headless)

    def _wait_for_element_located(self, by, value, timeout=15):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            raise NoSuchElementException(f"Element not found: {by}={value}")

    def _wait_for_element_clickable(self, by, value, timeout=15):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            raise NoSuchElementException(f"Element not found: {by}={value}")

    def _wait_for_element_invisible(self, by, value, timeout=15):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element((by, value))
            )
        except TimeoutException:
            self._log_message("Element did not disappear within the specified timeout")

    def login(self, wait_time=15):
        try:
            self._log_message('Logging into the account...')

            # Check if cookies file exists
            if self._cookies_exist(self.cookies_file_path):
                self._log_message('Cookies found. Logging into the account with the cookies...')

                # Load cookies from the existing file
                cookies = self._load_cookies()

                self.driver.get(self.LOGIN_URL)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)

                self.driver.refresh()
            else:
                self.driver.get(self.LOGIN_URL)
                self._log_message('No cookies found. Performing manual login...')

                input_email = self._wait_for_element_located(By.ID, 'email')
                input_email.send_keys(self.email)

                input_password = self._wait_for_element_located(By.ID, 'password')
                input_password.send_keys(self.password)

                login_button = self.driver.find_element(By.CSS_SELECTOR, "button.red.SignupButton.active")
                login_button.click()

                self._wait_for_element_invisible(By.ID, 'email', wait_time)

                self.driver.refresh()

                cookies = self.driver.get_cookies()

                self._save_cookies(cookies)

                self._log_message('Successful login to the account. Cookies saved.')
        except Exception as e:
            self._log_error("Login error:", e)

    def _drag_video(self, video_path, wait_time):
        upload_area = self._wait_for_element_located(By.ID, 'storyboard-upload-input', wait_time)
        upload_area.send_keys(video_path)

    def _input_title(self, title, wait_time, max_attempts=5):
        attempt = 0
        while attempt < max_attempts:
            try:
                title_box = self._wait_for_element_clickable(By.CSS_SELECTOR, 'input[id="storyboard-selector-title"]',
                                                           wait_time)
                title_box.send_keys(title)
                break
            except StaleElementReferenceException:
                self._log_message("StaleElementReferenceException occurred. Retrying...")
                attempt += 1
        else:
            raise Exception("Failed to input title after multiple attempts.")

    def _input_description(self, description, max_attempts=5):
        attempt = 0
        while attempt < max_attempts:
            try:
                text_div = self.driver.find_element(By.XPATH, '//div[@aria-autocomplete="list"]')
                text_div.clear()
                text_div.send_keys(description)
                text_div.send_keys(Keys.ENTER)
                break
            except StaleElementReferenceException:
                self._log_message("StaleElementReferenceException occurred. Retrying...")
                attempt += 1
        else:
            raise Exception("Failed to input description after multiple attempts.")

    def _input_link(self, link):
        link_box = self.driver.find_element(By.ID, "WebsiteField")
        link_box.send_keys(link)

    def _input_board(self, board):
        dropdown_menu = self.driver.find_element(By.CSS_SELECTOR, 'button[data-test-id="board-dropdown-select-button"]')
        dropdown_menu.click()
        search_field = self._wait_for_element_clickable(By.ID, 'pickerSearchField')
        search_field.send_keys(board)
        board_element = self._wait_for_element_clickable(By.CSS_SELECTOR, 'div[data-test-id*="board-row"]')
        board_element.click()

    def _upload_pin(self, uploading_data, wait_time=15):
        file_path = uploading_data.file_path
        title = uploading_data.pin_title
        description = uploading_data.pin_description
        link = uploading_data.pin_link
        board = uploading_data.board_name

        self.driver.get(self.UPLOAD_URL)

        self._log_message('Uploading the pin...')
        self._drag_video(file_path, wait_time)

        self._log_message('Entering the title...')
        self._input_title(title, wait_time, 5)

        self._log_message('Entering the description...')
        self._input_description(description, 5)

        if link:
            self._log_message('Entering the link...')
            self._input_link(link)

        self._log_message('Choosing the board...')
        self._input_board(board)

        publish_button = self._wait_for_element_clickable(By.CSS_SELECTOR,
                                                          'div[data-test-id="storyboard-creation-nav-done"]')
        publish_button.click()
        self._log_message('Waiting for the upload to complete...')

        sleep(10)

    def upload(self, uploading_data, pins=10, shuffle=False, timeout=(3, 8), move_data_after_upload=True):
        if shuffle:
            random.shuffle(uploading_data)

        uploading_data = self._validate_upload_data(uploading_data, pins)

        for i, elem in enumerate(uploading_data, start=1):
            pin_data = self._create_uploading_data(elem, self.random_boards, self.global_link)

            try:
                self._upload_pin(pin_data, wait_time=120)
                self._log_message(f'{i} Pin created')

                if move_data_after_upload:
                    self._after_success_pin(pin_data.file_path)
            except Exception as e:
                self._log_error('An error occurred while creating pin.', e)

            if i != len(uploading_data):
                delay_min, delay_max = timeout
                self._random_delay(delay_min, delay_max)

        self.driver.close()


class BoardData:
    def __init__(self, board_name='', board_description=''):
        self.board_name = self._truncate_text(board_name, 50)
        self.board_description = self._truncate_text(board_description, 495)

    @staticmethod
    def _truncate_text(text, max_length):
        if len(text) <= max_length:
            return text
        else:
            return text[:max_length]


class UploadingData:
    def __init__(self, file_path='', board_name='', hashtag='', pin_title='', pin_description='',
                 pin_link='', mode='', keyword=''):
        self.file_path = file_path
        self.board_name = board_name
        self._hashtag = self._prepare_hashtags(hashtag)
        self.pin_title = self._truncate_text(pin_title, 95)
        self.pin_description = self._prepare_description(pin_description, self._hashtag, 495, 400)
        self.pin_link = pin_link
        self.mode = mode
        self.keyword = keyword

    @staticmethod
    def _truncate_text(text, max_length):
        if len(text) <= max_length:
            return text
        else:
            return text[:max_length]

    @staticmethod
    def _prepare_hashtags(input_string):
        if not input_string:
            return ""

        if ',' in input_string:
            hashtags = input_string.split(',')
        else:
            hashtags = input_string.split()

        hashtags = [tag.strip().capitalize() for tag in hashtags]
        hashtags = ['#' + tag if not tag.startswith('#') else tag for tag in hashtags]
        result_string = ' '.join(hashtags)

        first_hashtag = '#' + ''.join(word.capitalize() for word in input_string.split())

        return f'{first_hashtag} {result_string}'

    @staticmethod
    def _prepare_description(description, hashtags, max_length, min_length_description):
        if len(description) + len(hashtags) <= max_length:
            return f'{description} {hashtags}'

        if len(description) > min_length_description:
            new_description = description[:min_length_description]
        else:
            remaining_space = max_length - len(hashtags)
            new_description = description[:remaining_space]

        if len(new_description) + len(hashtags) <= max_length:
            return f'{new_description} {hashtags}'
        else:
            remaining_space = max_length - len(new_description)
            new_hashtags = hashtags[:remaining_space]
            return f'{new_description} {new_hashtags}'


























