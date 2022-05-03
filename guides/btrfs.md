# installing linux with luks, lvm, and btrfs

## step 1 - boot

boot onto the usb media and then

```bash
sudo -i
```

## step 2 - partitioning, luks, lvm, btrfs

`lsblk` to show disks

look for the install media

partition layout will look like:

1. 512MiB bootloader partition (efi)
2. luks2 encrypted partition of the remaining space

won't use swap as we have lots of memory

won't use backup as everything I need to back up is either in git or on my nas

```shell
parted /dev/sda mklabel gpt # confirm yes
parted /dev/sda mkpart primary fat32 1MiB 512MiB
parted /dev/sda mkpart primary 513MiB 100%
parted /dev/sda name 1 EFI
parted /dev/sda name 2 POPOS
parted /dev/sda set 1 esp on
parted /dev/sda unit MiB print

# Number  Start    End        Size       File system  Name      Flags
#  1      1.00MiB  512MiB     511MiB     fat32        EFI       boot, esp
#  2      512MiB   1000MiB    1000MiB                 POPOS
```

### step 2a - luks

```shell
cryptsetup luksFormat /dev/sda2
# WARNING!
# ========
# This will overwrite data on /dev/sda2 irrevocably.
# Are you sure? (Type uppercase yes): YES
# Enter passphrase for /dev/sda2:
# Verify passphrase:
cryptsetup luksOpen /dev/sda2 cryptdata
# Enter passphrase for /dev/sda2:
ls /dev/mapper
# control cryptdata
```

### step2b - lvm

```shell
pvcreate /dev/mapper/cryptdata
# Physical volume "/dev/mapper/cryptdata" successfully created
vgcreate data /dev/mapper/cryptdata
# Volume group "data" successfully created
lvcreate -n root -l 100%FREE data
# Logical volume "root" created.
ls /dev/mapper/
# control cryptdata data-root
cryptsetup luksClose /dev/mapper/data-root
cryptsetup luksClose /dev/mapper/cryptdata
ls /dev/mapper
# control
```

## step 3 - install

Run the pop os installer and choose `Custom (Advanced)`.

1. On the first partition, select: `Use partition` + `Format` + `Boot /boot/efi` + fs `fat32`
2. On the second partition, click it, and `Decrypt` using the password from earlier
3. Select the new `LVM data` line, `use partition`, `format`, `root (/)` and `btrfs`.
4. `Erase and install`.

Do NOT reboot after finishing. Quit the installer.

## step 4 - post install

### step 4a - mounting the root fs

```shell
cryptsetup luksOpen /dev/nvme0n1p4 cryptdata
# Enter passphrase for /dev/nvme0n1p4
mount -o subvolid=5,ssd,noatime,commit=120,compress=zstd:3,discard=async /dev/mapper/data-root /mnt
```

### step 4b - create btrfs subvolumes

```shell
btrfs subvolume create /mnt/@
# Create subvolume '/mnt/@'
cd /mnt
ls | grep -v @ | xargs mv -t @ #move all files and folders to /mnt/@
ls -a /mnt
# . .. @
btrfs subvolume create /mnt/@home
# Create subvolume '/mnt/@home'
mv /mnt/@/home/* /mnt/@home/
ls -a /mnt/@/home
# . ..
ls -a /mnt/@home
# . .. wmutschl

btrfs subvolume list /mnt
# ID 264 gen 339 top level 5 path @
# ID 265 gen 340 top level 5 path @home
```

### step 4c - update fstab

note: update uuid placeholders once I have an example

```shell
sed -i 's/btrfs  defaults/btrfs  defaults,subvol=@,ssd,noatime,space_cache,commit=120,compress=zstd,discard=async/' /mnt/@/etc/fstab
echo "UUID=$(blkid -s UUID -o value /dev/mapper/data-root)  /home  btrfs  defaults,subvol=@home,ssd,noatime,space_cache,commit=120,compress=zstd,discard=async   0 0" >> /mnt/@/etc/fstab

cat /mnt/@/etc/fstab

# PARTUUID=<uuid1>  /boot/efi  vfat  umask=0077  0  0
# UUID=<uuid1>  /  btrfs  defaults,subvol=@,ssd,noatime,commit=120,compress=zstd:3,discard=async  0  0
# UUID=<uuid1> /home btrfs defaults,subvol=@home,ssd,noatime,commit=120,compress=zstd:3,discard=async 0 0
```

Async discard needs addition to crypttab

```shell
sed -i 's/luks/luks,discard/' /mnt/@/etc/crypttab
cat /mnt/@/etc/crypttab
# cryptswap UUID=<uuid> /dev/urandom swap,plain,offset=1024,cipher=aes-xts-plain64,size=512
# cryptdata UUID=<uuid> none luks,discard
```

### step 4d - update bootloader

```shell
mount /dev/nvme0n1p1 /mnt/@/boot/efi
```

Update the current conf to niclude the subvolume

nb again, `<uuid>` here is not literal

```shell
cat /mnt/@/boot/efi/loader/entries/Pop_OS-current.conf
# title Pop!_OS
# linux /EFI/Pop_OS-<uuid>/vmlinuz.efi
# initrd /EFI/Pop_OS-<uuid>/initrd.img
# options root=UUID=<uuid> ro quiet loglevel=0 systemd.show_status=false splash rootflags=subvol=@
```

Add `rootflags=subvol=@` to the user kernel options

```shell
cat /mnt/@/etc/kernelstub/configuration
# ...
#   "user": {
#     "kernel_options": [
#       "quiet",
#       "loglevel=0",
#       "systemd.show_status=false",
#       "splash",
#       "rootflags=subvol=@"
#     ],
# ...
```

### step 4e - update initramfs

first mount the system

```shell
cd /
umount -l /mnt
mount -o defaults,subvol=@,ssd,noatime,commit=120,compress=zstd:3,discard=async /dev/mapper/data-root /mnt
for i in /dev /dev/pts /proc /sys /run; do mount -B $i /mnt$i; done
chroot /mnt
mount -av
# /boot/efi                : successfully mounted
# none                     : ignored
# /                        : ignored
# /home                    : successfully mounted
```

now update initramfs

```shell
update-initramfs -c -k all
exit
reboot now
```

### step 5 - reboot to main os

after loading, check the following (noting again that `<id>` and `<uuid>` are not literal)

```shell
sudo mount -av
# /boot/efi                : already mounted
# none                     : ignored
# /                        : ignored
# /home                    : already mounted

sudo mount -v | grep /dev/mapper
# /dev/mapper/data-root on / type btrfs (rw,noatime,compress=zstd:3,ssd,discard=async,space_cache=v2,commit=120,subvolid=<id>,subvol=/@)
# /dev/mapper/data-root on /home type btrfs (rw,noatime,compress=zstd:3,ssd,discard=async,space_cache=v2,commit=120,subvolid=<id>,subvol=/@home)
```

if not using my setup script, enable fstrim timer

```shell
sudo systemctl enable fstrim.timer
```

update system and reboot

```shell
sudo apt purge libreoffice*
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
sudo apt autoclean
```
