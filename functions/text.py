import string


def convert_text_area_to_list(text):
    """ Takes a text area containing strings separated by spaces or punctuation and returns a list """
    for ch in string.punctuation:
        text = text.replace(ch, ',')
    text = text.replace(' ', ',')
    text_list = text.split(',')
    return text_list
