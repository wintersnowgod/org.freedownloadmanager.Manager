# org.freedownloadmanager.Manager
  
### Building Instructions:-  
```
git clone https://github.com/wintersnowgod/org.freedownloadmanager.Manager.git
cd org.freedownloadmanager.Manager
flatpak-builder --install-deps-from=flathub --force-clean --repo=.repo .build-dir org.freedownloadmanager.Manager.yaml
flatpak build-bundle .repo org.freedownloadmanager.Manager.flatpak org.freedownloadmanager.Manager --runtime-repo=https://flathub.org/repo/flathub.flatpakrepo
```
### Downloads
.flatpak bundle is available in releases for download.
