# spoti-common

spoti-common is a Python script that finds common songs across multiple Spotify users' public playlists.

## Features

- Fetches public playlists from multiple Spotify users
- Identifies songs that appear in playlists of multiple users
- Provides a count of users and total appearances for each common song
- Allows customization of the minimum number of users for a song to be considered common

## Prerequisites

- Python 3.6 or higher
- Spotify free account, used to create application ID and secret

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/spoti-common.git
   cd spoti-common
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root and add your Spotify application keys:
   ```
   SPOTIPY_CLIENT_ID=your_client_id_here
   SPOTIPY_CLIENT_SECRET=your_client_secret_here
   ```

## Usage

Run the script using Python:

```
python main.py [-u MIN_USERS]
```

- `-u MIN_USERS`: The minimum number of users for a song to be considered common. 0 means all users, 2 means at least 2 users, 3 means at least 3 users, and so on. Default is 2.

Example usage:

- `python main.py -u 0` will return songs common to all input users
- `python main.py -u 2` (or just `python main.py`) will return songs common to at least 2 users
- `python main.py -u 3` will return songs common to at least 3 users

Enter the user URLs when prompted, separated by commas. Press Ctrl+D to end input.

## Output

The script will print a list of common songs, along with the number of users and total appearances for each song.

Example output:

```
Common songs:
Song 1 - Artist 1: 3 users, 5 appearances
Song 2 - Artist 2: 2 users, 3 appearances
Song 3 - Artist 3: 4 users, 7 appearances
```
