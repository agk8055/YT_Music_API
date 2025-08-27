import threading
import time
import queue
from typing import List
import asyncio

from services.ytm_service import ytm_service
from services.stream_service import StreamService
from services.cache_service import cache_service

class BackgroundTask(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._queue = queue.Queue()
        self._stream_service = StreamService()

    def run(self):
        while True:
            # Process on-demand requests
            try:
                song_id = self._queue.get()
                self._fetch_and_cache_stream_url(song_id)
                self._queue.task_done()
            except Exception as e:
                print(f"Error in background task: {e}")


    def add_song_to_queue(self, song_id: str):
        self._queue.put(song_id)

    def _fetch_and_cache_stream_url(self, song_id: str):
        try:
            # Set status to "pending" in cache
            cache_service.set(song_id, {'status': 'pending'})
            print(f"Fetching stream URL for {song_id}...")

            start_time = time.time()
            stream_url = self._stream_service.get_stream_url_sync(song_id)
            end_time = time.time()

            duration = end_time - start_time
            print(f"Fetching stream URL for {song_id} took {duration:.2f} seconds.")

            if stream_url:
                cache_service.set(song_id, {'status': 'ready', 'url': stream_url})
                print(f"Successfully fetched stream URL for {song_id}.")
            else:
                cache_service.set(song_id, {'status': 'failed'})
                print(f"Failed to fetch stream URL for {song_id}.")
        except Exception as e:
            print(f"Error fetching stream url for {song_id}: {e}")
            cache_service.set(song_id, {'status': 'failed'})

# Create a global instance of the background task
background_task = BackgroundTask()