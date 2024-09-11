#!/usr/bin/env python

# SPDX-License-Identifier: MIT
# Author: https://github.com/Arcitec

from pathlib import Path
from PIL import Image
import io
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request


def is_terminal_output() -> bool:
    return sys.stdout.isatty()


def is_vt100_supported() -> bool:
    # Most Unix-based systems support VT100. Windows typically doesn't.
    return os.name != "nt"


def convert_bytes_to_string(size: int) -> str:
    if size >= 1073741824:  # 1024 * 1024 * 1024.
        return "{:.2f} GiB".format(size / 1073741824)
    elif size >= 1048576:  # 1024 * 1024.
        return "{:.2f} MiB".format(size / 1048576)
    elif size >= 1024:
        return "{:.2f} KiB".format(size / 1024)
    else:
        return "{} Bytes".format(size)


def download_with_progress(
    url: str, headers: dict[str, str], chunk_size: int = 8192
) -> io.BytesIO | None:
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request)

    if response.getcode() != 200:
        print(f"Error: HTTP {response.getcode()} response received.")
        return None

    total_size: int | None = None
    total_size_human = ""
    content_length_header = response.getheader("Content-Length")
    if content_length_header is not None:
        content_length = int(content_length_header)
        if content_length > 0:
            total_size = content_length
            total_size_human = convert_bytes_to_string(total_size)

    data = io.BytesIO()  # Store the downloaded data in-memory.
    bytes_downloaded = 0

    is_terminal = is_terminal_output()
    vt100_supported = is_vt100_supported()
    max_line_length = 0

    while True:
        chunk = response.read(chunk_size)
        if not chunk:
            break
        data.write(chunk)
        bytes_downloaded += len(chunk)
        bytes_downloaded_human = convert_bytes_to_string(bytes_downloaded)

        if not is_terminal:
            continue  # Don't print anything if we're piped or redirected.

        if total_size is not None:
            progress = (bytes_downloaded / total_size) * 100
            message = f"Downloaded {bytes_downloaded_human} of {total_size_human}... ({progress:.2f}%)"
        else:
            message = f"Downloaded {bytes_downloaded_human}..."

        if vt100_supported:
            # VT100-compatible terminals: Erase line and overwrite it completely.
            print(f"\033[2K\r{message}", end="")
        else:
            # Windows: Add trailing spaces to overwrite trailing junk.
            print(f"\r{message.ljust(max_line_length)}", end="")
            max_line_length = max(max_line_length, len(message))

    print(f"{'\n' if is_terminal else ''}Download complete.")

    # Reset the BytesIO object to the beginning for further processing.
    data.seek(0)

    return data


def extract_discord_icon(
    tar_data: io.BytesIO, discord_png_path: Path
) -> io.BytesIO | None:
    # Analyze the in-memory tar archive and extract the Discord icon.
    with tarfile.open(fileobj=tar_data, mode="r:gz") as tar:
        print("Files in the tar archive:")
        for name in tar.getnames():
            print(f"- {name}")

        # Extract the discord icon into a file-like in-memory object.
        discord_png = None
        try:
            discord_png = tar.extractfile(str(discord_png_path))
        except KeyError as e:
            # print(f"Error: {e}")
            pass

        if discord_png is None:
            print(f"Error: {discord_png_path} was not found in archive!")
            return None

        # Extract the raw bytes.
        discord_png_data = discord_png.read()
        print(
            f'Found "{discord_png_path.name}". File Size: {convert_bytes_to_string(len(discord_png_data))}.'
        )

        return io.BytesIO(discord_png_data)


def get_image_size(image_data: io.BytesIO) -> tuple[bool, int, int]:
    width: int = -1
    height: int = -1
    with Image.open(image_data) as im:
        width, height = im.size

    image_data.seek(0)  # Reset BytesIO position.

    success = not (width == -1 and height == -1)

    return (success, width, height)


def get_xdg_data_home() -> Path:
    # SEE: https://specifications.freedesktop.org/basedir-spec/latest/#variables
    xdg_data_home: str | None = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home)
    else:
        return Path.home() / ".local/share"


# Download the latest Discord tar.gz archive.
# SEE: https://discord.com/download?linux
discord_tar_url = "https://discord.com/api/download?platform=linux&format=tar.gz"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}
print(f'Fetching latest Discord tar.gz archive:\n- "{discord_tar_url}"')
tar_data = download_with_progress(discord_tar_url, headers)
if tar_data is None:
    exit(1)

