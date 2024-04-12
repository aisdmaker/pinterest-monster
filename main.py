
def creating_boards(timeout):
    from modules.account_manager import AccountManager
    from modules.base import Pinterest
    from modules.pinner import RequestsPinner

    account_manager = AccountManager()
    accounts = account_manager.get_accounts()

    for account in accounts:
        base = Pinterest(account['project_folder'])
        boards_data = base.open_csv(base.BOARDS_FILE)

        pinner = RequestsPinner(**account)
        pinner.login()
        created_boards = pinner.create_boards(boards_data, timeout)

        for row in created_boards:
            base.write_csv(row, base.CREATED_BOARDS_FILE)


def uploading(mode, pins, shuffle, headless, timeout, move_data_after_upload):
    from modules.account_manager import AccountManager
    from modules.base import Pinterest
    from modules.pinner import RequestsPinner
    from modules.pinner import SeleniumPinner

    account_manager = AccountManager()
    accounts = account_manager.get_accounts()

    for account in accounts:
        base = Pinterest(account['project_folder'])
        uploading_data = base.open_csv(base.UPLOADING_DATA_FILE)

        if mode == base.UPLOADER_MODE_1:
            pinner = RequestsPinner(**account)

            pinner.login(headless=headless)
            pinner.upload(uploading_data, pins=pins, shuffle=shuffle, timeout=timeout,
                          move_data_after_upload=move_data_after_upload)
        elif mode == base.UPLOADER_MODE_2:
            pinner = SeleniumPinner(**account, headless=headless)

            pinner.login()
            pinner.upload(uploading_data, pins=pins, shuffle=shuffle, timeout=timeout,
                          move_data_after_upload=move_data_after_upload)
        else:
            raise ValueError(f"Invalid mode: {mode}. Check the available modes in the base class.")


def image_generation(project_folder, mode):
    from modules.base import Pinterest
    from modules.image_generator import Template1ImageGenerator, Template2ImageGenerator

    base = Pinterest(project_folder)

    data = base.open_csv(base.GENERATOR_DATA_FILE)

    # Common parameters for all image generators
    common_params = {
        'width': 1000,  # Image width
        'height': 1500,  # Image height
        'save': False,  # Save flag
        'show': True,  # Show flag
        'write_uploading_data': False  # Write uploading data flag
    }

    # Dictionary mapping generation mode to image generator class
    generators = {
        base.GENERATOR_MODE_1: Template1ImageGenerator,  # Mode 1: Template 1 image generator
        base.GENERATOR_MODE_2: Template2ImageGenerator  # Mode 2: Template 2 image generator
    }

    # Check if the specified mode is in the generators dictionary
    if mode in generators:
        # Get the generator class for the specified mode
        generator_class = generators[mode]
        # Create an instance of the generator
        generator = generator_class(project_folder, **common_params)
        for number, row in enumerate(data, start=1):
            # Generate an image for each data row
            generator.generate_image(row, number)
    else:
        # Raise an exception if the mode is invalid
        raise ValueError(f"Invalid mode: {mode}. Check the available modes in the base class.")


def writing(project_folder, mode):
    from modules.writer import Writer

    table_id = '1IVFmYqJBcS92DPr029c1y9saD_YjgXxTA3GuL7wdTSw'
    writer = Writer(project_folder)

    data = writer.open_data(mode, google_sheet=True, table_id=table_id)

    for row in data:
        writer.write(row, mode)


if __name__ == '__main__':
    project_name = 'Keto'

    choice = input("Enter '1' to run the Writer,\n"
                   "'2' to run the Image generator,\n"
                   "'3' to run the Pinner,\n"
                   "'4' to run the Boards creator: ")

    if choice == '1':
        writer_modes = ['video', 'image', 'own_image']  # The "own_image" mode retrieves data from the video tab in the prompt builder and saves the data in the uploading_data table without a link (for your own link)
        writing(project_name, writer_modes[0])
    elif choice == '2':
        generator_modes = ['template_1', 'template_2']
        image_generation(project_name, generator_modes[0])
    elif choice == '3':
        pinner_modes = ['requests', 'selenium']
        uploading(mode=pinner_modes[0], pins=10, shuffle=True, headless=True, timeout=(3, 8),
                  move_data_after_upload=True)
    elif choice == '4':
        creating_boards(timeout=(3, 8))
    else:
        print("Invalid choice. Please enter '1', '2', '3' or '4'.")
