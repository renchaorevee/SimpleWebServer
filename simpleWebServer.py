__author__ = 'renchaorevee'

import SocketServer
import os
import urllib

serverRoot = os.getcwd()

def getServerPathFromFSPath(fsPath):
	absPath = os.path.abspath(fsPath)
	serverPath = '/' + os.path.relpath(absPath, serverRoot)
	return serverPath

def getServerPathFromRequest(myRequestHeader):
	serverPath = myRequestHeader['resource']
	return serverPath

def getFSPathFromServerPath(serverPath):
	fsPath = os.path.normpath(serverRoot + serverPath)
	return fsPath

def getFileAndLinkPair(serverPath, dir):
	files = os.listdir(dir)
	links = dict()
	for f in files:
		links[f] = getServerPathFromFSPath(dir + '/' + f)
	return links

def getMessageTemplate(msg):
	head = """HTTP/1.0 200 OK\r\nContent-Type:text/html\r\nConnection:close\r\n\r\n
		<!DOCTYPE html>
			<head>
				<title>Chao's Simple Web Server</title>
			</head>
			<body>
				<h1>Hello world!</h1>
				<hr>
			"""

	tail = """
			</body>
			</html>
			"""
	return head + msg + tail

def generateDirTemplate(serverPath, links):
	head = """HTTP/1.0 200 OK\r\nContent-Type:text/html\r\nConnection:close\r\n\r\n
		<!DOCTYPE html>
		<head><title>Chao's Simple Web Server</title></head>
		<body>
			<h1>Hello world!</h1>
		"""+ "<p>index of "+ serverPath +"</p>"+"""

			<hr>
		"""

	tail = """
		</body>
		</html>
		"""

	content = ''

	if serverPath == '/':
		pass
	else:
		idx = serverPath[1:-1].rfind('/')
		if idx == -1:
			parentDirectory = "<a href=\"/\" >Parent_Directory</a><br>\n"
			content = content + parentDirectory
		else:
			parentDirectory = "<a href=\""+ serverPath[:idx+1] + "\" >Parent_Directory</a><br>\n"
			content = content + parentDirectory

	for fn, link in sorted(links.iteritems(), key=lambda (k,v): (k,v)):
		oneFile = "<a href=\""+ link + "\" >"+ fn +"</a><br>\n"
		content = content + oneFile
	return head + content + tail

def getErrorTemplate():
	head = """HTTP/1.0 404 Not Found\r\nContent-Type:text/html\r\nConnection:close\r\n\r\n
			<!DOCTYPE html>
			<head>
				<title>Chao's Simple Web Server</title>
			</head>
			<body>
			<h1>404 Not Found</h1>
			 """

	tail = """
			</body>
			</html>\r\n
			"""
	return head + tail

def sendFileToClient(socket, fsPath):
	f = open(fsPath, 'r')
	if f.name.endswith('.txt'):
		socket.send("HTTP/1.1 200 OK\n Content-type: text/plain\n\n")
	elif f.name.endswith('.py'):
		socket.send("HTTP/1.1 200 OK\n Content-type: text/plain\n\n")
	elif f.name.endswith('.mp3'):
		socket.send("HTTP/1.1 200 OK\n Content-type: audio/mpeg3\n\n")
	elif f.name.endswith('.java'):
		socket.send("HTTP/1.1 200 OK\n Content-type: text/plain\n\n")
	else:
		socket.send("HTTP/1.1 200 OK\n Content-type: application/txt\n\n")

	# can add more MIME type mapping here,
	# or use dict() to store the mapping, use map[suffix] to get content type in O(1)
	socket.sendall(f.read())



class MyServerHandler(SocketServer.BaseRequestHandler):

	def handle(self):

		try:
			data = self.request.recv(1024).strip()
			lines = data.split('\n')

			firstLine = lines[0].split(' ')

			if len(firstLine) == 3:
				myRequestHeader = dict()
				myRequestHeader['method'] = firstLine[0]

				# only support GET so far
				if myRequestHeader['method'].upper() == "GET":
					myRequestHeader['resource'] = urllib.url2pathname(firstLine[1])
					myRequestHeader['version'] = firstLine[2]

					# first line has already been parsed, these headers isn't used so far
					for l in lines[1:]:
						idx = l.find(':')
						if idx == -1:
							continue
						key = l[:idx]
						value = l[idx+1:]
						myRequestHeader[key] = value

					serverPath = getServerPathFromRequest(myRequestHeader)
					fsPath = getFSPathFromServerPath(serverPath)

					if os.path.exists(fsPath):
						if os.path.isdir(fsPath) == True:
							links = getFileAndLinkPair(serverPath, fsPath) # link pair: file -> server absolute links
							respondData = generateDirTemplate(serverPath, links)
						else:
							# f is a file
							sendFileToClient(self.request, fsPath)
					else:
						# only returen 404,
						# may be support other response code in the furture
						respondData = getErrorTemplate()
				else:
					respondData = getErrorTemplate()

				self.request.sendall(respondData)
				self.request.close()

		except Exception:
			# always close connection
			self.request.close()


if __name__ == "__main__":

	# do not support custom port, will support later, and do input checking
	HOST, PORT = "localhost", 9999

	# Create the server, binding to localhost on PORT
	server = SocketServer.TCPServer((HOST, PORT), MyServerHandler)

	# Activate the server; this will keep running until you
	# interrupt the program with Ctrl-C
	# here maybe improved by provide a method to terminate the server,
	# such as sending "END" through socket, or create a page let user shutdown the server
	server.serve_forever()