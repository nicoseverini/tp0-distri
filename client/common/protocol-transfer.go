package common

import (
	"fmt"
	"io"
	"net"
)

func writeFull(conn net.Conn, data []byte) error {
	for len(data) > 0 {
		n, err := conn.Write(data)
		if err != nil {
			return err
		}
		if n == 0 {
			return io.ErrShortWrite
		}

		data = data[n:]
	}
	return nil
}

func readLine(conn net.Conn) (string, error) {
	buffer := make([]byte, 0)
	tmp := make([]byte, 1)

	for {
		n, err := conn.Read(tmp)
		if err != nil {
			return "", err
		}
		if n == 0 {
			break
		}

		buffer = append(buffer, tmp[0])
		if tmp[0] == '\n' {
			break
		}
	}
	return string(buffer), nil
}

func SendBet(conn net.Conn, bet *Bet) error {
	msg := fmt.Sprintf(
		"%s,%s,%s,%s,%s\n",
		bet.FirstName,
		bet.LastName,
		bet.Document,
		bet.Birthdate,
		bet.Number,
	)
	return writeFull(conn, []byte(msg))
}

func ReadAck(conn net.Conn) error {
	line, err := readLine(conn)
	if err != nil {
		return err
	}
	if line != "OK\n" {
		return fmt.Errorf("invalid ACK from server: %s", line)
	}

	return nil
}
