# To‐Do List: Building the OLG Classroom Game

Below is a **step‐by‐step** plan in Markdown format to guide implementation of the three‐period OLG classroom game. Each step can be refined according to your development environment (Python + Flask, Node.js, etc.). The checklist is broken down into **project setup**, **back‐end logic**, **front‐end interface**, **testing**, **deployment**, and **live classroom** details.

---

## 1. Project Setup

- [x] **Create Repository**  
  - Initialize a new repository (e.g., GitHub, GitLab).  
  - Decide on tech stack (Python/Flask, Node/Express, or similar).

- [x] **Environment Setup**  
  - Choose your server‐side language and framework.  
  - For Python: install dependencies (`Flask`, `SQLAlchemy`, etc.).  
  - For Node: install dependencies (`express`, `socket.io`, `sequelize`, etc.).

- [x] **Database Schema**  
  - Plan how to store user info, round data, policy settings, game parameters (borrowing limit, interest rates, etc.).  
  - Create tables for:
    - **Users** (`user_id`, `avatar`, `name`, `current_age_stage`, `current_assets`, etc.).
    - **Rounds** (`round_id`, `timestamp`, etc.).
    - **Decisions** (`decision_id`, `user_id`, `borrowed_amount`, `saved_amount`, etc.).
    - **Policies** / **Parameters** (`policy_id`, `tax_on_y`, `tax_on_m`, `tax_on_o`, `B_g`, etc.).

---

## 2. Modeling & Equilibrium Logic

- [x] **Model Equations Implementation**  
  1. **Household Budget Constraints**  
     - Young: `C_y = B^y`, with `B^y <= D/(1 + r)`.
     - Middle‐Aged: `C_m = Y^m - (1+r)*B^y + B^m`.
     - Old: `C_o = Y^o - (1+r)*B^m`.
  2. **Loan‐Market Clearing**: sum of all `B^y_i` + `B^g` = - (sum of all `B^m_j`).
  3. Solve for `r`.

- [x] **Implement the Solver**  
  - Write a function to:
    - Gather **sum of Young borrowing** and **sum of Middle‐Aged saving**.
    - Find `r` that clears the market (bisection or Newton iteration).  
  - Handle constraints: e.g., if a nominal interest rate is fixed or there's a ZLB.  

- [x] **Parameter / Policy Integration**  
  - If professor sets taxes, incorporate them into the budget constraints.  
  - If professor sets government debt `B^g`, add it to total loan demand.

- [x] **Lifecycle Progression**  
  - Implement logic to **advance** each user's age stage: Y → M → O → Y (reborn).  
  - On rebirth, reset assets or set them to 0.

---

## 3. Back‐End (Server) Implementation

