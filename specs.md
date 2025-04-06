Below is a **detailed design** for the **Player Interface**, covering exactly **what each player sees**, **which variables** are displayed, **which variables** they can **control**, and **how** they enter those decisions (with input validation to avoid invalid or impossible values). This design aims to be **clean**, **intuitive**, and **fast** to use.

---

## 1. General Layout and Design Principles

1. **Single Webpage or App Screen** per Player
   - Each student has a **dashboard** view that updates automatically every round.
   - The interface is **role‐based**: it shows different controls and information depending on whether the student is currently **Young**, **Middle‐Aged**, or **Old**.

2. **Organization**
   - **Header / Title Bar**: Shows the current *round* or *period number*, the player's *name/avatar*, and *life stage*.
   - **Main Panel**: Divided into two sections:
     1. **Information / Display** (top or left‐side)
     2. **Decision Controls** (bottom or right‐side)

3. **Data Validation**:
   - Numeric fields only allow numeric input.
   - No negative values for consumption, savings, or borrowing in contexts where they are disallowed.
   - Borrowing cannot exceed the borrowing limit $$D_t / (1+r_t)$$.
   - Inputs that violate constraints show a **red warning** or are disabled.

4. **Responsiveness**:
   - The interface should be quick: any user input (e.g. moving a slider) provides immediate feedback, or at least does not cause any lag.
   - Should look **modern**, e.g. with a minimal style, clear fonts, color highlights for important numbers.

---

## 2. Variables Shown to Each Player

Regardless of life stage, **all** players see:

