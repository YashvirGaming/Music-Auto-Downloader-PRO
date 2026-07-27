import os
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError

class MetadataManager:
    @staticmethod
    def apply_tags(file_path: str, artist: str, title: str):
        if not os.path.exists(file_path):
            return
        try:
            audio = EasyID3(file_path)
        except Exception:
            try:
                tags = ID3(file_path)
            except ID3NoHeaderError:
                tags = ID3()
            tags.save(file_path)
            audio = EasyID3(file_path)

        audio['artist'] = artist
        audio['title'] = title
        audio.save()