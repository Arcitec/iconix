#!/usr/bin/env python

# SPDX-License-Identifier: MIT
# Author: https://github.com/Arcitec
# Project: https://github.com/Arcitec/iconix
# Name: iconix
# Version: 2.1.0

from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request

svg_supported = False
try:
    import cairosvg  # type: ignore[import-untyped, import-not-found]

    svg_supported = True
except ImportError as e:
    print(
        f"{e}\nWarning: Unable to import the CairoSVG library. You will not be able to load SVG files.\n"
    )

Image.MAX_IMAGE_PIXELS = (
    None  # Disable "DecompressionBombWarning" (allow large inputs).
)


# We need to replace every Vesktop icon size, otherwise the desktop environment
# may still load their icons at certain screen resolutions since theirs is closer.
# NOTE: Can be retrieved with `rpm -qlp vesktop-*.rpm | grep icon`.
DEFAULT_ICON_SIZES: list[str | int] = [
    16,
    32,
    48,
    64,
    128,
    256,
    512,
    1024,
]


@dataclass
class IconSize:
    size: int
    scale: int

    def __init__(self, size: int | str, scale: int = 1) -> None:
        self.scale = scale
        if isinstance(size, int):
            self.size = size
        else:
            # Validate that it follows one of these exact formats:
            # - `<size>` ("32")
            # - `<size>x<same size>` ("32x32")
            # - `<size>x<same size>@<digit>` ("32x32@2")
            # NOTE: We only allow square sizes, exactly like Linux icon themes.
            m = re.search(r"^(\d+)(?:x\1(?:@(\d+))?)?$", size)
            if not m:
                raise ValueError(f'Invalid size specifier: "{size}".')

            # Save the extracted values.
            # NOTE: We allow scale from the input string to override scale arg.
            self.size = int(m.group(1), 10)
            if m.group(2) is not None:
                self.scale = int(m.group(2), 10)

        # Now validate that the size is an even number.
        # NOTE: We could hardcode a list of allowed sizes, but let's not babysit.
        if self.size % 2 != 0:
            raise ValueError(f'Size must be an even number: "{self.size}".')

        # We won't allow zero size or scale.
        if self.size <= 0:
            raise ValueError(f'Size must be a positive number: "{self.size}".')
        if self.scale <= 0:
            raise ValueError(f'Scale must be a positive number: "{self.scale}".')

    def get_name(self) -> str:
        return (
            f"{self.size}x{self.size}"
            if self.scale <= 1
            else f"{self.size}x{self.size}@{self.scale}"
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, IconSize):
            return NotImplemented

        if self.size == other.size:
            return self.scale < other.scale

        return self.size < other.size


def get_file_suffix(file: Path) -> str:
    return file.suffix.lower()


def validate_size(text: str) -> str | int:
    # Validate that it follows one of these exact formats:
    # - `<size>` ("32")
    # - `<size>x<same size>` ("32x32")
    # - `<size>x<same size>@<digit>` ("32x32@2")
    # NOTE: We only allow square sizes, exactly like Linux icon themes.
    m = re.search(r"^(\d+)(?:x\1(@\d+)?)?$", text)
    if not m:
        raise ValueError()

    # Now validate that the size is an even number.
    # NOTE: We could hardcode a list of allowed sizes, but let's not babysit.
    size_raw = m.group(1)
    size_num = int(size_raw, 10)
    if size_num % 2 != 0:
        raise ValueError()

    # We won't allow zero.
    if size_num <= 0:
        raise ValueError()

    # Turn it into an integer if they didn't provide an "@x" scale.
    if m.group(2) is not None:
        return text  # "WxH@s"
    else:
        return size_num


@dataclass
class Settings:
    name: str = field(kw_only=True)
    icon_sizes: list[IconSize] = field(kw_only=True)
    simulate: bool = field(kw_only=True)
    use_discord: bool = field(kw_only=True)
    icon_path: Path | None = field(kw_only=True)


