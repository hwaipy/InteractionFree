import threading
import time
import os


# TODO: to be upgrade. This should cache the static resources to reduce dist read.
class StaticResource:
    @classmethod
    def get(cls, path, binary=False):
        print('getting')
        file = open(path, 'rb' if binary else 'r')
        return file.read(os.path.getsize(path))
        # file =
#     @classmethod
#     def loop(cls):
#         while True:
#             time.sleep(1)
#
#     def __init__(self, path, binary=False):
#         self.path = path
#
#     def getContent(self):
#         print(self.request)
#         items = ["Item 1", "Item 2", "Item 3"]
#         self.render("app/index.html", title="My title", items=items)
#
#     def __load(self):
#         file = open(self.path, 'rb')
#
#
#     threading.Thread(target=loop, daemon=True).start()
#
#
# def loop():
#     StaticResource.loop()
