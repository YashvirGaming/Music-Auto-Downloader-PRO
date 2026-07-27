import os
import time
import random
from PySide6.QtCore import QThread, Signal
import yt_dlp

from youtube import YouTubeSearcher
from metadata import MetadataManager

class DownloadWorker(QThread):
    progress_signal = Signal(dict)
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        artists = self.settings.get("artists", [])
        limit = self.settings.get("limit", 10)
        base_output = self.settings.get("output_dir", "downloads")
        bitrate = self.settings.get("bitrate", "128")
        antiban = self.settings.get("antiban", True)

        if not artists:
            self.log_signal.emit("⚠️ No artists or URLs found in list.")
            self.finished_signal.emit()
            return

        total_artists = len(artists)

        for idx, item in enumerate(artists):
            if self._is_cancelled:
                self.log_signal.emit("🛑 Process cancelled by user.")
                break

            # 1. Check if input is a direct link or search query
            is_direct_url = item.startswith("http://") or item.startswith("https://")
            
            if is_direct_url:
                # Strip playlist parameters to avoid pulling whole playlists
                clean_url = item.split('?list=')[0].split('&list=')[0]
                self.log_signal.emit(f"\n🔗 Processing Direct Link: {clean_url}")
                folder_name = "Direct_Downloads"
                query = clean_url
            else:
                self.log_signal.emit(f"\n🔍 Searching tracks for query: {item}")
                folder_name = self.sanitize_folder_name(item)
                query = YouTubeSearcher.build_query(item, limit, self.settings.get("official_only", True))

            artist_folder = os.path.join(base_output, folder_name)
            os.makedirs(artist_folder, exist_ok=True)

            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': str(bitrate),
            }]

            if self.settings.get("embed_thumbnail", True):
                postprocessors.append({'key': 'FFmpegMetadata'})
                postprocessors.append({'key': 'EmbedThumbnail'})

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(artist_folder, '%(title)s.%(ext)s'),
                'restrictfilenames': True,  # Clean non-ASCII characters from Windows filenames
                'quiet': True,
                'noplaylist': True,
                'no_warnings': True,
                'no_color': True,
                'writethumbnail': self.settings.get("embed_thumbnail", True),
                'postprocessors': postprocessors,
            }

            try:
                # Extract initial search metadata
                extract_opts = {
                    'extract_flat': True,
                    'skip_download': True,
                    'quiet': True
                }
                
                with yt_dlp.YoutubeDL(extract_opts) as ydl_info:
                    info = ydl_info.extract_info(query, download=False)
                    entries = info.get('entries', [info]) if 'entries' in info else [info]

                downloaded_count = 0
                
                # Perform downloading with active options
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_dl:
                    for entry in entries:
                        if self._is_cancelled:
                            break
                        if not is_direct_url and downloaded_count >= limit:
                            break

                        # FIX: Reconstruct full YouTube URL to prevent videoplayback.mp3 renaming bug
                        video_id = entry.get('id')
                        video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else entry.get('url')
                        duration = entry.get('duration', 0)

                        if self.settings.get("skip_shorts") and duration and duration <= 60:
                            self.log_signal.emit(f"⏭️ Skipping Short track: {entry.get('title')}")
                            continue

                        title = entry.get('title', 'Unknown Title')
                        self.log_signal.emit(f"⬇️ Downloading [{downloaded_count + 1}/{limit if not is_direct_url else 1}]: {title}")

                        self.progress_signal.emit({
                            "artist": item,
                            "song": title,
                            "overall_percent": int(((idx + (downloaded_count / (limit if not is_direct_url else 1))) / total_artists) * 100)
                        })

                        try:
                            dl_info = ydl_dl.extract_info(video_url, download=True)
                            
                            if self.settings.get("add_metadata", True) and dl_info:
                                downloaded_filename = ydl_dl.prepare_filename(dl_info)
                                expected_mp3 = os.path.splitext(downloaded_filename)[0] + ".mp3"
                                MetadataManager.apply_tags(expected_mp3, item if not is_direct_url else "Unknown", dl_info.get('title', title))

                            downloaded_count += 1

                            # Anti-Ban Safe Delays
                            if antiban:
                                sleep_time = random.uniform(3.0, 7.0)
                                self.log_signal.emit(f"🛡️ Anti-Ban Active: Pausing {sleep_time:.1f}s...")
                                time.sleep(sleep_time)

                        except Exception as dl_err:
                            self.log_signal.emit(f"❌ Download error on {title}: {dl_err}")

            except Exception as e:
                self.log_signal.emit(f"❌ Error fetching {item}: {e}")

        self.progress_signal.emit({"artist": "Done", "song": "Finished all tasks.", "overall_percent": 100})
        self.log_signal.emit("\n✅ Downloads complete!")
        self.finished_signal.emit()

    @staticmethod
    def sanitize_folder_name(name):
        return "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()