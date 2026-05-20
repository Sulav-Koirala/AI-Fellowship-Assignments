import csv
import time
from agent_pipeline import run_text_to_sql

def run_evaluation():
    questions = []
    with open("sql_questions_only.csv", mode="r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row:
                questions.append(row[0].strip())

    total = len(questions)
    if total == 0:
        return

    successful = 0
    retries = 0
    total_latency = 0.0
    results = []

    for idx, question in enumerate(questions, 1):
        print(f"[{idx}/{total}] Running: '{question}'")
        start = time.perf_counter()
        try:
            state = run_text_to_sql(question)
        except Exception as e:
            state = {
                "status": "failed",
                "sql": "N/A",
                "retry_count": 0,
                "error": str(e)
            }
        
        latency = (time.perf_counter() - start) * 1000
        total_latency += latency

        executed = "Yes" if state["status"] == "success" else "No"
        retry = "Yes" if state["retry_count"] > 0 else "No"

        if state["status"] == "success":
            successful += 1
        if state["retry_count"] > 0:
            retries += 1

        results.append({
            "question": question,
            "sql": state["sql"].replace("\n", " ").strip(),
            "executed": executed,
            "retry_needed": retry,
            "status": state["status"].upper(),
            "latency": round(latency, 2)
        })

    success_rate = (successful / total) * 100
    avg_latency = total_latency / total

    with open("evaluation_report.md", "w", encoding="utf-8") as f:
        f.write("# Text-to-SQL Benchmark Evaluation Report\n\n")
        f.write("## Summary Metrics\n")
        f.write(f"- Total Benchmark Questions: {total}\n")
        f.write(f"- SQL Execution Success Rate: {success_rate:.2f}%\n")
        f.write(f"- Total Failed Queries: {total - successful}\n")
        f.write(f"- Total Queries Requiring Auto-Repair: {retries}\n")
        f.write(f"- Average Query Generation Latency: {avg_latency:.2f} ms\n\n")
        f.write("## Detailed Evaluation Output Table\n\n")
        f.write("| Question | Generated SQL | Executed Successfully | Retry Needed | Final Status | Latency (ms) |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in results:
            f.write(f"| {r['question']} | `{r['sql']}` | {r['executed']} | {r['retry_needed']} | {r['status']} | {r['latency']} |\n")

    with open("evaluation_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Question", "Generated SQL", "Executed Successfully", "Retry Needed", "Final Status", "Latency (ms)"])
        for r in results:
            writer.writerow([r["question"], r["sql"], r["executed"], r["retry_needed"], r["status"], r["latency"]])

    print("Evaluation completed successfully.")

if __name__ == "__main__":
    run_evaluation()