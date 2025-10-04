from alright import WhatsApp
import logging


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    consoleh = logging.StreamHandler()
    consoleh.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(levelname)s]-[%(name)s]-[%(asctime)s] => %(message)s')

    consoleh.setFormatter(formatter)

    logger.addHandler(consoleh)



    logger.info("test)")
    return


if __name__ == "__main__":
    main()