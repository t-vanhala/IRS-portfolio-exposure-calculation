# IRS-portfolio-exposure-calculation

Relevant parts of the source code for Master's thesis "Data-driven xVA exposure calculation for a portfolio of interest rate swaps"

Some parts of the code rely on or are based on the source code published by Isabelle Frodé & Viktor Sambergs as a part of their Master's thesis in the repository: https://github.com/frodiie/Credit-Exposure-Prediction-GRU

## Requirements

Requirements for the project given in `requirements.txt`.

## MongoDB setup with Docker

Requires Docker and Docker compose installation.

$ docker-compose up --build -d mongodb

$ docker-compose exec mongodb bash

Logging to the database inside the container:

$ mongosh -u username -p password
