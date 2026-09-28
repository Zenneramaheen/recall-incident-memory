# Recall — simple 3-minute video script

Read this naturally. You do not need to explain every technical word perfectly.

## Before you record

Open `http://127.0.0.1:8765` and click **New session**.

## Script

“Hi, I’m [YOUR NAME], and this is Recall.

Recall is an incident-response assistant that helps engineers when an application breaks.

The main problem is simple: when a production incident happens, engineers often spend time searching old messages, documents, and postmortems to find out whether the team has seen the problem before. Even when they find an old incident, they still need to know whether the old fix is safe to use today.

I built Recall to remember verified incident outcomes: what broke, what engineers tried, what failed, what eventually worked, and how they confirmed recovery.

For this demo, I built a safe shopping-checkout simulator called Sunday Supply. It does not take payments or connect to a real production system. It lets us create controlled failures and see how the agent uses memory.”

### Show the app

“On the left is the customer view. A customer is buying a demo mug.

On the right is the engineer view. It shows system metrics and checkout logs.

At the bottom is the agent view. This is where Recall explains the current problem and retrieves relevant experience from Hindsight.”

### First failure: no memory yet

Click **1. First failure**, then **Place demo order**.

“I have now introduced a simulated checkout failure. The customer sees an HTTP 503 timeout.

The engineer view shows that the database connection pool is full: 20 out of 20 connections are in use. The log also says an exception path failed to release a database connection.”

Click **Ask the incident agent**.

“At this point, there are zero recalled facts because this is the first incident in this memory bank.

Recall still analyzes the current logs and suggests what to investigate. But it does not pretend it knows the confirmed cause yet.”

### Fix and save the lesson

Open **Try a fix yourself**. Click **Restart checkout**, then place two demo orders.

“A restart may make one request work, but the failure comes back. That is important: Recall also remembers failed attempts, not only successful fixes.”

Click **Repair connection cleanup**, then **Place demo order**.

“Now the checkout works again. I verified recovery with a successful demo order.”

Click **Save this lesson to Hindsight**.

“This is where Hindsight is used. Recall sends the verified incident outcome to Hindsight as long-term memory: the symptoms, root cause, failed restart, successful connection-cleanup fix, and recovery verification.”

### Same failure again: memory helps

Click **2. Same problem again**, then **Place demo order**, then **Ask the incident agent**.

“Now the same kind of failure happens again.

This time, Recall uses Hindsight to retrieve the earlier incident. It remembers that restarting did not solve the real problem and that repairing connection cleanup worked.

The green comparison card shows why that old lesson applies: the current logs have the same timeout, full database pool, and connection-release error.”

### Similar failure: memory must not mislead

Click **3. Looks similar. Isn’t.**, then **Place demo order**, then **Ask the incident agent**.

“The customer still sees an HTTP 503 timeout, so it looks similar from the outside.

But the current evidence is different. The database is healthy at 4 out of 20 connections, and the payment gateway is unreachable.

Recall retrieves the old database incident, compares it with today’s evidence, and clearly says not to reuse the old connection fix. The orange comparison card explains the conflict.”

Click **Restore payment settings**, then **Place demo order**.

“The correct fix is restoring the payment settings, and the checkout works again.”

### Closing

“I used Python for the simulator and backend, HTML, CSS, and JavaScript for the web interface, and Hindsight Cloud for memory.

Hindsight gives Recall three important abilities: retain verified incident outcomes, recall related past facts, and reflect on past memory together with current evidence.

Recall does not automatically change a production system. It gives engineers grounded suggestions, shows the evidence behind them, and asks for human review before remediation.

The key idea is: memory should help engineers reuse proven lessons, but it should also tell them when an old fix does not apply. Thank you.”

## If someone asks what is real

Say: “The checkout failures are controlled simulations. The Hindsight memory and reflection calls are live. The next step is testing the same workflow with approved, sanitized incident postmortems.”
