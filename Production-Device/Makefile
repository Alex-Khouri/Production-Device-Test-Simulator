SOURCE_DIR = Src
OBJECT_DIR = Obj
BINARY_DIR = Bin

all: $(BINARY_DIR)/Program

$(OBJECT_DIR)/Program.o: $(SOURCE_DIR)/Program.cpp
	g++ -c $(SOURCE_DIR)/Program.cpp -o $(OBJECT_DIR)/Program.o
	
$(BINARY_DIR)/Program: $(OBJECT_DIR)/Program.o
	g++ $(OBJECT_DIR)/Program.o -o $(BINARY_DIR)/Program