- [x] **Core Server Routes**  
  - **`POST /submitDecision`**:  
    - Player sends their borrowing/saving decision.  
    - Validate the numeric input, store in DB.  
  - **`GET /currentState`**:  
    - Returns JSON of the game state (round, interest rate, each user's data, etc.) to be shown on the front‐end.  

- [x] **Game Orchestration**  
  - Build a routine (e.g., `runRound()`) that:  
    1. Waits for all players to submit decisions (or a timer expires).  
    2. Reads decisions from DB.  
    3. Computes equilibrium `r`.  
    4. Updates each player's consumption, utility, and next assets.  
    5. Advances the age stage.  
    6. Writes the updated states back to DB.  
  - Possibly triggered by a **"Next Round"** button or an automatic timer.

- [x] **Professor Interface Endpoints**  
  - **`POST /setPolicy`**: updates the current policy variables (taxes, `B^g`, `D`, etc.).  
  - **`GET /dashboardData`**: returns aggregated data for the big‐screen dashboard.

---

## 4. Front‐End Interface

### 4.1 Player UI

- [x] **Layout / Framework**  
  - Choose a front‐end framework (React, Vue, Angular) or pure HTML/JS.  
  - Create a main **Game Screen** with:
    - **Header**: Round #, Player's Name, Life Stage.
    - **Information Panel**: interest rate, borrowing limit, policy/taxes.
    - **Decision Panel** (sliders, text fields).

- [x] **Decision Forms**  
  - **Young**: Borrow slider / numeric input in `[0, D/(1+r)]`.  
  - **Middle‐Aged**: Save/borrow range `[ -someMin, someMax ]`, ensuring no negative consumption.  
  - **Old**: Typically no input if consumption is auto‐calculated.  
  - **Validation**:
    - Restrict text field to numeric values.
    - Show warnings or disable "Submit" if out of range.

- [x] **Feedback / Explanation**  
  - Display how the chosen input translates to consumption.  
  - Show last round's utility, or a short textual explanation: "Because the interest rate was 3%, your repayment was 1.03 × borrowed."

- [x] **Submit Button**  
  - On click, the front‐end calls `POST /submitDecision` with the chosen value.  
  - Provide a loading/spinner if needed, then confirm success.

### 4.2 Professor / Big‐Screen Dashboard

- [x] **Aggregated Data Display**  
  - Show the **loan supply/demand** or the **equilibrium** interest rate.  
  - Show distribution of decisions (histograms of borrowing/saving).  
  - Show scoreboard with each user's total lifetime utility or rank.  

- [x] **Control Panel**  
  - Buttons or input fields to set policy in real time (`B^g`, taxes, or new `D`).  
  - "Next Round" or "End Round" button if not automatic.

---

## 5. Testing & Validation

- [x] **Unit Tests**  
  - Test the solver function with known examples.  
  - Test age progression logic: Y→M→O→reborn Y.  
  - Test numeric field validations.

- [x] **Integration Tests**  
  - Spin up local server and front‐end, simulate 3–6 test users.  
  - Check that decisions are saved properly and equilibrium updates are correct.

- [x] **Edge Cases**  
  - ✅ All players try to borrow the max → does the solver handle it?  
  - ✅ All players try to save large amounts → negative interest rates?  
  - ✅ Fixed issues with Middle-aged players having negative disposable income.
  - ✅ Fixed round advancement to handle stuck test players.
  - ✅ Added Reset Game button to handle persistent state.
  - ✅ Professor sets unusual policy values (e.g., huge taxes or negative government debt).

---

## 6. Deployment & Classroom Setup

- [x] **Server Deployment**  
  - Decide if you'll run on a local machine or a hosted service.  
  - Ensure stable network / Wi‐Fi for all student devices.

- [ ] **Classroom Preparation**  
  - Provide students with the **URL** or instructions to join (e.g., `http://xx.xx.xx:port`).  
  - Assign them to log in with a code or auto‐generated name.  
  - Make sure the big‐screen **professor dashboard** is displayed on a projector/screen.

- [x] **Dry Run**  
  - Do a quick mock session with a few test accounts.  
  - Validate that the flow from "Submit Decision" → "Compute Equilibrium" → "Show Results" is smooth.

---

## 7. Live Session / Ongoing Iteration

- [ ] **Launch**  
  - Start the game. Each student logs in, sees their role (Y/M/O).  
  - Show them how to pick decisions and submit.

- [ ] **Monitor & Adjust**  
  - Observe real‐time data on the professor's dashboard.  
  - Possibly tweak policy mid‐session to demonstrate different outcomes.  
  - Let the game run for multiple rounds.

- [ ] **Feedback & Wrap‐Up**  
  - End the game. Show final scoreboard / utility ranks.  
  - Export logs for later analysis or discussion.  
  - Gather student feedback for future improvements.

---

## Recent Improvements

- [x] **Fixed Middle-aged Player Issues**
  - Fixed issues with middle-aged players having negative disposable income, ensuring they save 0 instead of causing errors.
  - Enhanced error handling with fallback strategies for test player decision generation.
  - Added multi-tiered approach to ensure rounds always advance, even with problem test players.

- [x] **Professor Dashboard Enhancements**
  - Improved test player naming with famous economist names (Keynes, Smith, etc.) for better tracking.
  - Removed popup confirmations for adding test players and policy updates for a cleaner experience.
  - Added real-time notifications when new students join the game.
  - Added Reset Game button to completely clear game state without server restart.

- [x] **Performance & Stability**
  - Fixed issues with game state persistence between server restarts.
  - Improved error handling throughout to prevent round advancement issues.
  - Added proper socket.io integration for real-time updates to all connected clients.

---

## Summary

The OLG game implementation is now largely complete and stable for classroom use. The following critical issues have been fixed:

1. Middle-aged players with negative disposable income no longer block game progression
2. The test player system now uses memorable names and works reliably across multiple rounds
3. The professor dashboard has been enhanced with real-time updates and smoother controls
4. A Reset Game button allows for complete game state reset without server restart

The main area still pending is final classroom preparation and the actual live session. The application is now stable and reliable enough for classroom deployment.

## Next Priority Task

Consider creating comprehensive documentation for professor use, including:
- Setup instructions for the classroom
- A quick reference guide for the professor dashboard features
- Troubleshooting tips for common classroom scenarios
- Guidance on policy adjustments to demonstrate different economic concepts
