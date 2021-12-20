NAME = gikkon
CON_NAME = config.toml

SRC_PATH = src
DEP_PATH = $(SRC_PATH)/dependencies
SYS_PATH = /usr/bin
CON_PATH = $${HOME}/.config/$(NAME)
TGT_PATH = target

update:
	poetry shell
	poetry update
	poetry export --without-hashes > requirements.txt
	python -m pip install --upgrade -r requirements.txt --target $(DEP_PATH)

build: update
	$(eval tmp_dir := $(shell mktemp -d --suffix="_gikkon"))
	cp $(SRC_PATH)/*.py $(tmp_dir)
	cp -r $(DEP_PATH)/* $(tmp_dir)
	
	mkdir -p $(TGT_PATH)
	python -m zipapp -o $(NAME) -p "/usr/bin/env python" $(tmp_dir)
	mv $(NAME) $(TGT_PATH)
	chmod +x $(TGT_PATH)/$(NAME)

	rm -r $(tmp_dir)

install: build
	mkdir -p $(CON_PATH)
	test -f $(CON_PATH)/$(CON_NAME) || cp ./$(CON_NAME) $(CON_PATH)
	sudo cp $(TGT_PATH)/$(NAME) $(SYS_PATH)