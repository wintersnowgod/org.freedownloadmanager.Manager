# org.freedownloadmanager.Manager  
Unofficial Flatpak Package of FreeDownloadManager.  
NOTE: This wrapper is not verified by, affiliated with, or supported by FreeDownloadManager Team.  

### Building Instructions:-  
For use of system-wide flatpak dependencies while building:  
```
git clone https://github.com/wintersnowgod/org.freedownloadmanager.Manager.git
cd org.freedownloadmanager.Manager
flatpak-builder --install-deps-from=flathub --force-clean --repo=.repo .build-dir org.freedownloadmanager.Manager.yaml
flatpak build-bundle .repo org.freedownloadmanager.Manager.flatpak org.freedownloadmanager.Manager --runtime-repo=https://flathub.org/repo/flathub.flatpakrepo
```
For use of user flatpak dependencies while building:  
```
git clone https://github.com/wintersnowgod/org.freedownloadmanager.Manager.git
cd org.freedownloadmanager.Manager
flatpak-builder --user --install-deps-from=flathub --force-clean --repo=.repo .build-dir org.freedownloadmanager.Manager.yaml
flatpak build-bundle .repo org.freedownloadmanager.Manager.flatpak org.freedownloadmanager.Manager --runtime-repo=https://flathub.org/repo/flathub.flatpakrepo
```
  
### Downloads  
.flatpak bundle is available in releases for download.  
  
### Install
first `cd` into the dir containing the .flatpak file and  
  
For system-wide installation:  
`flatpak install org.freedownloadmanager.Manager.flatpak --system`  

For user flatpak installation:  
`flatpak install org.freedownloadmanager.Manager.flatpak --user`  
