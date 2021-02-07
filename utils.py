def save_html(html, path):
    with open(path, 'w') as f:
        f.write(html)


def open_html(path):
    with open(path, 'r') as f:
        return f.read()
