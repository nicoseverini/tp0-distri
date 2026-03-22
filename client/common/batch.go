package common

import (
	"fmt"
	"io"
	"net"
)

func NextBatch(src BetSource, maxAmount int) ([]*Bet, error) {
	batch := make([]*Bet, 0, maxAmount)

	for len(batch) < maxAmount {
		bet, err := src.Next()
		if err != nil {
			if err == io.EOF {
				if len(batch) == 0 {
					return nil, io.EOF
				}
				return batch, nil
			}
			return nil, err
		}
		batch = append(batch, bet)
	}
	return batch, nil
}

func SendBatch(conn net.Conn, bets []*Bet) error {
	for _, bet := range bets {
		msg := fmt.Sprintf(
			"%s,%s,%s,%s,%s,%s\n",
			bet.Agency,
			bet.FirstName,
			bet.LastName,
			bet.Document,
			bet.Birthdate,
			bet.Number,
		)
		if err := writeFull(conn, []byte(msg)); err != nil {
			return err
		}
	}
	if err := writeFull(conn, []byte("END\n")); err != nil {
		return err
	}

	return nil
}
