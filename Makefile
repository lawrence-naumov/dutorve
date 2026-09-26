NAME        := dutorve
VERSION     := 0.1.2
DESCRIPTION := Configure machines with prepared ansible playbooks
MAINTAINER  := Lawrence Naumov <prostolawr@gmail.com>

BUILD_DIR := dist_root
ETC_DIR   := $(BUILD_DIR)/etc/$(NAME)
OPT_DIR   := $(BUILD_DIR)/opt/$(NAME)
BIN_DIR   := $(BUILD_DIR)/usr/bin

SHARE_DIR       := $(BUILD_DIR)/usr/share
BASH_COMPLETION := $(SHARE_DIR)/bash-completion/completions
ZSH_COMPLETION  := $(SHARE_DIR)/zsh/site-functions
FISH_COMPLETION := $(SHARE_DIR)/fish/vendor_completions.d

.PHONY: all clean prep completion deb rpm

all: deb rpm


prep: clean
	@echo "=== Prepare file structure ==="

	mkdir -p $(ETC_DIR)
	mkdir -p $(OPT_DIR)
	mkdir -p $(BIN_DIR)

	cp main.py $(OPT_DIR)/
	cp -r pymodules $(OPT_DIR)/
	cp -r ansible $(OPT_DIR)/

	cp config.toml $(ETC_DIR)/config.toml
	cp inventory.yml $(ETC_DIR)/inventory.yml

	@echo "=== Remove Python cache ==="

	find $(OPT_DIR) -type d -name __pycache__ -prune -exec rm -rf {} +

	@echo "=== Create executable ==="

	printf '%s\n' \
		'#!/bin/bash' \
		'export DUTORVE_ETC_DIR=/etc/$(NAME)' \
		'export DUTORVE_OPT_DIR=/opt/$(NAME)' \
		'exec /usr/bin/python3 -u /opt/$(NAME)/main.py "$$@"' \
		> $(BIN_DIR)/$(NAME)

	chmod +x $(BIN_DIR)/$(NAME)

	$(MAKE) completion


completion:
	@echo "=== Generate shell completions ==="

	mkdir -p $(BASH_COMPLETION)
	mkdir -p $(ZSH_COMPLETION)
	mkdir -p $(FISH_COMPLETION)

	python3 -m pymodules.completion \
		$(BUILD_DIR)/generated-completion

	cp $(BUILD_DIR)/generated-completion/dutorve.bash \
		$(BASH_COMPLETION)/dutorve

	cp $(BUILD_DIR)/generated-completion/_dutorve \
		$(ZSH_COMPLETION)/_dutorve

	cp $(BUILD_DIR)/generated-completion/dutorve.fish \
		$(FISH_COMPLETION)/dutorve.fish

	rm -rf $(BUILD_DIR)/generated-completion


deb: prep
	@echo "=== Build deb package ==="

	fpm -s dir -t deb \
		-n "$(NAME)" \
		-v "$(VERSION)" \
		--maintainer "$(MAINTAINER)" \
		--description "$(DESCRIPTION)" \
		--architecture "all" \
		-d "python3" \
		-d "python3-yaml" \
		-d "python3-click" \
		-d "bash-completion" \
		--config-files "etc/$(NAME)/config.toml" \
		--config-files "etc/$(NAME)/inventory.yml" \
		-C $(BUILD_DIR) .


rpm: prep
	@echo "=== Build rpm package ==="

	fpm -s dir -t rpm \
		-n "$(NAME)" \
		-v "$(VERSION)" \
		--maintainer "$(MAINTAINER)" \
		--description "$(DESCRIPTION)" \
		--architecture "noarch" \
		-d "python3" \
		-d "python3-pyyaml" \
		-d "python3-click" \
		-d "bash-completion" \
		--config-files "etc/$(NAME)/config.toml" \
		--config-files "etc/$(NAME)/inventory.yml" \
		-C $(BUILD_DIR) .


clean:
	@echo "=== Clean temporary files ==="

	rm -rf $(BUILD_DIR)

