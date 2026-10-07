from abc import ABC, abstractmethod
import os
import shutil
import sys
import tempfile
import time
import ftplib
import re
import gazu
import json
from typing import Tuple, Union

import pytvpaint.george
from pytvpaint.project import Project
from pytvpaint.utils import render_context

FTP_URL = "ftp.supamonks.com"
FTP_CONFIG_PATH = "./ftp_config.json"
MAX_RETRIES = 2
USE_FTPS = False
PROJECT_CONFIGURATION: dict[str, Union[str, list[str], bool]] = {
        "name" : "TWOK",
        "sequence" : "SEQ1",
        "task" : "Clean Anim",
        "server_output_templates" : [
            "TWOK_01/6_Compositing/{shot}/Layers",
            "TWOK_01/4_Animation/{shot}/Outputs"
            ],
        "shot_regex": "SH[0-9]{3}",
        "need_upload_to_kitsu": False,
        "kitsu_url": "https://kitsu.supamonks.com/",
        "kitsu_username": "supaservice@supamonks.com",
        "kitsu_password": "8dGYZqby!$JqWy",
        "kitsu_new_status": "To Check",
        "transfer_strategy" : "FileSystem"
}
SERVER_CONFIGURATION: dict[str, str] = {
    "server_root" : "M:/ULF_FAB/"
}

