# LinkedIn post

I built **Recall**, an Incident Memory Copilot that helps engineers learn from verified past incident fixes.

When a service fails, teams can spend time repeating investigations that have already been solved before. Recall stores engineer-confirmed lessons in Hindsight Cloud and compares them with current logs and metrics.

In the demo, Recall handles three situations:

• A first checkout failure with no previous memory
• The same failure again, where it recalls a verified database connection fix
• A similar-looking payment failure, where it safely rejects the old database fix because the evidence does not match

I built the prototype with Python, HTML, CSS, JavaScript, and Hindsight Cloud. It is a safe simulator with no real payments or customer data.

Project code: https://github.com/Zenneramaheen/recall-incident-memory

Hindsight: https://github.com/vectorize-io/hindsight

#AI #Python #SoftwareEngineering #IncidentResponse #Hindsight
