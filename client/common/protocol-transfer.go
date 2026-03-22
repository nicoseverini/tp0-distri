package common

import (
	"fmt"
	"io"
	"net"
	"strconv"
	"strings"
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

func NotifyDone(conn net.Conn, agency string) error {
	msg := fmt.Sprintf(
		"DONE,%s\n",
		agency,
	)

	return writeFull(
		conn,
		[]byte(msg),
	)
}

func agencyNumber(clientID string) string {
	return strings.TrimPrefix(
		clientID,
		"client",
	)

}

func SendQueryWinners(conn net.Conn, agency string) error {
	msg := fmt.Sprintf(
		"GET_WINNERS,%s\n",
		agency,
	)

	return writeFull(
		conn,
		[]byte(msg),
	)
}

func ReadWinners(conn net.Conn) ([]string, error) {
	line, err := readLine(conn)
	if err != nil {
		return nil, err
	}

	line = strings.TrimSpace(line)
	if !strings.HasPrefix(line, "WINS,") {
		return nil, fmt.Errorf(
			"invalid winners response: %s",
			line,
		)
	}

	parts := strings.Split(line, ",")
	if len(parts) != 2 {
		return nil, fmt.Errorf(
			"invalid winners format: %s",
			line,
		)
	}

	count, err := strconv.Atoi(parts[1])
	if err != nil {
		return nil, err
	}

	winners := make([]string, count)
	return winners, nil
}
