import os
import sys
import tempfile
import time
import ftplib
import re
import gazu
import json

import pytvpaint.george
from pytvpaint.project import Project
from pytvpaint.utils import render_context

FTP_URL = "ftp.supamonks.com"
FTP_CONFIG_PATH = "./ftp_config.json"
MAX_RETRIES = 2


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


def do_transfer(filepath, output_name, curr_dir, conn):
    attempts = 0
    try:
        file = open(filepath,'rb')
        ftps.storbinary('STOR {}'.format(output_name), file)
        file.close()
    except OSError as e:
        if attempts < MAX_RETRIES:
            attempts += 1 

            print("FTP Connection Error Occurred")
            print("Attempting FTP reconnect...")
            try:
                conn.quit()
            except ConnectionResetError:
                print("Connection was already closed")
            # allow OS to release port
            time.sleep(2)
            conn.connect(FTP_URL)
            conn.login(ftp_user, ftp_password)
            conn.prot_p()
            conn.cwd('{}'.format(curr_dir))
            print("FTP connection has been reset")

            do_transfer(filepath, output_name, curr_dir, conn)


def get_user_ftp_login_info():
    with open(FTP_CONFIG_PATH, 'r') as file:
        content = file.read()
    try:
        content = json.loads(content)
    except ValueError as e:
        print("The ftp config file %r is unreadable\n%r" % (FTP_CONFIG_PATH, e))
        return (None, None)

    return (content.get("username"), content.get("password"))


def get_server_output_roots(tokens):
    """
     Project-specific logic to use filename tokens to return 
     the output dirs where layers and movie will be written
    """
    shot = tokens.get("shot")
    if not shot:
        print("Error: shot could not be parsed from filename (expecting SHXXX), "
              "please fix the filename in order to export. \nPress Enter to close...")
        input()
        sys.exit(0)
    
    # Paths start from root of the FTP server
    return ("/5_COMPOSITING/{}/RENDER_LAYERS".format(shot), 
            "/2_ANIMATION/{}/OUTPUTS".format(shot))


def parse_tokens(filename):
    # Project-specific logic to parse tokens such as shot etc as needed from filename
    tokens = {}
    tokens["project"] = "TWOF_02"
    tokens["sequence"] = "SQ1"
    shot = re.search("SH[0-9]{3}", filename) 
    tokens["shot"] = shot.group() if shot else None
    return tokens


def publish_to_kitsu(filepath, tokens):
    """
    Seek the related animation task, create comment and upload media
    """
    kitsu_url = "https://kitsu.supamonks.com/"
    gazu.set_host("{}/api".format(kitsu_url))
    gazu.set_event_host(kitsu_url)
    gazu.log_in("supaservice@supamonks.com", "8dGYZqby!$JqWy")

    # Seek the current shot from the project and retrieve its tasks
    proj = gazu.project.get_project_by_name(tokens.get("project"))
    seq = gazu.shot.get_sequence_by_name(proj, tokens.get("sequence"))
    shot = gazu.shot.get_shot_by_name(seq, tokens.get("shot"))
    tasks = gazu.task.all_tasks_for_shot(shot)

    task_to_update = [task for task in tasks if task.get("task_type_name") == "Animation"][0]
    to_check_status = gazu.task.get_task_status_by_name("To Check")
    comment = gazu.task.add_comment(task_to_update, to_check_status, 
                                    comment="Uploaded by TVpaint render layer export tool")
    gazu.task.add_preview(
        task_to_update,
        comment,
        preview_file_path=filepath
    )


def render_layers():
    """
    Render each layer in project to tmp dir, then copy to server
    """
    for scene in project.scenes:
        for clip in scene.clips:
            layers_completed = 1
            for layer in clip.layers:
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
                ftps.mkd(layer_export_folder)  
                ftps.cwd(layer_export_folder)

                images = os.listdir(tmp_output_dir)
                print("Copying layer files to server")
                for image in images:
                    full_file_path = '{}/{}'.format(tmp_output_dir, image)
                    do_transfer(full_file_path, image, layer_export_folder, ftps)
                layers_completed += 1


def render_movie():
    """
    Export and copy to server flattened movie of all layers
    """
    print("Rendering all layers to movie...")
    tmp_movie_output = "{}/{}.mp4".format(tmpdir, filename.split(".")[0])
    try:
        project.render(tmp_movie_output, use_camera=True) 
        ftps.cwd(movie_output_root) 
        do_transfer(tmp_movie_output, os.path.basename(tmp_movie_output), movie_output_root, ftps)

        # Upload movie to kitsu
        print("Updating kitsu...")
        publish_to_kitsu(tmp_movie_output, tokens)
    except Exception as e:
        print("Movie export and upload to kitsu failed: {}".format(e))
        print("Press Enter to close...")
        input()
        sys.exit(0)


if __name__ == "__main__":
    project = Project.current_project()
    filename = os.path.basename(project.path)
    tokens = parse_tokens(filename)
    layer_output_root, movie_output_root = get_server_output_roots(tokens)
    ftp_user, ftp_password = get_user_ftp_login_info()
    
    if not ftp_user or not ftp_password:
        print("Username and/or password missing from config file. Check ftp_config.json")
        print("Press Enter to close...")
        input()
        sys.exit(0)
    
    # Prompt the user for which mode to run the tool in 
    mode = None
    while (mode not in ["1", "2"]):
        print("Sélectionnez un mode:\n1 - Render Layers and Anim Movie\n2 - Render Anim Movie Only")
        mode = input()
    
    with Explicit_FTP_TLS(host=FTP_URL, user=ftp_user, passwd=ftp_password) as ftps:
        ftps.set_pasv(True)
        ftps.prot_p()

        # Make sure all directories on output paths exist
        for path in [layer_output_root, movie_output_root]:
            dirs = path.strip("/").split("/")
            curr_path = ""
            for dir in dirs:
                curr_path = curr_path + "/" + dir
                try:
                    ftps.mkd(curr_path)
                except Exception as e:
                    print(f"Error while creating dir {curr_path} : {e}")

        with tempfile.TemporaryDirectory() as tmpdir:
            if (mode == "1"):
                render_layers()
            render_movie()

    print("Done exporting all layers in the project")