import requests
import json
import os 
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')
API_KEY = os.getenv('API_KEY')
CHANNEL_HANDLE = 'MrBeast'
maxResults = 50

def get_playlist_id():
    try: 
        url = f'https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={CHANNEL_HANDLE}&key={API_KEY}'

        response = requests.get(url)
        response.raise_for_status()

        data = response.json() # turns the object into a json format
        #print(json.dumps(data, indent=4)) # indent = 4 is a common convention for readibility

        channel_items = data["items"][0]
        channel_playlistId = channel_items["contentDetails"]["relatedPlaylists"]["uploads"]

        print(channel_playlistId)
        return channel_playlistId
    except requests.exceptions.RequestException as e:
        raise e


def get_video_id(playlistId):
    video_ids= []
    pageToken = None
    base_url = f'https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults={maxResults}&playlistId={playlistId}&key={API_KEY}'
    try:
        while True:
            url = base_url

            if pageToken:
                url += f"&pageToken={pageToken}" # append url with the token, headers order does not matter

            response = requests.get(url)
            response.raise_for_status()

            data = response.json()
            for item in data.get('items', []): # This will return an empty array if there is nothing inside the 'items'
                video_id = item['contentDetails']['videoId']
                video_ids.append(video_id)
            
            pageToken = data.get('nextPageToken') # same level as items, why we use get method

            if not pageToken:
                break

            return video_ids

    except requests.exceptions.RequestException as e:
        raise e
    

# We want to extract the publishedAt, title, duration, viewCount, likeCount, and commentCount
def extract_video_data(video_ids):
    extracted_data = []

    #Helper function: Need to split video batched arrays to have 50 items only
    def batch_list(video_id_list, batch_size):
        for video_id in range(0, len(video_id_list), batch_size):
            yield video_id_list[video_id: video_id + batch_size] # will return all batches, not using return as that will end the loop right away
    
    try:
        for batch in batch_list(video_ids, maxResults):
            video_ids_str = ",".join(batch) # grabs each id and separate them with a comma as a string ex: a1,b2,c3

            url = f'https://youtube.googleapis.com/youtube/v3/videos?part=contentDetails&part=snippet&part=statistics&id={video_ids_str}&key={API_KEY}'
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()

            for item in data.get('items', []): # will return 50 items or less
                video_id = item['id']
                snippet = item['snippet']
                contentDetails = item['contentDetails']
                statistics = item['statistics']

                video_data = {
                    "video_id": video_id,
                    "title": snippet['title'],
                    "publishedAt": snippet['publishedAt'],
                    "duration": contentDetails['duration'],
                    "viewCount": statistics.get('viewCount', None), # if not available return None
                    "likeCount" : statistics.get('likeCount', None),
                    "commentCount": statistics.get('commentCount', None)
                }

                extracted_data.append(video_data)

        return extracted_data
    
    except requests.exceptions.RequestException as e:
        raise e

if __name__ == "__main__":
    playlistId = get_playlist_id()
    video_ids_array = get_video_id(playlistId)

    extract_video_data(video_ids_array)