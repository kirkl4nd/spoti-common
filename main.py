import os
import sys
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import argparse

# Load environment variables from .env file
load_dotenv()

# Get Spotify API credentials from environment variables
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')

# Initialize the Spotify client
try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
except spotipy.SpotifyException as e:
    print(f"Error initializing Spotify client: {e}", file=sys.stderr)
    sys.exit(1)

# Simple cache to avoid redundant API calls
cache = {}
songs = {}  # Global dictionary to store song details

def get_user_playlists(user_id):
    if user_id in cache:
        return cache[user_id]

    playlists = []
    offset = 0
    limit = 50  # Spotify API limit per request

    while True:
        try:
            results = sp.user_playlists(user_id, limit=limit, offset=offset)
            playlists.extend(results['items'])
            if len(results['items']) < limit:
                break
            offset += limit
        except spotipy.SpotifyException as e:
            print(f"Spotify API error while fetching playlists for user {user_id}: {e}", file=sys.stderr)
            break
        except Exception as e:
            print(f"Unexpected error while fetching playlists for user {user_id}: {e}", file=sys.stderr)
            break

    cache[user_id] = playlists
    return playlists

def get_playlist_tracks(playlist_id):
    if playlist_id in cache:
        return cache[playlist_id]

    tracks = []
    try:
        results = sp.playlist_tracks(playlist_id)
        while results:
            for item in results['items']:
                if item['track']:
                    track = item['track']
                    song_id = track['id']
                    if song_id not in songs:
                        songs[song_id] = {
                            'title': track['name'],
                            'artist': track['artists'][0]['name']
                        }
                    tracks.append(item)
            if results['next']:
                results = sp.next(results)
            else:
                break
    except spotipy.SpotifyException as e:
        print(f"Spotify API error while fetching tracks for playlist {playlist_id}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error while fetching tracks for playlist {playlist_id}: {e}", file=sys.stderr)

    cache[playlist_id] = tracks
    return tracks

def process_user(user_url):
    try:
        user_id = user_url.split('/')[-1].split('?')[0]
        print(f"Scanning user: {user_id}", file=sys.stderr)
        playlists = get_user_playlists(user_id)
        
        results = []
        for playlist in playlists:
            if playlist['public']:
                print(f"Scanning playlist: {playlist['name']}", file=sys.stderr)
                tracks = get_playlist_tracks(playlist['id'])
                for track in tracks:
                    if track['track']:
                        song_id = track['track']['id']
                        results.append((song_id, user_id, playlist['id']))
        return results
    except IndexError:
        print(f"Error: Invalid user URL format - {user_url}", file=sys.stderr)
    except Exception as e:
        print(f"Error processing user {user_url}: {e}", file=sys.stderr)
    return []

def find_common_songs(user_urls, min_users):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(process_user, url): url for url in user_urls}
        for future in as_completed(future_to_url):
            results.extend(future.result())

    song_data = defaultdict(lambda: {'users': set(), 'appearances': 0})
    for song_id, user_id, playlist_id in results:
        song_data[song_id]['users'].add(user_id)
        song_data[song_id]['appearances'] += 1

    total_users = len(user_urls)
    min_users = total_users if min_users == 0 else min_users

    common_songs = [
        (f"{songs[song_id]['title']} - {songs[song_id]['artist']}", len(data['users']), data['appearances'])
        for song_id, data in song_data.items()
        if len(data['users']) >= min_users
    ]

    return sorted(common_songs, key=lambda x: (x[1], x[2]), reverse=True)

def main():
    parser = argparse.ArgumentParser(description="Find common songs across Spotify users' playlists.")
    parser.add_argument('-u', type=int, default=2, help='Minimum number of users for a song to be considered common. 0 means all users.')
    args = parser.parse_args()

    try:
        print("Enter comma-separated list of user urls. Press ctrl+D to end input. ", file=sys.stderr)
        user_urls = []
        for line in sys.stdin:
            urls = line.strip().split(',')
            user_urls.extend([url.strip() for url in urls if url.strip()])

        if not user_urls:
            print("Error: No user URLs provided.", file=sys.stderr)
            return

        common_songs = find_common_songs(user_urls, args.u)

        if not common_songs:
            print("No common songs found.")
        else:
            print("\nCommon songs:")
            for song, num_users, num_appearances in common_songs:
                # Split the song title into lines of 64 characters or less
                lines = []
                current_line = song
                while len(current_line) > 64:
                    split_index = current_line.rfind(' ', 0, 64)
                    if split_index == -1:
                        split_index = 64
                    lines.append(current_line[:split_index])
                    current_line = current_line[split_index:].lstrip()
                lines.append(current_line)

                # Print the first line with aligned user counts and appearances
                print(f"{lines[0]:<64} {num_users:>2} users, {num_appearances:>2} appearances")

                # Print any additional lines with indentation
                for line in lines[1:]:
                    print(f"\t{line}")

    except KeyboardInterrupt:
        print("\nProgram interrupted by user.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()