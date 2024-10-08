#include "Program.h"

using namespace Program;

int getLocalIP()
{
	int loopbackSocket = socket(PF_INET, SOCK_DGRAM, 0);
    if (loopbackSocket == -1)
	{
        std::cout << "Socket creation error" << std::endl;
        return 1;
    }

	sockaddr_in loopbackAddr;
    memset(&loopbackAddr, 0, sizeof(loopbackAddr));
    loopbackAddr.sin_family = AF_INET;
    loopbackAddr.sin_addr.s_addr = 3000;	// IP address doesn't matter (will be overridden)
    loopbackAddr.sin_port = htons(9);		// Debug port
	socklen_t loopbackAddrLen = sizeof(loopbackAddr);
	
	int connectResult = connect(loopbackSocket, reinterpret_cast<sockaddr*>(&loopbackAddr), sizeof(loopbackAddr));
    if (connectResult == -1)
	{
        close(loopbackSocket);
        std::cout << "Connection error" << std::endl;
        return 1;
    }

    int socketNameResult = getsockname(loopbackSocket, reinterpret_cast<sockaddr*>(&loopbackAddr), &loopbackAddrLen);
    if (socketNameResult == -1)
	{
        close(loopbackSocket);
        std::cout << "Socket name retrieval error" << std::endl;
        return 1;
    }

    close(loopbackSocket);

    char buffer[INET_ADDRSTRLEN];
    if (inet_ntop(AF_INET, &loopbackAddr.sin_addr, buffer, INET_ADDRSTRLEN) == 0x0)
	{
        std::cout << "Address decoding error" << std::endl;
        return 1;
    }
    else
	{
		std::string bufferString(buffer); 
		::localIP = bufferString;
    }
    
    return 0;
}

void getUserInput()
{
	////////////////////////////////////////
	// DEVELOPMENT CODE (start)
	// This is used for speed/convenience during development
	// ::localModel = "Device";
	// ::localSerial = "1";
	// ::localPort = "8080";
	// DEVELOPMENT CODE (end)
	////////////////////////////////////////
	// PRODUCTION CODE (start)
	std::cout << std::endl << "Enter details for the test device:" << std::endl;
	std::cout << "Device Model: ";
	std::getline(std::cin, ::localModel);
	std::cout << "Serial Number: ";
	std::getline(std::cin, ::localSerial);
	::localPort = "-1";	// Uninitialised
	while (std::stoi(::localPort) < ::MIN_PORT || std::stoi(::localPort) > ::MAX_PORT)
	{
		std::cout << "Port Number (" << std::to_string(::MIN_PORT)
					<< "-" << std::to_string(::MAX_PORT) << "): ";
		std::getline(std::cin, ::localPort);
		if (std::stoi(::localPort) < ::MIN_PORT || std::stoi(::localPort) > ::MAX_PORT)
		{
			std::cout << "*** Port number is outside valid range - please try again ***" << std::endl;
		}
	}
	// PRODUCTION CODE (end)
	////////////////////////////////////////
	
	::IDMessage = "ID;MODEL=" + ::localModel + ";Serial=" + ::localSerial + ";";
	std::cout << std::endl << "Activating connection for " << ::localModel
				<< " (Serial Number: " << ::localSerial << ")..." << std::endl;
}

std::string getMessageValue(std::string message, std::string value)
{
	int start = message.find(value) + value.length();
	int end;
	for (end = start; end < message.length(); end++)
	{
		if (message[end] == ::MSG_DELIMITER_CHAR) { break; }
	}
	int count = end - start;
	return message.substr(start, count);
}

void sendMessage(std::string message)
{
	int result = sendto(serverSocket, message.c_str(), strlen(message.c_str()), 0,
							(sockaddr*)&::clientAddr, sizeof(::clientAddr));
	if (result == SO_ERROR)
	{
		coutLock.lock();
		std::cout << std::endl << "Error sending message" << std::endl;
		coutLock.unlock();
	}
	// std::cout << "Message sent: " << message << std::endl;
}

/*
 * Duration: Measured in milliseconds
 * Rate: Measured in milliseconds
 */
void sendStatusMessages(int duration, int rate)
{
	statusLock.lock();
	::status = ::STARTED;
	statusLock.unlock();
	for (int i = 0; i <= duration; i += rate)
	{
		statusLock.lock();
		if (::status == ::CANCELLED) {
			statusLock.unlock();
			break;
		}
		statusLock.unlock();
		int mv = rand() % SIGNAL_LIMIT;
		int ma = rand() % SIGNAL_LIMIT;
		std::string message = "STATUS;TIME=" + std::to_string(i) +
								";MV=" + std::to_string(mv) +
								";MA=" + std::to_string(ma) + ";";
		::sendMessage(message);
		std::this_thread::sleep_for(std::chrono::milliseconds(rate));	// Simulates device polling delay
	}
	statusLock.lock();
	::status = ::STOPPED;
	statusLock.unlock();
}