def convert_args_to_settings() -> Settings:
    parser = argparse.ArgumentParser(
        description="Makes Vesktop feel more at home for the average Discord enjoyers."
    )

    parser.add_argument(
        "-d",
        "--discord",
        action="store_true",
        help="use the official Discord icon",
    )

    parser.add_argument(
        "-i",
        "--icon",
        type=Path,
        help="use your own, custom icon (an SVG file or a large PNG is recommended)",
    )

    parser.add_argument(
        "-n",
        "--name",
        type=str,
        default="vesktop",
        help="override the target icon name (advanced users only)",
    )

    parser.add_argument(
        "-s",
        "--size",
        type=IconSize,
        nargs="+",  # Demand at least 1 value when arg is provided.
        default=DEFAULT_ICON_SIZES,
        help="override the target icon sizes (advanced users only)",
    )

    parser.add_argument(
        "-x",
        "--simulate",
        action="store_true",
        help="show the results of the command without writing to disk",
    )

    # Automatically display the help if there aren't any arguments.
    total_args = len(sys.argv) - 1
    if total_args <= 0:
        parser.print_help()
        exit(1)

    # Parses all arguments and warns if encountering invalid values or commands.
    # NOTE: ArgParse also adds an automatic "-h/--help" command, and stops
    # execution here if they requested help.
    args = parser.parse_args()

    # Validate certain arguments.
    if args.name == "":
        raise ValueError("The target icon name cannot be empty.")

    if args.icon:
        icon_path: Path = args.icon
        if not icon_path.is_file():
            raise ValueError(
                f'The file "{icon_path}" does not exist or is not a regular file.'
            )

        if icon_path.stat().st_size <= 0:
            raise ValueError(f'The file "{icon_path}" is empty.')

        if not svg_supported and get_file_suffix(icon_path) == ".svg":
            raise ValueError(
                "You attempted to use an SVG file, but CairoSVG is not available on your system."
            )

    if not args.discord and not args.icon:
        raise ValueError("You must choose either the Discord icon or a custom icon.")

    # Determine which icon sizes we will target.
    target_icon_sizes: list[IconSize] = []
    raw_size: IconSize | str | int
    for raw_size in args.size:
        target_icon_sizes.append(
            raw_size if isinstance(raw_size, IconSize) else IconSize(raw_size)
        )
    target_icon_sizes.sort()
    if len(target_icon_sizes) <= 0:
        raise ValueError("You must provide at least one target icon size.")

    return Settings(
        name=args.name,
        icon_sizes=target_icon_sizes,
        simulate=args.simulate,
        use_discord=args.discord,
        icon_path=args.icon,
    )


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
) -> io.BytesIO:
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request)

    if response.getcode() != 200:
        raise Exception(f"HTTP {response.getcode()} response received.")

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

    if is_terminal:
        print("\nDownload complete.")
    else:
        print("Download complete.")

    # Reset the BytesIO object to the beginning for further processing.
    data.seek(0)

    return data


def extract_discord_icon(tar_data: io.BytesIO, discord_png_path: Path) -> io.BytesIO:
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
            raise Exception(f"Error: {discord_png_path} was not found in archive!")

        # Extract the raw bytes.
        discord_png_data = discord_png.read()
        print(
            f'Found "{discord_png_path.name}". File Size: {convert_bytes_to_string(len(discord_png_data))}.'
        )

        return io.BytesIO(discord_png_data)


def get_latest_discord_icon() -> io.BytesIO:
    # Download the latest Discord tar.gz archive.
    # SEE: https://discord.com/download?linux
    discord_tar_url = "https://discord.com/api/download?platform=linux&format=tar.gz"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    print(f'Fetching latest Discord tar.gz archive:\n- "{discord_tar_url}"')
    tar_data = download_with_progress(discord_tar_url, headers)

    # Extract their icon to memory as a file-like object.
    print("")
    discord_png_path = Path("Discord/discord.png")
    discord_png_data = extract_discord_icon(tar_data, discord_png_path)
    print("")

    return discord_png_data


def get_xdg_data_home() -> Path:
    # SEE: https://specifications.freedesktop.org/basedir-spec/latest/#variables
    xdg_data_home: str | None = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home)
    else:
        return Path.home() / ".local/share"


