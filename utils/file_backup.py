from dotenv import load_dotenv
from .backup import Backup
import subprocess
import os
import shutil
import zipfile

load_dotenv()


class FileBackup(Backup):
    def __init__(self, base_path: str) -> None:
        super().__init__(
            os.getenv("PROJECT"), base_path, os.getenv("BACKUP_PATH"), "file_backup"
        )
        self.folder_paths = (
            os.getenv("FOLDER_PATHS").split(",") if os.getenv("FOLDER_PATHS") else []
        )
        self.command = [
            f"scp -r -i {os.getenv('IDENTITY_FILE_PATH')}",
        ]
        # self.command = [f"scp -r {'-i ' + os.getenv('IDENTITY_FILE_PATH') if os.getenv('IDENTITY_FILE_PATH') else ''}"]

    def start_backup(self) -> None:
        if not self.folder_paths:
            return

        for paths in self.folder_paths:
            command = self.command.copy()
            command.append(
                f"{os.getenv('SERVER_USERNAME')}@{os.getenv('SERVER_HOST')}:{paths}"
            )
            command.append(self.save_path)
            subprocess.run(" ".join(command), shell=True)
            self.zip_backup()
        super().start_backup([{"storage_type": "folder", "path": self.save_path}])

    def zip_backup(self):
        # zip_path = f"{self.save_path}.zip"
        file_name = "media-backup.zip"
        zip_path = os.path.join(self.save_path, file_name)
        print(f"Zipping files to: {zip_path}")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.save_path):
                for file in files:
                    if file == file_name:
                        continue
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, self.save_path)
                    zipf.write(full_path, relative_path)

        print(f"files zipped successfully: {zip_path}")

        # Cleanup everything except zip
        if os.path.exists(zip_path):
            self.cleanup_except_zip(file_name)

        return zip_path

    def cleanup_except_zip(self, zip_file_name):
        for item in os.listdir(self.save_path):
            item_path = os.path.join(self.save_path, item)

            # Skip the zip file
            if item == zip_file_name:
                continue

            # If directory → delete recursively
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)

            # If file → delete normally
            elif os.path.isfile(item_path):
                os.remove(item_path)

        print("Cleanup completed. Only zip file remains.")