class TransferStrategy(ABC):
    @abstractmethod
    def do_transfer(self, source: str, destination_folder: str, destination_filename: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def create_destination_filepath(self, destination_folder: str, destination_filename: str) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def ensure_all_directories_on_path_exist(self, path: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_server_output_roots(self, tokens: dict[str, str], server_output_templates: list[str]) -> Tuple[str, str]:
        raise NotImplementedError

class FTPSTransferStrategy(TransferStrategy):
    def do_transfer(self, source: str, destination_folder: str, destination_filename: str) -> None:
        ftp_user, ftp_password = self.get_user_ftp_login_info()
        with Explicit_FTP_TLS(host=FTP_URL, user=ftp_user, passwd=ftp_password) as ftps:
            ftps.set_pasv(True)
            ftps.prot_p()

            try:
                self.ensure_all_directories_on_path_exist(destination_folder)
            except Exception as e:
                print(f"Error while creating dir {destination_folder} : {e}")
            
            ftps.cwd(destination_folder)

            try:
                with open(source, 'rb') as file:
                    ftps.storbinary('STOR {}'.format(destination_filename), file)
            
            # We're catching these exceptions that mainly indicate a loss of server connection
            except (OSError, EOFError, ftplib.error_temp, ftplib.error_proto) as e:
                print(f"FTP Connection Error Occurred on {destination_filename} : {e}")
                print("Attempting FTP reconnect...")
                try:
                    ftps.close()
                except ConnectionResetError:
                    print("Connection was already closed")

                # allow OS to release port
                time.sleep(2)
                ftps.connect(FTP_URL)
                ftps.login(ftp_user, ftp_password)
                ftps.set_pasv(True)
                ftps.prot_p()
                ftps.cwd(destination_folder)
                print("FTP connection has been reset")

                self.do_transfer(source, destination_filename, destination_folder)

    def create_destination_filepath(self, destination_folder: str, destination_filename: str) -> str:
        return f"{destination_folder}/{destination_filename}"
    
    def ensure_all_directories_on_path_exist(self, path: str) -> None:
        dirs = path.strip("/").split("/")
        curr_path = ""
        
        for dir in dirs:
            curr_path = curr_path + "/" + dir
            try:
                ftp_user, ftp_password = self.get_user_ftp_login_info()
                with Explicit_FTP_TLS(host=FTP_URL, user=ftp_user, passwd=ftp_password) as ftps:
                    ftps.set_pasv(True)
                    ftps.prot_p()
                    ftps.mkd(curr_path)
            except Exception as e:
                print(f"Error while creating dir {curr_path} : {e}")

    def get_user_ftp_login_info(self) -> Tuple[str, str]: 
        with open(FTP_CONFIG_PATH, 'r') as file:
            content = file.read()
        try:
            content = json.loads(content)
        except ValueError as e:
            print("The ftp config file %r is unreadable\n%r" % (FTP_CONFIG_PATH, e))
            return ("", "")

        if not content.get("username") or not content.get("password"):
            print("Username and/or password missing from config file. Check ftp_config.json")
            print("Press Enter to close...")
            input()
            sys.exit(0)

        return (content.get("username"), content.get("password"))

    def get_server_output_roots(self, tokens: dict[str, str], server_output_templates: list[str]) -> Tuple[str, str]:
        shot = tokens.get("shot")
        if not shot:
            print("Error: shot could not be parsed from filename (expecting SHXXX), "
                "please fix the filename in order to export. \nPress Enter to close...")
            input()
            sys.exit(0)
        
        # Paths start from root of the FTP server
        return (output.replace("{shot}", shot) for output in server_output_templates)

class FileSystemTransferStrategy(TransferStrategy):
    def do_transfer(self, source: str, destination_folder: str, destination_filename: str) -> None:
        self.ensure_all_directories_on_path_exist(destination_folder)
        shutil.move(source, f"{destination_folder}/{destination_filename}") #TODO: use Pathlib ?
    
    def create_destination_filepath(self, destination_folder: str, destination_filename: str) -> str:
        return f"{destination_folder}/{destination_filename}"
            
    def ensure_all_directories_on_path_exist(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def get_server_output_roots(self, tokens: dict[str, str], server_output_templates: list[str]) -> Tuple[str, str]:
        shot = tokens.get("shot")
        if not shot:
            print("Error: shot could not be parsed from filename (expecting SHXXX), "
                "please fix the filename in order to export. \nPress Enter to close...")
            input()
            sys.exit(0)

        server_output_templates = (output.replace("{shot}", shot) for output in server_output_templates)
        server_root = SERVER_CONFIGURATION.get("server_root")
        return (f"{server_root}/{output}" for output in server_output_templates)


# Lifted from https://stackoverflow.com/questions/33438456/python-ftps-upload-error-425-unable-to-build-data-connection-operation-not-per
class Explicit_FTP_TLS(ftplib.FTP_TLS):
    """Explicit FTPS, with shared TLS session"""
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(conn,
                                            server_hostname=self.host,
                                            session=self.sock.session)
        return conn, size

def parse_tokens(filename: str) -> dict[str, str]:
    # Project-specific logic to parse tokens such as shot etc as needed from filename
    tokens = {}
    tokens["project"] = PROJECT_CONFIGURATION.get("name")
    tokens["sequence"] = PROJECT_CONFIGURATION.get("sequence")
    shot = re.search(PROJECT_CONFIGURATION.get("shot_regex"), filename) 
    tokens["shot"] = shot.group() if shot else None
    return tokens

def upload_to_kitsu(filepath: str, tokens: dict[str, str]) -> None:
    """
    Seek the related animation task, create comment and upload media
    """
    kitsu_url = PROJECT_CONFIGURATION.get("kitsu_url")
    gazu.set_host("{}/api".format(kitsu_url))
    gazu.set_event_host(kitsu_url)
    gazu.log_in(PROJECT_CONFIGURATION.get("kitsu_username"), PROJECT_CONFIGURATION.get("kitsu_password"))

    # Seek the current shot from the project and retrieve its tasks
    proj = gazu.project.get_project_by_name(tokens.get("project"))
    seq = gazu.shot.get_sequence_by_name(proj, tokens.get("sequence"))
    shot = gazu.shot.get_shot_by_name(seq, tokens.get("shot"))
    tasks = gazu.task.all_tasks_for_shot(shot)

    task_to_update = [task for task in tasks if task.get("task_type_name") == PROJECT_CONFIGURATION.get("task")][0]
    new_status = gazu.task.get_task_status_by_name(PROJECT_CONFIGURATION.get("kitsu_new_status"))
    comment = gazu.task.add_comment(task_to_update, new_status, 
                                    comment="Uploaded by TVpaint render layer export tool")
    gazu.task.add_preview(
        task_to_update,
        comment,
        preview_file_path=filepath
    )

def render_layers(transfer_strategy: TransferStrategy):
    """
    Render each layer in project to tmp dir, then copy to server
    """
    for scene in project.scenes:
        for clip in scene.clips:
            layers_completed = 1
            for layer in clip.layers:
                if not layer.is_visible:
                    print("Layer {} is hidden in scene, skipping".format(layer.name))
                    layers_completed += 1
                    continue

                layer_name_clean = layer.name.replace(" ", "_")
                print("Processing layer {} ({}/{})...".format(layer_name_clean, layers_completed, len(list(clip.layers))))
                tmp_output_dir = os.path.join(tmpdir, layer_name_clean)
                tmp_output_path = os.path.join(tmp_output_dir, "{}.#.png".format(layer_name_clean))

                with render_context(background_mode=pytvpaint.george.BackgroundMode.NONE):
                    try:
                        layer.render(output_path=tmp_output_path, start=project.start_frame, end=project.end_frame)

                    except Exception as e:
                        print("Failed to export layer {}: {}".format(layer, e))
                        continue

                # For now, all shot layers export to same dir regardless of clip or scene
                layer_export_folder = "{}/{}".format(layer_output_root, layer_name_clean)

                images = os.listdir(tmp_output_dir)
                print("Copying layer files to server")
                for image in images:
                    transfer_strategy.do_transfer(f"{tmp_output_dir}/{image}", layer_export_folder, image)
                layers_completed += 1

    print("Done exporting all layers in the project")

def render_movie(transfer_strategy: TransferStrategy, need_upload_to_kitsu: bool):
    """
    Export and copy to server flattened movie of all layers
    """
    print("Rendering all layers to movie...")
    tmp_movie_output = "{}/{}.mp4".format(tmpdir, filename.split(".")[0])
    try:
        project.render(tmp_movie_output, use_camera=True) 
        transfer_strategy.do_transfer(tmp_movie_output, movie_output_root, os.path.basename(tmp_movie_output))
    except Exception as e:
        print("Movie export failed: {}".format(e))
        print("Press Enter to close...")
        input()
        sys.exit(0)
    
    if need_upload_to_kitsu:
        try:
            print("Updating kitsu...")
            upload_to_kitsu(tmp_movie_output, tokens)
        except Exception as e:
            print("Upload to kitsu failed: {}".format(e))
            print("Press Enter to close...")
            input()
            sys.exit(0)

    print("Done exporting movie")


if __name__ == "__main__":
    if PROJECT_CONFIGURATION.get("transfer_strategy") == "FileSystem":
        transfer_strategy = FileSystemTransferStrategy()
    else:
        transfer_strategy = FTPSTransferStrategy()
    
    project = Project.current_project()
    filename = os.path.basename(project.path)
    tokens = parse_tokens(filename)
    layer_output_root, movie_output_root = transfer_strategy.get_server_output_roots(
        tokens,
        PROJECT_CONFIGURATION.get("server_output_templates")
    )
    
    # Prompt the user for which mode to run the tool in 
    mode = None
    while (mode not in ["1", "2"]):
        print("Sélectionnez un mode:\n1 - Render Layers and Anim Movie\n2 - Render Anim Movie Only")
        mode = input()

    for path in [layer_output_root, movie_output_root]:
        transfer_strategy.ensure_all_directories_on_path_exist(path)

    with tempfile.TemporaryDirectory() as tmpdir:
        if (mode == "1"):
            render_layers(transfer_strategy)
        render_movie(transfer_strategy, need_upload_to_kitsu=PROJECT_CONFIGURATION.get("need_upload_to_kitsu"))
        