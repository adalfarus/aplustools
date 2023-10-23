import pytest
from aplustools import webtools, logs, imagetools, updaters, environment
import os
import threading
import requests

def test_search_google_provider():
    search = webtools.Search()
    result = search.google_provider("Cute puppies")
    assert result is not None

def test_logger():
    logger = logs.Logger("my_logs_file.log", show_time=True, capture_print=False, overwrite_print=True, print_passthrough=False, print_log_to_stdout=True)
    logger = logs.monitor_stdout(logger=logger)
    logger.log("Hello, world!")
    logger.close()
    assert os.path.exists("my_logs_file.log")
    os.remove("my_logs_file.log")

def test_image_download_and_conversion(tmpdir):
    imagetools.OnlineImage("https://www.simplilearn.com/ice9/free_resources_article_thumb/what_is_image_Processing.jpg", True)
    folder_path = tmpdir.mkdir("images")
    image = imagetools.OfflineImage("data:image/jpeg;base64,/9j/...")
    success = image.base64(str(folder_path), "Image", "png")
    assert success

def test_image_download_to_specified_path(tmpdir):
    folder_path = tmpdir.mkdir("images")
    image2 = imagetools.OnlineImage("https://www.simplilearn.com/ice9/free_resources_article_thumb/what_is_image_Processing.jpg")
    _, img_path, img_name = image2.download_image(str(folder_path))
    assert os.path.exists(img_path)

def test_updater(tmpdir):
    environment.set_working_dir_to_main_script_location()
    updater = updaters.gitupdater("exe")
    current_version = updater.get_latest_version("Adalfarus", "unicode-writer")[1]
    host, port, path = "localhost", 1264, tmpdir.mkdir("update")
    update_args = (str(tmpdir.join("update")), str(path), 
                    current_version, "Adalfarus", "unicode-writer", False, False, host, port)
    update_thread = threading.Thread(target=updater.update, args=update_args)
    update_thread.start()
    progress_bar = 1
    for i in updater.receive_update_status(host, port):
        if i == 100:
            progress_bar += 1

def test_check_url():
    search = webtools.Search()
    result = search.google_provider("Cute puppies")
    response = None
    if webtools.check_url(result, ''):
        response = requests.get(result)
        assert response.status_code == 200

def test_image_copy_and_removal(tmpdir):
    folder_path = tmpdir.mkdir("images")
    image2 = imagetools.OnlineImage("https://www.simplilearn.com/ice9/free_resources_article_thumb/what_is_image_Processing.jpg")
    _, img_path, img_name = image2.download_image(str(folder_path))
    a_imgpath = environment.absolute_path(img_path)
    try:
        environment.copy(a_imgpath, str(folder_path) + str(img_name).remove(".png") + str(" - Copy.png"))
    except ValueError:
        environment.copy(a_imgpath, str(folder_path) + str(img_name.split(".")[-1]) + str(" - Copy.png"))
    environment.remv(a_imgpath)
    environment.remv(str(folder_path))
