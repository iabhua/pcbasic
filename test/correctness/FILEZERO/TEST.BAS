5 OPEN "output.txt" FOR OUTPUT AS 1
7 ON ERROR GOTO 1000
10 OPEN "test" FOR OUTPUT AS 0
20 CLOSE
30 END
1000 PRINT #1, ERR, ERL
1010 RESUME NEXT

