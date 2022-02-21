NAME = gikkon
CON_NAME = config.toml

SRC_PATH = src
SYS_PATH = /usr/bin
CON_PATH = $${HOME}/.config/$(NAME)
TGT_PATH = target

update:
	poetry update
	poetry export --without-hashes > requirements.txt

build:
	$(eval tmp_dir := $(shell mktemp -d --suffix="_gikkon"))
	cp $(SRC_PATH)/*.py $(tmp_dir)
	python -m pip install --upgrade -r requirements.txt --target $(tmp_dir)
	
	mkdir -p $(TGT_PATH)
	python -m zipapp -o $(NAME) -p "/usr/bin/env python" $(tmp_dir)
	mv $(NAME) $(TGT_PATH)
	chmod +x $(TGT_PATH)/$(NAME)

	rm -r $(tmp_dir)

install:
	mkdir -p $(CON_PATH)
	test -f $(CON_PATH)/$(CON_NAME) || cp ./$(CON_NAME) $(CON_PATH)
	sudo install $(TGT_PATH)/$(NAME) $(SYS_PATH)

clean:
	poetry env remove $(shell python --version | sed 's/^Python //' | sed 's/\.[0-9]\+//2')
	rm requirements.txt


all: update build install clean
