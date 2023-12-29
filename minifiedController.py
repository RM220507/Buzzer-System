C=False
D=True
B=int
from microbit import uart as H,display as A
import radio as E
class F:
	def __init__(A):H.init(baudrate=9600);E.config(group=16,power=7);E.on();A.__teams=[];A.__waitingForBuzz=C;A.__displayLight=D
	def sendMsg(A,array):E.send_bytes(bytes(array))
	def teamFromID(B,buzzerID):
		for A in B.__teams:
			for C in A[1]:
				if C==buzzerID:return A[0]
	def mainloop(A):
		G=''
		while D:
			F=E.receive_bytes()
			if F:
				if B(F[0])==50:
					if A.__waitingForBuzz:A.__waitingForBuzz=C;A.__activeBuzzer=F[1];A.__activeTeam=A.teamFromID(A.__activeBuzzer);print('buzzed',str(A.__activeTeam),B(A.__activeBuzzer))
					else:A.sendMsg([55,F[1]])
			I=H.read(1)
			if I is None:continue
			J=str(I,'UTF-8')
			if J=='\n':A.executeCommand(G);G=''
			else:G+=J
	def executeCommand(A,data):
		B=data.split()
		if len(B)==0:return
		if B[0]=='light':A.handleLightCommand(B)
		elif B[0]=='open':A.handleOpenCommand(B)
		elif B[0]=='reset':A.sendMsg([20]);A.__waitingForBuzz=C
		elif B[0]=='close':A.sendMsg([15]);A.__waitingForBuzz=C
		elif B[0]=='teamSetup':D=A.parseTeamInput(B);A.__teams=D;A.setupTeams();A.__waitingForBuzz=C
		elif B[0]=='resendTeams':A.setupTeams()
	def handleLightCommand(A,command):
		C=command
		if C[1]=='toggle':A.__displayLight=not A.__displayLight;A.sendMsg([70,B(A.__displayLight)])
		elif C[1]=='set':A.__displayLight=bool(B(C[2]));A.sendMsg([70,B(A.__displayLight)])
		elif C[1]=='update':A.sendMsg([45])
	def handleOpenCommand(A,command):
		C=command
		if C[1]=='all':A.sendMsg([10]);A.__waitingForBuzz=D
		elif C[1]=='lockTeam':
			if C[2]=='active':A.sendMsg([25,A.__activeTeam]);A.__waitingForBuzz=D
			elif C[2].isdigit()and 0<=B(C[2])<A.teamCount():A.sendMsg([25,B(C[2])]);A.__waitingForBuzz=D
		elif C[1]=='team':
			if C[2].isdigit()and 0<=B(C[2])<A.teamCount():A.sendMsg([35,B(C[2])]);A.__waitingForBuzz=D
		elif C[1]=='lockInd':A.sendMsg([30]);A.__waitingForBuzz=D
	def parseTeamInput(J,command):
		E=' '.join(command[1:]);D=[]
		for A in E.split(';'):A=A.strip();C=A.split('/');F=B(C[0].strip());G=[B(A)for A in C[1].strip().split()];H=[B(A)for A in C[2].strip().split()];I=F,G,H;D.append(I)
		return D
	def setupTeams(B):
		for A in B.__teams:
			for D in A[1]:B.sendMsg([60,D,A[0]])
			C=[65,A[0]];C.extend(A[2]);B.sendMsg(C)
	def teamCount(A):return len(A.__teams)
A.scroll('Active')
G=F()
G.mainloop()