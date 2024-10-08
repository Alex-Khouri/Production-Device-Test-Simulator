SOURCE_DIR = Src
OBJECT_DIR = Obj
BINARY_DIR = Bin

# all: Program

# TODO: Fix this file

$(OBJECT_DIR)/Program.o: $(SOURCE_DIR)/Program.cpp
	g++ -c $(SOURCE_DIR)/Program.cpp
	
$(BINARY_DIR)/Program: $(OBJECT_DIR)/Program.o
	g++ -o $(BINARY_DIR)/Program $(OBJECT_DIR)/Program.o

########################################
# all: Program

# Program.o: Program.cpp
# 	g++ -c Program.cpp
	
# Program: Program.o
# 	g++ -o Program Program.o
########################################