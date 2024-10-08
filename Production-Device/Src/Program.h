#include <arpa/inet.h>
#include <chrono>
#include <errno.h>
#include <iostream>
#include <list>
#include <mutex>
#include <netinet/in.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <thread>
#include <unistd.h>
#include <vector>

namespace Program {
	////////////////////////////////////////
	// FUNCTIONS
	int getLocalIP();
	void getUserInput();
	void sendStatusMessages(int duration, int rate);
	std::string getMessageValue(std::string message, std::string value);
	void sendMessage();
	void processReceivedMsgs();
	void listenForMsgs();
	int openConnection();
	////////////////////////////////////////
	// GENERAL SETTINGS
	const int BUFFER_SIZE						= 1024;
	const int SIGNAL_LIMIT						= 1000;
	const int MIN_PORT							= 1024;
	const int MAX_PORT							= 65535;
	////////////////////////////////////////
	// CONSTANT MESSAGE VALUES
	const std::string MSG_DELIMITER 			= ";";
	const char MSG_DELIMITER_CHAR 				= ';';
	const std::string VAL_CMD  					= "CMD=";
	const int VAL_CMD_LEN						= 4;
	const std::string VAL_DURATION				= "DURATION=";
	const int VAL_DURATION_LEN					= 9;
	const std::string VAL_RATE					= "RATE=";
	const int VAL_RATE_LEN						= 5;
	const std::string MSG_STARTED				= "TEST;RESULT=STARTED;";
	const std::string MSG_STOPPED				= "TEST;RESULT=STOPPED;";
	////////////////////////////////////////
	// DYNAMIC MESSAGE VALUES
	std::string IDMessage;
	char* msgBuffer[Program::BUFFER_SIZE];
	////////////////////////////////////////
	// MESSAGING DATA STRUCTURES
	std::list<std::string> receivedMsgs;
	std::mutex msgLock;
	std::mutex coutLock;	// Keeps terminal messages tidy; Only needed after first multithreading fork
	////////////////////////////////////////
	// STATE VALUES
	const std::string STARTED					= "STARTED";
	const std::string STOPPED					= "STOPPED";
	const std::string CANCELLED					= "CANCELLED";
	/*
	 * Valid values for status:
	 * 
	 * STARTED
	 * STOPPED
	 * ----------------------------------------
	 * NB: These must also be defined as constants
	 */
	std::string status							= Program::STOPPED;
	std::mutex statusLock;
	bool listening								= false;
	bool processing								= false;
	////////////////////////////////////////
	// SOCKET VALUES
	int serverSocket;
	struct sockaddr_in serverAddr;
	socklen_t serverAddrLen;
	struct sockaddr_in clientAddr;
	socklen_t clientAddrLen;
	////////////////////////////////////////
	// DEVICE VALUES
	std::string localModel;
	std::string localSerial;
	std::string localIP;
	std::string localPort;
	////////////////////////////////////////
}