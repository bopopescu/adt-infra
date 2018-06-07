import os
import platform
import argparse
import shutil
from subprocess import PIPE, STDOUT
import psutil
import logging
import threading
import path_utils

parser = argparse.ArgumentParser(description='Download and unzip a list of files separated by comma')
parser.add_argument('--build-dir', dest='build_dir', action='store',
                    help='full path to build directory')
parser.add_argument('--log-dir', dest='log_dir', action='store',
                    help='full path to log directory')
parser.add_argument('--props', dest='props', action='store',
                    help='build properties')

args = parser.parse_args()
if not os.path.exists(args.log_dir):
    os.makedirs(args.log_dir)

log_formatter = logging.Formatter('%(message)s')
file_handler = logging.FileHandler(os.path.join(args.log_dir, "init_bot.log"))
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.DEBUG)

logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)


def clean_up():
    """
      clean up build directory and qemu-gles-[pid] files.
      On Windows, some system log file cannot be deleted since they're always being used by another process so try to
      delete each file or directory separately and ignore failures.
    """

    def remove_dir_content(path_to_dir):
        """
        Remove the contents of the passed in directory location.  We remove each item one-by-one to avoid Windows
        issues.
        :param path_to_dir: Filesystem path to the directory.
        :return: None.
        """
        if not os.path.isdir(path_to_dir):
            logger.info("Directory %s does not exist!" % path_to_dir)
            return
        for f in os.listdir(path_to_dir):
            file_path = os.path.join(path_to_dir, f)
            try:
                if os.path.isfile(file_path):
                    logger.info("Delete file %s", file_path)
                    os.remove(file_path)
                elif os.path.isdir(file_path) and args.log_dir != f:
                    logger.info("Delete directory %s", file_path)
                    shutil.rmtree(file_path, ignore_errors=True)
            except Exception as e:
                logger.error("Error in deleting %s, %r", file_path, e)
                pass
    # remove qemu-gles-[pid] files
    host = platform.system()
    if host in ["Linux", "Darwin"]:
        tmp_dir = "/tmp/android-%s" % os.environ["USER"]
    else:
        tmp_dir = os.path.join(os.path.expanduser("~"), 'AppData', 'Local', 'Temp')
    remove_dir_content(tmp_dir)
    # remove build directory
    remove_dir_content(args.build_dir)


def update_sdk_with_timeout(timeout):
    """
    Updates the SDK components located at the environment variable ANDROID_SDK_ROOT.  Update is performed by calling
    'sdkmanager --update' on the proper sdkmanager installation.
    :param timeout: Seconds that represent the max amount of time we will wait.
    :return: 0 on success.  Non-zero on failure.
    """
    # This variable handles communication from the thread back to main execution.
    update_task = {'process': None}

    def update_sdk():
        """
        Runs the sdkmanager binary file and iterates over output.  If a License needs to be accepted, attempts to
        accept the license by passing 'y' to stdin.
        :return: None.
        """
        sdkmanager_binary = path_utils.get_sdkmanager_binary()
        # update existing packages to latest version
        cmd = [sdkmanager_binary, "--update"]
        logger.info("Update android sdk, cmd: %s", ' '.join(cmd))
        update_task['process'] = psutil.Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=STDOUT, bufsize=1)
        with update_task['process'].stdout:
            update_task['process'].stdin.write('y\n')
            update_task['process'].stdin.flush()
            for line in iter(update_task['process'].stdout.readline, b""):
                logger.info(line)
                if "Do you accept the license" in line:
                    try:
                        update_task['process'].write('y\n')
                        update_task['process'].stdin.flush()
                    except:
                        pass
            update_task['process'].wait()
    thread = threading.Thread(target=update_sdk)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        logger.info('Terminating sdkmanager --update process.')
        for process in psutil.process_iter():
            try:
                if any([x == update_task['process'].pid for x in [process.ppid(), process.pid]]):
                    logger.info("Terminate subprocess: %s - %s" % (process.pid, process.cmdline()))
                    process.kill()
            except Exception as e:
                pass
        thread.join(5)
        return 1
    return 0


if __name__ == "__main__":
    """
    Start of main execution when called directly.
    """
    try:
        with open(os.path.join(args.log_dir, 'build.props'), 'w') as outfile:
            outfile.write(args.props)
        logger.info(args.props)
        clean_up()
    except:
        pass
    rc = update_sdk_with_timeout(3600)

    # kill adb process, during update of sdk tools, it will run adb start-server, which leaves
    # a child adb process, clean it up here to avoid hanging of script
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'status'])
            if 'adb' in pinfo['name'] and pinfo['status'] != 'zombie':
                logger.info("Kill adb process %s", pinfo)
                proc.kill()
                proc.wait(5)
        except psutil.NoSuchProcess:
            pass

    exit(rc)
