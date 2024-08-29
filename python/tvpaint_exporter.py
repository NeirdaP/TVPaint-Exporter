import os
import tempfile
import time
import ftplib
import re

import pytvpaint.george
from pytvpaint.project import Project
from pytvpaint.utils import render_context

FTP_URL = 'ftp.supamonks.com'
FTP_USER = 'WOF'
FTP_MDP = '5k3atKva2D2poU'
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
            conn.login(FTP_USER, FTP_MDP)
            conn.prot_p()
            conn.cwd('{}'.format(curr_dir))
            print("FTP connection has been reset")

            do_transfer(filepath, output_name, curr_dir, conn)


def get_server_output_root(filename):
    """
     Project-specific logic to parse tokens from filename and
     return the output dir where layers will be written
    """
    
    shot = re.search("SHO[0-9]{3}", filename)
    if not shot:
        print("Error: shot could not be parsed from filename \
              (expecting SHOXXX), please correct in order to export")
        quit()
    
    # Path starts from root of the FTP server
    return "/5_COMPOSITING/{}/RENDER_LAYERS".format(shot.group())


if __name__ == "__main__":
    project = Project.current_project()
    server_output_root = get_server_output_root(os.path.basename(project.path))

    with Explicit_FTP_TLS(host=FTP_URL, user=FTP_USER, passwd=FTP_MDP) as ftps:
        ftps.set_pasv(True)
        ftps.prot_p()

        # Make sure all directories on output path exist
        dirs = server_output_root.strip("/").split("/")
        curr_path = ""
        for dir in dirs:
            curr_path = curr_path + "/" + dir
            ftps.mkd(curr_path)

        with tempfile.TemporaryDirectory() as tmpdir:
            for scene in project.scenes:
                for clip in scene.clips:
                    for layer in clip.layers:

                        # Render each layer to tmp dir, then copy to server
                        layer_name_clean = layer.name.replace(" ", "_")
                        print("processing layer: {}".format(layer_name_clean))
                        tmp_output_dir = os.path.join(tmpdir, layer_name_clean)
                        tmp_output_path = os.path.join(tmp_output_dir, "{}.#.png".format(layer_name_clean))

                        with render_context(background_mode=pytvpaint.george.BackgroundMode.NONE):
                            layer.render(output_path=tmp_output_path, start=project.start_frame, end=project.end_frame)

                        # For now, all shot layers export to same dir regardless of clip or scene
                        layer_export_dossier = "{}/{}".format(server_output_root, layer_name_clean)
                        ftps.mkd(layer_export_dossier)  
                        ftps.cwd(layer_export_dossier)

                        images = os.listdir(tmp_output_dir)
                        for image in images:
                            full_file_path = '{}/{}'.format(tmp_output_dir, image)
                            print("Copying over file path: {}".format(full_file_path))
                            do_transfer(full_file_path, image, layer_export_dossier, ftps)
                        
    
    print("Done exporting all layers in the project")