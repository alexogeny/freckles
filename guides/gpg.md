# signing git commits with gpg

## step 1 - generate keypair

```shell
gpg --full-generate-key
1 # rsa/rsa key type
4096 # bit length
0 # no expire
alexogeny # name
<private github email> # email address for signing
github pgp key # human readable
```

Enter a secure passphrase (ideally generated from password manager) and store it in your vault for reuse

## step 2 - export keypair

```shell
gpg --list-secret-keys --keyid-format LONG
```

copy the long key id then replace `<id>` below

```shell
gpg --export -a <id> > public.asc
gpg --export-secret-key -a <id> > private.asc
```

Store these in your vault alongside the passphrase for later access

## step 3 - use the key to sign commits

I have this in my git config, but to set manually

```shell
git config --global user.signingkey <id>
git config --global commit.gpgsign true
```

To check a commit you made has a signature, do

```shell
git log --show-signature
```

## step 4 - put the PUBLIC key on github/lab

copy the contents of the PUBLIC key and paste on your git provider

it should start with

```plain
----BEGIN PGP PUBLIC KEY BLOCK-----
```

## step 5 - importing on another system

download the public and private .asc files from your vault

```shell
gpg --import my-key-public.asc
gpg --import my-key-private.asc
gpg --list-secret-keys --keyid-format LONG
```

copy the private key and trust it:

```shell
gpg --edit-key <id>
trust # trust the key
5 # give it ultimate trust
quit # leave the program
```
