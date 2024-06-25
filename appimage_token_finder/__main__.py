from dissect.squashfs import SquashFS

import os
import zlib
from bisect import bisect_right

# This script can find addresses of an individual zlib block inside an
# AppImage, useful for grabbing just those bytes of the AppImage via an HTTP
# range request and extracting something from them, e.g. for dynamically
# extracting an API key from a proprietary AppImage.

# Must be in your current working directory
APPIMAGE_FILENAME = "Example-0.198.1-21.AppImage"

# Path to your interesting file in the squashfs
INTERESTING_FILE = "/resources/app/dist/desktop/desktop.js"

# Fill in the offset of the squashfs filesystem inside the AppImage. You can
# find this by running `binwalk` on the AppImage. I'm too lazy to automate this
# because of https://github.com/ReFirmLabs/binwalk/issues/352. 
APPIMAGE_SQUASHFS_OFFSET = 188392

PRECEDING_INTERESTING = b"\"exampleCoreApiKey\":\""
SUCCEEDING_INTERESTING = b"\""

if __name__ == "__main__":
    squashfs_filename = "squashfs.img"

    # Extract the squashfs from the appimage
    with open(APPIMAGE_FILENAME, "rb") as appimage_handle, open(squashfs_filename, "wb") as squashfs_handle:
        appimage_handle.seek(APPIMAGE_SQUASHFS_OFFSET)
        appimage_bytes = appimage_handle.read()
        squashfs_handle.write(appimage_bytes)

    with open(squashfs_filename, "rb") as squashfs_handle:
        fs = SquashFS(squashfs_handle)
        inode = fs.get(INTERESTING_FILE)
        interesting_stream = inode.open()
        interesting_file_bytes = interesting_stream.read()

        # Find the location of the interesting bytes (including the preceding, surrounding bytes) within the interesting file
        interesting_start_offset = interesting_file_bytes.index(PRECEDING_INTERESTING)
        interesting_end_offset = interesting_file_bytes.index(SUCCEEDING_INTERESTING, interesting_start_offset) + 1

        # This logic comes from https://github.com/fox-it/dissect.squashfs/blob/a8e88c35853d0fecbead699cc8bbd97ee2d9a945/dissect/squashfs/squashfs.py#L453
        block_start_offset = interesting_start_offset // interesting_stream.block_size
        block_end_offset = interesting_end_offset // interesting_stream.block_size
        if block_start_offset != block_end_offset:
            raise ValueError("Start and end of API key string are in different blocks, this script currently cannot handle this case!")
        block_offset = block_start_offset

        run_idx = bisect_right(interesting_stream._runlist_offsets, block_offset)
        SQUASHFS_COMPRESSED_BIT_BLOCK = (1 << 24)
        start_block = inode.header.start_block + sum(
            v & ~SQUASHFS_COMPRESSED_BIT_BLOCK for v, _ in interesting_stream.runlist[:run_idx]
        )
        run_block_size, _ = interesting_stream.runlist[run_idx]

        appimage_block_start = APPIMAGE_SQUASHFS_OFFSET + start_block
        print(f"zlib block containing interesting bytes starts at {appimage_block_start} and has size {run_block_size} in {APPIMAGE_FILENAME}")
