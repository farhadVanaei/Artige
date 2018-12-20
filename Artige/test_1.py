from glob import glob
from instagram_private_api import Client, ClientCompatPatch

from private import user_name, password

path = '/home/mohammad/PycharmProjects/Artige/_artige/draft/'
pattern = '+*'
img = '.jpg'
txt = '.txt'

# user_name = 'YOUR_LOGIN_USER_NAME'
# password = 'YOUR_PASSWORD'
img_files = glob(path + pattern + img)
txt_files = glob(path + pattern + txt)
# print (path + pattern + img)
for i, t in zip(img_files, txt_files):
    print(i, t)

# exit()
api = Client(user_name, password)
results = api.feed_timeline()
items = [item for item in results.get('feed_items', [])
         if item.get('media_or_ad')]
for item in items:
    # Manually patch the entity to match the public api as closely as possible, optional
    # To automatically patch entities, initialise the Client with auto_patch=True
    ClientCompatPatch.media(item['media_or_ad'])
    print(item['media_or_ad']['code'])
