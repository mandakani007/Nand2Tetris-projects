// Draws a rectangle 16 pixels wide
// Height is specified in RAM[0]

@R0
D=M
@height
M=D

@SCREEN
D=A
@address
M=D

(LOOP)
@height
D=M
@END
D;JLE

@address
A=M
M=-1

@address
D=M
@32
D=D+A
@address
M=D

@height
M=M-1

@LOOP
0;JMP

(END)
@END
0;JMP