# Extract their icon to memory.
print("")
discord_png_path = Path("Discord/discord.png")
discord_png_data = extract_discord_icon(tar_data, discord_png_path)
if discord_png_data is None:
    exit(1)

# Load it with Pillow to analyze the dimensions.
# NOTE: We could hardcode the 256x256 size they currently use, but it may change
# in the future, so it's safer to extract it directly.
success, width, height = get_image_size(discord_png_data)
if not success:
    print("Error: Failed to get icon dimensions from PNG file.")
    exit(1)

# Verify that it's a square image and that the dimensions are divisible by 8.
# NOTE: This is a sanity check since Linux app icons MUST follow those rules.
if (width != height) or (width % 8) != 0:
    print(
        f"Error: Icon dimensions are not square or not divisible by 8 ({width}x{height})."
    )
    exit(1)

# Install the icon into the default "hicolor" theme.
# NOTE: All other correctly implemented Linux icon themes are derived from it.
# NOTE: The window icon of the running Vesktop app (visible in places like GNOME
# Overview) will not be replaced, since that's an internal part of Vesktop's app,
# but we'll see the custom icon in the desktop environment launcher and dock!
xdg_data_home = get_xdg_data_home()
icon_theme_name = "hicolor"
icon_theme_dir = xdg_data_home / f"icons/{icon_theme_name}"
icon_size_name = f"{width}x{height}"  # NOTE: "scalable" is used for ".svg" icons.
icon_context = "apps"  # Used for overriding app icons.
target_app_name = "vesktop"  # Replace Vesktop icon.

icon_parent_dir = icon_theme_dir / f"{icon_size_name}/{icon_context}"
icon_target_file = icon_parent_dir / f"{target_app_name}{discord_png_path.suffix}"

icon_parent_dir.mkdir(0o755, parents=True, exist_ok=True)
if not icon_parent_dir.is_dir():
    print(f'Error: Failed to create icon directory at "{icon_parent_dir}".')
    exit(1)

print(f'\nSaving new Vesktop app icon to disk:\n- "{icon_target_file}"')
with icon_target_file.open("wb") as f:  # Overwrites if target exists.
    f.write(discord_png_data.read())

# We now need to alert the system that the icon theme has changed.
# SEE: https://web.archive.org/web/20170130174106/https://fedoraproject.org/wiki/Packaging:Scriptlets#Icon_Cache
print(
    f'\nLetting the system know that the icon theme was updated:\n- Updating timestamp: "{icon_theme_dir}"'
)
os.utime(icon_theme_dir)  # Update directory modification time.
gnome_icon_cache_cmd = "gtk-update-icon-cache"
if shutil.which(gnome_icon_cache_cmd):
    # GNOME is a special snowflake which needs an extra command to update cache.
    # NOTE: "-f" = "Overwrite an existing cache, even if up to date",
    #       "-t" = "Don't check for the existence of index.theme"
    result = subprocess.run(
        [gnome_icon_cache_cmd, "-f", "-t", icon_theme_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print(f'Error: A problem occurred while executing "{gnome_icon_cache_cmd}".')
        exit(1)
    result_msg = result.stdout.strip()
    print(f'- GNOME\'s icon cache: "{result_msg}"')

# Generate removal instructions and save them to disk.
removal_msg = (
    "If you ever want to remove the custom Vesktop icon for some reason, simply execute the following commands:\n\n"
    f'rm -fv "{icon_target_file}"\n'
    f'touch --no-create "{icon_theme_dir}"\n'
    f'{gnome_icon_cache_cmd} -f -t "{icon_theme_dir}"\n'
)

removal_text_file = Path(__file__).absolute().parent / "how_to_remove.txt"
removal_text_file.write_text(removal_msg, encoding="utf-8")

print(
    "\n***\n"
    f"{removal_msg}\n"
    f'These instructions have also been saved to "{removal_text_file.name}".\n'
    "***\n\n"
    "Patching complete! It may take a few minutes for the new icon to become active in your desktop environment.\n\n"
    "If you're on GNOME, opening the Activities Overview and searching for Vesktop seems to help it detect the change a bit faster.\n\n"
    "The new app icon will remain active forever, even after future Vesktop app updates!\n\n"
    "You will never need to run this patcher again!"
)
