#!/bin/bash
# LuxTTS + Whisper MLX Server Uninstaller

INSTALL_DIR="$HOME/luxtts-whisper-server"
LAUNCHD_PLIST="$HOME/Library/LaunchAgents/com.simulacrum.luxtts-whisper.plist"

echo "Uninstalling LuxTTS + Whisper MLX Server..."

# Stop and unload service
if launchctl list | grep -q "com.simulacrum.luxtts-whisper"; then
    echo "Stopping service..."
    launchctl unload "$LAUNCHD_PLIST" 2>/dev/null
fi

# Remove plist
if [ -f "$LAUNCHD_PLIST" ]; then
    echo "Removing LaunchD configuration..."
    rm "$LAUNCHD_PLIST"
fi

# Ask about voices
echo ""
read -p "Remove voices directory ($HOME/voices)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$HOME/voices"
    echo "Voices removed."
else
    echo "Voices preserved at $HOME/voices"
fi

# Remove installation directory
if [ -d "$INSTALL_DIR" ]; then
    echo "Removing installation directory..."
    rm -rf "$INSTALL_DIR"
fi

echo ""
echo "Uninstallation complete."
echo ""
echo "Note: Python packages (mlx-whisper, fastapi, etc.) were NOT removed."
echo "To remove them manually, run:"
echo "  pip3 uninstall mlx-whisper fastapi uvicorn python-multipart soundfile librosa"
