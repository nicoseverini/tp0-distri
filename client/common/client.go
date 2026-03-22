package common

import (
	"io"
	"net"
	"os"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID             string
	ServerAddress  string
	LoopAmount     int
	LoopPeriod     time.Duration
	BatchMaxAmount int
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
func (c *Client) StartClientLoop(signalChannel chan os.Signal, betSrc BetSource) {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	defer betSrc.Close()
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		select {
		case <-signalChannel:
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		default:
		}

		batch, err := NextBatch(
			betSrc,
			c.config.BatchMaxAmount,
		)

		if err != nil {
			if err == io.EOF {
				log.Infof(
					"action: loop_finished | result: success | client_id: %v",
					c.config.ID,
				)
				return
			}
			log.Errorf(
				"action: read_batch | result: fail | error: %v",
				err,
			)
			return
		}

		if err := c.createClientSocket(); err != nil {
			return
		}

		if err := SendBatch(c.conn, batch); err != nil {
			log.Errorf(
				"action: send_batch | result: fail | error: %v",
				err,
			)
			_ = c.conn.Close()
			return
		}

		if err := ReadAck(c.conn); err != nil {
			log.Errorf(
				"action: read_ack | result: fail | error: %v",
				err,
			)
			_ = c.conn.Close()
			return
		}

		log.Infof(
			"action: apuesta_enviada | result: success | cantidad: %d",
			len(batch),
		)

		_ = c.conn.Close()

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