1. **Current Period** or **Round**: e.g. "Period 3"
2. **Their Life Stage**: "You are: Young / Middle‐Aged / Old."
3. **Policy / Parameters** (read‐only):
   - Current **real interest rate** $$r_t$$ (or nominal interest rate, if that's how you prefer).  
   - If the professor sets taxes, show the relevant tax rates $$T_t^y$$, $$T_t^m$$, $$T_t^o$$.  
   - If government debt $$B_t^g$$ is exogenous, show that as well.  
   - Borrowing limit $$D_t$$ or any other constraints.  
4. **Summary of the Previous Round** (personal):
   - Last round's consumption
   - Last round's saving/borrowing decision
   - Last round's realized utility contribution (e.g. $$\log(C)$$ or the fraction of max)
5. **A Quick Explanation**: A text box or pop‐up clarifying how the user's previous decisions factored into the new equilibrium. For example: "Because many Young agents borrowed heavily, the interest rate rose to 4%."

---

## 3. Life‐Stage‐Specific Display and Controls

### 3.1 If the Player is **Young (Y)**

**Information Panel** (top/left):
- **Income** (if any; often zero for Young).  
- **Borrowing Limit**:  
  $$
    B^y_{\text{max}} = \frac{D_t}{1 + r_t}
  $$
  This is displayed in a small box, e.g. "Maximum you can borrow this period: 47.2."

- **Current Debt or Assets**: If the Old → reborn Young transition sets them to zero, display "Your current net assets: 0." If for some reason you allow leftover assets, display that too.

**Decision Control** (bottom/right):
- A **slider** or **numeric text box** labeled **"How much do you borrow?"**. 
  - Default = 0 (or some recommended guess).
  - Range = $$[0, B^y_{\text{max}}]$$. If the user tries to exceed $$B^y_{\text{max}}$$, the slider or text box is capped or shows a warning.
  - If the user tries to type a negative number or letters, it's not allowed (validation).  
- **Consumption** is automatically **equal** to borrowing if $$Y^y=0$$. If some positive income $$Y^y$$ exists, let them decide how much to borrow *plus* income = total consumption. 
  - If you want them to see consumption explicitly, show a read‐only field "Your consumption this period = Borrowing + $$Y^y$$."

- **Confirm Button**: "Submit Borrowing Decision."

### 3.2 If the Player is **Middle‐Aged (M)**

**Information Panel**:
- **Income** $$Y^m$$ for the current period, displayed as a numeric read‐only label.
- **Outstanding Debt** from Young period, if any: "You owe $$(1+r_t) \times B^y$$."
- Possibly a **preview**: If they save $$S$$, they will have $$(1+r_t) \times S$$ next period. If they borrow more, they must repay next period.

**Decision Control**:
- A **numeric entry** or **slider** for the variable "How much do you **save**?" or equivalently "What is $$B_{t+1}^m$$?"
  - The range is from a negative (if you allow additional borrowing) up to "all disposable income," but do not allow it to exceed some max (e.g., no more than available resources). 
  - The interface calculates consumption automatically:
    $$
      C^m = Y^m - (1+r_t) \times B^y + B^m_{t+1}
    $$
- If you prefer, you can **split** it into:
  1. "Consumption this period"  
  2. "Saving (bond purchase) this period"
  They must sum up to disposable income.  
  - Ensure no negative consumption or negative saving if that's disallowed.  

- **Submit** button for confirming the choice.

### 3.3 If the Player is **Old (O)**

**Information Panel**:
- Shows any **assets** carried from the middle‐aged period: $$-B^m$$ if negative or positive if they saved.
- Possibly shows any **pension** $$Y^o$$. 
- A simple reminder that they will consume their resources.

**Decision Control**:
- If the simplest approach is that Old automatically consume all they have:
  - **No input** needed. Just a message: "You consume all that's left: $$C^o = Y^o - (1+r_{t+1}) \times B^m$$."
- If you wish to allow them a consumption choice (rare in a strict 3‐period OLG with no bequest motive):
  - Provide a numeric "How much do you consume?" field, but typically that's overshadowed by the fact that they can't carry assets further (they die).  

- **Next**: "You will be reborn as Young in the next period once you have finished Old."

---

## 4. Additional Interface Elements

### 4.1 Real‐Time Feedback / Validation

- When a Young user moves the "Borrow" slider, a small text says, "Your consumption = $$\text{slider value}$$."  
- If Middle‐Aged tries to set saving $$B_{t+1}^m$$ so large that consumption is negative, the interface shows a **red error**: "Consumption cannot be negative!"  
- Borrowing constraints are strictly enforced in code, so the user *cannot submit* an out‐of‐range number.

### 4.2 Error Handling

- If the player attempts to type a letter or symbol in a numeric box, either ignore it or revert to the previous valid value.
- If the player tries to leave a blank, set it to 0 or disallow submission until a valid number is entered.

### 4.3 "Summary" or "Stats" Box

Consider a small box on the side listing:
- **This Period**:  
  - Income (if any)  
  - Borrowing or Saving chosen (once decided)  
  - Consumption  
  - Taxes (if the professor set them)  
- **Expected Next Period**: (rough or partial)  
  - Debt repayment, if relevant.

This helps players see how their choice impacts next‐period finances.

---

## 5. Example Screen Mockups

### 5.1 Young Player Screen

```
 ----------------------------------------------------------
|  Round 3 / Period 3     Avatar: [Green Fox]   Stage: Y  |
 ----------------------------------------------------------
|   *** Information ***                                  |
|   • Borrowing limit: up to 47.2                        |
|   • Current interest rate: 3.2%                        |
|   • Policy: No taxes on Young this period              |
|                                                        |
|   *** Last Period Summary ***                          |
|   • You were Old, consumed 50, earned utility = 3.91   |
 ----------------------------------------------------------
|    [ Borrow Amount Slider: 0 --------------- 47.2 ]     |
|    Borrowing: 20.0  =>  Consumption: 20.0               |
|                                                        |
|    [ Submit Borrowing Decision ]                       |
 ----------------------------------------------------------
```

### 5.2 Middle‐Aged Player Screen

```
 -----------------------------------------------------------
|  Round 3 / Period 3    Avatar: [Blue Tiger]    Stage: M  |
 -----------------------------------------------------------
|   *** Information ***                                   |
|   • Income Y^m = 60                                     |
|   • Debt from Youth = (1 + 0.032)*25 = 25.8 owed        |
|   • Borrowing limit next period: ??? (shown for plan)   |
|   • No taxes on M or O                                  |
|                                                         |
|   *** Last Period Summary ***                           |
|   • You were Young, borrowed 25 => consumed 25, U=3.22  |
 -----------------------------------------------------------
|   ( Decision: B_{t+1}^m )                                |
|   Available resources = 60 - 25.8 = 34.2                 |
|                                                         |
|   "How much do you want to SAVE?"                       |
|      <0 means new borrowing>                            |
|   [ Text Field / Slider: from -10 up to 34.2 ]          |
|                                                         |
|   Computed consumption = 60 - 25.8 + (chosen B^m)        |
|   e.g. "If you save 10, then consumption = 24.2"        |
|                                                         |
|   [ Submit Saving Decision ]                            |
 -----------------------------------------------------------
```

### 5.3 Old Player Screen

```
 -----------------------------------------------------------
|  Round 3 / Period 3   Avatar: [Red Eagle]    Stage: O    |
 -----------------------------------------------------------
|   *** Information ***                                   |
|   • Assets from Middle Age: B_{t+1}^m = 20.0            |
|   • You have Y^o = 0 (no pension)                       |
|   • So you must repay or consume these assets           |
|                                                         |
|   *** Last Period Summary ***                           |
|   • You were Middle-Aged, saved 20, consumed 40         |
|   • Utility from last period = 3.69                     |
 -----------------------------------------------------------
|      No Decision: You simply consume your assets        |
|      => C^o = - (1 + r_{t+1}) * B^m if negative, or      |
|         B^m * (1 + r_{t+1}) if positive.                |
|                                                         |
|    [ Next Round: Rebirth as Young ]                     |
 -----------------------------------------------------------
```

---

## 6. Inputs Under User Control

1. **Young**:
   - **Borrowing** $$B^y \in [0, D_t/(1+r_t)]$$ if we assume no partial lending by Young.  
   - If negative lending is allowed, the range might be $$[-L, D_t/(1+r_t)]$$.

2. **Middle‐Aged**:
   - **Savings** $$B^m \in$$ [minimum feasible, maximum feasible]. Typically minimum feasible = $$-(Y^m - (1+r_t)B^y)$$ if they want to borrow more, maximum feasible = disposable income.  

3. **Old**:
   - Typically no decisions if the model forces them to consume all. Optionally let them choose consumption if you want an extended version (but usually not needed in the canonical 3‐period OLG).

**Data Validation**:
- Each numeric field must only accept digits (and possibly a decimal point). 
- The system dynamically checks if the user's chosen values remain within the legal range, and if not, it blocks or corrects them.

---

## 7. Putting It All Together

- The **player interface** is thus straightforward:  
  - At each new period, they see *their stage*, *their constraints*, *the relevant parameters (interest rate, borrowing limit, taxes)*, and *their net resources*.  
  - They make the **one main decision** (borrow, save, or no input if Old).  
  - They hit **Submit**.  
- **Validation** ensures only legitimate, feasible values can be submitted.  
- The **server** aggregates all inputs, finds the equilibrium interest rate, updates everyone's variables, and pushes new data to each interface for the next period.  
- The user sees a consistent, easy‐to‐read summary that helps them **understand** how their choice translates into consumption, utility, and next period's constraints.

This **design** guarantees:
- **Clarity** (fewer, simpler steps),
- **Correctness** (invalid inputs disallowed),
- **Speed** (no complicated multi‐step forms),
- **Engagement** (modern, minimal UI with immediate feedback).