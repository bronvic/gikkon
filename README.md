# Gikkon
Automate saving configs into git repository. Here and below *git repo* means you local copy of git repository with backup copies of files

[![coverage](https://codecov.io/gh/bronvic/gikkon/branch/main/graph/badge.svg?token=FLC476YZTB)](https://codecov.io/gh/bronvic/gikkon)

# Usage
* List files under gikkon control
```
gikkon list
```
* Add new file under backup control
```
gikkon add <fname>
```
* Copy changed in the host system files into git repo and push changes
```
gikkon backup
```
* Commit changes in git repo to the remote server
```
gikkon commit
```

See `gikkon --help` or `gikkon <command> --help` for more detailes

# Requirements
* python >= 3.7
* poetry >= 1.0

# Installation
* Simply run `make all`
* **Change `path` in config file (`$HOME/.config/gikkon/config.toml` by defalt) to path to your git repo for backups**

There is a [package](https://aur.archlinux.org/packages/gikkon/) for lucky Arch users

# See my config repo =^.^=
https://github.com/bronvic/config

And father of gikkon: https://github.com/bronvic/config/blob/c5a8a8ea9a0628638f1a1c4b828b91c5eae4e6fe/backup.sh
