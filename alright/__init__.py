"""
Alright is unofficial Python wrapper for whatsapp web made as an inspiration from PyWhatsApp
allowing you to send messages, images, video and documents programmatically using Python
"""


import os
import sys
import time
import logging
from typing import Optional
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    UnexpectedAlertPresentException,
    NoSuchElementException,
    TimeoutException,
)

class WhatsApp(object):

    logger: logging.Logger

    def __init__(self, driver: webdriver.Chrome | webdriver.Firefox, timeout:float=60, logger:logging.Logger|None=None):

        self.driver = driver
        self.wait = WebDriverWait(driver=self.driver, timeout=timeout) 
        self.current_mobile = ""
        if not logger:
            logger = self._build_logger()
        self.logger = logger
        self._build_logger()
        self.login()

    def _build_logger(self) -> logging.Logger:
        """
        self.logger settings  [nCKbr]
        """

        logger = logging.getLogger()
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s -- [%(levelname)s] >> %(message)s"
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def login(self):
        BASE_URL = "https://web.whatsapp.com/"
        self.driver.get(BASE_URL)

    def logout(self):
        prefix = "//div[@id='side']/header/div[2]/div/span/div[3]"
        dots_button = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    f"{prefix}/div[@role='button']",
                )
            )
        )
        dots_button.click()

        logout_item = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    f"{prefix}/span/div[1]/ul/li[last()]/div[@role='button']",
                )
            )
        )
        logout_item.click()

    def get_phone_link(self, mobile:str) -> str:
        """get_phone_link (), create a link based on whatsapp (wa.me) api

        Args:
            mobile (str): Phone Number

        Returns:
            str: url
        """
        suffix_link = "https://web.whatsapp.com/send?phone={mobile}&text&type=phone_number&app_absent=1"
        return suffix_link.format(mobile=mobile)

    def catch_alert(self, seconds=3):
        """catch_alert()

        catches any sudden alert
        """
        try:
            WebDriverWait(self.driver, seconds).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert.accept()
            return True
        except Exception as e:
            self.logger.exception(f"An exception occurred: {e}")
            return False

    def find_user(self, mobile:str) -> bool:
        """
        Tries to acces the chat for the given user.

        Args:
            mobile (str): The desired phone number. Must not contain '+' sign.
        Returns:
            bool: Wheter the contact exists or not.
        """
        try:
            self.current_mobile = mobile
            link = self.get_phone_link(mobile)
            self.driver.get(link)
            #waits to see if the message field exists
            #if it doesn't, then the user probably is not on whatsapp.
            inp_xpath = '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div[1]/div/div[1]/p'
            message_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, inp_xpath))
            )
            return True
        except TimeoutException:
            self.logger.warning(f"Timeout: {mobile} is probably not on Whatsapp.")
            return False
        except UnexpectedAlertPresentException as bug:
            self.logger.exception(f"An exception occurred: {bug}")
            time.sleep(1)
            return self.find_user(mobile)


    def query_chats(self, query:str) -> bool:
        """

        Locate existing contact by username or number

        Args:
            query (str): the username or number to be queried
        """
        search_box = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "/html/body/div[1]/div/div/div[4]/div/div[1]/div/div/div[2]/div/div[1]",
                )
            )
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)
        try:
            opened_chat = self.driver.find_elements(
                By.XPATH, '//div[@id="main"]/header/div[2]/div[1]/div[1]/span'
            )
            if len(opened_chat):
                title = opened_chat[0].get_attribute("title")
                if title.upper() == query.upper(): #type: ignore
                    self.logger.info(f'Successfully fetched chat "{query}"')
                return True
            else:
                self.logger.info(f'It was not possible to fetch chat "{query}"')
                return False
        except NoSuchElementException:
            self.logger.exception(f'It was not possible to fetch chat "{query}"')
            return False

    def username_exists(self, username):
        """username_exists ()

        Returns True or False whether the contact exists or not, and selects the contact if it exists, by checking if the search performed actually opens a conversation with that contact

        Args:
            username ([type]): [description]
        """
        try:
            search_box = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="side"]/div[1]/div/label/div/div[2]')
                )
            )
            search_box.clear()
            search_box.send_keys(username)
            search_box.send_keys(Keys.ENTER)
            opened_chat = self.driver.find_element(
                By.XPATH,
                "/html/body/div/div[1]/div[1]/div[4]/div[1]/header/div[2]/div[1]/div/span",
            )
            title = opened_chat.get_attribute("title")
            if title.upper() == username.upper(): #type:ignore
                return True
            else:
                return False
        except Exception as bug:
            self.logger.exception(f"Exception raised while finding user {username}\n{bug}")

    def get_first_chat(self, ignore_pinned=True):
        """get_first_chat()  [nCKbr]

        gets the first chat on the list of chats

        Args:
            ignore_pinned (boolean): parameter that flags if the pinned chats should or not be ignored - standard value: True (it will ignore pinned chats!)
        """
        try:
            search_box = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@id="side"]/div[1]/div/div/div/div')
                )
            )
            search_box.click()
            search_box.send_keys(Keys.ARROW_DOWN)
            chat = self.driver.switch_to.active_element
            time.sleep(1)
            if ignore_pinned:
                while True:
                    flag = False
                    for item in chat.find_elements(By.TAG_NAME, "span"):
                        if "pinned" in item.get_attribute("innerHTML"): #type:ignore
                            flag = True
                            break
                    if not flag:
                        break
                    chat.send_keys(Keys.ARROW_DOWN)
                    chat = self.driver.switch_to.active_element

            name = chat.text.split("\n")[0]
            self.logger.info(f'Successfully selected chat "{name}"')
            chat.send_keys(Keys.ENTER)

        except Exception as bug:
            self.logger.exception(f"Exception raised while getting first chat: {bug}")

    def search_chat_by_name(self, query: str):
        """search_chat_name()  [nCKbr]

        searches for the first chat containing the query parameter

        Args:
            query (string): query value to be located in the chat name
        """
        try:
            search_box = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@id="side"]/div[1]/div/div/div/div')
                )
            )
            search_box.click()
            search_box.send_keys(Keys.ARROW_DOWN)
            chat = self.driver.switch_to.active_element

            # excepcitonally acceptable here!
            time.sleep(1)
            flag = False
            prev_name = ""
            name = ""
            while True:
                prev_name = name
                name = chat.text.split("\n")[0]
                if query.upper() in name.upper():
                    flag = True
                    break
                chat.send_keys(Keys.ARROW_DOWN)
                chat = self.driver.switch_to.active_element
                if prev_name == name:
                    break
            if flag:
                self.logger.info(f'Successfully selected chat "{name}"')
                chat.send_keys(Keys.ENTER)
            else:
                self.logger.info(f'Could not locate chat "{query}"')
                search_box.click()
                search_box.send_keys(Keys.ESCAPE)

        except Exception as bug:
            self.logger.exception(f"Exception raised while getting first chat: {bug}")

    def get_list_of_messages(self):
        """get_list_of_messages()

        gets the list of messages in the page
        """
        messages = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '//*[@id="pane-side"]/div[2]/div/div/child::div')
            )
        )

        clean_messages = []
        for message in messages:
            _message = message.text.split("\n")
            if len(_message) == 2:
                clean_messages.append(
                    {
                        "sender": _message[0],
                        "time": _message[1],
                        "message": "",
                        "unread": False,
                        "no_of_unread": 0,
                        "group": False,
                    }
                )
            elif len(_message) == 3:
                clean_messages.append(
                    {
                        "sender": _message[0],
                        "time": _message[1],
                        "message": _message[2],
                        "unread": False,
                        "no_of_unread": 0,
                        "group": False,
                    }
                )
            elif len(_message) == 4:
                clean_messages.append(
                    {
                        "sender": _message[0],
                        "time": _message[1],
                        "message": _message[2],
                        "unread": _message[-1].isdigit(),
                        "no_of_unread": int(_message[-1])
                        if _message[-1].isdigit()
                        else 0,
                        "group": False,
                    }
                )
            elif len(_message) == 5:
                clean_messages.append(
                    {
                        "sender": _message[0],
                        "time": _message[1],
                        "message": "",
                        "unread": _message[-1].isdigit(),
                        "no_of_unread": int(_message[-1])
                        if _message[-1].isdigit()
                        else 0,
                        "group": True,
                    }
                )
            elif len(_message) == 6:
                clean_messages.append(
                    {
                        "sender": _message[0],
                        "time": _message[1],
                        "message": _message[4],
                        "unread": _message[-1].isdigit(),
                        "no_of_unread": int(_message[-1])
                        if _message[-1].isdigit()
                        else 0,
                        "group": True,
                    }
                )
            else:
                self.logger.info(f"Unknown message format: {_message}")
        return clean_messages

    def check_if_given_chat_has_unread_messages(self, query):
        """check_if_given_chat_has_unread_messages() [nCKbr]

        identifies if a given chat has unread messages or not.

        Args:
            query (string): query value to be located in the chat name
        """
        try:
            list_of_messages = self.get_list_of_messages()
            for chat in list_of_messages:
                if query.upper() == chat["sender"].upper():
                    if chat["unread"]:
                        self.logger.info(
                            f'Yup, {chat["no_of_unread"]} new message(s) on chat <{chat["sender"]}>.'
                        )
                        return True
                    self.logger.info(f'There are no new messages on chat "{query}".')
                    return False
            self.logger.info(f'Could not locate chat "{query}"')

        except Exception as bug:
            self.logger.exception(f"Exception raised while getting first chat: {bug}")

    def send_message1(self, mobile: str, message: str) -> str:
        # CJM - 20220419:
        #   Send WhatsApp Message With Different URL, NOT using https://wa.me/ to prevent WhatsApp Desktop to open
        #   Also include the Number we want to send to
        #   Send Result
        #   0 or Blank or NaN = Not yet sent
        #   1 = Sent successfully
        #   2 = Number to short
        #   3 = Error or Failure to Send Message
        #   4 = Not a WhatsApp Number
        return_msg = ""
        try:
            # Browse to a "Blank" message state
            self.driver.get(f"https://web.whatsapp.com/send?phone={mobile}&text")

            # This is the XPath of the message textbox
            inp_xpath = (
                '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]'
            )
            # This is the XPath of the "ok button" if the number was not found
            nr_not_found_xpath = (
                '//*[@id="app"]/div/span[2]/div/span/div/div/div/div/div/div[2]/div/div'
            )

            # If the number is NOT a WhatsApp number then there will be an OK Button, not the Message Textbox
            # Test for both situations -> find_elements returns a List
            ctrl_element = self.wait.until(
                lambda ctrl_self: ctrl_self.find_elements(By.XPATH, nr_not_found_xpath)
                or ctrl_self.find_elements(By.XPATH, inp_xpath)
            )
            # Iterate through the list of elements to test each if they are a textBox or a Button
            for i in ctrl_element:
                if i.aria_role == "textbox":
                    # This is a WhatsApp Number -> Send Message

                    for line in message.split("\n"):
                        i.send_keys(line)
                        ActionChains(self.driver).key_down(Keys.SHIFT).key_down(
                            Keys.ENTER
                        ).key_up(Keys.ENTER).key_up(Keys.SHIFT).perform()
                    i.send_keys(Keys.ENTER)

                    return_msg = f"1 "  # Message was sent successfully
                    # Found alert issues when we send messages too fast, so I called the below line to catch any alerts
                    self.catch_alert()

                elif i.aria_role == "button":
                    # Did not find the Message Text box
                    # BUT we possibly found the XPath of the error "Phone number shared via url is invalid."
                    if i.text == "OK":
                        # This is NOT a WhatsApp Number -> Press enter and continue
                        i.send_keys(Keys.ENTER)
                        return_msg = f"4 "  # Not a WhatsApp Number

        except (NoSuchElementException, Exception) as bug:
            self.logger.exception(f"An exception occurred: {bug}")
            return_msg = "3 "

        finally:
            self.logger.info(f"{return_msg}")
            return return_msg

    def send_message_to_current_chat(self, message: str, timeout:float=0.0):
        """
        Sends a message to the current chat on screen

        Args:
            message (str): The message to be sent
            timeout (float): time to wait after typing and before sending
        """
        try:
            inp_xpath = '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div[1]/div/div[1]/p'
            input_box = self.wait.until(
                EC.presence_of_element_located((By.XPATH, inp_xpath))
            )
            for line in message.split("\n"):
                # mimick human like typing behaviour
                for word in line.split():
                    input_box.send_keys(word)
                    input_box.send_keys(Keys.SPACE)
                    time.sleep(0.8)
                ActionChains(self.driver).key_down(Keys.SHIFT).key_down(
                    Keys.ENTER
                ).key_up(Keys.ENTER).key_up(Keys.SHIFT).perform()
            if timeout:
                time.sleep(timeout)
            input_box.send_keys(Keys.ENTER)
            self.logger.info(f"Message sent successfuly to {self.current_mobile}")
            return True
        except (NoSuchElementException, Exception) as bug:
            self.logger.exception(f"Failed to send a message to {self.current_mobile} - {bug}")
            #self.logger.info("send_message() finished running!")
        return False

    def find_attachment(self):
        clipButton = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//*[@id="main"]/footer//*[@data-icon="attach-menu-plus"]/..',
                )
            )
        )
        clipButton.click()

    def add_caption(self, message: str, media_type: str = "image"):
        xpath_map = {
            "image": "/html/body/div[1]/div/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]/div[1]/div[1]",
            "video": "/html/body/div[1]/div/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[1]/div[3]/div/div/div[1]/div[1]",
            "file": "/html/body/div[1]/div/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[1]/div[3]/div/div/div[1]/div[1]",
        }
        inp_xpath = xpath_map[media_type]
        input_box = self.wait.until(
            EC.presence_of_element_located((By.XPATH, inp_xpath))
        )
        for line in message.split("\n"):
            input_box.send_keys(line)
            ActionChains(self.driver).key_down(Keys.SHIFT).key_down(Keys.ENTER).key_up(
                Keys.ENTER
            ).key_up(Keys.SHIFT).perform()

    def send_attachment(self):
        # Waiting for the pending clock icon to disappear
        self.wait.until_not(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="main"]//*[@data-icon="msg-time"]')
            )
        )

        sendButton = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//*[@id="app"]/div[1]/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[2]/div[2]/div/div/span',
                )
            )
        )
        sendButton.click()

        # Waiting for the pending clock icon to disappear again - workaround for large files or loading videos.
        # Appropriate solution for the presented issue. [nCKbr]
        self.wait.until_not(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="main"]//*[@data-icon="msg-time"]')
            )
        )

    def send_picture(self, picture: Path, message: Optional[str] = None):
        """send_picture ()

        Sends a picture to a target user

        Args:
            picture ([type]): [description]
        """
        try:
            filename = os.path.realpath(picture)
            self.find_attachment()
            # To send an Image
            imgButton = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div[2]/div/span/div/ul/div/div[2]/li/div/input',
                    )
                )
            )
            imgButton.send_keys(filename)
            if message:
                self.add_caption(message, media_type="image")
            self.send_attachment()
            self.logger.info(f"Picture has been successfully sent to {self.current_mobile}")
        except (NoSuchElementException, Exception) as bug:
            self.logger.exception(f"Failed to send a message to {self.current_mobile} - {bug}")
        finally:
            self.logger.info("send_picture() finished running!")

    def convert_bytes(self, size) -> str | None:
        # CJM - 2022/06/10:
        # Convert bytes to KB, or MB or GB
        for x in ["bytes", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return "%3.1f %s" % (size, x)
            size /= 1024.0

    def _convert_bytes_to(self, size:float, to:str) -> float:
        # CJM - 2022 / 06 / 10:
        # Returns Bytes as 'KB', 'MB', 'GB', 'TB'
        conv_to = to.upper()
        if conv_to in ["BYTES", "KB", "MB", "GB", "TB"]:
            for x in ["BYTES", "KB", "MB", "GB", "TB"]:
                if x == conv_to:
                    return size
                size /= 1024
        raise TypeError('Parameter "to" must be in ["BYTES", "KB", "MB", "GB", "TB"]')

    def send_video(self, video: Path, message: Optional[str] = None):
        """send_video ()
        Sends a video to a target user
        CJM - 2022/06/10: Only if file is less than 14MB (WhatsApp limit is 15MB)

        Args:
            video ([type]): the video file to be sent.
        """
        try:
            filename = os.path.realpath(video)
            f_size = os.path.getsize(filename)
            x = self._convert_bytes_to(f_size, "MB")
            if x < 14:
                # File is less than 14MB
                self.find_attachment()
                # To send a Video
                video_button = self.wait.until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div[2]/div/span/div/ul/div/div[2]/li/div/input',
                        )
                    )
                )

                video_button.send_keys(filename)
                if message:
                    self.add_caption(message, media_type="video")
                self.send_attachment()
                self.logger.info(f"Video has been successfully sent to {self.current_mobile}")
            else:
                self.logger.info(f"Video larger than 14MB")
        except (NoSuchElementException, Exception) as bug:
            self.logger.exception(f"Failed to send a message to {self.current_mobile} - {bug}")
        finally:
            self.logger.info("send_video() finished running!")

    def send_file(self, file_path: str, message: Optional[str] = None):
        """send_file()

        Sends a file to target user

        Args:
            filename ([type]): [description]
        """
        try:
            file_path = os.path.realpath(file_path)
            self.find_attachment()
            document_button = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div[2]/div/span/div/ul/div/div[1]/li/div/input',
                    )
                )
            )
            document_button.send_keys(file_path)
            if message:
                self.add_caption(message, media_type="file")
            self.send_attachment()
        except (NoSuchElementException, Exception) as bug:
            self.logger.exception(f"Failed to send a file to {self.current_mobile} - {bug}")
        finally:
            self.logger.info("send_file() finished running!")

    def close_when_message_successfully_sent(self):
        """close_when_message_successfully_sent() [nCKbr]

        Closes the browser window to allow repeated calls when message is successfully sent/received.
        Ideal for recurrent/scheduled messages that would not be sent if a browser is already opened.
        [This may get deprecated when an opened browser verification gets implemented, but it's pretty useful now.]

        Friendly contribution by @euriconicacio.
        """

        self.logger.info("Waiting for message status update to close browser...")
        try:
            # Waiting for the pending clock icon shows and disappear
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="main"]//*[@data-icon="msg-time"]')
                )
            )
            self.wait.until_not(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="main"]//*[@data-icon="msg-time"]')
                )
            )
        except (NoSuchElementException, Exception) as bug:
            self.logger.exception(f"Failed to send a message to {self.current_mobile} - {bug}")
        finally:
            self.driver.close()
            self.logger.info("Browser closed.")

    def wait_until_message_successfully_sent(self):
        """wait_until_message_successfully_sent()

        Waits until message is finished sending before continuing to next action.

        Friendly contribution by @jeslynlamxy.
        """

        self.logger.info("Waiting for message status update to before continuing...")
        try:
            # Waiting for the pending clock icon shows and disappear
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="main"]//*[@data-icon="msg-time"]')
                )
            )
            self.wait.until_not(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="main"]//*[@data-icon="msg-time"]')
                )
            )
        except (NoSuchElementException, Exception) as bug:
            self.logger.exception(f"Failed to send a message to {self.current_mobile} - {bug}")

    def get_last_message_received(self, query: str):
        """get_last_message_received() [nCKbr]

        fetches the last message receive in a given chat, along with couple metadata, retrieved by the "query" parameter provided.

        Args:
            query (string): query value to be located in the chat name
        """
        try:
            if self.query_chats(query):
                self.wait.until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "/html/body/div[1]/div/div/div[4]/div/div[1]/div/div/div[2]/div/div[1]/p",
                        )
                    )
                )

                time.sleep(
                    3
                )  # clueless on why the previous wait is not respected - we need this sleep to load tha list.

                list_of_messages = self.wait.until(
                    EC.presence_of_all_elements_located((
                        By.XPATH,
                        '//div[@id="main"]/div[3]/div[1]/div[2]/div[3]/child::div[contains(@class,"message-in")]')
                    )
                )

                if len(list_of_messages) == 0:
                    self.logger.exception(
                        "It was not possible to retrieve the last message - probably it does not exist."
                    )
                else:
                    msg = list_of_messages[-1]

                    is_default_user = self.wait.until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                '//div[@id="main"]/header/div[1]/div[1]/div[1]/span',
                            )
                        )
                    ).get_attribute("data-testid")
                    if is_default_user == "default-user":
                        msg_sender = query
                    else:
                        msg_sender = msg.text.split("\n")[0]

                    if len(msg.text.split("\n")) > 1:
                        when = msg.text.split("\n")[-1]
                        msg = (
                            msg.text.split("\n")
                            if "media-play" not in msg.get_attribute("innerHTML") #type:ignore
                            else "Video or Image"
                        )
                    else:
                        when = msg.text.split("\n")[0]
                        msg = "Non-text message (maybe emoji?)"

                    header_group = self.wait.until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                '//div[@id="main"]/header/div[1]/div[1]/div[1]/span',
                            )
                        )
                    )
                    header_text = self.wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//div[@id="main"]/header/div[2]/div[2]/span')
                        )
                    )

                    if (
                        header_group.get_attribute("data-testid") == "default-group"
                        and msg_sender.strip() in header_text.text
                    ):
                        self.logger.info(f"Message sender: {msg_sender}.")
                    elif (
                        msg_sender.strip() != msg[0].strip()
                    ):  # it is not a messages combo
                        self.logger.info(f"Message sender: {msg_sender}.")
                    else:
                        self.logger.info(
                            f"Message sender: retrievable from previous messages."
                        )

                    # DISCLAIMER: messages answering other messages carry the previous ones in the text.
                    # Example: Message text: ['John', 'Mary', 'Hi, John!', 'Hi, Mary! How are you?', '14:01']
                    # TODO: Implement 'filter_answer' boolean paramenter to sanitize this text based on previous messages search.

                    self.logger.info(f"Message text: {msg}.")
                    self.logger.info(f"Message time: {when}.")

        except Exception as bug:
            self.logger.exception(f"Exception raised while getting first chat: {bug}")

    def fetch_all_unread_chats(self, limit=True, top=50):
        """fetch_all_unread_chats()  [nCKbr]

        retrieve all unread chats.

        Args:
            limit (boolean): should we limit the counting to a certain number of chats (True) or let it count it all (False)? [default = True]
            top (int): once limiting, what is the *approximate* number of chats that should be considered? [generally, there are natural chunks of 10-22]

        DISCLAIMER: Apparently, fetch_all_unread_chats functionallity works on most updated browser versions
        (for example, Chrome Version 102.0.5005.115 (Official Build) (x86_64)). If it fails with you, please
        consider updating your browser while we work on an alternative for non-updated broswers.

        """
        try:
            counter = 0
            pane = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@id="pane-side"]/div[2]')
                )
            )
            list_of_messages = self.get_list_of_messages()
            read_names = []
            names = []
            names_data = []

            while True:
                last_counter = counter
                for item in list_of_messages:
                    name = item["sender"]
                    if name not in read_names:
                        read_names.append(name)
                        counter += 1
                    if item["unread"]:
                        if name not in names:
                            names.append(name)
                            names_data.append(item)

                pane.send_keys(Keys.PAGE_DOWN)
                pane.send_keys(Keys.PAGE_DOWN)

                list_of_messages = self.get_list_of_messages()

                side_panel = self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//div[@id="pane-side"]/div[2]')))
                some_weird_counter = side_panel.get_attribute("aria-rowcount")
                if type(some_weird_counter) is not int:
                    raise TypeError
                
                if (
                    last_counter == counter
                    and counter >= int(some_weird_counter) * 0.9
                ):
                    break
                if limit and counter >= top:
                    break

                self.logger.info(f"The counter value at this chunk is: {counter}.")

            if limit:
                self.logger.info(
                    f"The list of unread chats, considering the first {counter} messages, is: {names}."
                )
            else:
                self.logger.info(f"The list of all unread chats is: {names}.")
            return names_data

        except Exception as bug:
            self.logger.exception(f"Exception raised while getting first chat: {bug}")
            return []