@dataclass
class IconImage:
    """Represents an immutable image."""

    id: str = field(kw_only=True, default="Unknown")
    path: Path | None = field(kw_only=True, default=None)
    raw_bytes: io.BytesIO | None = field(kw_only=True, default=None)
    img: Image.Image | None = field(kw_only=True, default=None)
    _path_suffix: str | None = field(init=False, default=None)
    _is_svg: bool | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        # Ensure that they havent't given us an illegal combination of inputs.
        input_count = 0
        if self.path is not None:
            input_count += 1
        if self.raw_bytes is not None:
            input_count += 1
        if self.img is not None:
            input_count += 1

        if input_count != 1:
            raise ValueError(
                "You must provide exactly one input to IconImage. Either path, raw_bytes or img."
            )

        # Prepare class fields with data from the given constructor inputs.

        # All formats: Read file to raw_bytes, if only given a path.
        if not self.img and not self.raw_bytes and self.path:
            self._load_bytes_from_path()

        # Non-SVG: Load image data with Pillow, if missing.
        if not self.img and not self.is_svg():
            self._load_image_from_bytes()

        # Verify that raw_bytes is non-empty if provided.
        if self.raw_bytes and self.raw_bytes.getbuffer().nbytes <= 0:
            raise ValueError("You have provided an empty raw_bytes image buffer.")

    def get_file_suffix(self) -> str:
        if self._path_suffix is None:
            self._path_suffix = (
                get_file_suffix(self.path) if self.path is not None else ""
            )

        return self._path_suffix

    def is_svg(self) -> bool:
        if self._is_svg is None:
            self._is_svg = False
            if self.path is not None:
                # File path is known, so we should trust the suffix.
                self._is_svg = self.get_file_suffix() == ".svg"
            elif self.raw_bytes is not None:
                # Check the first 4096 raw bytes for the CASE-sensitive `<svg` tag.
                # SEE: https://github.com/file/file/blob/master/magic/Magdir/sgml
                self.rewind_raw_bytes()
                early_bytes = self.raw_bytes.read(4096)
                self._is_svg = b"<svg" in early_bytes

        return self._is_svg

    def get_image_size(self) -> tuple[int, int]:
        # SVG files do not have any fixed dimensions.
        if self.is_svg():
            return (-1, -1)

        # Non-SVG: Attempt to fetch dimensions from Pillow Image.
        if self.img is None:
            raise Exception("IconImage doesn't contain any Image data.")

        width, height = self.img.size

        return (width, height)

    def resize_image_as_copy(
        self,
        icon_size: IconSize,
        resample: Image.Resampling = Image.Resampling.LANCZOS,
    ) -> Image.Image:
        width = icon_size.size
        height = icon_size.size

        if self.is_svg():
            if self.raw_bytes is None:
                raise Exception("IconImage doesn't contain any SVG raw bytes data.")

            # Rasterize to the desired dimensions via CairoSVG.
            # SEE: https://cairosvg.org/documentation/
            self.rewind_raw_bytes()
            rasterized_raw_bytes = io.BytesIO(
                cairosvg.svg2png(
                    file_obj=self.raw_bytes,
                    # "Unsafe": Resolve XML entities and allow very large files.
                    unsafe=True,
                    output_width=width,
                    output_height=height,
                )
            )

            # Load the resulting PNG with Pillow.
            new_img = Image.open(rasterized_raw_bytes)
            new_img.load()

            return new_img
        else:
            # Will automatically throw if the image hasn't been loaded.
            current_width, current_height = self.get_image_size()
            assert self.img is not None

            if current_width == width and current_height == height:
                return self.img.copy()  # Nothing to do. Just copy.
            else:
                return self.img.resize(
                    size=(width, height),
                    resample=resample,
                )

    def rewind_raw_bytes(self) -> None:
        """Seeks to the beginning of the raw_bytes data for processing."""

        if self.raw_bytes is not None:
            self.raw_bytes.seek(0)

    def _load_bytes_from_path(self) -> None:
        """Reads a file from disk into the raw bytes field."""

        if self.path is None:
            raise Exception("IconImage doesn't contain any image path.")

        self.raw_bytes = io.BytesIO(self.path.read_bytes())

    def _load_image_from_bytes(self) -> None:
        """Parses the raw byte data as a Pillow image."""

        if self.is_svg():
            raise Exception("Raw SVG data cannot be loaded as an Image.")

        if self.raw_bytes is None:
            raise Exception("IconImage doesn't contain any raw bytes data.")

        # Attempt to parse the raw bytes with Pillow. Throws if invalid format.
        self.rewind_raw_bytes()
        with Image.open(self.raw_bytes) as img:
            img.load()  # Force immediate loading.

            self.img = img