void processReceivedMsgs()
{
	while (true)
	{
		if (::receivedMsgs.size() > 0)
		{
			::processing = true;
			msgLock.lock();
			std::string message = ::receivedMsgs.front();
			::receivedMsgs.pop_front();
			msgLock.unlock();
			std::string msgType;
			if (message.find(::MSG_DELIMITER) == std::string::npos)
			{
				msgType = message;
			}
			else
			{
				int start = 0;
				int count = message.find(::MSG_DELIMITER);
				msgType = message.substr(start, count);
			}
			
			// Triage message types
			if (msgType == "ID")
			{
				::sendMessage(::IDMessage);
			}
			else if (msgType == "TEST")
			{
				std::string msgCommand = ::getMessageValue(message, ::VAL_CMD);
				
				if (msgCommand == "START")
				{
					statusLock.lock();
					if (::status == ::STARTED)
					{
						statusLock.unlock();
						std::string errorMsg = "TEST;RESULT=ERROR;MSG=Test was already started";
						::sendMessage(errorMsg);
					}
					else
					{
						coutLock.lock();
						std::cout << "Running test..." << std::endl;
						coutLock.unlock();
						statusLock.unlock();
						::sendMessage(::MSG_STARTED);
						int duration = std::stoi(::getMessageValue(message, ::VAL_DURATION));
						int rate = std::stoi(::getMessageValue(message, ::VAL_RATE));
						std::thread statusMessagesThread(::sendStatusMessages, duration, rate);
						std::thread processingThread2(::processReceivedMsgs);
						statusMessagesThread.join();
						statusLock.lock();
						if (::status == ::STOPPED)	// Don't do this if the test was cancelled by the interface
						{
							statusLock.unlock();
							::sendMessage(::MSG_STOPPED);
							coutLock.lock();
							std::cout << "Finished sending test data!" << std::endl;
							coutLock.unlock();
						}
						statusLock.unlock();
						processingThread2.join();
					}
					
				}
				else if (msgCommand == "STOP")
				{
					statusLock.lock();
					if (::status == ::CANCELLED)
					{
						statusLock.unlock();
						std::string errorMsg = "TEST;RESULT=ERROR;MSG=Test was already stopped";
						::sendMessage(errorMsg);
					}
					else
					{
						::status = ::CANCELLED;
						if (::status == ::STOPPED)
						{
							statusLock.unlock();
							coutLock.lock();
							std::cout << std::endl << "Cancel command received - stopping test" << std::endl;
							coutLock.unlock();
							::sendMessage(::MSG_STOPPED);
						}
						else { statusLock.unlock(); }	// Both separate branches must unlock the Mutex
					}
				}
			}
			else
			{
				// Do nothing
			}
			::processing = false;
		}
		else
		{
			std::this_thread::sleep_for(std::chrono::milliseconds(10));
		}
	}
}

void listenForMsgs()
{
	while (true)
	{
		::listening = true;
		coutLock.lock();
		std::cout << std::endl << "*** Device connection open - ready for transmission ***" << std::endl 
								<< "Model Name: "	 << ::localModel << std::endl
								<< "Serial Number: " << ::localSerial << std::endl
								<< "IP Address: " 	 << ::localIP   << std::endl
								<< "Port Number: "	 << ::localPort << std::endl
								<< "*** (Press Ctrl+C to terminate the program) ***" << std::endl << std::endl;
		coutLock.unlock();
		int receivedBytes = ::recvfrom(serverSocket, msgBuffer, sizeof(msgBuffer), 0,
								(struct sockaddr *)(&::clientAddr), &::clientAddrLen);
		if (receivedBytes > 0)
		{
			std::string receivedMsg((char*) msgBuffer);
			// std::cout << "Message received: " << receivedMsg << std::endl;
			msgLock.lock();
			::receivedMsgs.push_back(receivedMsg);
			msgLock.unlock();
			memset(&::msgBuffer, 0, sizeof(::msgBuffer));
		}
		else if (receivedBytes < 0)
		{
			int error = errno;
			coutLock.lock();
			std::cout << "Error: " << error << std::endl;
			coutLock.unlock();
			::close(serverSocket);
			exit(1);
		}
		else	// receivedBytes == 0
		{
			coutLock.lock();
			std::cout << "Empty message received" << std::endl;
			coutLock.unlock();
		}
		::listening = false;
		std::this_thread::sleep_for(std::chrono::milliseconds(10));
	}
}

int openConnection()
{
	std::string deviceIP			= ::localIP;
	std::string devicePortString	= ::localPort;
	int devicePortInt				= std::stoi(devicePortString);
	
	// Create socket
    serverSocket = ::socket(AF_INET, SOCK_DGRAM, 0);
	if (serverSocket < 0)
	{
        std::cout << "Error creating socket" << std::endl;
        return 1;
	}
	
	// Create server address
	memset(&::serverAddr, 0, sizeof(::serverAddr));
    ::serverAddr.sin_family = AF_INET;
	::serverAddr.sin_port = htons(devicePortInt);
	::serverAddr.sin_addr.s_addr = inet_addr(deviceIP.c_str());
	::serverAddrLen = sizeof(::serverAddr);
	
	// Create client address
	memset(&::clientAddr, 0, sizeof(::clientAddr));
	::clientAddr.sin_family = AF_INET;
	::clientAddr.sin_port = htons(9080);						// Doesn't matter (will be overridden upon receipt)
	::clientAddr.sin_addr.s_addr = inet_addr("192.168.1.2");	// Doesn't matter (will be overridden upon receipt)
	::clientAddrLen = sizeof(::clientAddr);
	
	// Bind socket to server address object
	int errorCode = bind(serverSocket, (struct sockaddr *) &::serverAddr, sizeof(::serverAddr));
    if (errorCode < 0)
	{
    	std::cout << "Error binding socket" << std::endl;
    	return 1;
    }

	return 0;
}

int main(int argc, char const *argv[])
{	
	::getLocalIP();
	::getUserInput();
	::openConnection();

	std::thread listeningThread(::listenForMsgs);
	std::thread processingThread(::processReceivedMsgs);
	listeningThread.join();
	processingThread.join();

	::close(serverSocket);
	
    return 0;
}