tbell config
systemctl --user start telegram_bell
systemctl --user daemon-reload
systemctl --user enable telegram_bell
loginctl enable-linger