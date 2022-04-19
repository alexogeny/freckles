# remove libreoffice from pop!_os/ubuntu since I have no need for office software
sudo apt remove --purge libreoffice* && sudo apt clean && sudo apt autoremove
# removes a few more related packages
sudo apt remove --purge fonts-noto

# remove unused locales
sudo apt install localepurge
# removes generated locales that are not "en"
sudo rm -rI /usr/share/local/!(en)

# vscode extensions
while read line; do code --install-extension "$line";done <vscode/extensions.txt
