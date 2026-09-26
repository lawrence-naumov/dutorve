NAME          := dutorve
VERSION       := 0.1.0
DESCRIPTION   := Configure machines with prepared ansible playbooks
MAINTAINER    := Lawrence Naumov <prostolawr@gmail.com>

BUILD_DIR     := dist_root
ETC_DIR       := $(BUILD_DIR)/etc/$(NAME)
OPT_DIR       := $(BUILD_DIR)/opt/$(NAME)
BIN_DIR       := $(BUILD_DIR)/usr/bin

.PHONY: all clean prep deb rpm

all: deb rpm

prep: clean
	@echo "=== Prepare file structure ==="
	mkdir -p $(ETC_DIR)
	mkdir -p $(OPT_DIR)
	mkdir -p $(BIN_DIR)

	cp main.py $(OPT_DIR)/
	cp -r pymodules/ $(OPT_DIR)/
	cp -r ansible/ $(OPT_DIR)/

	cp config.toml $(ETC_DIR)/config.toml
	cp inventory.yml $(ETC_DIR)/inventory.yml

	@echo '#!/bin/bash' > $(BIN_DIR)/$(NAME)
	@echo 'DUTORVE_ETC_DIR=$(ETC_DIR)' >> $(BIN_DIR)/$(NAME)
	@echo 'DUTORVE_OPT_DIR=$(OPT_DIR)' >> $(BIN_DIR)/$(NAME)
	@echo 'exec /usr/bin/python3 -u /opt/$(NAME)/main.py "$$@"' >> $(BIN_DIR)/$(NAME)
	chmod +x $(BIN_DIR)/$(NAME)

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
		--config-files "etc/$(NAME)/config.toml" \
		--config-files "etc/$(NAME)/inventory.yml" \
		-C $(BUILD_DIR) .

clean:
	@echo "=== Clean temporally files ==="
	rm -rf $(BUILD_DIR)

