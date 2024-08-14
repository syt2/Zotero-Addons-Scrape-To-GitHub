class AddonInfo:
    def __init__(self, name: str,
                 tag_name: str,
                 xpi_url: str,
                 **kwargs):
        self.name = name
        self.tag_name = tag_name
        self.xpi_url = xpi_url
        [setattr(self, key, value) for (key, value) in kwargs.items()]
