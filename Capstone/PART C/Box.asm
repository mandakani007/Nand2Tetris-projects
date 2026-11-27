// BOX PROGRAM
// K = 54
// Starting row = 54
// Height = 20 rows
// Width = 48 pixels

(START)
    @KBD
    D=M
    @DRAW
    D;JNE

    @ERASE
    0;JMP

// DRAW BLACK BOX
(DRAW)
    @18112
    D=A
    @addr
    M=D

    @20
    D=A
    @rows
    M=D

(DRAW_ROW)
    @3
    D=A
    @words
    M=D

(DRAW_WORD)
    @addr
    A=M
    M=-1

    @addr
    M=M+1

    @words
    M=M-1
    D=M
    @DRAW_WORD
    D;JGT

    @29
    D=A
    @addr
    M=D+M

    @rows
    M=M-1
    D=M
    @DRAW_ROW
    D;JGT

    @START
    0;JMP

// ERASE BOX
(ERASE)
    @18112
    D=A
    @addr
    M=D

    @20
    D=A
    @rows
    M=D

(ERASE_ROW)
    @3
    D=A
    @words
    M=D

(ERASE_WORD)
    @addr
    A=M
    M=0

    @addr
    M=M+1

    @words
    M=M-1
    D=M
    @ERASE_WORD
    D;JGT

    @29
    D=A
    @addr
    M=D+M

    @rows
    M=M-1
    D=M
    @ERASE_ROW
    D;JGT

    @START
    0;JMP