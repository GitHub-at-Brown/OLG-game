# OLG Classroom Game

A web-based classroom game for teaching Overlapping Generations (OLG) models in economics. This application allows students to play as agents in different life stages (Young, Middle-Aged, and Old) and make economic decisions about borrowing, saving, and consumption.

## Features

- **Role-Based Interface**: Different views and controls for players based on their life stage (Young, Middle-Aged, Old)
- **Real-Time Updates**: Uses WebSockets to provide immediate feedback when policy changes or rounds advance
- **Professor Dashboard**: Controls for setting policy parameters and advancing rounds
- **Equilibrium Calculation**: Automatically calculates market-clearing interest rates
- **Data Validation**: Prevents players from making economically invalid decisions

## Setup and Installation

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
python app.py
```

3. Access the application at http://localhost:5000

## Usage

### Professor Interface

1. Access the professor dashboard at `/professor`
2. Set policy parameters:
   - Interest rate (or let it be determined by the market)
   - Tax rates for different age groups
   - Government debt and borrowing limits
3. Use the "Advance to Next Round" button to move the game forward once all students have made their decisions

### Student Interface

1. Access the student dashboard at `/player?user_id=[YOUR_ID]`
2. Make decisions based on your current life stage:
   - **Young**: Choose how much to borrow against future income
   - **Middle-Aged**: Decide how much to save or borrow
   - **Old**: Automatically consume all available resources
3. See the immediate impact of your decisions on consumption and utility
4. Move to the next life stage when the professor advances the round

## Game Logic

- **Young players** start with zero assets and can borrow against future income, up to a borrowing limit.
- **Middle-Aged players** earn income, must repay their debt from youth, and decide how much to save for old age.
- **Old players** consume all their savings plus any pension income.
- The **interest rate** can be set by the professor or determined by market clearing (when loan demand equals loan supply).
- **Government debt** and **taxes** can be used to influence the equilibrium.

## Development

The application is built with:
- **Backend**: Flask, Flask-SocketIO
- **Frontend**: Bootstrap, vanilla JavaScript
- **Database**: In-memory for simplicity (can be extended to use SQLAlchemy)

## License

This project is developed for educational purposes.
