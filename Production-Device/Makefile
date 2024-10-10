########################################
# NEW VERSION

# TODO: Fix this new version
# Changes from Old Version:
#     * Different folders for different file types
#     * Placeholders used for base directory names

SOURCE_DIR = Src
OBJECT_DIR = Obj
BINARY_DIR = Bin

# all: Program

$(OBJECT_DIR)/Program.o: $(SOURCE_DIR)/Program.cpp
	g++ -c $(SOURCE_DIR)/Program.cpp
	
$(BINARY_DIR)/Program: $(OBJECT_DIR)/Program.o
	g++ -o $(BINARY_DIR)/Program $(OBJECT_DIR)/Program.o

########################################
# OLD VERSION

# all: Program

# Program.o: Program.cpp
# 	g++ -c Program.cpp
	
# Program: Program.o
# 	g++ -o Program Program.o
########################################