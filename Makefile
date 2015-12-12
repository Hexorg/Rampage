CPPFLAGS = -O0 -g

CC = g++

BUILD_DIR = build
OBJ_DIR = $(BUILD_DIR)/obj
SRC_DIR = src

SOURCES = $(wildcard $(SRC_DIR)/*.cpp)
OBJECTS = $(addprefix $(OBJ_DIR)/, $(notdir $(SOURCES:.cpp=.o)))

all: prep build

prep:
	mkdir -p $(BUILD_DIR)
	mkdir -p $(OBJ_DIR)

build:	$(BUILD_DIR)/Rampage

$(BUILD_DIR)/Rampage: $(OBJECTS)
	$(CC) $(CPPFLAGS) $^ -o $@

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp
	$(CC) -c $(CPPFLAGS) $< -o $@
