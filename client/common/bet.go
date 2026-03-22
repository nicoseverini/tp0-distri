package common

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"io"
	"os"
	"strings"
)

type Bet struct {
	Agency    string
	FirstName string
	LastName  string
	Document  string
	Birthdate string
	Number    string
}

func betFromCSVRow(agencyID string, row []string) (*Bet, error) {
	if len(row) < 5 {
		return nil, fmt.Errorf(
			"invalid CSV row (expected 5 fields): %v",
			row,
		)
	}

	norm := func(s string) string {
		return strings.TrimSpace(s)
	}

	return &Bet{
		Agency:    agencyID,
		FirstName: norm(row[0]),
		LastName:  norm(row[1]),
		Document:  norm(row[2]),
		Birthdate: norm(row[3]),
		Number:    norm(row[4]),
	}, nil
}

type BetSource interface {
	Next() (*Bet, error)
	Close() error
}

type CSVBetIterator struct {
	file     *os.File
	reader   *csv.Reader
	agencyID string
}

func NewCSVBetIterator(path string, agencyID string) (*CSVBetIterator, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf(
			"could not open %s: %w",
			path,
			err,
		)
	}
	reader := csv.NewReader(
		bufio.NewReader(file),
	)
	reader.TrimLeadingSpace = true
	return &CSVBetIterator{
		file:     file,
		reader:   reader,
		agencyID: agencyID,
	}, nil
}

func (it *CSVBetIterator) Next() (*Bet, error) {
	for {
		row, err := it.reader.Read()
		if err != nil {
			if err == io.EOF {
				return nil, io.EOF
			}
			return nil, fmt.Errorf(
				"error reading CSV: %w",
				err,
			)
		}
		allEmpty := true
		for _, col := range row {
			if strings.TrimSpace(col) != "" {
				allEmpty = false
				break
			}
		}
		if allEmpty {
			continue
		}
		return betFromCSVRow(
			it.agencyID,
			row,
		)
	}
}

func (it *CSVBetIterator) Close() error {
	if it.file != nil {
		return it.file.Close()
	}
	return nil
}
