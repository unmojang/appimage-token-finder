# appimage-token-finder

This script can find addresses of an individual zlib block inside an
AppImage, useful for grabbing just those bytes of the AppImage via an HTTP
range request and extracting something from them, e.g. for dynamically
extracting an API key from a proprietary AppImage.

To get started, edit `appimage_token_finder/__main__.py` and place the AppImage in your current working directory. Then:

```
nix develop
poetry run python -m appimage_token_finder
```
