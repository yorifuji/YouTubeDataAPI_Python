# -*- coding: utf-8 -*-

import sys
from os import getenv
from dotenv import load_dotenv, find_dotenv
import json
import googleapiclient.discovery

load_dotenv(find_dotenv())

api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = getenv('DEVELOPER_KEY')

# python - How do you split a list into evenly sized chunks? - Stack Overflow
# https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_authenticated_service():
    return googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

def get_uploads_playlist_id(channelId):
    request = youtube.channels().list(
        part="contentDetails",
        id=channelId,
        fields="items/contentDetails/relatedPlaylists/uploads"
    )
    response = request.execute()
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_video_id_in_playlist(playlistId):
    video_id_list = []

    request = youtube.playlistItems().list(
        part="snippet",
        maxResults=50,
        playlistId=playlistId,
        fields="nextPageToken,items/snippet/resourceId/videoId"
    )

    while request:
        response = request.execute()
        video_id_list.extend(list(map(lambda item: item["snippet"]["resourceId"]["videoId"], response["items"])))
        request = youtube.playlistItems().list_next(request, response)

    return video_id_list

def get_video_items(video_id_list):
    video_items = []

    chunk_list = list(chunks(video_id_list, 50)) # max 50 id per request.
    for chunk in chunk_list:
        video_ids = ",".join(chunk)
        request = youtube.videos().list(
            part="snippet,statistics",
            id=video_ids,
            fields="items(id,snippet(title,description,publishedAt,thumbnails),statistics(viewCount,likeCount))"
        )
        response = request.execute()
        video_items.extend(response["items"])

    return video_items

def get_image_url(video_item):
    qualities = ['standard', 'high', 'medium', 'default']
    for quality in qualities:
        if quality in video_item['snippet']['thumbnails'].keys():
            return video_item['snippet']['thumbnails'][quality]['url']
    return ''

def convertVideoItems(video_items):
    return list(map(lambda item: {
        'id': item["id"],
        'title': item["snippet"]["title"],
        'publishedAt': item["snippet"]["publishedAt"],
        'views': int(item["statistics"]["viewCount"]) if 'viewCount' in item["statistics"].keys() else 0,
        'likes': int(item["statistics"]["likeCount"]) if 'likeCount' in item["statistics"].keys() else 0,
        'image': get_image_url(item),
    }, video_items))

def main(channelId):
    uploads_playlist_id = get_uploads_playlist_id(channelId)
    video_id_list = get_video_id_in_playlist(uploads_playlist_id)
    video_items = get_video_items(video_id_list)
    # print(len(video_items))

    print(json.dumps(convertVideoItems(video_items), sort_keys=True, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    youtube = get_authenticated_service()
    main(sys.argv[1])
