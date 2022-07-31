import time
from typing import Optional

import googleapiclient.errors
from attr import define
from cardpicker.models import Source, SourceTypeChoices
from cardpicker.sources.api import (
    Folder,
    Image,
    execute_google_drive_api_call,
    find_or_create_google_drive_service,
)
from tqdm import tqdm


@define
class SourceType:
    @staticmethod
    def get_identifier() -> SourceTypeChoices:
        raise NotImplementedError

    @staticmethod
    def get_name() -> str:
        raise NotImplementedError

    @staticmethod
    def get_description() -> str:
        raise NotImplementedError

    @staticmethod
    def get_download_link(card_id: str) -> Optional[str]:
        raise NotImplementedError

    @staticmethod
    def get_all_folders(sources: list[Source]) -> dict[str, Optional[Folder]]:
        raise NotImplementedError

    @staticmethod
    def get_all_folders_inside_folder(folder: Folder) -> list[Folder]:
        raise NotImplementedError

    @staticmethod
    def get_all_images_inside_folder(folder: Folder) -> list[Image]:
        raise NotImplementedError


class GoogleDrive(SourceType):
    @staticmethod
    def get_identifier() -> SourceTypeChoices:
        return SourceTypeChoices.GOOGLE_DRIVE

    @staticmethod
    def get_name() -> str:
        return SourceTypeChoices.GOOGLE_DRIVE.label

    @staticmethod
    def get_description() -> str:
        return "whatever"  # TODO

    @staticmethod
    def get_download_link(card_id: str) -> Optional[str]:
        return f"https://drive.google.com/uc?id={card_id}&export=download"

    @staticmethod
    def get_all_folders(sources: list[Source]) -> dict[str, Optional[Folder]]:
        service = find_or_create_google_drive_service()
        print("Retrieving Google Drive folders...")
        bar = tqdm(total=len(sources))
        folders: dict[str, Optional[Folder]] = {}
        for x in sources:
            try:
                if (folder := execute_google_drive_api_call(service.files().get(fileId=x.drive_id))) is not None:
                    folders[x.key] = Folder(id=folder["id"], name=folder["name"], parents=[])
                else:
                    raise googleapiclient.errors.HttpError
            except googleapiclient.errors.HttpError:
                folders[x.key] = None
                print(f"Failed on drive: {x.key}")
            finally:
                bar.update(1)

        print("...and done!")
        return folders

    @staticmethod
    def get_all_folders_inside_folder(folder: Folder) -> list[Folder]:
        service = find_or_create_google_drive_service()
        results = execute_google_drive_api_call(
            service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and " f"'{folder.id}' in parents",
                fields="files(id, name, parents)",
                pageSize=500,
            )
        )
        folders = [Folder(id=x["id"], name=x["name"], parents=x["parents"]) for x in results.get("files", [])]
        return folders

    @staticmethod
    def get_all_images_inside_folder(folder: Folder) -> list[Image]:
        service = find_or_create_google_drive_service()
        page_token = None
        images = []
        while True:
            results = execute_google_drive_api_call(
                service.files().list(
                    q="(mimeType contains 'image/png' or "
                    "mimeType contains 'image/jpg' or "
                    "mimeType contains 'image/jpeg') and "
                    f"'{folder.id}' in parents",
                    fields="nextPageToken, files("
                    "id, name, trashed, size, parents, createdTime, imageMediaMetadata"
                    ")",
                    pageSize=500,
                    pageToken=page_token,
                )
            )

            image_results = results.get("files", [])
            if len(image_results) == 0:
                break
            for item in image_results:
                if not item["trashed"]:
                    images.append(
                        Image(
                            id=item["id"],
                            name=item["name"],
                            created_time=item["createdTime"],
                            folder=folder,
                            height=item["imageMediaMetadata"]["height"],
                            size=item["size"],
                        )
                    )

            page_token = results.get("nextPageToken", None)
            if page_token is None:
                break
        return images


class LocalFile(SourceType):
    ...


class AWSS3(SourceType):
    ...


__all__ = ["Folder", "Image", "SourceType", "SourceTypeChoices", "GoogleDrive", "LocalFile", "AWSS3"]
