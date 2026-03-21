package common

import (
	"fmt"
	"os"
)

type Bet struct {
	Agency    string
	FirstName string
	LastName  string
	Document  string
	Birthdate string
	Number    string
}

func LoadBetFromEnv(agencyId string) (*Bet, error) {
	firstName := os.Getenv("NOMBRE")
	lastName := os.Getenv("APELLIDO")
	document := os.Getenv("DOCUMENTO")
	birthdate := os.Getenv("NACIMIENTO")
	number := os.Getenv("NUMERO")

	if firstName == "" || lastName == "" || document == "" || birthdate == "" || number == "" {
		return nil, fmt.Errorf("missing environment variables for bet")
	}

	bet := &Bet{
		Agency:    agencyId,
		FirstName: firstName,
		LastName:  lastName,
		Document:  document,
		Birthdate: birthdate,
		Number:    number,
	}

	return bet, nil
}
