package common

import (
	"net"
	"os"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(signalChannel chan os.Signal, bet *Bet) {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		select {
		case <-signalChannel:
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		default:
		}

		// Create the connection the server in every loop iteration. Send an
		if err := c.createClientSocket(); err != nil {
			return
		}

		if err := SendBet(c.conn, bet); err != nil {
			_ = c.conn.Close()
			log.Errorf(
				"action: send_bet | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		if err := ReadAck(c.conn); err != nil {
			_ = c.conn.Close()
			log.Errorf(
				"action: receive_ack | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		_ = c.conn.Close()
		log.Infof(
			"action: apuesta_enviada | result: success | dni: %s | numero: %s",
			bet.Document,
			bet.Number,
		)

		select {
		case <-signalChannel:
			log.Infof(
				"action: shutdown | result: success | client_id: %v",
				c.config.ID,
			)

			return
		case <-time.After(c.config.LoopPeriod):
		}

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
