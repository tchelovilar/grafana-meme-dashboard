from posixpath import split
import requests
import os
import sys
import shutil
import urllib.request
import re

from string import Template


def get_recent(query, headers, max_results=10):
    url = "https://api.twitter.com/2/tweets/search/recent"

    params = {
                'query': query,
                'max_results': max_results,
                'expansions': "attachments.media_keys",
                'media.fields': "url"
            }

    response = requests.request("GET", url, headers = headers, params = params)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


bearer_token = os.getenv('TOKEN')
headers = {"Authorization": "Bearer {}".format(bearer_token)}
query = "from:PR0GRAMMERHUM0R"
tweet_info = get_recent(query, headers)


if len(tweet_info['data'][0]['attachments']) == 0:
    print("Message has no attachments")
    sys.exit(0)

tweet_id = tweet_info['data'][0]['id']
tweet_message = tweet_info['data'][0]['text']
attach_id = tweet_info['data'][0]['attachments']['media_keys'][0]

with open("dash/tweet_id") as tweet_id_file:
    current_tweet_id = tweet_id_file.readline()


if current_tweet_id == tweet_id:
    print("There is no new tweet available")
    sys.exit(0)


for media in tweet_info['includes']['media']:
    if media["media_key"] == attach_id:
        media_url = media["url"]
        media_type = media["type"]
        media_name = media_url.split("/")[-1]

if media_type not in ["photo", "animated_gif"]:
    print(f"Media type '{media_type}' not supported")
    sys.exit(0)

images_dir = "dash/images/"
shutil.rmtree(images_dir, ignore_errors=True)
os.mkdir(images_dir)

image_path = os.path.join(images_dir, media_name)
urllib.request.urlretrieve(media_url, image_path)


with open("template/index.j2") as index_template_file:
    template = Template(index_template_file.read())

clean_text = re.sub(r'https://[\w\.]*/[\w]*', '', tweet_message)
template_values = {
    "message": clean_text,
    "image": media_name
}
result = template.substitute(template_values)

with open("dash/index.html", "w") as index_file:
    index_file.write(result)

with open("dash/tweet_id", "w") as tweet_id_file:
    tweet_id_file.write(tweet_id)

print(f"::set-output name=new_tweet_id::{tweet_id}")
