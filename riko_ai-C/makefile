# Makefile — Riko AI C GUI
# Usage:
#   make          → build
#   make run      → build then launch
#   make clean    → remove binary

CC      = gcc
TARGET  = riko_gui
SRC     = gui.c
PKGS    = gtk4 json-glib-1.0
CFLAGS  = $(shell pkg-config --cflags $(PKGS)) -Wall -Wextra -O2 -Wno-deprecated-declarations
LDFLAGS = $(shell pkg-config --libs   $(PKGS))

.PHONY: all run clean install-deps

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LDFLAGS)
	@echo "✅ Build complete: ./$(TARGET)"

run: all
	./$(TARGET)

clean:
	rm -f $(TARGET)

install-deps:
	@echo "Installing dependencies (Arch Linux)..."
	sudo pacman -S --needed gtk4 json-glib