# Load the icon from the user's chosen source.
try:
    settings = convert_args_to_settings()

    # Retrieve the chosen image.
    icon_image = (
        IconImage(id=f'Custom Icon ("{settings.icon_path}")', path=settings.icon_path)
        if settings.icon_path
        else IconImage(id="Official Discord Icon", raw_bytes=get_latest_discord_icon())
    )
    print(f"Loaded Icon:\n- Source: {icon_image.id}")
    original_width, original_height = icon_image.get_image_size()
    human_size = (
        "Scalable Vector Graphics"
        if icon_image.is_svg()
        else f"{original_width}x{original_height}"
    )
    print(f"- Input Size: {human_size}")

    # Verify that it's a square image, since we'll be scaling it to the target
    # dimensions, and it will look awful and stretched if it's not a square.
    # NOTE: We don't check SVGs, since they do pixel-perfect scaling, and we cannot
    # retrieve their default dimensions anyway since there are no such SVG libraries.
    if not icon_image.is_svg() and (original_width != original_height):
        raise Exception(f"Icon dimensions are not square ({human_size}).")
except Exception as e:
    print(f"Error: {e}")
    exit(1)


# We will install the icons into the default "hicolor" theme.
# NOTE: All other correctly implemented Linux icon themes are derived from it.
# NOTE: We'll see the custom icon in the desktop environment launcher and dock.
# The window icon of the running Vesktop app (visible in GNOME Overview) will
# also be replaced, since it's actually loaded from the icon theme rather than
# being an internal part of Vesktop's app bundle.
xdg_data_home = get_xdg_data_home()
icon_theme_name = "hicolor"
icon_theme_dir = xdg_data_home / f"icons/{icon_theme_name}"
icon_context = "apps"  # Used for overriding app icons.
target_icon_name: str = settings.name  # Named icon identifier to override.
target_icon_name_titlecase = target_icon_name.title()

print(f"\nSaving new {target_icon_name_titlecase} app icons to disk:")
installed_icons: list[Path] = []
try:
    for icon_size in settings.icon_sizes:
        # Determine the directory name of the icon size we'll be using.
        # NOTE: Icons must always be square (such as "32x32").
        # NOTE: "scalable" is used for ".svg" icons.
        icon_size_name = icon_size.get_name()

        # Calculate the final icon path and filename.
        icon_parent_dir = icon_theme_dir / f"{icon_size_name}/{icon_context}"
        icon_target_file = icon_parent_dir / f"{target_icon_name}.png"

        # Generate an icon at the correct dimensions.
        # NOTE: Some DEs will not try to scale them, so we must pre-scale.
        scaled_icon_img = icon_image.resize_image_as_copy(icon_size)

        # Install the icon, unless this is a simulated run.
        print(f'- "{icon_target_file}"')
        if not settings.simulate:
            icon_parent_dir.mkdir(0o755, parents=True, exist_ok=True)
            if not icon_parent_dir.is_dir():
                raise Exception(
                    f'Failed to create icon directory at "{icon_parent_dir}".'
                )

            with icon_target_file.open("wb") as f:  # Overwrites if target exists.
                scaled_icon_img.save(
                    f,
                    "PNG",
                    # PNG options.
                    # SEE: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#png-saving
                    optimize=True,
                    compress_level=9,
                )

        installed_icons.append(icon_target_file)
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# We now need to alert the system that the icon theme has changed.
# NOTE: We don't bother disabling this during simulations, since it's harmless.
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
# NOTE: We write them even during simulations, for easy reference.
cmd_remove_icons = "\n".join(
    [f'rm -fv "{icon_target_file}"' for icon_target_file in installed_icons]
)
removal_msg = (
    f"If you ever want to remove the custom {target_icon_name_titlecase} icons for some reason, simply execute the following commands:\n\n"
    f"{cmd_remove_icons}\n"
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
    f"If you're on GNOME, opening the Activities Overview and searching for {target_icon_name_titlecase} seems to help it detect the change a bit faster.\n\n"
    f"The new app icon will remain active forever, even after future {target_icon_name_titlecase} app updates!\n\n"
    "You will never need to run this patcher again!"
)

if settings.simulate:
    print("\n[This was a simulated run. Icons have not been written to disk.]")
